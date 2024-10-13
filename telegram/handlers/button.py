from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from database import UserDatabase, RAG
import os
from dotenv import load_dotenv
from handlers.config import Config
from ollama import Client

async def remove_prompt_from_database(query, user_id: int, prompt: str) -> None:
    database = UserDatabase()
    database.connect()
    database.delete_prompt(user_id, prompt)
    await query.edit_message_text(text=f"Prompt '{prompt}' deleted successfully.")

async def summarize_paper(query, user_id: int, paper_id: int) -> None:
    rag = RAG(Config.DB_HOST, Config.DB_PORT, Config.EMBEDDING_LINK, Config.DB_USER, Config.DB_PASSWORD, Config.DB_NAME)
    id, title, content = rag.get_document(paper_id)

    ollama = Client(Config.EMBEDDING_LINK)

    print(content)

    messages = [
        {
            "role": "user",
            "content": f"Please summarize the following paper for me. \n Paper: {content}"
        }
    ]

    summary = ollama.chat(model="qwen2.5:1.5b", messages=messages)

    summary_text = summary["message"]["content"]

    await query.edit_message_text(text=summary_text)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    input_data = query.data

    if input_data.startswith("delete_"):
        prompt_to_delete = input_data.split("_")[1]
        user_id = query.from_user.id
        await remove_prompt_from_database(query, user_id, prompt_to_delete)
    
    if input_data.startswith("summarize_"):
        paper_id = int(input_data.split("_")[1])
        user_id = query.from_user.id
        await summarize_paper(query, user_id, paper_id)