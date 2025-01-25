import os
import json
import pickle
import sys
from tqdm import tqdm
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk import sent_tokenize, word_tokenize, pos_tag
from nltk.stem.porter import PorterStemmer
import pandas as pd
import re
import torch
from transformers import BertTokenizer, BertModel
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from googlesearch import search

def get_top_unique_domain_results(keyword, num_results=10, max_domains=30):
    try:
        results = []
        domains = set()
        for url in search(keyword, num_results=20, lang="en", region="us"):
            domain = urlparse(url).netloc
            if domain not in domains:
                domains.add(domain)
                results.append(url)
            if len(results) >= max_domains:
                break
        return results
    except Exception as e:
        print(f"Error during Google search: {e}")
        return []

# Function to extract content from a URL
def extract_content_from_url(url, retries=2, timeout=5):
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/58.0.3029.110 Safari/537.3'
        )
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text() for p in paragraphs]).strip()
                if content:
                    return content
        except requests.RequestException as e:
            print(f"An error occurred while fetching {url}: {e}")
        time.sleep(2)
    return None


########################
#   PREPROCESS UTILS   #
########################

def remove_html_tags(text: str) -> str:
    """
    Removes anything that looks like <tag> from the text.
    This includes multi-character tags like <div id="test">.
    """
    return re.sub(r"<[^>]*>", "", text)

class Config:
    def __init__(self, emb_model="bert-base-uncased"):
        self.EMB_MODEL = emb_model

def deduplicate_phrases(kp_list):
    seen = set()
    out = []
    for kp in kp_list:
        lower_kp = kp.strip().lower()
        if lower_kp in seen:
            continue
        seen.add(lower_kp)
        out.append(kp)
    return out

def vec_vec_dist(vec1, vec2, method='dot'):
    assert len(vec1) == len(vec2), "len(vec1) != len(vec2)"
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    if method == "euc":
        dist = np.linalg.norm(vec1 - vec2)
    elif method == "man":
        d_abs = np.sum(np.abs(vec1 - vec2))
        dist = d_abs if d_abs != 0 else 1e-12
    elif method == "cos":
        dist = vec1.dot(vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)+1e-12)
    else:  # dot
        dist = vec1.dot(vec2)
    return dist

def vec_vec_sim(vec1, vec2, method='dot'):
    val = vec_vec_dist(vec1, vec2, method)
    if method in ['cos','dot']:  # bigger = more similar
        return val
    else:                        # 'man','euc': bigger distance => smaller similarity => 1/dist.
        return 1/(val + 1e-12)

def sent_position(sents_len, max_len):
    doc_sents_lens = []
    offset = 0
    for slen in sents_len:
        if offset + slen >= max_len:
            doc_sents_lens.append((offset, max_len))
            break
        else:
            doc_sents_lens.append((offset, offset+slen))
        offset += slen
    return doc_sents_lens

def compute_embs(doc_embs, start_end_tuple, pooling='max'):
    start_idx, end_idx = start_end_tuple
    if start_idx == end_idx:
        return doc_embs[start_idx]

    embs = np.array(doc_embs[start_idx:end_idx])
    if pooling == 'mean':
        emb_np = np.mean(embs, axis=0)
    else:
        emb_np = np.max(embs, axis=0)
    return emb_np

def position_weight(total_cnt):
    arr = []
    for i in range(1, total_cnt+1):
        arr.append(1.0/i)
    arr = np.array(arr)
    arr = np.exp(arr)
    arr = arr / np.sum(arr)
    return arr

def simple_word_overlap_similarity(expression1, expression2, isstem=True, islower=True, lambda1=0):
    if islower:
        expression1 = expression1.lower()
        expression2 = expression2.lower()
    words1 = expression1.split()
    words2 = expression2.split()
    ps = PorterStemmer()
    if isstem:
        words1 = [ps.stem(w.strip()) for w in words1]
        words2 = [ps.stem(w.strip()) for w in words2]
    intersection = set(words1) & set(words2)
    union = set(words1) | set(words2)
    sim = float(len(intersection))/float(len(union)) if len(union)>0 else 0.0
    return sim if sim >= lambda1 else 0

##################################
#   BERT EMBEDDING-RELATED       #
##################################

