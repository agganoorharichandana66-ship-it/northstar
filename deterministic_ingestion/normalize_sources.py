#!/usr/bin/env python3
"""Normalize raw GitHub repositories and LMS notes into source-specific JSON."""
import json
import os
import re
from glob import glob
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent
CONFIG_PATH = BASE / 'config.json'
if not CONFIG_PATH.exists():
    CONFIG_PATH = BASE / 'config.example.json'
with CONFIG_PATH.open(encoding='utf-8') as f:
    cfg = json.load(f)

ROOT = BASE.parent
RAW_GITHUB = ROOT / cfg['paths'].get('raw_github_dir', 'second_brain/raw/github')
RAW_LEARNING = ROOT / cfg['paths']['raw_learning_dir']
OUT_GITHUB = ROOT / cfg['paths'].get('normalized_github_dir', 'second_brain/normalized/github')
OUT_LEARNING = ROOT / cfg['paths'].get('normalized_learning_dir', 'second_brain/normalized/learning')
OUT_GITHUB.mkdir(parents=True, exist_ok=True)
OUT_LEARNING.mkdir(parents=True, exist_ok=True)

SKILLS = {
    'pytorch', 'tensorflow', 'transformers', 'hugging face', 'langchain',
    'docker', 'kubernetes', 'mlops', 'inference', 'llm', 'prompt engineering',
    'fine-tuning', 'generative ai', 'gen ai', 'machine learning', 'deep learning',
    'data science', 'spark', 'python', 'etl', 'nlp', 'computer vision', 'rag',
    'agents', 'mcp', 'vector database', 'model serving',
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.search(r'^---\n(.*?)\n---\n', text, flags=re.S)
    if not match:
        return {}, text.strip()
    meta = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            meta[key.strip()] = value.strip().strip('"\'')
    return meta, text[match.end():].strip()


def detect_skills(text: str) -> list[str]:
    lowered = (text or '').lower()
    return sorted(skill for skill in SKILLS if skill in lowered)


def write_json(path: Path, data: dict) -> None:
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('Normalized', path)


def normalize_github(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    meta, body = parse_frontmatter(text)
    try:
        repo = json.loads(body)
    except json.JSONDecodeError:
        repo = {}
    description = repo.get('description') or ''
    topics = repo.get('topics') or []
    normalized = {
        'raw_id': meta.get('raw_id', path.stem),
        'source': 'github',
        'item_type': 'repository',
        'date': meta.get('date') or repo.get('updated_at') or datetime.now(timezone.utc).isoformat(),
        'title': repo.get('full_name') or meta.get('repo') or path.stem,
        'company': repo.get('owner', {}).get('login') or meta.get('owner', ''),
        'description': description,
        'url': repo.get('html_url') or meta.get('url', ''),
        'skills': detect_skills(' '.join([description, ' '.join(topics), repo.get('name', '')])),
        'topics': topics,
        'language': repo.get('language') or '',
        'stars': repo.get('stargazers_count', 0),
        'forks': repo.get('forks_count', 0),
        'raw_text_excerpt': (description or body)[:500],
        'search_query': meta.get('search_query', ''),
    }
    write_json(OUT_GITHUB / f'{path.stem}.json', normalized)


def normalize_learning(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    meta, body = parse_frontmatter(text)
    title = meta.get('title') or next((line.strip() for line in body.splitlines() if line.strip()), path.stem)
    normalized = {
        'raw_id': meta.get('raw_id', path.stem),
        'source': 'lms',
        'item_type': 'learning',
        'date': meta.get('date') or datetime.now(timezone.utc).isoformat(),
        'title': title,
        'description': body[:2000],
        'url': meta.get('url', ''),
        'skills': detect_skills(body),
        'source_file': meta.get('original_file', path.name),
        'raw_text_excerpt': body[:500],
    }
    write_json(OUT_LEARNING / f'{path.stem}.json', normalized)


def main() -> None:
    github_files = list(RAW_GITHUB.glob('*.md'))
    learning_files = list(RAW_LEARNING.glob('*.md'))
    for path in github_files:
        normalize_github(path)
    for path in learning_files:
        normalize_learning(path)
    print(f'Done: GitHub={len(github_files)}, LMS={len(learning_files)}')


if __name__ == '__main__':
    main()
