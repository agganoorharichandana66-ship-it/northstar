#!/usr/bin/env python3
import os, requests

url = "https://api.tavily.com/v1/search"
headers = {"Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}"}
params = {"query": "latest AI research"}  # Tavily expects query params

r = requests.get(url, params=params, headers=headers, timeout=10)
print("Status:", r.status_code)
try:
    print("Response:", r.json())
except Exception:
    print("Raw body:", r.text)

