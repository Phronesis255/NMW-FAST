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

create_database_and_table()