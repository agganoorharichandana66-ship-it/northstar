#!/usr/bin/env python3
"""Identity verification helper using Tavily search (best-effort).

Provides `verify_profile(target)` which returns a dict:
  {"verified": bool, "score": 0.0-1.0, "provider": "tavily", "raw": <provider response>}

If `TAVILY_API_KEY` is not set, returns a conservative non-verified result and a note.
"""
import os, json

def verify_profile(target: str) -> dict:
    """Verify a profile URL or handle using Tavily search API.

    This is a lightweight, best-effort wrapper. It expects `TAVILY_API_KEY`
    in the environment and will POST {"query": target} to the Tavily /search endpoint.
    The exact provider response is kept under `raw`.
    """
    if not target:
        return {"verified": False, "score": 0.0, "provider": "tavily",
                "raw": {"error": "no target provided"}}

    key = os.environ.get('TAVILY_API_KEY')
    url = os.environ.get('TAVILY_API_URL', 'https://api.tavily.com/v1/search')
    if not key:
        return {"verified": False, "score": 0.0, "provider": "tavily",
                "raw": {"error": "no TAVILY_API_KEY configured"}}

    try:
        import requests
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {"query": target, "search_depth": "basic"}
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

        # Best-effort scoring: check if target string appears in results
        verified = False
        score = 0.0
        if isinstance(data, dict) and "results" in data:
            results = data.get("results", [])
            hits = [res for res in results if target.lower() in json.dumps(res).lower()]
            if hits:
                verified = True
                score = min(1.0, len(hits) / len(results))

        return {"verified": verified, "score": score, "provider": "tavily", "raw": data}
    except Exception as e:
        return {"verified": False, "score": 0.0, "provider": "tavily",
                "raw": {"error": str(e)}}


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: verify_identity.py <profile_url_or_handle>')
        raise SystemExit(1)
    print(json.dumps(verify_profile(sys.argv[1]), indent=2))
