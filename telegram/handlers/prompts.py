from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from database import UserDatabase, RAG
from handlers.config import Config
from handlers.helper import get_url

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
        prompt_exist, prompt_id, user_id = database.prompt_exists(update.message.from_user.id, prompt)

        if prompt_exist:
            database.set_prompt_active(user_id, prompt_id)
            await update.message.reply_text("Prompt added successfully!")
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
        telegram_id = update.message.from_user.id
        prompts, ids = database.get_prompts(telegram_id, active=True)

        if not prompts:
            await update.message.reply_text("No prompts to delete.")
            return

        show_prompts = []
        for prompt in prompts:
            if len(prompt) > 10:
                show_prompts.append(prompt[:10] + "...")
            else:
                show_prompts.append(prompt)

        keyboard = [
            [InlineKeyboardButton(show_prompt, callback_data=f"delete_{id}") for show_prompt, id in zip(show_prompts, ids)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Please choose a prompt to delete:', reply_markup=reply_markup)
    else:
        await update.message.reply_text("Please register with this service first using /start.")


async def get_prompts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    database = UserDatabase()
    database.connect()
    if database.user_exists(update.message.from_user.id):
        telegram_id = update.message.from_user.id
        prompts, ids = database.get_prompts(telegram_id, active=True)

        if not prompts:
            await update.message.reply_text("No prompts found.")
            return
        
        prompts_string = '\n\n'.join(prompts)
        await update.message.reply_text(f"Your prompts:\n\n{prompts_string}")
    else:
        await update.message.reply_text("Please register with this service first using /start.")