import requests
import os
import json

SECRET = os.getenv('SECRET')
FRONTEND_URL = os.getenv('FRONTEND_URL')
ENDPOINT = f"{FRONTEND_URL}/api/links"

def get_url(url, user_id, prompt_id, paper_id):
    # Define the request payload
    payload = {
        "paper_id": paper_id,
        "paper_url": url,
        "prompt_id": prompt_id,
        "user_id": user_id
    }

    # Set the headers, including the Authorization header
    headers = {
        "Content-Type": "application/json",
        "Authorization": SECRET
    }

    response = requests.post(ENDPOINT, headers=headers, data=json.dumps(payload))

    if response.status_code != 201:
        return url
    else:
        return response.json()["data"]["url"]