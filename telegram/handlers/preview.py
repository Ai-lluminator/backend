from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from database import UserDatabase, RAG
from handlers.config import Config
from handlers.helper import get_url

def escape_markdown(text):
    special_chars = [
        '-'
    ]
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

async def preview_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a prompt like '/preview_prompt I want to know everything'.")
        return
    # Print the prompt to the console (server-side)
    database = UserDatabase()
    database.connect()
    if database.user_exists(update.message.from_user.id):
        prompt = ' '.join(context.args)  # Joining all arguments into a single string as a prompt
        telegram_id = update.message.from_user.id
        user_id = database.get_user_id(telegram_id)
        prompt_id = database.insert_prompt(telegram_id, prompt, active=False)
        rag = RAG(Config.DB_HOST, Config.DB_PORT, Config.EMBEDDING_LINK, Config.DB_USER, Config.DB_PASSWORD, Config.DB_NAME)
        papers = rag.query(prompt, limit=6)
        message_id = database.record_message_sent(user_id, prompt_id)
        response_string = "*Potential papers for this prompt:*"
        for paper in papers:
            redirect_url = get_url(paper['link'], user_id, prompt_id, paper['id'])
            title = escape_markdown(paper['title'])
            response_string += f"\n\n*{paper['title']}*\nLink: {redirect_url}"
            database.add_paper_to_message(message_id, paper['id'])

        await update.message.reply_markdown(response_string, disable_web_page_preview=True)
    else:
        await update.message.reply_text("Please register with this service first using /start.")