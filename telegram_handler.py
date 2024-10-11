from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import threading
from database import UserDatabase, RAG
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')

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
    endpoints = """/start registers your account with the bot\n\n
    /add_prompt Adds a prompt that is queried twice a day\n\n
    /delete_prompt Returns a selection of your prompts that you can delete\n\n
    /get_prompts Returns a list of your prompts\n\n
    /preview_prompt Returns a list of past papers for a given prompt"""
    await update.message.reply_text(endpoints)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Echo the user message
    response_string = "Use /start to register with this service. Use /help to see all commands."
    await update.message.reply_text(response_string)

async def add_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Print the prompt to the console (server-side)
    if not context.args:
        await update.message.reply_text("Please provide a prompt like '/add_prompt I want to know everything'.")
        return
    prompt = ' '.join(context.args)  # Joining all arguments into a single string as a prompt
    database = UserDatabase()
    database.connect()

    # Check if the prompt already exists
    if database.user_exists(update.message.from_user.id):
        if database.prompt_exists(update.message.from_user.id, prompt):
            await update.message.reply_text("This prompt already exists!")
        else:
            # Add the prompt to the database
            database.insert_prompt(update.message.from_user.id, prompt)
            await update.message.reply_text("Prompt added successfully!")
            print(f"Added prompt '{prompt}' for user {update.message.from_user.id}")
    else:
        await update.message.reply_text("Please register with this service first using /start.")

async def delete_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database = UserDatabase()
    database.connect()
    if database.user_exists(update.message.from_user.id):
        user_id = update.message.from_user.id
        prompts = database.get_prompts(user_id)

        if not prompts:
            await update.message.reply_text("No prompts to delete.")
            return

        keyboard = [
            [InlineKeyboardButton(prompt, callback_data=prompt) for prompt in prompts]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Please choose a prompt to delete:', reply_markup=reply_markup)
    else:
        await update.message.reply_text("Please register with this service first using /start.")

async def preview_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a prompt like '/preview_prompt I want to know everything'.")
        return
    # Print the prompt to the console (server-side)
    database = UserDatabase()
    database.connect()
    if database.user_exists(update.message.from_user.id):
        prompt = ' '.join(context.args)  # Joining all arguments into a single string as a prompt
        user_id = database.get_user_id(update.message.from_user.id)
        database.store_preview(user_id, prompt)
        db_host = "localhost"
        db_name = os.environ.get("DB_NAME")
        db_user = os.environ.get("POSTGRES_USER")
        db_password = os.environ.get("POSTGRES_PASSWORD")
        db_port = 5432
        rag = RAG(db_host, db_port, "localhost:11434", db_user, db_password, db_name)
        papers = rag.query(prompt, limit=6)
        response_string = "*Potential papers for this prompt:*"
        for paper in papers:
            link = paper['link']
            title = paper['title']
            response_string += f"\n\n*{title}*\nLink: {link}"
        await update.message.reply_markdown(response_string, disable_web_page_preview=True)
    else:
        await update.message.reply_text("Please register with this service first using /start.")
    
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    prompt_to_delete = query.data
    user_id = query.from_user.id
    
    database = UserDatabase()
    database.connect()
    database.delete_prompt(user_id, prompt_to_delete)
    await query.edit_message_text(text=f"Prompt '{prompt_to_delete}' deleted successfully.")

async def get_prompts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database = UserDatabase()
    database.connect()
    if database.user_exists(update.message.from_user.id):
        telegram_id = update.message.from_user.id
        prompts = database.get_prompts(telegram_id)

        if not prompts:
            await update.message.reply_text("No prompts found.")
            return
        
        prompts_string = '\n\n'.join(prompts)
        await update.message.reply_text(f"Your prompts:\n\n{prompts_string}")
    else:
        await update.message.reply_text("Please register with this service first using /start.")


def main():
    # Create the application and pass it your bot's token.
    print(token)
    application = Application.builder().token(token).build()

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
