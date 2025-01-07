# generator.py

import os
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import time
from dotenv import load_dotenv
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textstat
import nltk
import sys

# Initialize NLTK (if not already done)
nltk.download('punkt')

# --------------------------------------------
# llm_model = "HG-Qwen-2.5-72B-Instruct"
# llm_model = "HG-Llama-3.2-3B-Instruct"
llm_model = "gpt-4o-mini"
# llm_model = "gpt-4o"
# llm_model = "o1-mini"

#----------------------------------------------
load_dotenv()
OPENAI = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Initialize LLM and embedding model
llm = ChatOpenAI(model=llm_model, temperature=1, api_key=OPENAI)


def compute_reading_difficulty(blog_post):
    """
    Computes the Flesch-Kincaid grade level of the blog post.
    
    Returns the grade level as a float.
    """
    return textstat.flesch_kincaid_grade(blog_post)

def compute_flesch_kincaid_ease(blog_post):
    """
    Computes the Flesch Reading Ease score of the blog post.
    
    Returns the ease score as a float.
    """
    return textstat.flesch_reading_ease(blog_post)

def compute_gunning_fog(blog_post):
    """
    Computes the Gunning Fog readability score of the blog post.
    
    Returns the Gunning Fog score as a float.
    """
    return textstat.gunning_fog(blog_post)

def compute_keyword_density(blog_post, keyword):
    """
    Computes the keyword density of the focus keyword in the blog post using regular expressions.
    
    Args:
        blog_post (str): The content of the blog post.
        keyword (str): The keyword to calculate density for.
        
    Returns:
        float: Keyword density as a percentage.
    """
    if not blog_post or not keyword:
        return 0.0

    # Convert both blog post and keyword to lowercase for case-insensitive matching
    blog_post_lower = blog_post.lower()
    keyword_lower = keyword.lower()
    
    # Escape the keyword to handle any special regex characters
    escaped_keyword = re.escape(keyword_lower)
    
    # Create a regex pattern to match the whole word or exact phrase
    # \b ensures word boundaries for single-word keywords
    # For multi-word keywords, word boundaries at the start and end suffice
    pattern = r'\b{}\b'.format(escaped_keyword)
    
    # Find all non-overlapping occurrences of the keyword
    matches = re.findall(pattern, blog_post_lower)
    keyword_count = len(matches)
    
    # Tokenize the blog post to count total words
    # Using simple split; alternatively, use nltk.word_tokenize for more accurate word counts
    total_words = len(blog_post_lower.split())
    
    if total_words == 0:
        return 0.0
    
    # Calculate density
    density = (keyword_count / total_words) * 100
    return density

def compute_similarity(title, blog_post):
    """
    Computes the cosine similarity between the blog post and its title.
    
    Returns a similarity score between 0 and 1.
    """
    vectorizer = TfidfVectorizer().fit([title, blog_post])
    vectors = vectorizer.transform([title, blog_post])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    return similarity * 100

def generate_outline(llm, keyword, title):
    """
    Calls the LLM to create an SEO-optimized blog post outline given a keyword and title.
    """
    outline_prompt_template = """
    You are an SEO expert and a professional blog writer.
    Given a keyword: "{keyword}"
    And a blog title: "{title}"
    
    Please create a detailed SEO-optimized blog post outline.
    - The outline should include major sections and subsections.
    - Start each major section with a heading label (e.g., "## Section Title").
    - Subsections should be labeled (e.g., "### Subsection Title").
    - Make it clear, easy to parse, and in Markdown format.
    - Don't use bullet points in the outline.
    - Don't add comments before or after the outline itself. Just return the outline.
    """
    
    # Create the prompt
    prompt = PromptTemplate(
        input_variables=["keyword", "title"],
        template=outline_prompt_template
    )
    
    # Create the chain with prompt | llm
    chain = prompt | llm
    
    # Correct the call to `invoke` by passing inputs as a dictionary
    outline = chain.invoke({"keyword": keyword, "title": title})
    
    return outline
