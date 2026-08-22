#!/usr/bin/env python3
"""Fetch RSS/Atom feeds (LinkedIn, X jobs) and write raw markdown files.
Requires `feedparser`.
"""
import os, json, re
from datetime import datetime
import feedparser

BASE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, 'config.example.json')
with open(CONFIG_PATH, 'r') as f:
    cfg = json.load(f)

OUT_DIR = os.path.normpath(os.path.join(BASE, '..', cfg['paths']['raw_jobs_dir']))
os.makedirs(OUT_DIR, exist_ok=True)

feeds = []
if cfg.get('rss', {}).get('linkedin_rss'):
    feeds.append(cfg['rss']['linkedin_rss'])
if cfg.get('rss', {}).get('x_jobs_rss'):
    feeds.append(cfg['rss']['x_jobs_rss'])


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", '-', s.lower())
    return re.sub(r"-+", '-', s).strip('-')[:60]

for feed_url in feeds:
    d = feedparser.parse(feed_url)
    for entry in d.entries:
        title = entry.get('title', 'No title')
        link = entry.get('link', '')
        date = entry.get('published', datetime.utcnow().isoformat() + 'Z')
        raw_id = entry.get('id', link or title)
        slug = slugify(title)
        filename = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{slug}.md"
        out_path = os.path.join(OUT_DIR, filename)
        front = ['---', f"source: rss", f"date: {date}", f"url: {link}", f"raw_id: {raw_id}", '---', '\n']
        content = entry.get('summary', entry.get('description', ''))
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write('\n'.join(front))
            out.write(content)
        print('Wrote', out_path)

print('Done')