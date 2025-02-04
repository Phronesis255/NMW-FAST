# backend/main.py
from typing import List, Dict, Optional, Any
import time
import re
import math
import string
from urllib.parse import urlparse, urljoin
import ssl
import base64
import difflib

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
from googlesearch import search
from transformers import pipeline
from transformers.pipelines import QuestionAnsweringPipeline

from sentence_transformers import SentenceTransformer, util
from sklearn.cluster import AgglomerativeClustering
import os
import operator

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
import logging
from generator import create_blog_post, llm
import sqlite3
import json  # [ADDED]
# main.py
from hcuke import extract_keyphrases_from_texts

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

CURRENT_USER_KEYWORD: str = ""

from dotenv import load_dotenv
load_dotenv()  # This will read .env file in the current directory

import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Load SpaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    from spacy.cli import download
    download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

origins = [
    "http://localhost:5173",  # Our frontend app runs here
    "http://localhost:8000",  # For testing directly with the backend server
    "http://127.0.0.1:5173", # Also allow localhost on port 5173
    "https://ominous-space-meme-9qvp7w6xwpw37r49-5173.app.github.dev"    
]
DATABASE_PATH = "analysis_data.db"
CHUNK_GRAMMAR = r"""
  NP: {<JJ.*>*<NN.*>+}
"""
chunk_parser = nltk.RegexpParser(CHUNK_GRAMMAR)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of allowed origins
    allow_origin_regex=r"https://.*\.app\.github\.dev$",    
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Enable CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embedding model (HuggingFace SentenceTransformer)
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Error loading embedding model: {e}")
    embedding_model = None

class GenerateArticleInput(BaseModel):
    keyword: str
    title: str

class AnalysisResponse(BaseModel):
    titles: List[str]
    urls: List[str]
    favicons: List[str]
    word_counts: List[int]
    headings_data: List[Dict]
    tfidf_terms: List[Dict]  # Include terms with their scores
    ideal_word_count: Optional[int] = 1000
    top_terms: Optional[List[str]] = None  # add this
    long_tail_keywords: List[Dict] = []


class AnalysisInput(BaseModel):
    keyword: str

def get_db_connection():
    return sqlite3.connect("analysis_data.db")

