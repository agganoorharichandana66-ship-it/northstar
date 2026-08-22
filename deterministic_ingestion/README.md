Deterministic Ingestion Backend

Purpose
- Deterministically fetch and store raw items from your real sources (LMS, LinkedIn/job-alerts, X, GitHub, YouTube playlists) into a file-based "second_brain/raw/" archive.
- Keep all fetching and deterministic extraction in backend code (no LLMs in ingestion). A separate scoring step (LLM) consumes the stored files and produces synthesized outputs.

Architecture
- Fetchers: small scripts (email, RSS, GitHub, LMS export importer) that run on a schedule and write raw Markdown files with frontmatter into `second_brain/raw/`.
- Normalizer: deterministic text processors that extract minimal metadata (title, company, date, url, tags, raw text, detected skills) and write JSON/MD into `second_brain/raw/` or `second_brain/normalized/`.
- Synthesizer (separate): LLM-based scoring/filter that reads normalized items and writes `second_brain/synthesized/jobs/` and `second_brain/synthesized/learning/`.

Storage layout (recommended)
- second_brain/raw/jobs/         — raw job posts as markdown (frontmatter + body)
- second_brain/raw/learning/     — raw learning items (LMS notes, YouTube metadata)
- second_brain/normalized/jobs/  — normalized JSON for job items (ready for scoring)
- second_brain/synthesized/jobs/ — scored & labeled job items (final output)
- second_brain/synthesized/learning/ — learning items with practice repos and tasks

File format (raw Markdown example frontmatter)
---
source: LinkedIn
date: 2026-08-21T12:34:00Z
url: https://...
raw_id: linkedin-12345
---
Full job posting text...

Scheduling
- Linux: cron entries to run fetchers every N minutes/hours. Example in `cron_example.txt`.
- Windows: use Task Scheduler to invoke the Python scripts on schedule.
- Keep schedules conservative to avoid rate limits on APIs.

Security & verification
- Store API tokens as environment variables, not in repo.
- For social scraping (X/Instagram), prefer third-party APIs like Apify only if necessary and legal.
- Before acting on social accounts, run a small verification step (author account age, followers, cross-links).

Determinism rules
- All network requests, parsing, and storage must be handled in code with deterministic output (timestamps, canonical filenames).
- Never inject LLM results into the raw/normalized data. LLMs only run in the synth step.

Quick start (example)
1. Copy `config.example.json` → `config.json` and fill API keys and paths.
2. Create the folder structure under `second_brain/`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run one fetcher manually, e.g. `python ingest_email.py`.
5. Run normalizer: `python normalize_job.py`.

Next steps
- Hook your job-alert email forwarding to `inbox_emails/` or use an IMAP fetcher.
- Add LMS export/importer once you can download lecture notes programmatically or place them in `inbox_lms/`.

Notes
- This scaffold focuses on deterministic collection and basic extraction. The LLM scoring/filter should be implemented as a separate process that reads `second_brain/normalized/` and produces final outputs.