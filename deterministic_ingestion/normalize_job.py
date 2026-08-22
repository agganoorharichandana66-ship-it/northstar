#!/usr/bin/env python3
"""Deterministic normalizer: reads markdown files from raw/jobs and writes normalized JSON.

Supports:
- LinkedIn job-alert digest emails (multiple listings → one JSON per job)
- Zapier / structured single-job bodies (title:, company:, url:, etc.)
- Keyword-based skills and responsibility detection
"""
import glob
import json
import os
import re
from datetime import datetime, timezone

from verify_identity import verify_profile

BASE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, 'config.example.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

RAW_DIR = os.path.normpath(os.path.join(BASE, '..', cfg['paths']['raw_jobs_dir']))
OUT_DIR = os.path.normpath(os.path.join(BASE, '..', cfg['paths']['normalized_jobs_dir']))
os.makedirs(OUT_DIR, exist_ok=True)

SKILLS = [
    'pytorch', 'tensorflow', 'transformers', 'hugging face', 'huggingface',
    'langchain', 'docker', 'kubernetes', 'k8s', 'mlops', 'inference', 'llm',
    'large language model', 'prompt engineering', 'fine-tun', 'generative ai',
    'gen ai', 'genai', 'machine learning', 'deep learning', 'data science',
    'spark', 'python', 'etl', 'nlp', 'computer vision', 'rag',
]
RESP_PATS = [
    'fine-tun', 'prompt', 'inference', 'production', 'deploy', 'productionize',
    'build and optimize', 'model serving', 'design etl', 'manage streaming', 'mentor',
]

LINKEDIN_JOB_URL = re.compile(r'View job:\s*(https://\S+)', re.I)
LINKEDIN_ALERT_CREATED = re.compile(
    r'Your job alert has been created:\s*(.+?)(?:\.|\n)', re.I
)
LINKEDIN_JOB_ID = re.compile(r'/jobs/view/(\d+)')
STRUCTURED_FIELD = re.compile(
    r'^(title|company|location|url|date_posted|source):\s*["\']?(.+?)["\']?\s*$',
    re.I | re.M,
)
TAGS_FIELD = re.compile(r'tags:\s*\[(.*?)\]', re.I | re.S)
NOISE_LINE = re.compile(
    r'\b(\d+\s+connections?|\d+\s+company alumni|apply with resume|view job)\b',
    re.I,
)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    meta = {}
    body = text
    m = re.search(r'^---\n(.*?)\n---\n', text, flags=re.S)
    if not m:
        return meta, body.strip()
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():].strip()


def linkedin_job_id(url: str) -> str:
    m = LINKEDIN_JOB_ID.search(url or '')
    return m.group(1) if m else ''


def clean_url(url: str) -> str:
    return (url or '').strip().rstrip('.,)')


def detect_skills(text: str) -> list[str]:
    b = (text or '').lower()
    return sorted({s for s in SKILLS if s in b})


def detect_responsibilities(text: str) -> list[str]:
    b = (text or '').lower()
    found = sorted({p for p in RESP_PATS if p in b})
    m = re.search(r'Responsibilities:\s*(.+?)(?:\n\n|\nApply:|\Z)', text, re.I | re.S)
    if m:
        found.append(m.group(1).strip()[:300])
    return list(dict.fromkeys(found))


def parse_structured_body(body: str) -> dict | None:
    """Parse Zapier-style key: value fields from the email body."""
    fields = {}
    for m in STRUCTURED_FIELD.finditer(body):
        fields[m.group(1).lower()] = m.group(2).strip().strip('"').strip("'")

    tags_match = TAGS_FIELD.search(body)
    if tags_match:
        fields['tags'] = re.findall(r'["\']([^"\']+)["\']', tags_match.group(1))

    if fields.get('title') or fields.get('url'):
        return fields
    return None


def parse_linkedin_digest(body: str) -> tuple[str, list[dict]]:
    """Extract individual job listings from a LinkedIn job-alert digest email."""
    alert_match = LINKEDIN_ALERT_CREATED.search(body)
    alert_query = alert_match.group(1).strip() if alert_match else ''

    jobs = []
    for block in re.split(r'-{20,}', body):
        url_match = LINKEDIN_JOB_URL.search(block)
        if not url_match:
            continue

        url = clean_url(url_match.group(1))
        before = block[:url_match.start()]
        lines = [
            ln.strip()
            for ln in before.splitlines()
            if ln.strip() and not NOISE_LINE.search(ln)
        ]
        if not lines:
            continue

        title = company = location = ''
        if len(lines) >= 3:
            title, company, location = lines[-3], lines[-2], lines[-1]
        elif len(lines) >= 2:
            title, company = lines[-2], lines[-1]
        elif len(lines) == 1:
            title = lines[-1]

        jobs.append({
            'title': title,
            'company': company,
            'location': location,
            'url': url,
            'linkedin_job_id': linkedin_job_id(url),
        })

    return alert_query, jobs