def doc_embedding(tokenizer, model, tokens):
    input_tokens = ['[CLS]']
    token_subwords_lens = []
    for token in tokens:
        sub_toks = tokenizer.tokenize(token)
        if len(input_tokens) + len(sub_toks) >= 511:
            break
        input_tokens.extend(sub_toks)
        token_subwords_lens.append(len(sub_toks))
    input_tokens.append("[SEP]")

    input_ids = tokenizer.convert_tokens_to_ids(input_tokens)
    input_ids = torch.LongTensor([input_ids])  # shape (1, seq_len)

    with torch.no_grad():
        outputs = model(input_ids, output_hidden_states=True)
        subwords_embs = outputs.last_hidden_state  # (1, seq_len, 768)
        subwords_embs = subwords_embs.squeeze(0).cpu().numpy()  # shape (seq_len, 768)

    bert_cls_emb = subwords_embs[0]  # [CLS] at position 0

    idx = 1
    tokens_emb = []
    for length in token_subwords_lens:
        if length == 1:
            tokens_emb.append(subwords_embs[idx])
            idx += 1
        else:
            tokens_emb.append(np.mean(subwords_embs[idx:idx+length], axis=0))
            idx += length

    return tokens_emb, bert_cls_emb, bert_cls_emb

def truncate_tokens_to_512(tokens, tokenizer, max_subwords=512):
    input_subwords = ["[CLS]"]
    truncated_tokens = []
    current_subword_count = 1  # Because we have [CLS]

    for word in tokens:
        word_subtoks = tokenizer.tokenize(word)
        if current_subword_count + len(word_subtoks) >= (max_subwords):
            break
        input_subwords.extend(word_subtoks)
        current_subword_count += len(word_subtoks)
        truncated_tokens.append(word)

    return truncated_tokens

def generate_document_embeddings(docs, model_name="bert-base-uncased"):
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)
    model.eval()

    doc_embeddings_list = []

    for doc in tqdm(docs, desc="Generating doc embeddings"):
        tokens_2d = doc["tokens"]
        flattened_tokens = [t for sent in tokens_2d for t in sent]
        truncated_flat_tokens = truncate_tokens_to_512(flattened_tokens, tokenizer, max_subwords=512)

        truncated_2d = [truncated_flat_tokens]
        if "tokens_pos" in doc and len(doc["tokens_pos"]) > 0:
            pos_2d = doc["tokens_pos"]
            flattened_pos = [p for pos_sent in pos_2d for p in pos_sent]
            truncated_flat_pos = flattened_pos[:len(truncated_flat_tokens)]
            truncated_2d_pos = [truncated_flat_pos]
        else:
            truncated_2d_pos = [["NN"] * len(truncated_flat_tokens)]

        tokens_embs, bertcls_emb, cls_token_emb = doc_embedding(tokenizer, model, truncated_flat_tokens)

        outdic = {}
        outdic["d_id"] = doc.get("document_id", "doc_"+str(id(doc)))
        outdic["d_tokens"] = truncated_flat_tokens
        outdic["d_tokens_pos"] = truncated_flat_pos
        outdic["d_keyphrases"] = doc.get("keyphrases", [])
        outdic["d_sents_len"] = [len(t) for t in truncated_2d]
        outdic["d_cls_emb"] = cls_token_emb
        outdic["d_bertcls_emb"] = bertcls_emb
        outdic["d_tokens_embs"] = tokens_embs

        doc_embeddings_list.append(outdic)

    return doc_embeddings_list

########################################
#  SENTENCE & CANDIDATE EMB CALC       #
########################################

def extract_candidates(tokens_tagged, offset=0):
    """
    Using a simple Noun-Phrase chunker. Returns a list of (candidate_string, (start, end)).
    Only candidates with >= 3 words are considered.
    """
    grammar = r"""NP: {<NN.*|JJ>*<NN.*>}"""
    np_parser = nltk.RegexpParser(grammar)
    np_parse_tree = np_parser.parse(tokens_tagged)

    result = []
    for node in np_parse_tree:
        if isinstance(node, nltk.Tree) and node.label() == "NP":
            phrase_tokens = [w for (w, _) in node.leaves()]
            phrase = " ".join(phrase_tokens)
            length = len(node.leaves())

            # Only keep candidates with 3+ words
            if len(phrase_tokens) >= 2:
                result.append((phrase, (offset, offset + length)))

            offset += length
        else:
            offset += 1

    return result

def cans_embeddings(doc_embeddings, can_phrases):
    can_embs_max = []
    can_embs_mean = []
    for phr, (start,end) in can_phrases:
        if end <= start or end > len(doc_embeddings):
            can_embs_max.append(np.zeros(768))
            can_embs_mean.append(np.zeros(768))
            continue
        v_max = compute_embs(doc_embeddings, (start,end), pooling='max')
        v_mean = compute_embs(doc_embeddings, (start,end), pooling='mean')
        can_embs_max.append(v_max)
        can_embs_mean.append(v_mean)
    return can_embs_max, can_embs_mean

