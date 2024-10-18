from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from database import UserDatabase, RAG
from handlers.config import Config
from handlers.helper import get_url

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Sends a message to the user
    database = UserDatabase()
    database.connect()
    if not database.user_exists(update.message.from_user.id):
        database.insert_user(update.message.chat_id, update.message.from_user.id)
        await update.message.reply_text('You successfully registered with this service. Use /add_prompt to add a prompt. Use /help to see all commands.')
    else:
        await update.message.reply_text('You are already registered with this service. Use /add_prompt to add a prompt. Use /help to see all commands.')

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Sends a message to the user
    database = UserDatabase()
    database.connect()
    database.delete_user(update.message.from_user.id)
    await update.message.reply_text('Goodbye!')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Sends a message to the user
    endpoints = """*Available Commands*

    /start registers your account with the bot

    /add\\_prompt Adds a prompt that is queried twice a day

    /delete\\_prompt Returns a selection of your prompts that you can delete

    /get\\_prompts Returns a list of your prompts

    /preview\\_prompt Returns a list of past papers for a given prompt

    /summarize Returns a LLM generated summary of the paper"""
    await update.message.reply_markdown(endpoints)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Echo the user message
    response_string = "Use /start to register with this service. Use /help to see all commands."
    await update.message.reply_text(response_string)

async def delete_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Sends a message to the user
    database = UserDatabase()
    database.connect()
    database.delete_user(update.message.from_user.id)
    await update.message.reply_text('All of your data has been removed!')