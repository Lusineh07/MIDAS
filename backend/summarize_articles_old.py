import http.client
import json
import os
from dotenv import load_dotenv

def summarize_articles(formatted_string):

    # Loads APY token from .env file
    load_dotenv()
    APY_TOKEN = os.getenv("APY_TOKEN")

    # Establishes connection with apyhub
    conn = http.client.HTTPSConnection("api.apyhub.com")

    # Payload obj for API call body
    payload_obj = {
        "text": formatted_string,
        "summary_length": "short",
        "output_language": "en"
    }

    # API body
    payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")

    # API call headers
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "apy-token": APY_TOKEN
    }

    # Makes HTTP request to API through established connection
    conn.request("POST", "/ai/summarize-text", body=payload, headers=headers)
    # Gets response
    res = conn.getresponse()
    # Parses response
    data = res.read()

    return data.decode("utf-8", errors="replace")
