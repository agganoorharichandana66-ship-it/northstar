#!/usr/bin/env python3
"""Fetch recent repo activity for a GitHub user/org and save as raw markdown entries.
Uses the public GitHub events API. For higher rate limits set GITHUB_TOKEN env var and edit config.
"""
import os, json, re, requests
from datetime import datetime

BASE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, 'config.example.json')
with open(CONFIG_PATH, 'r') as f:
    cfg = json.load(f)

OUT_DIR = os.path.normpath(os.path.join(BASE, '..', cfg['paths']['raw_learning_dir']))
os.makedirs(OUT_DIR, exist_ok=True)

username = cfg.get('github', {}).get('username')
if not username:
    print('Set username in config.example.json')
    raise SystemExit(1)

api = f'https://api.github.com/users/{username}/events'
headers = {}
import os as _os
if _os.getenv(cfg.get('github', {}).get('token_env_var', 'GITHUB_TOKEN')):
    headers['Authorization'] = f"token {_os.getenv(cfg.get('github', {}).get('token_env_var', 'GITHUB_TOKEN'))}"

r = requests.get(api, headers=headers, timeout=10)
if r.status_code != 200:
    print('GitHub API error', r.status_code, r.text)
    raise SystemExit(1)

for ev in r.json()[:50]:
    t = ev.get('type')
    repo = ev.get('repo', {}).get('name')
    created = ev.get('created_at', datetime.utcnow().isoformat() + 'Z')
    raw_id = ev.get('id')
    title = f"GitHub {t} — {repo}"
    filename = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_github_{repo.replace('/', '_')}.md"
    out_path = os.path.join(OUT_DIR, filename)
    front = ['---', f"source: github", f"date: {created}", f"raw_id: {raw_id}", f"repo: {repo}", '---', '\n']
    body = json.dumps(ev, indent=2)
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(front))
        out.write(body)
    print('Wrote', out_path)

print('Done')