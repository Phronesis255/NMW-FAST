# backend/main.py
from typing import List, Dict, Optional
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

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
# import logging
# logging.basicConfig(level=logging.DEBUG)
from fastapi.middleware.cors import CORSMiddleware


try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


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
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
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

# Load embedding model
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Error loading embedding model: {e}")
    embedding_model = None

# Load GloVe embeddings
try:
    glove_embeddings_index = {}
    file_path='glove.6B.100d.txt'
    with open(file_path, 'r', encoding='utf8') as f:
        for line in f:
            values = line.split()
            word = values[0]
            coefs = np.asarray(values[1:], dtype='float32')
            glove_embeddings_index[word] = coefs
except Exception as e:
    print(f"Error loading Glove model: {e}")
    glove_embeddings_index = {}

class GenerateArticleInput(BaseModel):
    keyword: str
    title: str

@app.post("/api/generate-article")
def generate_article(input_data: GenerateArticleInput):
    keyword = input_data.keyword
    title = input_data.title

    try:
        # Generate the blog post
        output_file = "generated_blog_post.md"
        create_blog_post(llm=llm, keyword=keyword, title=title, output_file=output_file)

        # Read the generated blog post content
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        return {"message": f"Article '{title}' generated successfully with keyword '{keyword}'.", "content": content}
    except Exception as e:
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

    # For each cluster, select the shortest question as representative
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
                # Return None for content if status code is not 200
                return None, "", "", None
        except requests.RequestException:
            # Continue to next attempt
            pass
        time.sleep(2)  # Wait before retrying
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
    # Your lemmatization code
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


# Function to filter out value-less terms and custom stopwords
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
        # Use lemmatization and check for stopwords and custom stopwords
        lemma_tokens = [token.lemma_.lower() for token in doc]
        # Exclude terms if any token is a stopword or in custom stopwords
        if any(token in custom_stopwords or token in nlp.Defaults.stop_words for token in lemma_tokens):
            continue
        lemma = ' '.join(lemma_tokens)
        filtered_terms.append(lemma)
    return filtered_terms


def compute_embedding(text):
    if not glove_embeddings_index:
       return None

    words = text.lower().split()
    embeddings = []
    for word in words:
        if word in glove_embeddings_index:
            embeddings.append(glove_embeddings_index[word])
    if embeddings:
        return np.mean(embeddings, axis=0)
    else:
        return None

def get_sentence_embedding(sentence):
    if not glove_embeddings_index:
       return np.zeros(100) #Assuming 100 dimensional embeddings

    words = sentence.lower().split()
    embeddings = [glove_embeddings_index[word] for word in words if word in glove_embeddings_index]
    if embeddings:
        sentence_embedding = np.mean(embeddings, axis=0)
    else:
        sentence_embedding = np.zeros(100)  # Assuming 100-dimensional embeddings
    return sentence_embedding

def extract_brand_name(url, title):
    # Extract the domain name
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    
    # Remove common prefixes (e.g., 'www')
    if domain_parts[0] == 'www':
        domain_parts.pop(0)

    # Take the root domain (e.g., 'lawruler' from 'lawruler.com')
    domain_root = domain_parts[0].capitalize()

    # Attempt to extract the brand name from the title
    if title:
        # Split title into parts (e.g., "Client Intake Software - Law Ruler")
        title_parts = title.split(' - ')
        for part in reversed(title_parts):  # Start from the end
            ratio = difflib.SequenceMatcher(None, domain_root.lower(), part.lower()).ratio()
            if ratio > 0.8:  # Threshold for fuzzy matching
                return part.strip()  # Return the part containing the domain root

    # Fallback to the root domain as the brand name
    return domain_root

def is_brand_mentioned(term, brand_name):
    # Case-insensitive check
    if brand_name.lower() in term.lower():
        return True

    # Optionally use difflib for partial matches
    ratio = difflib.SequenceMatcher(None, term.lower().replace(' ', ''), brand_name.lower().replace(' ', '')).ratio()
    # Consider it a match if similarity is high enough (adjust threshold as needed)
    if ratio > 0.8:
        return True

    # Check NER: if a named entity matches or closely resembles the brand
    doc = nlp(term)
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PRODUCT', 'PERSON', 'GPE']:
            # Compare entity text with brand_name using a ratio
            ratio_ent = difflib.SequenceMatcher(None, ent.text.lower().replace(' ', ''), brand_name.lower().replace(' ', '')).ratio()
            if ratio_ent > 0.8:
                return True

    return False

def is_not_branded(question, brands):
    """
    Checks if a given question string is branded.

    Args:
        question (str): The question string to check.

    Returns:
        bool: True if the question is not branded, False otherwise.
    """
    # Check if the question mentions any brand name
    for brand in brands:
        if is_brand_mentioned(question, brand):
            return False  # The question is branded
    return True  # The question is not branded


