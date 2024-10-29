import feedparser
import time
from database import RAG
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables for the database and embedding service configuration
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("DB_NAME")
POSTGRES_PORT = int(os.environ.get("DB_PORT"))
POSTGRES_LINK = os.environ.get("DB_HOST")
EMBEDDING_LINK = os.environ.get("EMBEDDING_LINK")

def fetch_cs_updates():
    # Define the arXiv categories and base RSS feed URL
    categories = [
        "animal behavior and cognition",
        "biochemistry",
        "bioengineering",
        "bioinformatics",
        "biophysics",
        "cancer biology",
        "cell biology",
        "clinical trials",
        "developmental biology",
        "ecology",
        "epidemiology",
        "evolutionary biology",
        "genetics",
        "genomics",
        "immunology",
        "microbiology",
        "molecular biology",
        "neuroscience",
        "paleontology",
        "pathology",
        "pharmacology and toxicology",
        "physiology",
        "plant biology",
        "scientific communication and education",
        "synthetic biology",
        "systems biology",
        "zoology"
    ]

    feed_url_base = "http://connect.biorxiv.org/biorxiv_xml.php?subject="

    # Initialize the RAG instance with database and embedding service details
    rag = RAG(POSTGRES_LINK, POSTGRES_PORT, EMBEDDING_LINK, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

    timestamp = time.time()

    urls = []
    titles = []
    contents = []

    batch_size = 32

    # Iterate over each arXiv category to fetch and parse the RSS feed
    for category in categories:
        current_feed_url = feed_url_base + category.lower().replace(" ", "_")
        feed = feedparser.parse(current_feed_url)
        
        print(f"Fetching updates from: {feed.feed.title}")
        print(f"Number of papers: {len(feed.entries)}")

        # Collect only new entries not already in the RAG database
        entry_urls = [entry.link for entry in feed.entries]
        existing_ids = rag.check_id_exists(entry_urls)
        data = [entry for entry in feed.entries if entry.link not in existing_ids]

        urls = [entry.link for entry in data]
        titles = [entry.title for entry in data]
        contents = [f"{entry.title} \n {entry.description}" for entry in data]

        # Add new documents to the RAG if any new entries were found
        if urls:
            rag.add_documents(urls, titles, contents)

# Execute the function to fetch updates
fetch_cs_updates()