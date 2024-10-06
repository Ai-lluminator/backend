import feedparser
import schedule
import time
from database import RAG
import numpy as np
import requests
import os

def fetch_cs_updates():

    feed_url = "https://aisel.aisnet.org/recent.rss"

    rag = RAG()

    timestamp = time.time()

    documents = []
    metadata = []
    ids = []

    # Parse the RSS feed
    feed = feedparser.parse(feed_url)
    
    print(f"Fetching updates from: {feed.feed.title}")
    print(f"Number of papers: {len(feed.entries)}")
    
    # Loop through each entry in the RSS feed
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        description = entry.summary
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