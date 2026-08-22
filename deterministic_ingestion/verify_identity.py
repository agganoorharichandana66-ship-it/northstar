#!/usr/bin/env python3
"""Identity verification helper using Tavily search (best-effort).

Provides `verify_profile(target)` which returns a dict:
  {"verified": bool, "score": 0.0-1.0, "provider": "tavily", "raw": <provider response>}

If `TAVILY_API_KEY` is not set, returns a conservative non-verified result and a note.
"""
import json
import os
import re
from urllib.parse import urlparse


def canonical_url(value: str) -> str:
    """Remove tracking parameters so equivalent URLs can be compared."""
    parsed = urlparse((value or '').strip().lower())
    host = parsed.netloc.removeprefix('www.')
    path = parsed.path.rstrip('/')
    return f'{host}{path}'


def same_identity(target: str, result: dict) -> bool:
    target_canonical = canonical_url(target)
    result_url = result.get('url', '') if isinstance(result, dict) else ''
    result_canonical = canonical_url(result_url)
    if target_canonical and target_canonical == result_canonical:
        return True

    # LinkedIn commonly returns a localized URL for the same numeric job ID.
    target_id = re.search(r'(?:/comm)?/jobs/view/[^?#]*?(\d{6,})(?:[/?#]|$)', target.lower())
    result_id = re.search(r'(?:/comm)?/jobs/view/[^?#]*?(\d{6,})(?:[/?#]|$)', result_url.lower())
    return bool(
        target_id and result_id and target_id.group(1) == result_id.group(1)
    )

def verify_profile(target: str, context: str = '') -> dict:
    """Verify a profile URL or handle using Tavily search API.

    This is a lightweight, best-effort wrapper. It expects `TAVILY_API_KEY`
    in the environment and will POST {"query": target} to the Tavily /search endpoint.
    The exact provider response is kept under `raw`.
    """
    if not target:
        return {"verified": False, "score": 0.0, "provider": "tavily",
                "raw": {"error": "no target provided"}}

    key = os.environ.get('TAVILY_API_KEY')
    url = os.environ.get('TAVILY_API_URL', 'https://api.tavily.com/search')
    if not key:
        return {"verified": False, "score": 0.0, "provider": "tavily",
                "raw": {"error": "no TAVILY_API_KEY configured"}}

    try:
        import requests
        headers = {"Content-Type": "application/json"}
        query = ' '.join(
            part.strip()
            for part in (context, canonical_url(target))
            if part and part.strip()
        )
        payload = {
            "api_key": key,
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": False,
        }
        if os.environ.get('TAVILY_DEBUG'):
            print('TAVILY DEBUG: POST', url)
            print('TAVILY DEBUG: payload=', payload)
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if not (200 <= r.status_code < 300):
            return {"verified": False, "score": 0.0, "provider": "tavily",
                    "raw": {"http_status": r.status_code, "body": r.text}}
        try:
            data = r.json()
        except Exception:
            return {"verified": False, "score": 0.0, "provider": "tavily",
                    "raw": {"http_status": r.status_code, "body": r.text}}

        # Evidence-based scoring: match canonical URL or LinkedIn numeric job ID.
        verified = False
        score = 0.0
        evidence = []
        if isinstance(data, dict) and "results" in data:
            results = data.get("results", [])
            hits = [res for res in results if same_identity(target, res)]
            if hits:
                verified = True
                score = max(float(hit.get('score') or 0.0) for hit in hits)
                evidence = [
                    {
                        'url': hit.get('url', ''),
                        'title': hit.get('title', ''),
                        'score': hit.get('score', 0.0),
                    }
                    for hit in hits
                ]

        return {
            "verified": verified,
            "score": score,
            "provider": "tavily",
            "evidence": evidence,
            "raw": data,
        }
    except Exception as e:
        return {"verified": False, "score": 0.0, "provider": "tavily",
                "raw": {"error": str(e)}}


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: verify_identity.py <profile_url_or_handle>')
        raise SystemExit(1)
    print(json.dumps(verify_profile(sys.argv[1]), indent=2))