class AnalysisResponse(BaseModel):
    titles: List[str]
    urls: List[str]
    favicons: List[str]
    word_counts: List[int]
    headings_data: List[Dict]
    tfidf_terms: List[Dict]  # Include terms with their scores
    ideal_word_count: Optional[int] = 1000

class AnalysisInput(BaseModel):
    keyword: str

@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_keyword(input_data: AnalysisInput):
    keyword = input_data.keyword
    start_time = time.time()
    print(f'Starting Analysis of Keyword: {keyword} ...')
    top_urls = get_top_unique_domain_results(keyword, num_results=50, max_domains=50)
    if not top_urls:
        raise HTTPException(status_code=404, detail='No results found.')

    # Initialize lists to store data
    titles = []
    urls = []
    favicons = []
    retrieved_content = []
    successful_urls = []
    word_counts = []
    max_contents = 3
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

        if headings and isinstance(headings, list):  # Ensure headings is a list
            for heading in headings:
                if isinstance(heading, dict) and 'text' in heading:  # Ensure heading is a dictionary with 'text'
                    # Append title along with heading text and URL
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
                # Already have enough content, break the loop
                break
        time.sleep(0.5)
        if len(retrieved_content) >= max_contents:
            break

    if len(retrieved_content) < max_contents:
        print(f"Only retrieved {len(retrieved_content)} out of {max_contents} required contents.")

    if not retrieved_content:
        raise HTTPException(status_code=404, detail='Failed to retrieve sufficient content from the URLs.')

    print(f"Completed content retrieval. {len(retrieved_content)} contents retrieved.")

    # Calculating ideal word count
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

        print("Headings data processed successfully")
    else:
        filtered_headings_data = []
        print('No headings were extracted')

    # Initialize TF and TF-IDF Vectorizers with n-grams (uni-, bi-, tri-grams)
    tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 3))
    tf_vectorizer = CountVectorizer(ngram_range=(1, 3))

    # Fit the model and transform the documents into TF and TF-IDF matrices
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents_lemmatized).toarray()
    tf_matrix = tf_vectorizer.fit_transform(documents_lemmatized).toarray()

    # Extract feature names (terms)
    feature_names = tfidf_vectorizer.get_feature_names_out()

    # Filter feature names to exclude less informative words
    filtered_feature_names = filter_terms(feature_names)

    # Filter TF-IDF and TF matrices to only include filtered terms
    filtered_indices = [i for i, term in enumerate(feature_names) if term in filtered_feature_names]
    tfidf_matrix_filtered = tfidf_matrix[:, filtered_indices]
    tf_matrix_filtered = tf_matrix[:, filtered_indices]

    # Update feature names after filtering
    filtered_feature_names = [feature_names[i] for i in filtered_indices]

    # Calculate average TF-IDF and TF scores
    avg_tfidf_scores = np.mean(tfidf_matrix_filtered, axis=0)
    avg_tf_scores = np.mean(tf_matrix_filtered, axis=0)
    max_tf_scores = np.max(tf_matrix_filtered, axis=0)
    print(max_tf_scores)
    # Create a dictionary mapping terms to their scores
    term_scores = {
        term: {
            "tfidf": avg_tfidf_scores[i],
            "tf": avg_tf_scores[i],
            "max_tf_score": max_tf_scores
        }
        for i, term in enumerate(filtered_feature_names)
    }
    # Get the top 50 terms based on TF-IDF scores
    top_terms = sorted(term_scores, key=lambda t: term_scores[t]["tf"], reverse=True)[:50]
    for i, term in enumerate(top_terms):
        print(f"Word: {term}, {max_tf_scores[i]}")

    # Create a list of dictionaries for terms with both TF and TF-IDF scores
    tfidf_terms = [
        {
            "word": term,
            "tfidf_score": term_scores[term]["tfidf"],
            "tf_score": term_scores[term]["tf"],
            "max_tf": term_scores[term]["max_tf_score"]
        }
        for term in top_terms
    ]

    ideal_word_count = int(np.median(word_counts)) + 500 if word_counts else 1000

    elapsed_time = time.time() - start_time
    print(f"Time taken for Analysis Endpoint: {elapsed_time:.2f} seconds")

    return AnalysisResponse(
        titles=titles,
        urls=successful_urls,
        favicons=favicons,
        word_counts=word_counts,
        headings_data=filtered_headings_data,
        top_terms=top_terms,
        tfidf_terms=tfidf_terms,
        ideal_word_count=ideal_word_count
    )

class EditorContent(BaseModel):
    content: str

@app.post("/api/save-content")
async def save_content(content: EditorContent):
    try:
        # Here you would typically save the content to a database
        # For now, we'll just return a success message
        return {"message": "Content saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)