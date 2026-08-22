#!/usr/bin/env python3
"""Score normalized items using an LLM prompt.

Usage:
 - Without an API key the script prints the assembled prompt for manual use.
 - With GROQ_API_KEY set, it will attempt a call and save scores to
   second_brain/normalized/jobs_scores/*.json
"""
import os, json, re, textwrap, time
from glob import glob
from pathlib import Path

BASE = Path(__file__).parent
NORM_DIR = BASE.parent / 'second_brain' / 'normalized' / 'jobs'
OUT_DIR = BASE.parent / 'second_brain' / 'normalized' / 'jobs_scores'
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT_TEMPLATE = (BASE / 'SCORE_PROMPT.md').read_text(encoding='utf-8')

def build_prompt(north_star: str, item: dict) -> str:
    header = 'You are an assistant that scores items against a user North Star.\n'
    body = textwrap.dedent(f"""
    {PROMPT_TEMPLATE}

    north_star: {json.dumps(north_star)}

    item: {json.dumps(item, ensure_ascii=False)}
    """)
    return header + '\n' + body


def estimate_tokens(text: str) -> int:
    # rough heuristic: 4 chars per token
    if not text:
        return 0
    return max(1, len(text) // 4)


def retrieve_local_context(item: dict, max_chars: int = 4000):
    """Simple local retrieval: find normalized items sharing skills or title keywords.
    Returns a list of text snippets (strings) up to max_chars total.
    """
    snippets = []
    seen = set()
    keywords = []
    if item.get('title'):
        keywords += [w.lower() for w in re.findall(r"\w{4,}", item['title'])]
    for s in item.get('skills', []):
        keywords += [s.lower()]

    # scan normalized files for matches
    for p in sorted(glob(str(NORM_DIR / '*.json'))):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                other = json.load(f)
        except Exception:
            continue
        if other.get('raw_id') == item.get('raw_id'):
            continue
        text = (other.get('title','') + '\n' + other.get('raw_text_excerpt',''))
        tlow = text.lower()
        score = 0
        for kw in keywords:
            if kw and kw in tlow:
                score += 1
        if score > 0:
            key = other.get('raw_id') or p
            if key in seen:
                continue
            seen.add(key)
            snippets.append(text.strip())
            # stop if accumulated chars exceed limit
            if sum(len(s) for s in snippets) > max_chars:
                break
    return snippets

def call_llm(prompt: str) -> str:
    groq_key = os.environ.get('GROQ_API_KEY')
    groq_url = os.environ.get(
        'GROQ_API_URL',
        'https://api.groq.com/openai/v1/chat/completions',
    )

    if not groq_key:
        print('\n----- PROMPT PREVIEW -----\n')
        print(prompt[:4000])
        print('\n(Set GROQ_API_KEY to call the GROQ API)')
        return None

    try:
        import requests
        model = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-20b')
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that MUST respond with JSON only. Return a single top-level JSON object and nothing else."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.0
        }

        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        max_retries = int(os.environ.get('GROQ_MAX_RETRIES', '5'))
        for attempt in range(max_retries):
            r = requests.post(groq_url, json=payload, headers=headers, timeout=30)
            if r.status_code == 429 and attempt < max_retries - 1:
                wait = min(60, 2 ** attempt * 3)
                print(f'Rate limited; retrying in {wait}s (attempt {attempt + 1}/{max_retries})')
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            break
        else:
            r.raise_for_status()
        # Common shapes: OpenAI-compatible chat completions ('choices'...) or other providers.
        if isinstance(data, dict):
            # OpenAI/Groq chat response
            if "choices" in data and data["choices"]:
                c = data["choices"][0]
                # Chat-completion style
                if isinstance(c, dict) and "message" in c and "content" in c["message"]:
                    return c["message"]["content"]
                # Some variants return 'text' or 'message' directly
                if "text" in c:
                    return c["text"]
            # Some providers return a top-level 'output' or 'result'
            if "output" in data:
                return json.dumps(data["output"]) if not isinstance(data["output"], str) else data["output"]
            if "result" in data:
                return json.dumps(data["result"]) if not isinstance(data["result"], str) else data["result"]
        return str(data)
    except Exception as e:
        print("GROQ call failed:", e)
        return None

