import feedparser
import time
from database import RAG, UserDatabase
import numpy as np
import requests
import os

def fetch_cs_updates():
    # RSS feed URL
    arxiv_categories = ["cs", "stat", "q-bio", "q-fin", "math", "physics", "astro-ph", "eess", "econ"]

    feed_url = "https://rss.arxiv.org/rss/"

    rag = RAG()

    timestamp = time.time()

    documents = []
    metadata = []
    ids = []
    
    for category in arxiv_categories:
        current_feed = feed_url + category
        # Parse the RSS feed
        feed = feedparser.parse(current_feed)
        
        print(f"Fetching updates from: {feed.feed.title}")
        print(f"Number of papers: {len(feed.entries)}")
        
        # Loop through each entry in the RSS feed
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            # pub_data = entry.pubDate
            description = entry.description
            authors = entry.author
            document = title + " " + description
            meta_data = {"link": link, "authors": authors, "title": title, "timestamp": timestamp}

            if rag.check_id_exists(entry.id) or entry.id in ids:
                continue
            else:
                documents.append(document)
                metadata.append(meta_data)
                ids.append(entry.id)

        print(f"Fetching {len(ids)} new papers")
    
    if len(ids) > 0:
        rag.add_documents(documents, metadata, ids)

fetch_cs_updates()