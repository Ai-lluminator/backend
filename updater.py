from database import RAG, UserDatabase
import numpy as np
import time
import os
import requests

rag = RAG()
userDatabase = UserDatabase("/Users/cowolff/Documents/GitHub/AIlluminator/database.db")
userDatabase.connect()
users = userDatabase.extract_data()

for user in users['data']:
    if user['updated_at'] is None:
        updated_at = time.time() - 21600
    else:
        updated_at = user['updated_at']
    
    chat_id = userDatabase.get_chat_id(user["id"])
    for prompt in user['prompt']:
        papers = rag.query(prompt, limit=4, updated_at=updated_at)
        message = f"*Update:*\nHere are some papers for your prompt '{prompt}' that might interest you:\n\n"
        number_of_message = 0
        for paper in zip(papers['documents'][0], papers['metadatas'][0], papers['distances'][0]):
            link = paper[1]['link']
            title = paper[1]['title']
            distance = paper[2]
            if distance > 0.5:
                message += f"*{title}*\nLink: {link}\n\n"
                number_of_message += 1

        userDatabase.record_messages_sent(user["id"], number_of_message)
        if number_of_message > 0:
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(url, data=data)
    userDatabase.update_user(user["id"], time.time())