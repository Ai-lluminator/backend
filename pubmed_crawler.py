import ftplib
import gzip
import os
import xml.etree.ElementTree as ET
import datetime
from database import RAG
import time

def parse_pubmed_articles(file_path):
    # Load and parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # List to hold article data
    articles_data = []

    # Iterate over each PubmedArticle in the XML
    for article in root.findall('PubmedArticle'):
        # Extract the article title
        title = article.find('.//ArticleTitle').text if article.find('.//ArticleTitle') is not None else 'No title available'

        # Extract the abstract
        abstract = article.find('.//AbstractText').text if article.find('.//AbstractText') is not None else 'No abstract available'

        # Extract DOI
        pmid = article.find('.//PMID').text if article.find('.//PMID') is not None else 'No PMID available'

        # Extract PubMedPubDate
        pubmed_date = '-'.join([
            article.find(".//PubMedPubDate[@PubStatus='pubmed']/Year").text,
            article.find(".//PubMedPubDate[@PubStatus='pubmed']/Month").text,
            article.find(".//PubMedPubDate[@PubStatus='pubmed']/Day").text
        ]) if article.find('.//PubMedPubDate') is not None else 'No PubDate'

        # Extract DateCompleted
        date_completed = '-'.join([
            article.find(".//DateCompleted/Year").text,
            article.find(".//DateCompleted/Month").text,
            article.find(".//DateCompleted/Day").text
        ]) if article.find('.//DateCompleted') is not None else 'No DateCompleted'

        language = article.find('.//Language').text if article.find('.//Language') is not None else 'No language available'

        # Extract authors
        authors = []
        for author in article.findall('.//Author'):
            first_name = author.find('ForeName').text if author.find('ForeName') is not None else ''
            last_name = author.find('LastName').text if author.find('LastName') is not None else ''
            initials = author.find('Initials').text if author.find('Initials') is not None else ''
            full_name = f"{first_name} {last_name} {initials}".strip()
            authors.append(full_name)

        # Collect all extracted data into a dictionary
        article_data = {
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'pmid': pmid,
            'date_completed': date_completed,
            'pubmed_date': pubmed_date,
            'language': language
        }

        articles_data.append(article_data)

    return articles_data

def get_newest_files(ftp, num_files=3):
    # Change to the desired directory

    # Get list of files with details
    files = []
    ftp.dir(lambda x: files.append(x))

    # Parse the list into a structured format and retrieve timestamps
    detailed_files = []
    for file in files:
        try:
            parts = file.split()
            file_info = {
                'permissions': parts[0],
                'num_hardlinks': parts[1],
                'owner': parts[2],
                'group': parts[3],
                'size': parts[4],
                'date': ' '.join(parts[5:8]),
                'name': ' '.join(parts[8:]),
                'timestamp': datetime.datetime.strptime(' '.join(parts[5:8]), '%b %d %H:%M')
            }
            id = file_info['name'].split('.')[0]
            id = int(id.split('n')[-1])
            if id > 1245:
                detailed_files.append(file_info)
        except ValueError as e:
            continue

    # Sort files by timestamp
    sorted_files = sorted(detailed_files, key=lambda x: x['timestamp'], reverse=True)

    # Return the newest 'num_files' files
    return sorted_files[:num_files]

def convert_to_chromadb_format(articles_data, rag):
    documents = []
    metadata = []
    ids = []
    timestamp = time.time()
    for article in articles_data:
        if article['abstract'] is None or article['abstract'] == 'No abstract available':
            article['abstract'] = ''
        document = article['title'] + " " + article['abstract']
        meta_data = {
            'link': f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}",
            'authors': ', '.join(article['authors']),
            'title': article['title'],
            'timestamp': timestamp
        }
        documents.append(document)
        metadata.append(meta_data)
        ids.append(article['pmid'])

    # Check if the papers already exist in the database
    existing_ids = rag.check_id_exists(ids)
    documents = [document for document, exists in zip(documents, existing_ids) if not exists]
    metadata = [meta for meta, exists in zip(metadata, existing_ids) if not exists]
    ids = [id for id, exists in zip(ids, existing_ids) if not exists]

    return documents, metadata, ids

# FTP server details
FTP_HOST = "ftp.ncbi.nlm.nih.gov"
SUBFOLDER = "/pubmed/updatefiles/"

# Connect to the FTP server
ftp = ftplib.FTP(FTP_HOST)
ftp.login()
ftp.cwd('pubmed/updatefiles/')

# Find the latest .xml.gz file
files = get_newest_files(ftp)
files = [file['name'] for file in files]
for file in files:
    if file.endswith('.xml.gz'):
        latest_file = file
        break

if latest_file:
    # Download the latest file
    with open(latest_file, 'wb') as f:
        ftp.retrbinary(f'RETR {latest_file}', f.write)
    ftp.quit()
    # Unpack the gzip file to get the XML
    with gzip.open(latest_file, 'rb') as f_in:
        with open(latest_file.replace('.gz', ''), 'wb') as f_out:
            f_out.write(f_in.read())

    # Parse the XML file
    article_data = parse_pubmed_articles(latest_file.replace('.gz', ''))
    
    # Remove papers without a title
    article_data = [article for article in article_data if article['title'] != 'No title available' and article['title'] != None]

    # Remove all articles with a missing DOI
    article_data = [article for article in article_data if article['pmid'] != 'No PMID available']

    # Remove all papers that have no pubdate
    article_data = [article for article in article_data if article['pubmed_date'] != 'No PubDate']

    # Remove all papers that are not in English
    article_data = [article for article in article_data if article['language'] == 'eng']

    # Convert date_completed into datetime object
    for article in article_data:
        if article['date_completed'] != 'No DateCompleted':
            article['date_completed'] = datetime.datetime.strptime(article['date_completed'], '%Y-%m-%d')
        article['pubmed_date'] = datetime.datetime.strptime(article['pubmed_date'], '%Y-%m-%d')

    # Remove all papers that are older than 2 days
    two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
    article_data = [article for article in article_data if article['pubmed_date'] > two_days_ago]

    ninty_days_ago = datetime.datetime.now() - datetime.timedelta(days=730)
    article_data = [article for article in article_data if article['date_completed'] == "No DateCompleted" or article['date_completed'] > ninty_days_ago]

    print(f"Number of articles crawled: {len(article_data)}")
    # Clean up downloaded files
    os.remove(latest_file)
    os.remove(latest_file.replace('.gz', ''))

    # Initialize the RAG database
    rag = RAG()
    documents, metadata, ids = convert_to_chromadb_format(article_data, rag)
    print(f"Number of articles added to the database: {len(ids)}")
    rag.add_documents(documents, metadata, ids)
else:
    ftp.quit()
    print("No .xml.gz files found.")