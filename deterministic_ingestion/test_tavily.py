#!/usr/bin/env python3
"""Test the Tavily search API used by verify_identity.py."""
import os
import requests

key = os.environ.get('TAVILY_API_KEY')
if not key:
    raise SystemExit('Set TAVILY_API_KEY before running this test')

url = os.environ.get('TAVILY_API_URL', 'https://api.tavily.com/search')
headers = {'Content-Type': 'application/json'}
payload = {
    'api_key': key,
    'query': os.environ.get('TEST_PROFILE', 'https://www.linkedin.com/jobs/view/123456'),
    'search_depth': 'basic',
    'max_results': 5,
    'include_answer': False,
}

r = requests.post(url, json=payload, headers=headers, timeout=10)
print('URL:', url)
print('Status:', r.status_code)
try:
    print('Response:', r.json())
except Exception:
    print('Raw body:', r.text)

