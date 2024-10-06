import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import sqlite3
from ollama import Client

class LargeEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str) -> None:
        # This model supports two prompts: "s2p_query" and "s2s_query" for sentence-to-passage and sentence-to-sentence tasks, respectively.
        self.model_name = model_name
        self.client = Client("http://localhost:7869")

    def __call__(self, input: Documents) -> Embeddings:
        response = self.client.embed(model=self.model_name, input=input)
        print(response.keys())
        embedding = response["embeddings"]
        # embed the documents somehow
        return embedding

class RAG:

    def __init__(self) -> None:
        self.embedding_model = LargeEmbeddingFunction("mxbai-embed-large")
        # self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="dunzhang/stella_en_400M_v5")
        self.client = chromadb.PersistentClient(path="chromadb")
        self.__init_database()
        self.collection = self.client.get_or_create_collection(
            name=f"Green-AI",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_model,
        )

    def __init_database(self):
        collection_exists = "Green-AI" in [collection.name for collection in self.client.list_collections()]
        if not collection_exists:
            collection = self.client.create_collection(
                name=f"Green-AI",
                metadata={"hnsw:space": "cosine"}, # l2 is the default
                embedding_function=self.embedding_model,
            )

    def vectorize(self, document):
        embedding = self.embedding_model(document)
        return embedding
    
    def check_id_exists(self, ids):
        if isinstance(ids, list):
            exists = [id in self.collection.get()["ids"] for id in ids]
            return exists
        else:
            if id in self.collection.get()["ids"]:
                return True
            return False

    def add_documents(self, documents, metadata, ids):
        self.collection.add(
            documents=documents,
            metadatas=metadata,
            ids=ids,
        )

    def query(self, prompt, limit=1, updated_at=None):
        if updated_at is None:
            return self.collection.query(query_texts=prompt, n_results=limit)
        else:
            statement = {
                "timestamp": {
                    "$gt": updated_at
                }
            }
            return self.collection.query(query_texts=prompt, n_results=limit, where=statement)
    

class UserDatabase:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        """Establish a connection to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by names

    def close(self):
        """Close the connection to the SQLite database."""
        if self.conn:
            self.conn.close()

    def extract_data(self):
        """Extract data and format it according to the specified dictionary format."""
        cursor = self.conn.cursor()
        # Join users and prompts tables to get the required information
        query = """
        SELECT u.email AS name, u.id AS id, u.telegram_id, p.prompt, u.updated_at
        FROM users u
        JOIN prompts p ON u.id = p.user_id
        """
        cursor.execute(query)

        users_data = {}
        for row in cursor.fetchall():
            user_key = row['id']
            if user_key not in users_data:
                users_data[user_key] = {}
                users_data[user_key]['telegram_id'] = row['telegram_id']
                users_data[user_key]['prompt'] = []
                users_data[user_key]['name'] = row['name']
                users_data[user_key]['updated_at'] = row['updated_at']
            users_data[user_key]['prompt'].append(row['prompt'])

        # Format the data as required
        data_list = [{"id": key, "telegram_id": data['telegram_id'], "prompt": data['prompt'], "updated_at":data['updated_at']} for key, data in users_data.items()]

        return {"data": data_list}

    def user_exists(self, telegram_id):
        """Check if a user exists in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id = ?", (telegram_id,))
        count = cursor.fetchone()[0]
        return count > 0

    def insert_user(self, chat_id, telegram_id):
        """Insert a new user into the database."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            # Insert the user into the users table
            cursor.execute("INSERT INTO users (chat_id, telegram_id) VALUES (?, ?)", (chat_id, telegram_id))
            self.conn.commit()
        finally:
            self.close()

    def insert_prompt(self, telegram_id, prompt):
        """Insert a new prompt into the database."""
        cursor = self.conn.cursor()
        # Get the user's ID
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()[0]
        # Insert the prompt into the prompts table
        cursor.execute("INSERT INTO prompts (user_id, prompt) VALUES (?, ?)", (user_id, prompt))
        self.conn.commit()

    def delete_user(self, telegram_id):
        """Delete a user from the database."""
        cursor = self.conn.cursor()
        # Get the user's ID
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()[0]
        # Delete the user's prompts
        cursor.execute("DELETE FROM prompts WHERE user_id = ?", (user_id,))
        # Delete the user
        cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()

    def get_prompts(self, telegram_id):
        """Get all prompts for a user."""
        cursor = self.conn.cursor()
        # Get the user's ID
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()[0]
        # Get the user's prompts
        cursor.execute("SELECT prompt FROM prompts WHERE user_id = ?", (user_id,))
        prompts = [row[0] for row in cursor.fetchall()]
        return prompts

    def prompt_exists(self, telegram_id, prompt):
        """Check if a prompt exists for a user."""
        cursor = self.conn.cursor()
        # Get the user's ID
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()[0]
        # Check if the prompt exists
        cursor.execute("SELECT COUNT(*) FROM prompts WHERE user_id = ? AND prompt = ?", (user_id, prompt))
        count = cursor.fetchone()[0]
        return count > 0

    def delete_prompt(self, telegram_id, prompt):
        cursor = self.conn.cursor()
        # Get the user's ID
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()[0]
        # Delete the prompt
        cursor.execute("DELETE FROM prompts WHERE user_id = ? AND prompt = ?", (user_id, prompt))
        self.conn.commit()

    def get_user_id(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()[0]
        return user_id

    def get_chat_id(self, user_id):
        cursor = self.conn.cursor()
        print(type(user_id))
        cursor.execute("SELECT chat_id FROM users WHERE id = ?", (user_id,))
        chat_id = cursor.fetchone()[0]
        return chat_id
    
    def record_messages_sent(self, user_id, messages_sent):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO messages_sent (num_papers, user_id) VALUES (?, ?)", (messages_sent, user_id))
        self.conn.commit()

    def record_num_users(self, num_users):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO number_users (num_users) VALUES (?)", (num_users,))
        self.conn.commit()

    def store_preview(self, user_id, prompt):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO preview_papers (user_id, prompt) VALUES (?, ?)", (user_id, prompt))
        self.conn.commit()

    def update_user(self, user_id, updated_at):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET updated_at = ? WHERE id = ?", (updated_at, user_id))
        self.conn.commit()