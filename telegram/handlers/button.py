from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from database import UserDatabase, RAG
import os
from dotenv import load_dotenv
from handlers.config import Config

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    prompt_to_delete = query.data
    user_id = query.from_user.id
    
    database = UserDatabase()
    database.connect()
    database.delete_prompt(user_id, prompt_to_delete)
    await query.edit_message_text(text=f"Prompt '{prompt_to_delete}' deleted successfully.")