def fetch_cached_analysis(keyword: str) -> Optional[AnalysisResponse]:
    """
    Returns an AnalysisResponse if found in analysis_cache table,
    plus retrieves data from tfidf_data and headings_data.
    Otherwise, returns None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1) Check analysis_cache
    cursor.execute("SELECT response_json FROM analysis_cache WHERE keyword = ?", (keyword,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None  # Not cached

    # 2) We have JSON in analysis_cache
    cached_json_str = row[0]
    cached_data = json.loads(cached_json_str)

    # 3) Also retrieve TF-IDF from tfidf_data
    cursor.execute("""
        SELECT term, tf, tfidf, max_tf 
        FROM tfidf_data
        WHERE keyword = ?
        ORDER BY tf DESC
        LIMIT 50
    """, (keyword,))
    tfidf_rows = cursor.fetchall()

    # Rebuild tfidf_terms from these rows
    tfidf_terms = []
    top_terms = []
    for (term, tf_val, tfidf_val, max_tf_val) in tfidf_rows:
        tfidf_terms.append({
            "word": term,
            "tf_score": tf_val,
            "tfidf_score": tfidf_val,
            "max_tf": max_tf_val
        })
        top_terms.append(term)

    # 4) Retrieve headings from headings_data
    cursor.execute("""
        SELECT heading_text, heading_url, heading_title
        FROM headings_data
        WHERE keyword = ?
    """, (keyword,))
    heading_rows = cursor.fetchall()
    headings_data = []
    for (h_text, h_url, h_title) in heading_rows:
        headings_data.append({
            "text": h_text,
            "url": h_url,
            "title": h_title
        })

    conn.close()

    # 5) Rebuild final AnalysisResponse
    cached_data["tfidf_terms"] = tfidf_terms
    cached_data["headings_data"] = headings_data
    cached_data["top_terms"] = top_terms

    return AnalysisResponse(**cached_data)

def store_analysis_in_db(keyword: str, analysis: AnalysisResponse):
    """
    1) Insert the entire analysis JSON into analysis_cache
    2) Insert each TF-IDF item into tfidf_data
    3) Insert each heading into headings_data
    4) Insert each long-tail keyword into long_tail_keywords
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1) Store JSON in analysis_cache (analysis_cache has columns: keyword, response_json, updated_at)
    analysis_dict = analysis.dict()
    json_str = json.dumps(analysis_dict)

    cursor.execute(
        """
        INSERT OR REPLACE INTO analysis_cache (keyword, response_json, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
        (keyword, json_str)
    )

    # 2) Insert tfidf_data (tfidf_data has columns: keyword, term, tf, tfidf, max_tf)
    cursor.execute("DELETE FROM tfidf_data WHERE keyword = ?", (keyword,))
    for item in analysis.tfidf_terms:
        cursor.execute(
            """
            INSERT INTO tfidf_data (keyword, term, tf, tfidf, max_tf)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                keyword,
                item["word"],
                item["tf_score"],
                item["tfidf_score"],
                item["max_tf"]
            )
        )
    print("Passed this point")
    # 3) Insert headings_data (headings_data has columns: keyword, heading_text, heading_url, heading_title)
    cursor.execute("DELETE FROM headings_data WHERE keyword = ?", (keyword,))
    for heading in analysis.headings_data:
        cursor.execute(
            """
            INSERT INTO headings_data (keyword, heading_text, heading_url, heading_title)
            VALUES (?, ?, ?, ?)
            """,
            (
                keyword,
                heading["text"],
                heading["url"],
                heading["title"]
            )
        )

    # 4) Insert long_tail_keywords (you'll need a matching table schema, e.g.):
    #    CREATE TABLE IF NOT EXISTS long_tail_keywords (
    #        id INTEGER PRIMARY KEY AUTOINCREMENT,
    #        keyword TEXT,
    #        keyphrase TEXT,
    #        relevance_score REAL,
    #        frequency INTEGER,
    #        kw_length INTEGER,
    #        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #    );

    cursor.execute("DELETE FROM long_tail_keywords WHERE keyword = ?", (keyword,))
    if hasattr(analysis, "long_tail_keywords") and analysis.long_tail_keywords:
        for lt in analysis.long_tail_keywords:
            cursor.execute(
                """
                INSERT INTO long_tail_keywords (keyword, keyphrase, relevance_score, frequency, kw_length)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    keyword,
                    lt["keyword"],         # e.g. "best running shoes for men"
                    lt["relevanceScore"],  # e.g. 0.8732
                    lt["frequency"],       # e.g. 3
                    lt["kwLength"]         # e.g. 5
                )
            )

    conn.commit()
    conn.close()

def google_custom_search(query, api_key, cse_id, num_results=10, delay=1): # Added delay parameter
    """Performs Google Custom Search with rate limiting."""
    if not api_key:
        api_key = os.getenv("CSE_API")
    if not cse_id:
        cse_id = os.getenv("CSE_ID")

    all_results = []
    start_index = 1
    while len(all_results) < num_results:
      remaining_results = num_results - len(all_results)
      current_num = min(10, remaining_results)
      url = "https://customsearch.googleapis.com/customsearch/v1"
      params = {
          'q': query,
          'key': api_key,
          'cx': cse_id,
          'num': current_num,
          'start': start_index
      }
      try:
          response = requests.get(url, params=params)
          response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
          data = response.json()
          items = data.get('items', [])
          if not items:
            break
          all_results.extend(items)
          start_index += current_num
          time.sleep(delay)  # Introduce a delay between requests
      except requests.exceptions.RequestException as e:
          if response.status_code == 429: # Check if it's a rate limit error
              print("Rate limit exceeded. Retrying in 60 seconds...")
              time.sleep(120) # Wait 60 seconds before retrying
              continue # Retry the current request
          else:
              print(f"Error: {e}")
              if response.text:
                print(response.text)
              return []
    return all_results

@app.post("/api/generate-article")
def generate_article(input_data: GenerateArticleInput):
    keyword = input_data.keyword
    title = input_data.title

    try:
        # Generate the blog post
        output_file = "generated_blog_post.md"
        outline_id = create_blog_post(llm=llm, keyword=keyword, title=title, output_file=output_file)
        print(outline_id)
        # Read the generated blog post content
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        conn = sqlite3.connect('generator.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT final_blog_post_length, total_generation_time, llm_model,
                similarity_to_title, reading_difficulty_grade, keyword_density, gunning_fog
            FROM blog_posts
            WHERE outline_id = ?
            ORDER BY rowid DESC
            LIMIT 1
        ''', (outline_id,))
        row = cursor.fetchone()
        conn.close()

        # Convert row to a dictionary
        if row is not None:
            metrics = {
                "final_blog_post_length": row[0],
                "total_generation_time": row[1],
                "model_name": row[2],
                "similarity_to_title": row[3],
                "reading_difficulty_grade": row[4],
                "keyword_density": row[5],
                "gunning_fog": row[6],
            }
        else:
            metrics = {}

        return {
            "message": f"Article '{title}' generated successfully with keyword '{keyword}'.",
            "content": content,
            "metrics": metrics,
        }

    except Exception as e:
        logging.error(f"Error generating article: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Function to remove duplicate questions
def remove_duplicate_questions(questions, similarity_threshold=0.75):
    if not embedding_model:
        return questions

    # Preprocess questions
    def preprocess(text):
        # Lowercase, remove punctuation
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text

    preprocessed_questions = [preprocess(q) for q in questions]

    # Encode questions using SentenceTransformer
    embeddings = embedding_model.encode(preprocessed_questions)

    # Compute cosine similarity matrix
    similarity_matrix = cosine_similarity(embeddings)

    # Cluster questions
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        affinity='precomputed',
        linkage='complete',
        distance_threshold=1 - similarity_threshold
    )
    clustering_model.fit(1 - similarity_matrix)  # Convert similarity to distance

    cluster_labels = clustering_model.labels_

    # Select a representative question from each cluster
    cluster_to_questions = {}
    for idx, label in enumerate(cluster_labels):
        if label not in cluster_to_questions:
            cluster_to_questions[label] = [questions[idx]]
        else:
            cluster_to_questions[label].append(questions[idx])

    representative_questions = []
    for cluster_questions in cluster_to_questions.values():
        representative = min(cluster_questions, key=len)
        representative_questions.append(representative)

    return representative_questions

# Function to extract content from a URL with retries and user-agent header
def extract_content_from_url(url, extract_headings=False, retries=2, timeout=5):
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
                title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
                headings = []
                if extract_headings:
                    for level in ['h2', 'h3', 'h4']:
                        for tag in soup.find_all(level):
                            headings.append({'level': level, 'text': tag.get_text(strip=True)})
                # Extract favicon
                icon_link = soup.find('link', rel=lambda x: x and ('icon' in x.lower()))
                if icon_link and icon_link.get('href'):
                    favicon_url = urljoin(url, icon_link['href'])
                else:
                    # Default to /favicon.ico
                    favicon_url = urljoin(url, '/favicon.ico')

                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text() for p in paragraphs])
                return title, content.strip(), favicon_url, headings
            else:
                return None, "", "", None
        except requests.RequestException:
            pass
        time.sleep(2)
    return None, "", "", None

# Function to get top unique domain results for a keyword (more than 10 URLs)
def get_top_unique_domain_results(keyword, num_results=50, max_domains=50):
    try:
        results = []
        domains = set()
        for url in search(keyword, num_results=num_results, lang="en"):
            domain = urlparse(url).netloc
            if domain not in domains and "refact.co" not in domain:
                print(domain)
                domains.add(domain)
                results.append(url)
            if len(results) >= max_domains:
                break
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during Google search: {e}")

# Function to lemmatize text
def lemmatize_text(text):
    doc = nlp(text)
    lemmatized_tokens = []
    for token in doc:
        # Context-aware overrides for specific terms
        if token.text.lower() == "media" and token.lemma_.lower() == "medium":
            lemmatized_tokens.append("media")
        elif token.text.lower() == "data" and token.lemma_.lower() == "datum":
            lemmatized_tokens.append("data")
        elif token.text.lower() == "publishers" and token.lemma_.lower() == "publisher":
            lemmatized_tokens.append("publisher")
        else:
            lemmatized_tokens.append(token.lemma_)
    return ' '.join(lemmatized_tokens)

def filter_terms(terms):
    custom_stopwords = set(["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "way", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "like", "need"])

    filtered_terms = []
    for term in terms:
        # Exclude terms that contain numbers
        if any(char.isdigit() for char in term):
            continue
        doc = nlp(term)
        # Exclude terms that have undesired POS tags
        if any(token.pos_ in ['AUX', 'PRON', 'DET', 'ADP', 'CCONJ', 'NUM', 'SYM', 'PUNCT'] for token in doc):
            continue
        # Use lemmatization and check for stopwords
        lemma_tokens = [token.lemma_.lower() for token in doc]
        if any(token in custom_stopwords or token in nlp.Defaults.stop_words for token in lemma_tokens):
            continue
        lemma = ' '.join(lemma_tokens)
        filtered_terms.append(lemma)
    return filtered_terms

#
# Replaced GloVe-based compute_embedding and get_sentence_embedding
# with a HuggingFace SentenceTransformer approach:
#
def compute_embedding(text):
    """
    Returns an embedding vector from the HuggingFace SentenceTransformer model.
    """
    if not embedding_model:
        return None
    # Encode the text as a single string, return first (and only) embedding
    return embedding_model.encode([text], convert_to_numpy=True)[0]

def get_sentence_embedding(sentence):
    """
    Returns an embedding vector for a single sentence from the
    HuggingFace SentenceTransformer model.
    """
    if not embedding_model:
        # Fallback: return an all-zero vector of a typical dimension
        # for 'all-MiniLM-L6-v2' (384 dims)
        return np.zeros(384)
    return embedding_model.encode([sentence], convert_to_numpy=True)[0]


def extract_brand_name(url, title):
    # Extract the domain name
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    
    if domain_parts and domain_parts[0] == 'www':
        domain_parts.pop(0)

    domain_root = domain_parts[0].capitalize() if domain_parts else "Unknown"

    if title:
        title_parts = title.split(' - ')
        for part in reversed(title_parts):
            ratio = difflib.SequenceMatcher(None, domain_root.lower(), part.lower()).ratio()
            if ratio > 0.8:
                return part.strip()

    return domain_root

def is_brand_mentioned(term, brand_name):
    if brand_name.lower() in term.lower():
        return True

    ratio = difflib.SequenceMatcher(None, term.lower().replace(' ', ''), brand_name.lower().replace(' ', '')).ratio()
    if ratio > 0.8:
        return True

    doc = nlp(term)
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PRODUCT', 'PERSON', 'GPE']:
            ratio_ent = difflib.SequenceMatcher(None, ent.text.lower().replace(' ', ''), brand_name.lower().replace(' ', '')).ratio()
            if ratio_ent > 0.8:
                return True

    return False

def is_not_branded(question, brands):
    for brand in brands:
        if is_brand_mentioned(question, brand):
            return False
    return True


# Initialize the embedding model (ensure this is the same as used previously)
# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# RAKE and supporting functions (as provided)

def is_noun_phrase(phrase: str, min_tokens: int = 2) -> bool:
    tokens = nltk.word_tokenize(phrase)
    if len(tokens) < min_tokens:
        return False
    tagged = nltk.pos_tag(tokens)
    tree = chunk_parser.parse(tagged)
    return (len(tree) == 1 and isinstance(tree[0], nltk.Tree) and
            tree[0].label() == 'NP' and len(tree[0].leaves()) == len(tokens))

def load_stop_words(stop_words_file_path: str) -> list:
    with open(stop_words_file_path) as file:
        return [word for line in file if not line.strip().startswith("#") 
                for word in line.split()]

def build_stop_word_regex(stop_words_file_path: str) -> re.Pattern:
    stop_words = load_stop_words(stop_words_file_path)
    regex_list = [r'\b' + re.escape(word) + r'(?![\w-])' for word in stop_words]
    return re.compile('|'.join(regex_list), re.IGNORECASE)

class RAKE:
    def __init__(self, stop_words_file: str = 'SmartStoplist.txt'):
        self.stop_words_pattern = build_stop_word_regex(stop_words_file)

    def exec(self, text: str):
        sentences = self.split_sentences(text)
        phrases = self.generate_candidate_keywords(sentences)
        word_scores = self.calculate_word_scores(phrases)
        keyword_candidates = self.generate_candidate_keyword_scores(phrases, word_scores)
        return sorted(keyword_candidates.items(), key=operator.itemgetter(1), reverse=True)

    def split_sentences(self, text: str) -> list:
        return re.split(u'[.!?,;:\t\\\\"\\(\\)\\\'\u2019\u2013]|\\s\\-\\s', text)

    def generate_candidate_keywords(self, sentences: list) -> list:
        phrases = []
        for sentence in sentences:
            parts = re.sub(self.stop_words_pattern, '|', sentence.strip()).split('|')
            for phrase in parts:
                phrase = phrase.strip().lower()
                if phrase and is_noun_phrase(phrase):
                    phrases.append(phrase)
        return phrases

    def is_number(self, s: str) -> bool:
        try:
            float(s) if '.' in s else int(s)
            return True
        except ValueError:
            return False

    def separate_words(self, text: str, word_min_size: int = 0) -> list:
        words = re.split('[^a-zA-Z0-9_\\+\\-/]', text)
        return [word.lower() for word in words if len(word) > word_min_size and not self.is_number(word)]

    def calculate_word_scores(self, phrases: list) -> dict:
        word_freq, word_degree = {}, {}
        for phrase in phrases:
            words = self.separate_words(phrase)
            degree = len(words) - 1
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
                word_degree[word] = word_degree.get(word, 0) + degree
        return {word: (word_degree[word] + word_freq[word]) / word_freq[word] for word in word_freq}

    def generate_candidate_keyword_scores(self, phrases: list, word_scores: dict) -> dict:
        candidates = {}
        for phrase in phrases:
            candidates[phrase] = sum(word_scores[word] for word in self.separate_words(phrase))
        return candidates

def get_keyphrases(user_query: str, raw_texts: List[str]) -> Dict[str, Any]:
    # 1) Extract keyphrases using RAKE + TF-IDF
    tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 5), stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(raw_texts)
    features = tfidf_vectorizer.get_feature_names_out()
    
    all_keyphrases_data = {}  # phrase: max overall score
    
    for i, doc_text in enumerate(raw_texts):
        rake_obj = RAKE()
        rake_results = rake_obj.exec(doc_text)
        
        doc_vector = tfidf_matrix[i]
        doc_tfidf_dict = {feature: doc_vector[0, idx] for idx, feature in enumerate(features)}
        
        seen_phrases = set()
        for phrase, rake_score in rake_results:
            if phrase in seen_phrases:
                continue
            seen_phrases.add(phrase)
            
            phrase_tfidf = doc_tfidf_dict.get(phrase, 0.0)
            
            if (rake_score + phrase_tfidf) == 0:
                overall_score = 0.0
            else:
                overall_score = 2 * (rake_score * phrase_tfidf) / (rake_score + phrase_tfidf) * 10
            
            if phrase not in all_keyphrases_data or overall_score > all_keyphrases_data[phrase]:
                all_keyphrases_data[phrase] = overall_score
    
    # Get top 100 phrases by overall score
    sorted_phrases = sorted(all_keyphrases_data.items(), key=lambda x: x[1], reverse=True)[:100]
    top_phrases = [phrase for phrase, _ in sorted_phrases]
    all_keyphrases = [top_phrases]  # Format to match existing structure
    
    # 2) Flatten the list of lists
    flattened_all_keyphrases = [kp for sublist in all_keyphrases for kp in sublist]
    
    # 3) Build frequency dict
    combined_text = " ".join(raw_texts).lower()
    frequency_dict = {kp: combined_text.count(kp.lower()) for kp in flattened_all_keyphrases}
    
    # 4) Compute similarity to user query
    user_query_embedding = embedding_model.encode([user_query], convert_to_numpy=True)
    keyphrase_embeddings = embedding_model.encode(flattened_all_keyphrases, convert_to_numpy=True)
    similarity_scores = util.cos_sim(user_query_embedding, keyphrase_embeddings)[0]
    
    # 5) Build keyphrase objects
    seen_keyphrases = set()
    keyphrase_objects = []
    for i, kp in enumerate(flattened_all_keyphrases):
        sim = float(similarity_scores[i])
        if sim >= 0.5 and kp not in seen_keyphrases:
            keyphrase_objects.append({
                "keyword": kp,
                "relevanceScore": round(sim, 4),
                "frequency": frequency_dict.get(kp, 0),
                "kwLength": len(kp.split()),
                "similarity": round(sim, 4),
            })
            seen_keyphrases.add(kp)
    
    # 6) Sort by similarity descending
    keyphrase_objects.sort(key=lambda x: x["similarity"], reverse=True)
    
    return {
        "keyphrases": keyphrase_objects,
        "count": len(keyphrase_objects)
    }

@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_keyword(input_data: AnalysisInput):
    global CURRENT_USER_KEYWORD

    keyword = input_data.keyword
    CURRENT_USER_KEYWORD = keyword  # <-- store in global variable

    cached = fetch_cached_analysis(keyword)
    if cached:
        print(f"[DEBUG] Returning cached results for '{keyword}' from DB.")
        return cached

    start_time = time.time()
    print(f'Starting Analysis of Keyword: {keyword} ...')
    api_key = os.getenv("CSE_API")
    cse_id = os.getenv("CSE_ID")
    search_items = google_custom_search(query=keyword, num_results=15, api_key=api_key, cse_id=cse_id,delay=0.5)
    if not search_items:
        raise HTTPException(status_code=404, detail='No results found from custom search.')

    top_urls = [item['link'] for item in search_items if 'link' in item]
    if not top_urls:
        raise HTTPException(status_code=404, detail='No URLs found in the custom search results.')

    # Initialize lists to store data
    titles = []
    urls = []
    favicons = []
    retrieved_content = []
    successful_urls = []
    word_counts = []
    max_contents = 15
    headings_data = []
    brand_names = set()  # To store unique brand names

    for idx, url in enumerate(top_urls):
        print(f"Retrieving content from {url}...")
        title, content, favicon_url, headings = extract_content_from_url(url, extract_headings=True)
        time.sleep(0.5)  # To limit the number of requests per second
        if title is None:
            title = "No Title"

        brand_name = extract_brand_name(url, title)
        brand_names.add(brand_name)

        if headings and isinstance(headings, list):
            for heading in headings:
                if isinstance(heading, dict) and 'text' in heading:
                    headings_data.append({
                        'text': heading['text'].strip(),
                        'url': url,
                        'title': title
                    })

        if content:
            word_count = len(content.split())
            if len(retrieved_content) < max_contents:
                retrieved_content.append(content)
                successful_urls.append(url)
                titles.append(title)
                favicons.append(favicon_url)
                if word_count > 1000:
                    word_counts.append(word_count)
                else:
                    word_counts.append(1000)
            else:
                break
        time.sleep(0.5)
        if len(retrieved_content) >= max_contents:
            break

    if len(retrieved_content) < max_contents:
        print(f"Only retrieved {len(retrieved_content)} out of {max_contents} required contents.")

    if not retrieved_content:
        raise HTTPException(status_code=404, detail='Failed to retrieve sufficient content from the URLs.')

    print(f"Completed content retrieval. {len(retrieved_content)} contents retrieved.")

    documents = retrieved_content

    # Lemmatize the documents
    documents_lemmatized = [lemmatize_text(doc) for doc in documents]

    if headings_data:
        print("Processing headings...")
        question_words = ['how', 'why', 'what', 'who', 'which', 'is', 'are', 'can', 'does', 'will']
        filtered_headings_data = [
            heading for heading in headings_data
            if (heading['text'].endswith('?') or
                (heading['text'].split() and heading['text'].split()[0].lower() in question_words))
        ]

        # Remove duplicates based on both text and URL
        filtered_headings_data = list({(heading['text'], heading['url'], heading.get('title', 'No Title')) for heading in filtered_headings_data})
        filtered_headings_data = [
            {'text': text, 'url': url, 'title': title}
            for text, url, title in filtered_headings_data
        ]

        if filtered_headings_data:
            
            # Encode keyword and headings
            keyword_embedding = embedding_model.encode(keyword, convert_to_tensor=True)
            headings_texts = [heading['text'] for heading in filtered_headings_data]
            headings_embeddings = embedding_model.encode(headings_texts, convert_to_tensor=True)
            
            # Calculate similarities between keyword and headings
            similarities = util.cos_sim(keyword_embedding, headings_embeddings)
            
            # Filter headings with similarity > 0.65
            filtered_headings_data = [
                heading for idx, heading in enumerate(filtered_headings_data)
                if similarities[0][idx].item() > 0.65
            ]
        print("Headings data processed successfully")
    else:
        filtered_headings_data = []
        print('No headings were extracted')

    tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 3))
    tf_vectorizer = CountVectorizer(ngram_range=(1, 3))

    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_lemmatized).toarray()
    tf_matrix = tf_vectorizer.fit_transform(documents_lemmatized).toarray()

    feature_names = tfidf_vectorizer.get_feature_names_out()

    # Filter feature names
    filtered_feature_names = filter_terms(feature_names)
    filtered_indices = [i for i, term in enumerate(feature_names) if term in filtered_feature_names]
    tfidf_matrix_filtered = tfidf_matrix[:, filtered_indices]
    tf_matrix_filtered = tf_matrix[:, filtered_indices]

    filtered_feature_names = [feature_names[i] for i in filtered_indices]

    avg_tfidf_scores = np.mean(tfidf_matrix_filtered, axis=0)
    avg_tf_scores = np.mean(tf_matrix_filtered, axis=0)
    max_tf_scores = np.max(tf_matrix_filtered, axis=0)

    word_counts_per_doc = [len(doc.split()) for doc in documents_lemmatized]
    average_doc_length = float(sum(word_counts_per_doc)) / max(1, len(word_counts_per_doc))

    # Normalize
    avg_tfidf_scores = avg_tfidf_scores.astype(float) / average_doc_length
    avg_tf_scores = avg_tf_scores.astype(float) / average_doc_length
    max_tf_scores = max_tf_scores.astype(float) / average_doc_length

    term_scores = {
        term: {
            "tfidf": avg_tfidf_scores[i],
            "tf": avg_tf_scores[i],
            "max_tf_score": float(max_tf_scores[i])
        }
        for i, term in enumerate(filtered_feature_names)
    }
    top_terms = sorted(term_scores, key=lambda t: term_scores[t]["tf"], reverse=True)[:50]

    tfidf_terms = [
        {
            "word": term,
            "tfidf_score": term_scores[term]["tfidf"],
            "tf_score": term_scores[term]["tf"],
            "max_tf": term_scores[term]["max_tf_score"]
        }
        for term in top_terms
    ]
    long_tail_data = get_keyphrases(keyword, retrieved_content)
    ideal_word_count = int(np.median(word_counts)) + 500 if word_counts else 1000

    elapsed_time = time.time() - start_time
    print(f"Time taken for Analysis Endpoint: {elapsed_time:.2f} seconds")

    final_response = AnalysisResponse(
        titles=titles,
        urls=successful_urls,
        favicons=favicons,
        word_counts=word_counts,
        headings_data=filtered_headings_data,
        top_terms=top_terms,
        tfidf_terms=tfidf_terms,
        ideal_word_count=ideal_word_count,
        long_tail_keywords = long_tail_data["keyphrases"]

    )

    # [ADDED] Save to DB
    store_analysis_in_db(keyword, final_response)

    return final_response

class EditorContent(BaseModel):
    content: str

@app.post("/api/save-content")
async def save_content(content: EditorContent):
    try:
        # Here you would typically save the content to a database
        return {"message": "Content saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
