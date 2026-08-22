100XENGINEERS  ·  LLM MODULE  ·  ASSIGNMENT 2
Build the Brain That Outlives the Cohort
Two weeks. One verifiable North Star. A folder that filters the internet for you.
Assignment Brief  ·  Follows Live Lecture: Connecting the Dots of the LLM  ·  Due: 15-08-2026
THE ASSIGNMENT IN ONE SENTENCE
Write a North Star a stranger can verify, then build a second brain that ingests your real sources and filters everything against it.


1  Why This Exercise Exists
The lecture solved this problem for one persona: a consultant whose North Star was 3 paying real estate clients worth $5,000 per month by November 2026. The lead prospecting engine on the whiteboard was a proxy. The actual skill is deriving a personal output from a verifiable goal, and it is the skill you will reuse on your capstone, your job, and every freelance project after this cohort.
Two caveats from the session, before you touch a tool. First, the North Star comes before any pipeline. Second, do not automate for automation's sake, and do not send AI slop. Every outbound artefact your engine helps produce gets human review; the engine buys you clarity and speed, not an excuse to spam.
One more honest note: this list starts big and shrinks. You may begin wanting 100 sources connected. Within weeks you will find one or two carry most of the signal. Doubling down on those, and deleting the rest, is the assignment working.
2  The Build, Step by Step
Both tracks build the same system.
Write the North Star. Four parts in one sentence: current state, goal with a time constraint, a specific provable activity, and the reason. Anchor the timeline to something real; the cohort's own calendar is a fine first horizon. Run the verifier’s test before proceeding: could a stranger verify this after the deadline? If not, sharpen it. Nothing else in this assignment works without this step.
"By [month + year], I am [role or identity] doing [specific thing] at [level, income, or scale]."

Examples: "By November 2026, I am the go-to AI person on my team, leading the internal LLM rollout, and I've earned a $15K raise.”

"By November 2026, I am running an AI consulting service with 3 paying clients generating $5K/month.”

"By November 2026, I have built and launched a working AI product that 50 real users are actively using."

List your sources. Every place information actually reaches you today: the LMS, social media, email and newsletters, GitHub Trending, your own notes and observations, anything else you genuinely use. Mark which ones you suspect carry the signal.
Define your output. Derive it from the North Star the way the lecture derived name, contact, description for the consultant. A job seeker's output is ranked openings; an educator's is lecture material; a builder's is releases relevant to what they ship. If your output would help everyone, it helps no one: it must be personal.
Build deterministic ingestion. A backend routine (a cron job if you automate it, a manual weekly pass if you do not yet) that pulls from your sources. Apify covers Instagram and LinkedIn (about $1.5 per 1,000 results); Deterministic systems stay in the backend, never in the model's context.
Build the personalization engine. One LLM prompt whose only job is scoring each incoming item against your North Star. Ask an LLM to draft the scoring criteria from your North Star, inputs, and output, then edit it by hand until it reflects your actual judgment.
Store it as files. Markdown, in folders: raw ingestion in one, synthesized notes in another. Obsidian to visualize it if you like.  LLMs read markdown best and it burns the fewest tokens. 
Optional stretch. Host the folder and connect it to an LLM as a tool, so the brain becomes queryable.
3  Rules of the Build
North Star before pipeline. No ingestion, no scraping, no prompt gets written until your North Star passes the verifier’s test. This is the gate.
Real sources only. Ingest from feeds you actually consume. A brain fed aspirational source you never read is dead on arrival.
Deterministic work stays deterministic. Anything an API answers reliably (fetching, storing, scheduling) lives in the backend. The LLM only filters and synthesizes. Loading everything into the context window wastes time and money.
Verify what you scrape. If your engine ingests from social platforms, add the verification layer (Tavily has 1,000 free API credits per month) before you act on anything. Fake accounts are the norm, not the exception.
Escalate to RAG only on evidence. The two parameters are context window fit and token budget. Until one of them breaks, an index, chunks, metadata, and keyword search are the whole retrieval strategy.
LLM assistance policy. Use LLMs freely for hints, debugging, and drafting the scoring criteria. Do not paste this brief in and submit whatever comes out: the exercise is deriving your own North Star and your own filter, and a generated one filters someone else's life.
4  What to Submit
Deliverable
What it must show
North Star statement
One sentence, four parts visible (current state, time-bound goal, provable activity, reason). A third party reading it can state exactly what to check, and when, to declare success.
Source list
Every source you ingest from, with the one or two you believe carry most signal marked, and at least one source you consciously cut.
Second brain folder
A link or screenshot showing the folder structure: raw ingestion and synthesized notes as markdown, with at least 10 real items already ingested.
Personalization engine
The filter prompt or scoring criteria, plus one before-and-after: a batch of raw incoming items and the filtered output your engine produced from them.
Ingestion mechanism
Evidence the pipeline runs: the cron or workflow screenshot, the clipper in action, or the manual pass documented with dates.


5  Where to Post, and How to Get Unblocked
Submit on the LMS in the Assignment 2 slot; post questions and blockers in the discord channel.
6  After Submission
You have two weeks. Fine-tuning lectures run in parallel and do not depend on this. The Agents Module does: the agent you build in Module 3 will read this second brain to make decisions on your behalf, the same way the 100x sales and design teams query the production brain today. Submitting this is what makes Module 3 personalised for you.