def get_sents_embeddings(doc_embeddings, sents_len):
    d_sents_embs_max = []
    d_sents_embs_mean = []
    max_tokens = len(doc_embeddings)
    sents_pos_idx = sent_position(sents_len, max_tokens)
    token_sent_idx = []

    for sidx, (begin,end) in enumerate(sents_pos_idx):
        s_emb = doc_embeddings[begin:end]
        d_sents_embs_max.append(np.max(np.array(s_emb), axis=0))
        d_sents_embs_mean.append(np.mean(np.array(s_emb), axis=0))
        token_sent_idx.extend([sidx]*(end-begin))
    return d_sents_embs_max, d_sents_embs_mean, token_sent_idx

def prepare_word_tags(tokens_1dlist, pos_tags_1dlist):
    stopword_dict = set(stopwords.words('english'))
    tokens_tags = []
    for t, p in zip(tokens_1dlist, pos_tags_1dlist):
        if t.lower() in stopword_dict:
            tokens_tags.append((t, "IN"))
        else:
            tokens_tags.append((t, p))
    return tokens_tags

def extend_cans(doc_cans, can_embs, token2sent_idx):
    porter = PorterStemmer()
    doc_cans_new = []
    used = set()

    max_idx = len(token2sent_idx)

    doc_cans = doc_cans[:len(can_embs)]
    for c_idx, (can, (start,_)) in enumerate(doc_cans):
        if start >= max_idx:
            continue
        if c_idx in used:
            continue

        same_idxs = [c_idx]
        same_sent_positions = [token2sent_idx[start]]
        same_c_positions = [start]

        for c_idx2 in range(c_idx+1, len(doc_cans)):
            if c_idx2 in used:
                continue
            can2, (st2,_) = doc_cans[c_idx2]
            if st2 >= max_idx:
                continue
            if can2.strip().lower() == can.strip().lower():
                same_idxs.append(c_idx2)
                same_sent_positions.append(token2sent_idx[st2])
                same_c_positions.append(st2)

        for j, cid in enumerate(same_idxs):
            cp = doc_cans[cid][0]
            cp_len = len(cp.split())
            doc_cans_new.append((
                cp,
                can_embs[cid],
                cid,
                same_c_positions[j],
                same_sent_positions[j],
                cp_len,
                same_c_positions,
                same_sent_positions
            ))
        used.update(same_idxs)

    return doc_cans_new

def get_sents_cans_embs(docs_embeddings):
    out = []
    for doc in docs_embeddings:
        dic = {}
        doc_tokens_embs = doc['d_tokens_embs']
        dic['d_tokens_cnt'] = len(doc_tokens_embs)
        dic['d_keyphrases'] = doc.get('d_keyphrases', [])
        dic['d_cls_emb'] = doc['d_cls_emb']
        dic['d_bertcls_emb'] = doc['d_bertcls_emb']

        d_emb_max = np.max(np.array(doc_tokens_embs), axis=0)
        d_emb_mean = np.mean(np.array(doc_tokens_embs), axis=0)
        dic['d_emb'] = (d_emb_max, d_emb_mean)

        s_len = doc['d_sents_len']
        first_len = s_len[0] if len(s_len)>0 else len(doc_tokens_embs)
        d_emb_t_max = np.max(np.array(doc_tokens_embs[:first_len]), axis=0)
        d_emb_t_mean = np.mean(np.array(doc_tokens_embs[:first_len]), axis=0)
        dic['d_emb_t'] = (d_emb_t_max, d_emb_t_mean)

        d_sents_embs_max, d_sents_embs_mean, token2sent_idx = get_sents_embeddings(doc_tokens_embs, s_len)
        dic['d_sent_embs'] = (d_sents_embs_max, d_sents_embs_mean)

        doc_tokens = doc['d_tokens']
        doc_pos = doc['d_tokens_pos']
        doc_tokens_tags = prepare_word_tags(doc_tokens, doc_pos)
        doc_cans = extract_candidates(doc_tokens_tags)
        d_can_embs_max, d_can_embs_mean = cans_embeddings(doc_tokens_embs, doc_cans)

        d_can_author_max = extend_cans(doc_cans, d_can_embs_max, token2sent_idx)
        d_can_author_mean = extend_cans(doc_cans, d_can_embs_mean, token2sent_idx)
        dic['d_can_author'] = (d_can_author_max, d_can_author_mean)

        all_c_embs = []
        for v in d_can_embs_max:
            all_c_embs.append(v)
        if len(all_c_embs)>0:
            embedrank_max = np.max(np.array(all_c_embs), axis=0)
            embedrank_mean = np.mean(np.array(all_c_embs), axis=0)
        else:
            embedrank_max = d_emb_max
            embedrank_mean = d_emb_mean
        dic['d_emb_embedrank'] = (embedrank_max, embedrank_mean)

        out.append(dic)
    return out

