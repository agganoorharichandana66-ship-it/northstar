#!/usr/bin/env python3
"""Import files dropped into inbox_lms/ into second_brain/raw/learning as markdown notes.
Simple deterministic importer: moves files into raw learning and creates a markdown wrapper with frontmatter.
"""
import os
import shutil
import re
from datetime import datetime

BASE = os.path.dirname(__file__)
INBOX = os.path.normpath(os.path.join(BASE, 'inbox_lms'))
OUT_DIR = os.path.normpath(os.path.join(BASE, '..', 'second_brain', 'raw', 'learning'))
ATTACH_DIR = os.path.join(OUT_DIR, 'attachments')

os.makedirs(INBOX, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ATTACH_DIR, exist_ok=True)


def slugify(s: str) -> str:
    s = (s or '')
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s[:80]


def process_file(path: str):
    name = os.path.basename(path)
    mtime = datetime.utcfromtimestamp(os.path.getmtime(path)).isoformat() + 'Z'
    title = os.path.splitext(name)[0]
    slug = slugify(title)
    md_name = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{slug}.md"
    md_path = os.path.join(OUT_DIR, md_name)

    # move original into attachments folder to keep one place
    attach_name = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{name}"
    attach_dest = os.path.join(ATTACH_DIR, attach_name)
    shutil.move(path, attach_dest)

    front = [
        '---',
        'source: LMS',
        f'date: {mtime}',
        f'title: {title}',
        f'original_file: {attach_name}',
        '---',
        '\n'
    ]

    body = ''
    # If it's a markdown/html/text file, try to include its text
    ext = os.path.splitext(attach_name)[1].lower()
    if ext in ['.md', '.markdown', '.txt', '.html']:
        try:
            with open(attach_dest, 'r', encoding='utf-8', errors='ignore') as f:
                body = f.read()
        except Exception:
            body = f'(Unable to read file {attach_name})'
    else:
        body = f'Attachment saved: attachments/{attach_name}'

    with open(md_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(front))
        out.write(body)

    print('Imported LMS file ->', md_path)


def main():
    files = [os.path.join(INBOX, f) for f in os.listdir(INBOX) if os.path.isfile(os.path.join(INBOX, f))]
    if not files:
        print('No files in inbox_lms to import')
        return
    for p in files:
        try:
            process_file(p)
        except Exception as e:
            print('Failed to process', p, e)


if __name__ == '__main__':
    main()
