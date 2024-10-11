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
    arxiv_categories = ["cs", "stat", "q-bio", "q-fin", "math", "physics", "astro-ph", "eess", "econ"]
    feed_url_base = "https://rss.arxiv.org/rss/"

    # Initialize the RAG instance with database and embedding service details
    rag = RAG(POSTGRES_LINK, POSTGRES_PORT, EMBEDDING_LINK, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

    timestamp = time.time()

    documents = []
    metadata = []
    ids = []

    # Iterate over each arXiv category to fetch and parse the RSS feed
    for category in arxiv_categories:
        current_feed_url = feed_url_base + category
        feed = feedparser.parse(current_feed_url)
        
        print(f"Fetching updates from: {feed.feed.title}")
        print(f"Number of papers: {len(feed.entries)}")

        # Collect only new entries not already in the RAG database
        entry_ids = [entry.id for entry in feed.entries]
        existing_ids = rag.check_id_exists(entry_ids)
        new_entries = [entry for entry in feed.entries if entry.id not in existing_ids and entry.id not in ids]

        # Process new entries
        for entry in new_entries:
            title = entry.title
            link = entry.link
            description = entry.description
            authors = entry.author
            document = f"{title} {description}"
            meta_data = {
                "link": link,
                "authors": authors,
                "title": title,
                "timestamp": timestamp
            }

            documents.append(document)
            metadata.append(meta_data)
            ids.append(entry.id)

        print(f"Fetched {len(new_entries)} new papers from {category}")

    # Add new documents to the RAG if any new entries were found
    if documents:
        rag.add_documents(documents, metadata, ids)

# Execute the function to fetch updates
fetch_cs_updates()