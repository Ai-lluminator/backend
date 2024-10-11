import ftplib
import gzip
import os
import xml.etree.ElementTree as ET
import datetime
import time
from database import RAG
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FTP and Database Configuration
FTP_HOST = "ftp.ncbi.nlm.nih.gov"
SUBFOLDER = "/pubmed/updatefiles/"
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("DB_NAME")
POSTGRES_PORT = int(os.environ.get("DB_PORT"))
POSTGRES_LINK = os.environ.get("DB_HOST")
EMBEDDING_LINK = os.environ.get("EMBEDDING_LINK")

def parse_pubmed_articles(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    articles_data = []

    for article in root.findall('PubmedArticle'):
        title = article.find('.//ArticleTitle').text if article.find('.//ArticleTitle') is not None else 'No title available'
        abstract = article.find('.//AbstractText').text if article.find('.//AbstractText') is not None else 'No abstract available'
        pmid = article.find('.//PMID').text if article.find('.//PMID') is not None else 'No PMID available'
        pubmed_date = '-'.join([
            article.find(".//PubMedPubDate[@PubStatus='pubmed']/Year").text,
            article.find(".//PubMedPubDate[@PubStatus='pubmed']/Month").text,
            article.find(".//PubMedPubDate[@PubStatus='pubmed']/Day").text
        ]) if article.find('.//PubMedPubDate') is not None else 'No PubDate'
        date_completed = '-'.join([
            article.find(".//DateCompleted/Year").text,
            article.find(".//DateCompleted/Month").text,
            article.find(".//DateCompleted/Day").text
        ]) if article.find('.//DateCompleted') is not None else 'No DateCompleted'
        language = article.find('.//Language').text if article.find('.//Language') is not None else 'No language available'

        authors = []
        for author in article.findall('.//Author'):
            first_name = author.find('ForeName').text if author.find('ForeName') is not None else ''
            last_name = author.find('LastName').text if author.find('LastName') is not None else ''
            initials = author.find('Initials').text if author.find('Initials') is not None else ''
            full_name = f"{first_name} {last_name} {initials}".strip()
            authors.append(full_name)

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
    files = []
    ftp.dir(lambda x: files.append(x))
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
            file_id = file_info['name'].split('.')[0].split('n')[-1]
            if int(file_id) > 1245:
                detailed_files.append(file_info)
        except ValueError:
            continue

    sorted_files = sorted(detailed_files, key=lambda x: x['timestamp'], reverse=True)
    return sorted_files[:num_files]

def convert_to_chromadb_format(articles_data, rag):
    documents = []
    metadata = []
    ids = []
    timestamp = time.time()

    for article in articles_data:
        if article['abstract'] == 'No abstract available':
            article['abstract'] = ''
        document = f"{article['title']} {article['abstract']}"
        meta_data = {
            'link': f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}",
            'authors': ', '.join(article['authors']),
            'title': article['title'],
            'timestamp': timestamp
        }
        documents.append(document)
        metadata.append(meta_data)
        ids.append(article['pmid'])

    existing_ids = rag.check_id_exists(ids)
    documents = [doc for doc, exists in zip(documents, existing_ids) if not exists]
    metadata = [meta for meta, exists in zip(metadata, existing_ids) if not exists]
    ids = [id for id, exists in zip(ids, existing_ids) if not exists]

    return documents, metadata, ids

def main():
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login()
    ftp.cwd(SUBFOLDER)

    files = get_newest_files(ftp)
    files = [file['name'] for file in files if file['name'].endswith('.xml.gz')]
    latest_file = files[0] if files else None

    if latest_file:
        with open(latest_file, 'wb') as f:
            ftp.retrbinary(f'RETR {latest_file}', f.write)
        ftp.quit()

        with gzip.open(latest_file, 'rb') as f_in, open(latest_file.replace('.gz', ''), 'wb') as f_out:
            f_out.write(f_in.read())

        article_data = parse_pubmed_articles(latest_file.replace('.gz', ''))
        article_data = [article for article in article_data if article['title'] != 'No title available']
        article_data = [article for article in article_data if article['pmid'] != 'No PMID available']
        article_data = [article for article in article_data if article['pubmed_date'] != 'No PubDate']
        article_data = [article for article in article_data if article['language'] == 'eng']

        for article in article_data:
            if article['date_completed'] != 'No DateCompleted':
                article['date_completed'] = datetime.datetime.strptime(article['date_completed'], '%Y-%m-%d')
            article['pubmed_date'] = datetime.datetime.strptime(article['pubmed_date'], '%Y-%m-%d')

        two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
        article_data = [article for article in article_data if article['pubmed_date'] > two_days_ago]

        ninety_days_ago = datetime.datetime.now() - datetime.timedelta(days=730)
        article_data = [article for article in article_data if article['date_completed'] == "No DateCompleted" or article['date_completed'] > ninety_days_ago]

        print(f"Number of articles crawled: {len(article_data)}")

        os.remove(latest_file)
        os.remove(latest_file.replace('.gz', ''))

        rag = RAG(POSTGRES_LINK, POSTGRES_PORT, EMBEDDING_LINK, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
        documents, metadata, ids = convert_to_chromadb_format(article_data, rag)
        print(f"Number of articles added to the database: {len(ids)}")
        rag.add_documents(documents, metadata, ids)
    else:
        ftp.quit()
        print("No .xml.gz files found.")

if __name__ == "__main__":
    main()
