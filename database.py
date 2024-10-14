import psycopg2
from ollama import Client
import json
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

class LargeEmbeddingFunction():
    def __init__(self, model_name: str, embedding_link: str) -> None:
        # This model supports two prompts: "s2p_query" and "s2s_query" for sentence-to-passage and sentence-to-sentence tasks, respectively.
        self.model_name = model_name
        self.client = Client(embedding_link)

    def __call__(self, input):
        response = self.client.embed(model=self.model_name, input=input)
        embedding = response["embeddings"][0]

        return json.dumps(embedding)

class RAG:

    def __init__(self, postgres_link, postgres_port, embedding_link, db_user, db_password, db_name) -> None:
        self.embedding_model = LargeEmbeddingFunction("cowolff/science_bge_large", embedding_link)
        # self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="dunzhang/stella_en_400M_v5")
        self.conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=postgres_link,
            port=postgres_port,  # The port you exposed in docker-compose.yml
            database=db_name
        )

    def vectorize(self, document):
        embedding = self.embedding_model(document)
        return embedding
    
    def check_id_exists(self, urls):
        # Checks whether the urls are already in the papers table and returns a boolean list
        cur = self.conn.cursor()
        cur.execute("SELECT link FROM papers WHERE link = ANY(%s);", (urls,))
        # cur.execute("SELECT link FROM papers")
        results = cur.fetchall()
        results = [result[0] for result in results]
        return results
    
    def check_summary_exists(self, paper_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id, summary FROM summary WHERE paper_id = %s;", (paper_id,))
        results = cur.fetchall()
        if len(results) == 0:
            return False, ""
        else:
            return True, results[0][1]

    def add_documents(self, urls, titles, contents):
        vectors = [self.vectorize(content) for content in contents]
        cur = self.conn.cursor()

        for url, title, content, vector in zip(urls, titles, contents, vectors):
            cur.execute("INSERT INTO papers (link, title, content, embedding) VALUES (%s, %s, %s, %s)", (url, title, content, vector))

        self.conn.commit()
        cur.close()

    def get_document(self, paper_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id, title, content FROM papers WHERE id = %s;", (paper_id,))
        id, title, content = cur.fetchone()
        cur.close()
        return id, title, content

   
    def query(self, prompt, limit=4, updated_at=None):
        cur = self.conn.cursor()
        query_embedding = self.vectorize(prompt)

        if updated_at:
            cur.execute(
                """SELECT id, title, link, 1 - (embedding <=> %s) AS cosine_similarity
                FROM papers
                WHERE created_at > %s
                ORDER BY cosine_similarity DESC
                LIMIT %s;""",
                (query_embedding, updated_at, limit)
            )
        else:
            cur.execute(
                """SELECT id, title, link, 1 - (embedding <=> %s) AS cosine_similarity
                FROM papers
                ORDER BY cosine_similarity DESC
                LIMIT %s;""",
                (query_embedding, limit)
            )

        papers = []
        for row in cur.fetchall():
            try:
                paper_data = {
                    "id": row[0],
                    "title": row[1],
                    "link": row[2]
                }
                papers.append(paper_data)
            except Exception as e:
                print(e)
        cur.close()
        return papers

class UserDatabase:
    def __init__(self):
        # self.db_host = os.environ.get("DB_HOST")
        self.db_host = os.environ.get("DB_HOST")
        self.db_name = os.environ.get("DB_NAME")
        self.db_user = os.environ.get("POSTGRES_USER")
        self.db_password = os.environ.get("POSTGRES_PASSWORD")
        self.db_port = 5432

    def connect(self):
        """Establish a connection to the PostgreSQL database."""
        self.conn = psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            port=self.db_port
        )
        self.conn.autocommit = True

    def close(self):
        """Close the connection to the PostgreSQL database."""
        if self.conn:
            self.conn.close()

    def extract_data(self):
        """Extract data and format it according to the specified dictionary format."""
        self.connect()
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        query = """
        SELECT u.email AS name, u.id AS id, u.telegram_id, p.prompt, u.updated_at
        FROM users u
        JOIN prompts p ON u.id = p.user_id;
        """
        cursor.execute(query)

        users_data = {}
        for row in cursor.fetchall():
            user_key = row['id']
            if user_key not in users_data:
                users_data[user_key] = {
                    'telegram_id': row['telegram_id'],
                    'prompt': [],
                    'name': row['name'],
                    'updated_at': row['updated_at']
                }
            users_data[user_key]['prompt'].append(row['prompt'])

        data_list = [{"id": key, "telegram_id": data['telegram_id'], "prompt": data['prompt'], "updated_at": data['updated_at']} for key, data in users_data.items()]
        self.close()
        return {"data": data_list}

    def user_exists(self, telegram_id):
        """Check if a user exists in the database."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id = %s;", (telegram_id,))
        count = cursor.fetchone()[0]
        self.close()
        return count > 0

    def insert_user(self, chat_id, telegram_id):
        """Insert a new user into the database."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (chat_id, telegram_id) VALUES (%s, %s);", (chat_id, telegram_id))
            self.conn.commit()
        finally:
            self.close()

    def insert_prompt(self, telegram_id, prompt, active=True):
        """Insert a new prompt into the database."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s;", (telegram_id,))
        user_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO prompts (user_id, prompt, active) VALUES (%s, %s, %s);", (user_id, prompt, active))
        self.conn.commit()
        cursor.close()

         # return prompt_id
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM prompts WHERE user_id = %s AND prompt = %s;", (user_id, prompt))
        prompt_id = cursor.fetchone()[0]
        self.close()
        return prompt_id

    def delete_user(self, telegram_id):
        """Delete a user from the database."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s;", (telegram_id,))
        user_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM prompts WHERE user_id = %s;", (user_id,))
        cursor.execute("DELETE FROM users WHERE telegram_id = %s;", (telegram_id,))
        self.close()

    def get_prompts(self, telegram_id):
        """Get all prompts for a user."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s;", (telegram_id,))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT prompt FROM prompts WHERE user_id = %s;", (user_id,))
        prompts = [row[0] for row in cursor.fetchall()]
        self.close()
        return prompts

    def prompt_exists(self, telegram_id, prompt):
        """Check if a prompt exists for a user."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s;", (telegram_id,))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM prompts WHERE user_id = %s AND prompt = %s;", (user_id, prompt))
        results = cursor.fetchall()
        if len(results) == 0:
            self.close()
            return False, -1, user_id
        else:
            self.close()
            return True, results[0][0], user_id
        
    def set_prompt_active(self, user_id, prompt_id):
        """Set the prompt to active."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE prompts SET active = TRUE WHERE user_id = %s AND id = %s;", (user_id, prompt_id))
        self.close()

    def delete_prompt(self, telegram_id, prompt):
        """Delete a prompt for a user."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s;", (telegram_id,))
        user_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM prompts WHERE user_id = %s AND prompt = %s;", (user_id, prompt))
        self.close()

    def get_user_id(self, telegram_id):
        """Get the user ID based on telegram ID."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s;", (telegram_id,))
        user_id = cursor.fetchone()[0]
        self.close()
        return user_id

    def get_chat_id(self, user_id):
        """Get the chat ID based on user ID."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT chat_id FROM users WHERE id = %s;", (user_id,))
        chat_id = cursor.fetchone()[0]
        self.close()
        return chat_id

    def record_message_sent(self, user_id, prompt_id):
        """Record the number of messages sent by a user."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO messages_sent (user_id, prompt_id) VALUES (%s, %s);", (user_id, prompt_id))
        cursor.close()

        # Get message id of the last sent message to the user
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM messages_sent WHERE user_id = %s ORDER BY id DESC LIMIT 1;", (user_id,))
        message_id = cursor.fetchone()[0]
        self.close()
        return message_id
    
    def get_papers_from_last_message(self, user_id):
        """Get papers from the last message sent to the user."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM messages_sent WHERE user_id = %s ORDER BY id DESC LIMIT 1;", (user_id,))
        message_id = cursor.fetchone()[0]
        cursor.execute("SELECT paper_id FROM paper_in_message WHERE message_id = %s;", (message_id,))
        paper_ids = [row[0] for row in cursor.fetchall()]
        papers = []
        print(paper_ids)
        for paper_id in paper_ids:
            cursor.execute("SELECT title, link FROM papers WHERE id = %s;", (paper_id,))
            title, link = cursor.fetchone()
            papers.append({"id": paper_id, "title": title, "link": link})
        self.close()
        return papers
    
    def add_paper_to_message(self, message_id, paper_id):
        """Add a paper to a message."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO paper_in_message (message_id, paper_id) VALUES (%s, %s);", (message_id, paper_id))
        self.close()

    def record_num_users(self, num_users):
        """Record the total number of users."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO number_users (num_users) VALUES (%s);", (num_users,))
        self.close()

    def store_preview(self, user_id, prompt):
        """Store a preview of the prompt."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO preview_papers (user_id, prompt) VALUES (%s, %s);", (user_id, prompt))
        self.close()

    def update_user(self, user_id, updated_at):
        """Update the user’s last updated timestamp."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET updated_at = %s WHERE id = %s;", (updated_at, user_id))
        self.close()
