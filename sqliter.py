import sqlite3
import pandas as pd

def create_database_and_table():
    """
    This function creates the SQLite database and the necessary tables if they don't exist.
    """
    # Connect to SQLite database (creates the file if it doesn't exist)
    conn = sqlite3.connect('generator.db')
    cursor = conn.cursor()

    # Create the 'outlines' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            title TEXT,
            outline TEXT,
            outline_length INTEGER,
            generation_time REAL,
            llm_model TEXT
        )
    ''')

    # Create the 'blog_posts' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outline_id INTEGER,
            final_blog_post TEXT,
            final_blog_post_length INTEGER,
            total_generation_time REAL,
            llm_model TEXT,
            similarity_to_title REAL,
            reading_difficulty_grade REAL,
            keyword_density REAL,
            gunning_fog REAL,
            flesch_kincaid_ease REAL,
            FOREIGN KEY(outline_id) REFERENCES outlines(id)
        )
    ''')

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    print("Database and tables 'outlines' and 'blog_posts' have been created (if not already present).")

def csv_to_sqlite(csv_file: str, db_file: str, table_name: str = "Pages"):
    """
    Converts a CSV file into a SQLite database table.

    Args:
        csv_file (str): Path to the input CSV file.
        db_file (str): Path to the output SQLite database file.
        table_name (str): Name of the table to create in the SQLite database.
    """
    try:
        # Load the CSV file into a Pandas DataFrame
        df = pd.read_csv(csv_file)

        # Connect to SQLite database (it creates the file if it doesn't exist)
        conn = sqlite3.connect(db_file)

        # Save the DataFrame to a SQLite table
        df.to_sql(table_name, conn, if_exists='replace', index=False)

        # Close the connection
        conn.close()

        print(f"Successfully created SQLite database '{db_file}' with table '{table_name}'.")

    except Exception as e:
        print(f"Error converting CSV to SQLite: {e}")

# # Example usage
# csv_file_path = "Pages.csv"  # Path to your CSV file
# sqlite_db_path = "seo_data.db"  # Path for the SQLite database
# table_name = "Pages"  # Name of the table to create
# csv_to_sqlite(csv_file_path, sqlite_db_path, table_name)

# setup_db.py

def create_database():
    conn = sqlite3.connect("analysis_data.db")

    # 1) Create analysis_cache table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS analysis_cache (
        keyword TEXT PRIMARY KEY,
        response_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2) Create tfidf_data table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tfidf_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        term TEXT,
        tf REAL,
        tfidf REAL,
        max_tf REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3) Create headings_data table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS headings_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        heading_text TEXT,
        heading_url TEXT,
        heading_title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4) Create long_tail_keywords table (new table for long-tail keywords)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS long_tail_keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        keyphrase TEXT,
        relevance_score REAL,
        frequency INTEGER,
        kw_length INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("Database and tables created successfully.")

def create_longtail():
    conn = sqlite3.connect("analysis_data.db")

    # Create the long_tail_keywords table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS long_tail_keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        keyphrase TEXT,
        relevance_score REAL,
        frequency INTEGER,
        kw_length INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

# create_longtail()
conn = sqlite3.connect("analysis_data.db")
cursor = conn.cursor()

# List all tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:", tables)

conn.close()

