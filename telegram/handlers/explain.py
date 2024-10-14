from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from database import UserDatabase, RAG
from handlers.config import Config
from handlers.helper import get_url

async def summarize_paper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database = UserDatabase()
    database.connect()

    if database.user_exists(update.message.from_user.id):
        telegram_id = update.message.from_user.id
        user_id = database.get_user_id(telegram_id)
        papers = database.get_papers_from_last_message(user_id)

        if not papers:
            await update.message.reply_text("No papers found.")
            return

        keyboard = [
            [InlineKeyboardButton(paper['title'], callback_data=f"summarize_{paper['id']}") for paper in papers]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Please choose a paper to summarize:', reply_markup=reply_markup)