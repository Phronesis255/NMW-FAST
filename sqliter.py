import sqlite3
import pandas as pd

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

# Example usage
csv_file_path = "Pages.csv"  # Path to your CSV file
sqlite_db_path = "seo_data.db"  # Path for the SQLite database
table_name = "Pages"  # Name of the table to create
csv_to_sqlite(csv_file_path, sqlite_db_path, table_name)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert a CSV file to SQLite database.")
    parser.add_argument("csv_file", type=str, help="Path to the CSV file.")
    parser.add_argument("db_file", type=str, help="Path to the SQLite database file.")
    parser.add_argument("--table_name", type=str, default="Pages", help="Name of the table in the SQLite database.")

    args = parser.parse_args()

    csv_to_sqlite(args.csv_file, args.db_file, args.table_name)