def excerpt_for(text: str, limit: int = 200) -> str:
    return (text or '').strip()[:limit]


def base_record(meta: dict, body: str, email_type: str) -> dict:
    return {
        'source': meta.get('source', 'unknown'),
        'date': meta.get('date', datetime.now(timezone.utc).isoformat()),
        'from': meta.get('from', ''),
        'email_type': email_type,
        'alert_query': '',
        'parent_raw_id': meta.get('raw_id', ''),
    }


def maybe_verify(url: str) -> dict:
    target = clean_url(url)
    if not target.startswith('http'):
        return {
            'verified': False,
            'score': 0.0,
            'provider': 'tavily',
            'raw': {'skipped': True, 'reason': 'no job url to verify'},
        }
    try:
        return verify_profile(target)
    except Exception as e:
        return {
            'verified': False,
            'score': 0.0,
            'provider': 'tavily',
            'raw': {'error': str(e)},
        }


def job_record(meta: dict, body: str, email_type: str, job: dict, idx: int | None = None) -> dict:
    parent_raw_id = meta.get('raw_id') or ''
    job_id = job.get('linkedin_job_id') or ''
    suffix = f'__job-{job_id}' if job_id else (f'__job-{idx}' if idx is not None else '')
    raw_id = f'{parent_raw_id}{suffix}' if suffix else parent_raw_id

    combined_text = '\n'.join(
        filter(None, [
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            body,
        ])
    )

    record = {
        **base_record(meta, body, email_type),
        'raw_id': raw_id,
        'title': job.get('title', ''),
        'company': job.get('company', ''),
        'location': job.get('location', ''),
        'url': job.get('url', ''),
        'date_posted': job.get('date_posted', ''),
        'tags': job.get('tags', []),
        'skills': detect_skills(combined_text),
        'responsibilities': detect_responsibilities(combined_text),
        'raw_text_excerpt': excerpt_for(combined_text),
        'alert_query': job.get('alert_query', ''),
    }
    record['verification'] = maybe_verify(record['url'])
    return record


def normalize_markdown(md_path: str) -> list[tuple[str, dict]]:
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    meta, body = parse_frontmatter(text)
    parent_raw_id = meta.get('raw_id') or os.path.splitext(os.path.basename(md_path))[0]
    meta['raw_id'] = parent_raw_id
    stem = os.path.splitext(os.path.basename(md_path))[0]
    frm = (meta.get('from') or '').lower()

    structured = parse_structured_body(body)
    alert_query, linkedin_jobs = parse_linkedin_digest(body)

    outputs: list[tuple[str, dict]] = []

    if linkedin_jobs:
        for i, job in enumerate(linkedin_jobs, start=1):
            job['alert_query'] = alert_query
            record = job_record(meta, body, 'linkedin_job_digest', job, idx=i)
            job_id = job.get('linkedin_job_id') or str(i)
            out_name = f'{stem}__job-{job_id}.json'
            outputs.append((out_name, record))
        return outputs

    if structured:
        job = {
            'title': structured.get('title', ''),
            'company': structured.get('company', ''),
            'location': structured.get('location', ''),
            'url': structured.get('url', ''),
            'date_posted': structured.get('date_posted', ''),
            'tags': structured.get('tags', []),
        }
        email_type = 'structured_single_job'
        if 'zapiermail.com' in frm:
            email_type = 'zapier_single_job'
        record = job_record(meta, body, email_type, job)
        outputs.append((f'{stem}.json', record))
        return outputs

    # Fallback: best-effort single record from body text
    first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), 'No title')
    job = {
        'title': meta.get('title') or first_line,
        'company': meta.get('company', ''),
        'location': meta.get('location', ''),
        'url': meta.get('url', ''),
    }
    record = job_record(meta, body, 'unstructured_email', job)
    outputs.append((f'{stem}.json', record))
    return outputs


def cleanup_stale_outputs(stem: str) -> None:
    pattern = os.path.join(OUT_DIR, f'{stem}*.json')
    for path in glob.glob(pattern):
        os.remove(path)


def main() -> None:
    for md_path in sorted(glob.glob(os.path.join(RAW_DIR, '*.md'))):
        stem = os.path.splitext(os.path.basename(md_path))[0]
        cleanup_stale_outputs(stem)
        outputs = normalize_markdown(md_path)
        for out_name, record in outputs:
            out_path = os.path.join(OUT_DIR, out_name)
            with open(out_path, 'w', encoding='utf-8') as out:
                json.dump(record, out, indent=2, ensure_ascii=False)
            print('Normalized', out_path)


if __name__ == '__main__':
    main()
    print('Done')
