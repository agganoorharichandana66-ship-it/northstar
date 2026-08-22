% LLM Scoring Prompt (draft — edit by hand)

Purpose: score a single incoming item (job or learning) against the user's North Star. Output must be JSON only.

North Star (example to include when calling):
"By April 2027, starting from my current role as Data Engineer, I will be working as a Generative AI Engineer at a company, verified by an employment start date and an official offer letter."

Scoring scale: 0-100 (higher = better match to North Star).

Scoring breakdown (return as `breakdown` object with percentages summing to ~100):
- Alignment (40): How directly the item advances the North Star (job matches target role, learning item teaches skills clearly needed).
- Impact on Goal (20): Likelihood the item moves you closer to being hired (for jobs: seniority, company profile; for learning: coverage depth and practical application).
- Feasibility / Proximity (15): How achievable is this item given current role (time, seniority, required experience).
- Skill Match (15): Presence and strength of target skills (LLMs, prompt engineering, inference, MLOps, etc.).
- Urgency / Timing (10): Timeliness (job application window, trending technology relevance).

Confidence: return `confidence` 0-1 expressing model confidence in the score.

Required output format (JSON only):
{
  "score": 0-100,
  "breakdown": {
    "alignment": 0-100,
    "impact": 0-100,
    "feasibility": 0-100,
    "skill_match": 0-100,
    "urgency": 0-100
  },
  "confidence": 0.0-1.0,
  "notes": "short human-readable rationale (1-3 sentences)"
}

Inputs to include when calling the LLM (populate these fields):
- `north_star`: the user's North Star text (one paragraph)
- `item`: the normalized JSON for the item (fields: title, company, skills, responsibilities, url, date, source, raw_text_excerpt)

Instructions for the model (to prepend when calling):
1. Read `north_star` carefully. Use it as the single evaluation lens.
2. Read `item` fully. Consider `skills` and `responsibilities` as important signals.
3. Score each sub-criterion (alignment, impact, feasibility, skill_match, urgency) on 0-100, then compute `score` as a weighted sum using the percentages above.
4. Set `confidence` based on how much explicit evidence the item contains (0.9 for clear matches with links/keywords, 0.5 for indirect, 0.2 for guesses).
5. Provide a short `notes` justification focused on the North Star.
6. Output JSON only. No commentary outside JSON.

Example (job):
Input: north_star = "...Generative AI Engineer..."
item.title = "Senior Machine Learning Engineer — Acme"; item.skills includes ["pytorch","mlops","inference","llm"]

Expected JSON (illustrative):
{
  "score": 86,
  "breakdown": {"alignment":90,"impact":80,"feasibility":70,"skill_match":95,"urgency":60},
  "confidence":0.88,
  "notes":"Senior role at a reputable company with strong LLM skill requirements; good match though may require internal transition to GenAI-specific responsibilities."
}

Edit this prompt to match your final judgment. Use short, factual `notes` only.

Strict output requirements (apply these to avoid parsing errors):

- Return JSON ONLY. Do not include any extra text before or after the JSON.
- Wrap the JSON in a `json` code fence AND also include an explicit marker block to make extraction robust.

Required wrapper (both):

```json
{ ... }
```

and

<JSON>{ ... }</JSON>

Example (copy/paste this exact shape as the model output):

```json
{
  "score": 86,
  "breakdown": {
    "alignment": 90,
    "impact": 80,
    "feasibility": 70,
    "skill_match": 95,
    "urgency": 60
  },
  "confidence": 0.88,
  "notes": "Senior role at a reputable company with strong LLM skill requirements; good match though may require internal transition to GenAI-specific responsibilities."
}
```

And the same payload inside markers:

<JSON>{
  "score": 86,
  "breakdown": {"alignment":90,"impact":80,"feasibility":70,"skill_match":95,"urgency":60},
  "confidence": 0.88,
  "notes": "Senior role at a reputable company with strong LLM skill requirements; good match though may require internal transition to GenAI-specific responsibilities."
}</JSON>

If the model cannot produce this exactly, reduce temperature to 0 and instruct it again to output JSON only.

LLM Assistance Policy (for maintainers/operators):

 - Use LLMs for hints, debugging, and drafting scoring criteria only. Do not blindly accept generated scoring rules as authoritative.
 - The North Star and scoring filters must represent the user's own goals and reasoning; generated content may be used as a draft or suggestion but requires human validation before being used as the final filter.
 - Escalate to RAG only when local retrieval fails due to:
   * Context window overflow (prompt + local context > token budget), or
   * Explicit need for external evidence not present in local normalized items.
 - Default retrieval strategy: index, chunk, metadata, and keyword search over local normalized items. Do not call external retrieval or RAG until one of the above conditions is met.

