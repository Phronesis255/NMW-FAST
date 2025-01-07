# analysis.py

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configure Seaborn aesthetics
sns.set(style="whitegrid", palette="muted", color_codes=True)

def connect_db(db_path='generator.db'):
    """
    Connects to the SQLite database and returns the connection object.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file '{db_path}' does not exist.")
    conn = sqlite3.connect(db_path)
    return conn

def fetch_data(conn):
    """
    Fetches data from the 'outlines' and 'blog_posts' tables.
    
    Returns:
        outlines_df (DataFrame): Data from 'outlines' table.
        blog_posts_df (DataFrame): Data from 'blog_posts' table.
    """
    outlines_query = "SELECT * FROM outlines"
    blog_posts_query = "SELECT * FROM blog_posts"
    
    outlines_df = pd.read_sql_query(outlines_query, conn)
    blog_posts_df = pd.read_sql_query(blog_posts_query, conn)
    
    return outlines_df, blog_posts_df

def preprocess_data(blog_posts_df):
    """
    Preprocesses the blog_posts DataFrame for analysis.
    
    Args:
        blog_posts_df (DataFrame): Raw data from 'blog_posts' table.
    
    Returns:
        blog_posts_df (DataFrame): Cleaned and processed DataFrame.
    """
    # Convert relevant columns to numeric types if not already
    numeric_columns = ['final_blog_post_length', 'total_generation_time', 'similarity_to_title',
                       'reading_difficulty_grade', 'keyword_density', 'gunning_fog',
                       'flesch_kincaid_ease']
    
    for col in numeric_columns:
        blog_posts_df[col] = pd.to_numeric(blog_posts_df[col], errors='coerce')
    
    # Drop rows with missing values in critical columns
    blog_posts_df.dropna(subset=numeric_columns, inplace=True)
    
    return blog_posts_df

def create_box_plots(blog_posts_df):
    """
    Creates box plots for selected metrics.
    """
    plt.figure(figsize=(12, 8))
    metrics = ['keyword_density', 'gunning_fog', 'flesch_kincaid_ease']
    sns.boxplot(data=blog_posts_df[metrics])
    plt.title('Box Plot of Keyword Density, Gunning Fog, and Flesch-Kincaid Ease')
    plt.xlabel('Metrics')
    plt.ylabel('Values')
    plt.savefig('box_plot_metrics.png', bbox_inches='tight')
    plt.show()

def create_violin_plots(blog_posts_df):
    """
    Creates violin plots for selected metrics.
    """
    plt.figure(figsize=(12, 8))
    metrics = ['similarity_to_title', 'reading_difficulty_grade']
    sns.violinplot(data=blog_posts_df[metrics])
    plt.title('Violin Plot of Similarity to Title and Reading Difficulty Grade')
    plt.xlabel('Metrics')
    plt.ylabel('Values')
    plt.savefig('violin_plot_metrics.png', bbox_inches='tight')
    plt.show()

def create_area_chart(blog_posts_df):
    """
    Creates an area chart showing blog post length over total generation time.
    """
    plt.figure(figsize=(14, 8))
    sorted_df = blog_posts_df.sort_values(by='total_generation_time')
    plt.fill_between(sorted_df['total_generation_time'], sorted_df['final_blog_post_length'], color="skyblue", alpha=0.4)
    plt.plot(sorted_df['total_generation_time'], sorted_df['final_blog_post_length'], color="Slateblue", alpha=0.6)
    plt.title('Area Chart of Blog Post Length Over Total Generation Time')
    plt.xlabel('Total Generation Time (seconds)')
    plt.ylabel('Blog Post Length (characters)')
    plt.savefig('area_chart_length_time.png', bbox_inches='tight')
    plt.show()

def create_stacked_bar_chart(blog_posts_df):
    """
    Creates a stacked bar chart showing counts of blog posts across LLM models and keyword density categories.
    """
    # Define keyword density categories
    bins = [0, 1, 2, 3, 4, 100]
    labels = ['<1%', '1-2%', '2-3%', '3-4%', '>4%']
    blog_posts_df['keyword_density_category'] = pd.cut(blog_posts_df['keyword_density'], bins=bins, labels=labels)
    
    # Group by LLM model and keyword density category
    counts = blog_posts_df.groupby(['llm_model', 'keyword_density_category']).size().unstack(fill_value=0)
    
    # Plot
    counts.plot(kind='bar', stacked=True, figsize=(14, 8), colormap='viridis')
    plt.title('Stacked Bar Chart of Keyword Density Categories by LLM Model')
    plt.xlabel('LLM Model')
    plt.ylabel('Number of Blog Posts')
    plt.legend(title='Keyword Density', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('stacked_bar_chart_keyword_density.png', bbox_inches='tight')
    plt.show()

def create_scatter_plots(blog_posts_df):
    """
    Creates scatter plots to show relationships between different metrics.
    """
    # Scatter plot: Keyword Density vs. Similarity to Title
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=blog_posts_df, x='keyword_density', y='similarity_to_title', hue='llm_model', palette='deep', alpha=0.7)
    plt.title('Scatter Plot: Keyword Density vs. Similarity to Title by LLM Model')
    plt.xlabel('Keyword Density (%)')
    plt.ylabel('Similarity to Title')
    plt.legend(title='LLM Model', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('scatter_plot_keyword_similarity.png', bbox_inches='tight')
    plt.show()
    
    # Scatter plot: Reading Difficulty Grade vs. Flesch-Kincaid Ease
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=blog_posts_df, x='reading_difficulty_grade', y='flesch_kincaid_ease', hue='llm_model', palette='deep', alpha=0.7)
    plt.title('Scatter Plot: Reading Difficulty Grade vs. Flesch-Kincaid Ease by LLM Model')
    plt.xlabel('Reading Difficulty Grade')
    plt.ylabel('Flesch-Kincaid Ease')
    plt.legend(title='LLM Model', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('scatter_plot_reading_ease.png', bbox_inches='tight')
    plt.show()

def create_histograms(blog_posts_df):
    """
    Creates histograms for selected metrics.
    """
    metrics = ['keyword_density', 'gunning_fog', 'reading_difficulty_grade', 'flesch_kincaid_ease']
    blog_posts_df[metrics].hist(bins=15, figsize=(16, 12), layout=(2, 2), color='skyblue', edgecolor='black')
    plt.suptitle('Histograms of Keyword Density, Gunning Fog, Reading Difficulty Grade, and Flesch-Kincaid Ease')
    plt.savefig('histograms_metrics.png', bbox_inches='tight')
    plt.show()

def create_correlation_heatmap(blog_posts_df):
    """
    Creates a heatmap showing correlation between different metrics.
    """
    plt.figure(figsize=(10, 8))
    corr = blog_posts_df[['keyword_density', 'gunning_fog', 'reading_difficulty_grade',
                          'flesch_kincaid_ease', 'similarity_to_title', 'final_blog_post_length',
                          'total_generation_time']].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('Correlation Heatmap of Blog Post Metrics')
    plt.tight_layout()
    plt.savefig('correlation_heatmap.png', bbox_inches='tight')
    plt.show()

def main():
    # Step 1: Connect to the database
    try:
        conn = connect_db()
    except FileNotFoundError as e:
        print(e)
        return
    
    # Step 2: Fetch data
    outlines_df, blog_posts_df = fetch_data(conn)
    
    # Close the database connection
    conn.close()
    
    # Step 3: Preprocess data
    blog_posts_df = preprocess_data(blog_posts_df)
    
    # Check if there's data to analyze
    if blog_posts_df.empty:
        print("No data available in 'blog_posts' table for analysis.")
        return
    
    # Step 4: Create Visualizations
    create_box_plots(blog_posts_df)
    create_violin_plots(blog_posts_df)
    create_area_chart(blog_posts_df)
    create_stacked_bar_chart(blog_posts_df)
    create_scatter_plots(blog_posts_df)
    create_histograms(blog_posts_df)
    create_correlation_heatmap(blog_posts_df)
    
    print("All visualizations have been created and saved successfully.")

if __name__ == "__main__":
    main()