def parse_and_save(raw: str, item_id: str):
    # Try several strategies to extract JSON from the model output.
    import re
    raw_str = raw.strip()
    data = None
    # 1) Raw is JSON
    try:
        data = json.loads(raw_str)
    except Exception:
        pass

    # 2) JSON inside ```json code fence
    if data is None:
        m = re.search(r'```json\s*(\{.*?\})\s*```', raw, flags=re.S)
        if m:
            try:
                data = json.loads(m.group(1))
            except Exception:
                data = None

    # 3) JSON inside any code fence
    if data is None:
        m = re.search(r'```\s*(\{.*?\})\s*```', raw, flags=re.S)
        if m:
            try:
                data = json.loads(m.group(1))
            except Exception:
                data = None

    # 4) JSON between explicit markers <JSON>...</JSON>
    if data is None:
        m = re.search(r'<JSON>(\{.*?\})</JSON>', raw, flags=re.S | re.I)
        if m:
            try:
                data = json.loads(m.group(1))
            except Exception:
                data = None

    # 5) Fallback: first {...} block
    if data is None:
        m = re.search(r'\{.*\}', raw, flags=re.S)
        if m:
            try:
                data = json.loads(m.group(0))
            except Exception:
                data = None

    if data is None:
        print('No JSON found in LLM output')
        raw_path = OUT_DIR / f'{item_id}.raw.txt'
        try:
            with open(raw_path, 'w', encoding='utf-8') as rf:
                rf.write(raw)
            print('Wrote raw LLM output to', raw_path)
            print('Excerpt:')
            print(raw[:1000].replace('\n',' '))
        except Exception as e:
            print('Failed to write raw output:', e)
        return
    out_path = OUT_DIR / f'{item_id}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('Saved score ->', out_path)

def main():
    north_star = os.environ.get(
        'NORTH_STAR',
        'By April 2027, starting from my current role as Data Engineer, I will be working as a Generative AI Engineer at a company, verified by an employment start date and an official offer letter.'
    )
    files = sorted(glob(str(NORM_DIR / '*.json')))
    if not files:
        print('No normalized items found in', NORM_DIR)
        return
    delay_s = float(os.environ.get('GROQ_REQUEST_DELAY', '2.5'))
    for p in files:
        item_id = Path(p).stem
        out_path = OUT_DIR / f'{item_id}.json'
        if out_path.exists() and os.environ.get('GROQ_RESCORE', '').lower() not in ('1', 'true', 'yes'):
            print('Skipping already scored', out_path.name)
            continue

        with open(p, 'r', encoding='utf-8') as f:
            item = json.load(f)
        # Retrieval step: gather local context and decide whether to escalate to RAG
        snippets = retrieve_local_context(item)
        context_text = '\n\n'.join(snippets)
        # estimate token budget
        prompt_text = build_prompt(north_star, item)
        est_tokens = estimate_tokens(prompt_text + context_text)
        token_budget = int(os.environ.get('LLM_TOKEN_BUDGET', '4000'))
        if est_tokens > token_budget:
            # If prompt+context exceed budget, escalate to RAG (external retrieval) or truncate
            print(f"Escalate to RAG for {item.get('raw_id')} — est_tokens={est_tokens} budget={token_budget}")
            # For now, we will truncate context to fit
            allowed_chars = max(0, token_budget * 4 - len(prompt_text))
            context_text = context_text[:allowed_chars]

        # If context is empty or fits, do not call RAG — local retrieval is sufficient
        if context_text:
            prompt = prompt_text + '\n\nLocal context:\n' + context_text
        else:
            prompt = prompt_text

        output = call_llm(prompt)
        if output:
            parse_and_save(output, item_id)
        time.sleep(delay_s)

if __name__ == '__main__':
    main()
