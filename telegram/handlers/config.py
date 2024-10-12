import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class to load and store environment variables."""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('POSTGRES_USER')
    DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    DB_PORT = os.getenv('DB_PORT')
    EMBEDDING_LINK = os.getenv('EMBEDDING_LINK')
    
    SECRET = os.getenv('SECRET')
    FRONTEND_URL = os.getenv('FRONTEND_URL')