def generate_section_content(llm, keyword, title, section_outline, target_audience, tone):
    now=time.time()
    content_prompt_template = """
        You are a skilled content writer and SEO strategist tasked with crafting a detailed and engaging section of a blog post. Please adhere to the following requirements:

        Focus Keyword: {KEYWORD} - Integrate this keyword naturally throughout the text, ensuring optimal keyword density without overstuffing.
        Title of the Blog Post: {TITLE} - Write content aligned with the overall theme and relevance of the title.
        Section Outline: {SECTION_OUTLINE} - Follow this outline to maintain coherence and logical progression.
        Target Audience: {TARGET_AUDIENCE} - Tailor the tone, style, and complexity of the content to resonate with this specific audience.
        Tone: {TONE} - Write in this tone, whether it is professional, conversational, or inspirational.

        Additional Requirements:
        - Provide information-rich content supported by credible data, including statistics, case studies, and references to reputable industry reports.
        - Use real-world examples to enhance relatability and reader engagement.
        - Avoid vague generalizations or repetitive content.
        - Offer practical tips, strategies, or actionable insights wherever possible to enrich the reader’s understanding.
        - Ensure that the content aligns with best SEO practices to maximize visibility and reader retention.

        Provide the text in Markdown format, without repeating the heading verbatim. 
    """
    prompt = PromptTemplate(
        input_variables=[
            "KEYWORD", 
            "TITLE", 
            "SECTION_OUTLINE", 
            "TARGET_AUDIENCE", 
            "TONE"
        ],
        template=content_prompt_template
    )

    chain = prompt | llm
    content = chain.invoke({
        "KEYWORD": keyword,
        "TITLE": title,
        "SECTION_OUTLINE": section_outline,
        "TARGET_AUDIENCE": target_audience,
        "TONE": tone,
    })
    then=time.time()
    print(f"Generated section in {then-now:.2f} seconds.")
    return content.content.strip()

def parse_outline(outline_text):
    """
    Parses the LLM-generated outline text into a structured list of sections.
    
    Handles outlines with optional bullet points and varying indentation.

    Returns a list of dictionaries:
    [
      {
        "heading": "## Introduction",
        "subsections": ["### What are UTM Codes?", "### What is a UTM Generator?"]
      },
      ...
    ]
    """
    lines = outline_text.split("\n")
    sections = []
    current_section = None

    # Regex pattern to match headings with optional bullets and spaces
    heading_pattern = re.compile(r'^\s*[-*]*\s*(#{2,3})\s+(.*)$')

    for line in lines:
        stripped = line.strip()
        match = heading_pattern.match(line)
        if match:
            hashes, title = match.groups()
            heading = f"{hashes} {title}"
            if hashes == '##':
                # If it's a major section
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "heading": heading,
                    "subsections": []
                }
            elif hashes == '###':
                # If it's a subsection
                if current_section:
                    current_section["subsections"].append(heading)
                else:
                    # Handle case where subsection appears before any section
                    current_section = {
                        "heading": "## Untitled Section",
                        "subsections": [heading]
                    }
        else:
            # Non-heading lines can be ignored or handled as needed
            pass

    # Add the final section if it exists
    if current_section:
        sections.append(current_section)

    return sections
