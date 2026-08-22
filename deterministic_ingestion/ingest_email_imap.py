#!/usr/bin/env python3
"""IMAP fetcher: connect to an IMAP mailbox, download UNSEEN messages,
write each as a deterministic markdown file into second_brain/raw/jobs/,
and mark messages as SEEN."""
import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import re

BASE = os.path.dirname(__file__)
OUT_DIR = os.path.normpath(os.path.join(BASE, '..', 'second_brain', 'raw', 'jobs'))
os.makedirs(OUT_DIR, exist_ok=True)

IMAP_HOST = os.getenv('IMAP_HOST')
IMAP_USER = os.getenv('IMAP_USER')
# Accept either IMAP_PASS or IMAP_PASSS (some environments have a typo)
IMAP_PASS = os.getenv('IMAP_PASS') or os.getenv('IMAP_PASSS')

# Filtering configuration (comma-separated regex or keywords)
ALLOWED_SENDERS = os.getenv('IMAP_ALLOWED_SENDERS', '')
ALLOWED_SUBJECT_PATTERNS = os.getenv('IMAP_ALLOWED_SUBJECT_PATTERNS', '')
REQUIRED_KEYWORDS = os.getenv('IMAP_REQUIRED_KEYWORDS', 'job,hire,hiring,opportunity,remote,data engineer,generative,gen ai,genai,llm,large language')
BLOCKLIST_KEYWORDS = os.getenv('IMAP_BLOCKLIST_KEYWORDS', 'security alert,password changed,google security,pipedream')
# If true, mark skipped messages as seen to avoid repeated re-processing
MARK_SKIPPED_AS_SEEN = os.getenv('MARK_SKIPPED_AS_SEEN', '1') in ('1', 'true', 'True')

if not (IMAP_HOST and IMAP_USER and IMAP_PASS):
    print('IMAP_HOST, IMAP_USER and IMAP_PASS (or IMAP_PASSS) must be set as env vars')
    raise SystemExit(1)


def slugify(s: str) -> str:
    s = s or ''
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s[:80]


def decode_str(s):
    if not s:
        return ''
    parts = decode_header(s)
    out = ''
    for part, enc in parts:
        if isinstance(part, bytes):
            try:
                out += part.decode(enc or 'utf-8', errors='ignore')
            except Exception:
                out += part.decode('utf-8', errors='ignore')
        else:
            out += part
    return out


def get_text_from_msg(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset('utf-8'), errors='ignore')
        # fallback to first part
        for part in msg.walk():
            payload = part.get_payload(decode=True)
            if payload:
                try:
                    return payload.decode(part.get_content_charset('utf-8'), errors='ignore')
                except Exception:
                    return str(payload)
        return ''
    else:
        payload = msg.get_payload(decode=True)
        if not payload:
            return ''
        return payload.decode(msg.get_content_charset('utf-8'), errors='ignore')


def main():
    print('Connecting to IMAP host', IMAP_HOST)
    M = imaplib.IMAP4_SSL(IMAP_HOST)
    M.login(IMAP_USER, IMAP_PASS)
    M.select('INBOX')
    typ, data = M.search(None, 'UNSEEN')
    if typ != 'OK':
        print('No messages or search error', typ)
        return
    ids = data[0].split()
    print('Found', len(ids), 'UNSEEN messages')
    for num in ids:
        typ, msg_data = M.fetch(num, '(RFC822)')
        if typ != 'OK':
            print('Failed to fetch', num)
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        subject = decode_str(msg.get('Subject'))
        frm = decode_str(msg.get('From'))
        date_hdr = msg.get('Date')
        try:
            date = email.utils.parsedate_to_datetime(date_hdr).isoformat()
        except Exception:
            date = datetime.utcnow().isoformat() + 'Z'
        body = get_text_from_msg(msg)

        # Decide whether this message is relevant
        def is_relevant(subject, frm, body):
            s = (subject or '').lower()
            f = (frm or '').lower()
            b = (body or '').lower()

            # blocklist quick check
            for bk in [k.strip().lower() for k in BLOCKLIST_KEYWORDS.split(',') if k.strip()]:
                if bk and bk in s or bk in f or bk in b:
                    return False, f'blocked by keyword:{bk}'

            # allowed senders
            if ALLOWED_SENDERS:
                import re as _re
                for pat in [p.strip() for p in ALLOWED_SENDERS.split(',') if p.strip()]:
                    try:
                        if _re.search(pat, f):
                            return True, f'allowed_sender:{pat}'
                    except Exception:
                        if pat in f:
                            return True, f'allowed_sender_literal:{pat}'

            # subject patterns
            if ALLOWED_SUBJECT_PATTERNS:
                import re as _re
                for pat in [p.strip() for p in ALLOWED_SUBJECT_PATTERNS.split(',') if p.strip()]:
                    try:
                        if _re.search(pat, s):
                            return True, f'allowed_subject:{pat}'
                    except Exception:
                        if pat in s:
                            return True, f'allowed_subject_literal:{pat}'

            # required keyword presence
            for kw in [k.strip().lower() for k in REQUIRED_KEYWORDS.split(',') if k.strip()]:
                if kw and (kw in s or kw in b or kw in f):
                    return True, f'keyword_match:{kw}'

            return False, 'no_match'

        relevant, why = is_relevant(subject, frm, body)
        if not relevant:
            print('Skipping message:', subject, 'from', frm, 'reason:', why)
            # mark skipped messages as seen optionally
            if MARK_SKIPPED_AS_SEEN:
                M.store(num, '+FLAGS', '\\Seen')
            continue

        slug = slugify(subject + '-' + frm)
        filename = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{slug}.md"
        out_path = os.path.join(OUT_DIR, filename)
        front = ['---', f"source: email", f"date: {date}", f"raw_id: {slug}", f"from: {frm}", '---', '\n']
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write('\n'.join(front))
            out.write(body)
        print('Wrote', out_path)
        # mark as seen
        M.store(num, '+FLAGS', '\\Seen')

    M.close()
    M.logout()


if __name__ == '__main__':
    main()