def build_data_structure(docs_feats, pooling='max'):
    pool_idx = {"max":0,"mean":1}
    p_idx = pool_idx[pooling]

    data_dict_lst = []
    for doc_feats in tqdm(docs_feats, desc="Building data for ranker"):
        d_emb_cls = doc_feats['d_cls_emb']
        d_emb_bertcls = doc_feats['d_bertcls_emb']
        d_emb = doc_feats['d_emb']
        d_emb_t = doc_feats['d_emb_t']
        d_emb_erank = doc_feats.get('d_emb_embedrank',(d_emb[0],d_emb[1]))
        d_sents_embs = doc_feats['d_sent_embs']

        d_can = doc_feats['d_can_author'][p_idx]
        cp, can_embs, _, _, _, _, _, _ = list(zip(*d_can)) if len(d_can)>0 else ([],[],[],[],[],[],[],[])

        datas_dict = {}
        datas_dict['cnt_can'] = len(d_can)
        datas_dict['cnt_sent'] = len(d_sents_embs[0])
        datas_dict['cans'] = d_can
        datas_dict['keyphrases'] = doc_feats['d_keyphrases']

        datas_dict['doc_embs'] = {
            'cls': d_emb_cls,
            'pool_max': d_emb[0],
            'pool_mean': d_emb[1],
            't_max': d_emb_t[0],
            't_mean': d_emb_t[1],
            'erank_max': d_emb_erank[0],
            'erank_mean': d_emb_erank[1]
        }
        datas_dict['can_embs'] = can_embs
        datas_dict['sent_embs'] = d_sents_embs

        datas_dict['can_pos_w'] = position_weight(len(d_can)) if len(d_can)>0 else []
        datas_dict['word_pos_w'] = position_weight(doc_feats['d_tokens_cnt'])
        datas_dict['sent_pos_w'] = position_weight(datas_dict['cnt_sent'])

        data_dict_lst.append(datas_dict)
    return data_dict_lst

######################################
#   Minimal Ranker (CentralityRank)  #
######################################

class DirectedCentralityRank(object):
    def __init__(self, doc_feats):
        self.doc_feats = doc_feats
        self.can_embs = doc_feats['can_embs']
        self.cans = doc_feats['cans']
        self.can_pos_w = doc_feats['can_pos_w']
        self.word_pos_w = doc_feats['word_pos_w']
        self.sent_pos_w = doc_feats['sent_pos_w']
        self.doc_embs = doc_feats['doc_embs']

    def rank(self):
        if len(self.cans)==0:
            return []
        doc_cls = self.doc_feats['doc_embs']['cls']
        scores = []
        for i, ctuple in enumerate(self.cans):
            phrase_str = ctuple[0]
            emb = self.can_embs[i]
            sim = vec_vec_sim(doc_cls, emb, 'dot')
            pos_w = self.can_pos_w[i] if i < len(self.can_pos_w) else 1.0
            final_score = sim * pos_w
            scores.append((phrase_str, final_score))
        scores.sort(key=lambda x:x[1], reverse=True)
        result = []
        seen = set()
        for (ph, sc) in scores:
            low = ph.lower()
            if low in seen:
                continue
            seen.add(low)
            result.append(ph)
        return result

def run_ranker(data_dict_lst):
    all_results = []
    for doc_feats in data_dict_lst:
        ranker = DirectedCentralityRank(doc_feats)
        preds = ranker.rank()
        all_results.append(preds)
    return all_results

########################################
#  End-to-end keyphrase extraction     #
########################################

def preprocess_texts(raw_texts):
    nltk_stopwords = set(stopwords.words("english"))
    docs = []
    for i, text in enumerate(raw_texts):
        cleaned_text = remove_html_tags(text)
        sents = sent_tokenize(cleaned_text)
        tokenized_sents = []
        pos_sents = []
        for s in sents:
            words = word_tokenize(s)
            tagged = pos_tag(words)
            tokenized_sents.append([w for (w,p) in tagged])
            pos_sents.append([p for (w,p) in tagged])

        doc_dict = {
            "document_id": f"doc_{i}",
            "tokens": tokenized_sents,
            "tokens_pos": pos_sents,
            "keyphrases": []
        }
        docs.append(doc_dict)
    return docs

def extract_keyphrases_from_texts(raw_texts, model_name="bert-base-uncased", pooling='max'):
    doc_dicts = preprocess_texts(raw_texts)
    doc_embs = generate_document_embeddings(doc_dicts, model_name=model_name)
    docs_feats = get_sents_cans_embs(doc_embs)
    data_dict_lst = build_data_structure(docs_feats, pooling=pooling)
    all_predictions = run_ranker(data_dict_lst)
    return all_predictions

