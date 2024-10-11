import feedparser
import time
from database import RAG
import numpy as np
import requests
import os
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("DB_NAME")
POSTGRES_PORT = int(os.environ.get("DB_PORT"))
POSTGRES_LINK = os.environ.get("DB_HOST")
EMBEDDING_LINK = os.environ.get("EMBEDDING_LINK")

def fetch_cs_updates():

    feed_url = "https://aisel.aisnet.org/recent.rss"

    rag = RAG(POSTGRES_LINK, POSTGRES_PORT, EMBEDDING_LINK, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

    documents = []
    metadata = []
    ids = []

    # Parse the RSS feed
    feed = feedparser.parse(feed_url)
    
    print(f"Fetching updates from: {feed.feed.title}")
    print(f"Number of papers: {len(feed.entries)}")
    
    # Loop through each entry in the RSS feed

    links = [entry.link for entry in feed.entries]
    links_to_remove = rag.check_id_exists(links)
    data = [entry for entry in feed.entries if entry.link not in links_to_remove]

    print("Number of new papers: ", len(data))

    urls = [entry.link for entry in data]
    titles = [entry.title for entry in data]
    contents = [f"{entry.title} \n {entry.summary}" for entry in data]

    rag.add_documents(urls, titles, contents)

    if len(ids) > 0:
        rag.add_documents(documents, metadata, ids)

fetch_cs_updates()