#!/usr/bin/env python3
"""Simple deterministic email inbox importer.
Reads plain-text files from `inbox_emails/` and writes raw markdown files to configured raw_jobs_dir.
This is intentionally simple — replace with an IMAP fetcher for automation.
"""
import os
import sys
import json
import argparse
from datetime import datetime
import re

BASE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, 'config.example.json')

with open(CONFIG_PATH, 'r') as f:
    cfg = json.load(f)

INBOX = os.path.join(BASE, cfg['email']['inbox_dir'])
OUT_DIR = os.path.join(BASE, '..', cfg['paths']['raw_jobs_dir'])
OUT_DIR = os.path.normpath(OUT_DIR)

os.makedirs(INBOX, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

def slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", '-', s)
    s = re.sub(r"-+", '-', s).strip('-')
    return s[:60]

for fname in os.listdir(INBOX):
    if not fname.lower().endswith(('.txt', '.eml', '.md')):
        continue
    path = os.path.join(INBOX, fname)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read().strip()
    # Heuristics: look for subject, title, company
    subject = ''
    m = re.search(r'^Subject:\s*(.*)$', text, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        subject = m.group(1).strip()
    title = ''
    m = re.search(r'^Title:\s*(.*)$', text, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        title = m.group(1).strip()
    company = ''
    m = re.search(r'^Company:\s*(.*)$', text, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        company = m.group(1).strip()
    if not title:
        title = subject or (text.splitlines()[0] if text else 'No title')
    date = datetime.utcnow().isoformat() + 'Z'
    slug = slugify(title + '-' + (company or ''))
    filename = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{slug}.md"
    out_path = os.path.join(OUT_DIR, filename)
    front = [
        '---',
        f"source: email",
        f"date: {date}",
        f"raw_id: {slug}",
    ]
    if company:
        front.append(f"company: {company}")
    front += ['---', '\n']
    body = text
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(front))
        out.write(body)
    print('Wrote', out_path)
    # Move processed files to inbox_emails/processed
    proc_dir = os.path.join(INBOX, 'processed')
    os.makedirs(proc_dir, exist_ok=True)
    os.rename(path, os.path.join(proc_dir, fname))

print('Done')