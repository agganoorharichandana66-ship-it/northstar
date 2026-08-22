#!/usr/bin/env python3
"""Fetch configured RSS/Atom feeds and save entries as raw job markdown."""
import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone

try:
    import feedparser
except ImportError:
    raise SystemExit('Missing dependency: install it with: python -m pip install feedparser')

BASE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, 'config.json')
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(BASE, 'config.example.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

OUT_DIR = os.path.normpath(os.path.join(BASE, '..', cfg['paths']['raw_jobs_dir']))
os.makedirs(OUT_DIR, exist_ok=True)

rss_cfg = cfg.get('rss', {})
feeds = []
if os.getenv('RSS_FEEDS'):
    feeds.extend(url.strip() for url in os.getenv('RSS_FEEDS').split(',') if url.strip())
else:
    for key in ('linkedin_rss', 'x_jobs_rss'):
        value = rss_cfg.get(key, '')
        if value:
            feeds.append(value)
    feeds.extend(url for url in rss_cfg.get('feeds', []) if url)


def slugify(value: str) -> str:
    value = re.sub(r'[^a-z0-9]+', '-', (value or '').lower())
    return re.sub(r'-+', '-', value).strip('-')[:70]


def clean_text(value: str) -> str:
    value = re.sub(r'<[^>]+>', ' ', value or '')
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


def entry_id(entry: dict) -> str:
    value = entry.get('id') or entry.get('link') or entry.get('title') or ''
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]


def write_entry(feed_url: str, entry: dict) -> bool:
    stable_id = entry_id(entry)
    title = clean_text(entry.get('title', 'No title'))
    link = entry.get('link', '')
    date = entry.get('published') or entry.get('updated') or datetime.now(timezone.utc).isoformat()
    content = clean_text(entry.get('summary') or entry.get('description') or entry.get('content', ''))
    filename = f'rss_{stable_id}_{slugify(title)}.md'
    out_path = os.path.join(OUT_DIR, filename)
    if os.path.exists(out_path):
        return False

    front = [
        '---',
        'source: rss',
        f'date: {date}',
        f'url: {link}',
        f'raw_id: rss-{stable_id}',
        f'feed_url: {feed_url}',
        '---',
        '\n',
    ]
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(front))
        out.write(f'{title}\n\n{content}')
    print('Wrote', out_path)
    return True


def main() -> None:
    if not feeds:
        print('No RSS feeds configured. Set rss.feeds in config.json or RSS_FEEDS.')
        return

    total = 0
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        if getattr(parsed, 'bozo', False) and not parsed.entries:
            print('RSS parse error:', feed_url, parsed.bozo_exception)
            continue
        print('Reading RSS feed:', feed_url, 'entries:', len(parsed.entries))
        for entry in parsed.entries:
            total += int(write_entry(feed_url, entry))
    print('Done: wrote', total, 'new RSS entries')


if __name__ == '__main__':
    main()