def create_blog_post(
    llm,
    keyword, 
    title,
    target_audience="General Audience",
    tone="professional",
    model_name="gpt-4o-mini", 
    output_file="blog_post.md"
):
    """
    Orchestrates the blog creation:
    1. Creates an outline
    2. Parses the outline into sections/subsections
    3. Loops through each section/subsection to generate content
    4. Saves the final blog post as a Markdown file
    5. Computes metrics and saves to the database
    """
    
    # 2) Generate Outline
    t0 = time.time()
    outline_text = generate_outline(llm, keyword, title)
    t1 = time.time()
    td = t1 - t0
    if not isinstance(outline_text, str):
        outline_text = outline_text.content
    print("Generated Outline:")
    print(outline_text)
    with open('outline.txt', 'w', encoding='utf-8') as f:
        f.write(outline_text)
    
    # 3) Parse Outline into structured sections
    sections = parse_outline(outline_text)
    
    # Connect to SQLite and insert into 'outlines' table
    conn = sqlite3.connect('generator.db')
    cursor = conn.cursor()
    outline_length = len(outline_text)
    # Insert the data into the 'outlines' table
    cursor.execute('''
        INSERT INTO outlines (keyword, title, outline, outline_length, generation_time, llm_model)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (keyword, title, outline_text, outline_length, td, model_name))

    # Retrieve the last inserted outline_id
    outline_id = cursor.lastrowid

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    # 4) Generate content for each section and its subsections
    blog_post_markdown = []
    
    for section in sections:
        # Add the section heading
        blog_post_markdown.append(section["heading"])
        
        # Combine the section heading + subsections as "section_outline"
        # so the LLM knows the overall plan for this section.
        section_outline_text = section["heading"]
        if section["subsections"]:
            subsection_text = "\n".join(section["subsections"])
            section_outline_text += "\n" + subsection_text
        
        # Generate content for the entire section (including any subsections)
        section_content = generate_section_content(
            llm=llm,
            keyword=keyword,
            title=title,
            section_outline=section_outline_text,
            target_audience=target_audience,
            tone=tone
        )
        blog_post_markdown.append(section_content)    

    # 5) Combine all sections into final Markdown
    final_blog_post = "\n\n".join(blog_post_markdown)

    # 6) Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_blog_post)

    print(f"\nBlog post saved to {output_file}")

    # 7) Compute additional metrics
    similarity_to_title = compute_similarity(title, final_blog_post)
    reading_difficulty_grade = compute_reading_difficulty(final_blog_post)
    flesch_kincaid_ease = compute_flesch_kincaid_ease(final_blog_post)
    gunning_fog = compute_gunning_fog(final_blog_post)
    keyword_density = compute_keyword_density(final_blog_post, keyword)
    final_blog_post_length = len(final_blog_post)
    total_generation_time = time.time() - t0  # Total time from outline generation to blog post creation

    # 8) Save the blog post data to the database
    conn = sqlite3.connect('generator.db')
    cursor = conn.cursor()

    # Insert the data into the 'blog_posts' table
    cursor.execute('''
        INSERT INTO blog_posts (
            outline_id, 
            final_blog_post, 
            final_blog_post_length, 
            total_generation_time, 
            llm_model, 
            similarity_to_title, 
            reading_difficulty_grade,
            keyword_density,
            gunning_fog,
            flesch_kincaid_ease
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        outline_id, 
        final_blog_post, 
        final_blog_post_length, 
        total_generation_time, 
        model_name, 
        similarity_to_title, 
        reading_difficulty_grade,
        keyword_density,
        gunning_fog,
        flesch_kincaid_ease
    ))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    print("\nBlog post data saved to 'generator.db' in 'blog_posts' table.")
    print(f"Similarity to Title: {similarity_to_title:.2f}")
    print(f"Reading Difficulty Grade: {reading_difficulty_grade:.2f}")
    print(f"Flesch-Kincaid Ease: {flesch_kincaid_ease:.2f}")
    print(f"Gunning Fog: {gunning_fog:.2f}")
    print(f"Keyword Density: {keyword_density:.2f}%")
    print(f"Total word count: {final_blog_post_length}")
def add_columns_if_missing():
    conn = sqlite3.connect('generator.db')
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(outlines)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Define required columns for 'outlines' table
    required_columns = {
        'keyword': 'TEXT',
        'title': 'TEXT',
        'outline': 'TEXT',
        'outline_length': 'INTEGER',
        'generation_time': 'REAL',
        'llm_model': 'TEXT'
    }
    
    for column, col_type in required_columns.items():
        if column not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE outlines ADD COLUMN {column} {col_type}")
                print(f"Added column '{column}' to 'outlines' table.")
            except sqlite3.OperationalError as e:
                print(f"Error adding column '{column}': {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns_if_missing()
    keyword = "UTM generator"
    title = "How to Create Correct UTM codes with UTM Generator"
    start_time = time.time()
    create_blog_post(llm=llm, keyword=keyword, title=title, model_name=llm_model)
    end_time = time.time()
    generation_time = end_time - start_time
    print(f"Generated blog in {generation_time:.2f} seconds.")
