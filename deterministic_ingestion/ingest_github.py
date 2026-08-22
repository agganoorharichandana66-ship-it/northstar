#!/usr/bin/env python3
"""Fetch relevant GitHub repositories and trending GenAI projects.

GitHub has no official public "trending API", so this uses the repository
search API with configured topic queries and deterministic sorting.
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests

BASE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, 'config.json')
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(BASE, 'config.example.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

github_cfg = cfg.get('github', {})
out_dir = os.path.normpath(os.path.join(
    BASE, '..',
    github_cfg.get('raw_dir', cfg['paths'].get('raw_github_dir', 'second_brain/raw/github')),
))
os.makedirs(out_dir, exist_ok=True)

token_env_var = github_cfg.get('token_env_var', 'GITHUB_TOKEN')
token = os.getenv(token_env_var)
headers = {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
}
if token:
    headers['Authorization'] = f'Bearer {token}'

queries = github_cfg.get('repository_queries') or [
    '"generative ai"', 'llm', 'rag', 'inference mlops',
]
per_query = int(github_cfg.get('results_per_query', 10))
sorts = github_cfg.get('sorts') or ['stars', 'updated']


def slugify(value: str) -> str:
    value = re.sub(r'[^a-zA-Z0-9]+', '-', value or '')
    return value.strip('-').lower()[:100]


def search_repositories(query: str, sort: str) -> list[dict]:
    params = {'q': query, 'sort': sort, 'order': 'desc', 'per_page': per_query}
    url = f'https://api.github.com/search/repositories?{urlencode(params)}'
    max_retries = int(os.getenv('GITHUB_MAX_RETRIES', '4'))
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as error:
            if attempt == max_retries - 1:
                print(f'GitHub request failed for query={query!r}, sort={sort!r}: {error}')
                return []
            wait = min(60, 2 ** attempt * 2)
            print(f'GitHub request failed; retrying in {wait}s (attempt {attempt + 1}/{max_retries})')
            time.sleep(wait)
            continue

        if response.status_code == 200:
            return response.json().get('items', [])

        transient = response.status_code == 429 or 500 <= response.status_code < 600
        if transient and attempt < max_retries - 1:
            retry_after = response.headers.get('Retry-After')
            try:
                wait = max(1, int(retry_after)) if retry_after else min(60, 2 ** attempt * 2)
            except ValueError:
                wait = min(60, 2 ** attempt * 2)
            print(f'GitHub returned {response.status_code}; retrying in {wait}s (attempt {attempt + 1}/{max_retries})')
            time.sleep(wait)
            continue

        print(f'GitHub search skipped query={query!r}, sort={sort!r}: HTTP {response.status_code} {response.text[:300]}')
        return []

    return []


def write_repository(repo: dict, query: str, sort: str) -> None:
    full_name = repo.get('full_name', '')
    raw_id = str(repo.get('id') or slugify(full_name))
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    filename = f'{timestamp}_github_repo_{raw_id}_{slugify(full_name)}.md'
    out_path = os.path.join(out_dir, filename)
    front = [
        '---', 'source: github',
        f'date: {repo.get("updated_at") or datetime.now(timezone.utc).isoformat()}',
        f'raw_id: github-repo-{raw_id}',
        f'repo: {full_name}', f'url: {repo.get("html_url", "")}',
        f'owner: {repo.get("owner", {}).get("login", "")}',
        'content_type: repository', f'search_query: {query}', f'sort: {sort}',
        '---', '\n',
    ]
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(front))
        out.write(json.dumps(repo, indent=2, ensure_ascii=False))
    print('Wrote', out_path)


def main() -> None:
    repositories = {}
    for query in queries:
        for sort in sorts:
            for repo in search_repositories(query, sort):
                repositories.setdefault(repo.get('full_name'), (repo, query, sort))
    for repo, query, sort in repositories.values():
        write_repository(repo, query, sort)
    print(f'Done: collected {len(repositories)} unique repositories')


if __name__ == '__main__':
    main()
