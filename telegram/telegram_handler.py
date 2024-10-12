from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import threading
from database import UserDatabase, RAG
import os
from dotenv import load_dotenv

from handlers.config import Config
from handlers.helper import get_url
from handlers.basic import start, stop, help, handle_message, delete_me
from handlers.preview import preview_prompt
from handlers.prompts import add_prompt, delete_prompt, get_prompts
from handlers.button import button
from handlers.explain import summarize_paper

load_dotenv()

def main():
    # Create the application and pass it your bot's token.
    application = Application.builder().token(Config.TOKEN).build()

    # Add a command handler for command '/start'
    application.add_handler(CommandHandler('start', start))

    # Add a command handler for command '/add_prompt'
    application.add_handler(CommandHandler('add_prompt', add_prompt))

    # Add a command handler for command '/delete_prompt'
    application.add_handler(CommandHandler('delete_prompt', delete_prompt))
    application.add_handler(CallbackQueryHandler(button))

    # Add a command handler for command '/get_prompts'
    application.add_handler(CommandHandler('get_prompts', get_prompts))

    # Add a command handler for command '/preview_prompt'
    application.add_handler(CommandHandler('preview_prompt', preview_prompt))

    # Add a command handler for command '/summarize_paper'
    application.add_handler(CommandHandler('summarize', summarize_paper))
    application.add_handler(CallbackQueryHandler(button))

    # Add a command handler for command '/delete_me'
    application.add_handler(CommandHandler('delete_me', delete_me))

    # Add a command handler for command '/help'
    application.add_handler(CommandHandler('help', help))

    # Add a command handler for command '/stop'
    application.add_handler(CommandHandler('stop', stop))

    # Add a message handler for all messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until you press Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()
