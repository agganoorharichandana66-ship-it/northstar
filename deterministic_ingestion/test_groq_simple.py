#!/usr/bin/env python3
import os, requests

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"}
payload = {
    "model": "openai/gpt-oss-20b",   # use a model from your /models list
    "messages": [
        {"role": "system", "content": "You are an assistant that scores items."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
}

r = requests.post(url, json=payload, headers=headers, timeout=30)
print(r.status_code)
print(r.json())

