import os
import requests
import datetime
from ollama import Client
import psycopg2  # Assuming PostgreSQL, change if needed
from psycopg2.extras import RealDictCursor
from database import RAG, UserDatabase
from dotenv import load_dotenv
from helper import get_url
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)

# Telegram bot token from environment variable
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Database connection details
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_PORT = int(os.getenv('DB_PORT'))
EMBEDDING_LINK = os.getenv('EMBEDDING_LINK')

SECRET = os.getenv('SECRET')
FRONTEND_URL = os.getenv('FRONTEND_URL')

# Establish database connection
def connect_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logging.info('Database connection established successfully.')
        return conn
    except Exception as e:
        logging.error(f'Failed to connect to database: {e}')
        raise

# Retrieve all users
def get_all_users(conn):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, chat_id FROM users;")
            users = cur.fetchall()
        logging.info('Successfully retrieved users from database.')
        return users
    except Exception as e:
        logging.error(f'Error retrieving users: {e}')
        raise

# Retrieve all prompts for a given user where active=True
def get_user_prompts(conn, user_id):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, prompt FROM prompts WHERE user_id = %s AND active = TRUE;", (user_id,))
            prompts = cur.fetchall()
        logging.info(f'Successfully retrieved prompts for user {user_id}.')
        return [{'id': prompt['id'], 'prompt': prompt['prompt']} for prompt in prompts]
    except Exception as e:
        logging.error(f'Error retrieving prompts for user {user_id}: {e}')
        raise

# Embed the prompts using ollama.embed
def embed_prompts(prompts):
    embeddings = []
    for prompt in prompts:
        try:
            client = Client(EMBEDDING_LINK)
            response = client.embed(model="all-minilm", input=prompt["prompt"])
            current_data = {"prompt_id": prompt["id"], "embedding": response["embeddings"][0]}
            embeddings.append(current_data)
            logging.info(f'Embedding generated for prompt {prompt["id"]}.')
        except Exception as e:
            logging.error(f'Error embedding prompt {prompt["id"]}: {e}')
            raise
    return embeddings

# Retrieve the 4 most similar papers from the last 24 hours (pseudo code, assumes a papers API or database)
def get_similar_papers(prompt):
    try:
        last_24_hours = datetime.datetime.now() - datetime.timedelta(days=1)
        rag = RAG(DB_HOST, DB_PORT, EMBEDDING_LINK, DB_USER, DB_PASSWORD, DB_NAME)
        similar_papers = rag.query(prompt, limit=4, updated_at=last_24_hours)
        logging.info('Successfully retrieved similar papers.')
        return similar_papers
    except Exception as e:
        logging.error(f'Error retrieving similar papers for embedding: {e}')
        raise

# Send papers via Telegram
def send_papers_via_telegram(chat_id, papers, user_id, prompt_id, prompt):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    message = "New papers for your prompt\n'{}':\n\n".format(prompt['prompt'])
    userDatabase = UserDatabase()
    message_id = userDatabase.record_message_sent(user_id, prompt_id)
    for paper in papers:
        redirect_url = get_url(paper['link'], user_id, prompt_id, paper['id'])
        message += f"*{paper['title']}*\n[Link to Paper]({redirect_url})\n\n"
        userDatabase.add_paper_to_message(message_id, paper['id'])
    
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            logging.error(f"Error sending message to chat_id {chat_id}: {response.text}")
        else:
            logging.info(f"Successfully sent message to chat_id {chat_id}.")
    except Exception as e:
        logging.error(f'Error sending Telegram message to chat_id {chat_id}: {e}')
        raise

# Main function
def main():
    try:
        conn = connect_db()
        try:
            # Step 1: Retrieve all users
            users = get_all_users(conn)
            
            # Step 2: For each user, retrieve prompts and generate embeddings
            for user in users:
                user_id = user['id']
                chat_id = user['chat_id']
                
                prompts = get_user_prompts(conn, user_id)
                if not prompts:
                    logging.info(f'No active prompts found for user {user_id}.')
                    continue
                
                # Step 4: For each embedding, get similar papers
                for prompt in prompts:
                    similar_papers = get_similar_papers(prompt['prompt'])
                    
                    # Step 5: Send papers to the user via Telegram
                    send_papers_via_telegram(chat_id, similar_papers, user_id, prompt["id"], prompt)
                    
        finally:
            conn.close()
            logging.info('Database connection closed.')
    except Exception as e:
        logging.critical(f'An unexpected error occurred: {e}')

if __name__ == '__main__':
    main()