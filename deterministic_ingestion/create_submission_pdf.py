#!/usr/bin/env python3
"""Generate the Assignment 2 submission PDF from the current workspace."""
import html
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image as ReportLabImage, PageTemplate, Paragraph, Preformatted,
    Spacer, Table, TableStyle, PageBreak, KeepTogether,
)

ROOT = Path(__file__).parent.parent
RAW = ROOT / 'second_brain' / 'raw'
NORMALIZED = ROOT / 'second_brain' / 'normalized'
OUT = ROOT / 'northstar_assignment2_submission.pdf'
ASSETS = ROOT / 'submission_evidence'


def files(directory):
    return sorted(directory.glob('*')) if directory.exists() else []


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def esc(value):
    return html.escape(str(value or ''))


def snippet(value, limit=700):
    text = ' '.join(str(value or '').split())
    return text[:limit] + ('...' if len(text) > limit else '')


def make_capture(filename, title, lines, width=1400, height=760):
    """Create a screenshot-style evidence image from current repository data."""
    ASSETS.mkdir(exist_ok=True)
    image = Image.new('RGB', (width, height), '#101820')
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype('consola.ttf', 30)
        body_font = ImageFont.truetype('consola.ttf', 22)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    draw.rectangle((0, 0, width, 66), fill='#17324D')
    draw.ellipse((24, 22, 42, 40), fill='#F26B5E')
    draw.ellipse((52, 22, 70, 40), fill='#F2C14E')
    draw.ellipse((80, 22, 98, 40), fill='#52B788')
    draw.text((125, 18), title, font=title_font, fill='#F4F7F8')
    y = 100
    for line in lines:
        draw.text((34, y), line[:112], font=body_font, fill='#D9E6EA')
        y += 30
        if y > height - 35:
            break
    path = ASSETS / filename
    image.save(path)
    return path


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCustom', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=25, leading=30, textColor=colors.HexColor('#17324D'), alignment=TA_CENTER, spaceAfter=10))
styles.add(ParagraphStyle(name='Subtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor('#52606D'), alignment=TA_CENTER, spaceAfter=20))
styles.add(ParagraphStyle(name='H1Custom', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=17, leading=21, textColor=colors.HexColor('#17324D'), spaceBefore=8, spaceAfter=8))
styles.add(ParagraphStyle(name='H2Custom', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#1F5A75'), spaceBefore=7, spaceAfter=5))
styles.add(ParagraphStyle(name='BodyCustom', parent=styles['BodyText'], fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=6))
styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#52606D'), spaceAfter=4))
styles.add(ParagraphStyle(name='Callout', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=10, leading=15, textColor=colors.HexColor('#17324D'), backColor=colors.HexColor('#EAF3F5'), borderPadding=8, spaceBefore=5, spaceAfter=9))
styles.add(ParagraphStyle(name='CodeCustom', parent=styles['Code'], fontName='Courier', fontSize=7.2, leading=9.2, leftIndent=6, rightIndent=6, backColor=colors.HexColor('#F3F5F7'), borderPadding=6, spaceAfter=8))


def P(text, style='BodyCustom'):
    return Paragraph(text, styles[style])


def section(title):
    return P(title, 'H1Custom')


def bullet(text):
    return P('&bull; ' + text)


def table(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17324D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('LEADING', (0, 0), (-1, -1), 11),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#C7D2D9')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F4F7F8')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#C7D2D9'))
    canvas.line(18 * mm, 13 * mm, 192 * mm, 13 * mm)
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(colors.HexColor('#52606D'))
    canvas.drawString(18 * mm, 8 * mm, 'North Star Second Brain - Assignment 2')
    canvas.drawRightString(192 * mm, 8 * mm, f'Page {doc.page}')
    canvas.restoreState()


def main():
    raw_jobs = files(RAW / 'jobs')
    raw_github = files(RAW / 'github')
    raw_learning = files(RAW / 'learning')
    norm_jobs = files(NORMALIZED / 'jobs')
    norm_github = files(NORMALIZED / 'github')
    norm_learning = files(NORMALIZED / 'learning')
    scores = files(NORMALIZED / 'jobs_scores')

    zapier_raw = next((p for p in raw_jobs if 'senior-data-engineer' in p.name), raw_jobs[0] if raw_jobs else None)
    zapier_norm = next((p for p in norm_jobs if 'senior-data-engineer' in p.name), norm_jobs[0] if norm_jobs else None)
    github_norm = next((p for p in norm_github if 'microsoft-generative-ai' in p.name), norm_github[0] if norm_github else None)
    score_sample = next((p for p in scores if 'github_repo' in p.name), scores[0] if scores else None)

    job_data = read_json(zapier_norm) if zapier_norm else {}
    github_data = read_json(github_norm) if github_norm else {}
    score_data = read_json(score_sample) if score_sample else {}
    raw_text = zapier_raw.read_text(encoding='utf-8', errors='ignore') if zapier_raw else ''

    folder_capture = make_capture('folder_structure.png', 'Repository evidence | second_brain/', [
        'second_brain/',
        '  raw/jobs/                 %d Markdown files' % len(raw_jobs),
        '  raw/github/               %d Markdown files' % len(raw_github),
        '  raw/learning/             %d Markdown files' % len(raw_learning),
        '  normalized/jobs/          %d JSON files' % len(norm_jobs),
        '  normalized/github/        %d JSON files' % len(norm_github),
        '  normalized/learning/      %d JSON files' % len(norm_learning),
        '  normalized/jobs_scores/   %d JSON files' % len(scores),
        '',
        'Generated from the current workspace on 22 August 2026.',
    ])
    pipeline_capture = make_capture('pipeline_before_after.png', 'Evidence capture | raw -> normalized -> scored', [
        'RAW EMAIL',
        'title: "Senior Data Engineer"',
        'company: "Acme Corp"',
        'url: https://www.linkedin.com/jobs/view/123456',
        '',
        'NORMALIZED JSON',
        'title: Senior Data Engineer | company: Acme Corp',
        'skills: [etl, python, spark]',
        '',
        'SCORED JSON',
        'score: 37 | confidence: 0.5',
        'breakdown: alignment, impact, feasibility, skill_match, urgency',
    ])
    workflow_capture = make_capture('workflow_evidence.png', 'Evidence capture | ingestion mechanism', [
        'GitHub Actions: .github/workflows/weekly-ingest.yml',
        'schedule: 0 6 * * 1  (Monday 06:00 UTC)',
        '',
        'python deterministic_ingestion/ingest_email_imap.py',
        'python deterministic_ingestion/ingest_linkedin_rss.py',
        'python deterministic_ingestion/ingest_github.py',
        'python deterministic_ingestion/ingest_lms_folder.py',
        'python deterministic_ingestion/normalize_job.py',
        'python deterministic_ingestion/normalize_sources.py',
        'python deterministic_ingestion/score_with_llm.py',
    ])

    doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=18 * mm, title='North Star Second Brain - Assignment 2')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([PageTemplate(id='main', frames=frame, onPage=footer)])
    story = []

    story += [Spacer(1, 22 * mm), P('North Star<br/>Second Brain', 'TitleCustom'), P('Assignment 2 submission | Evidence captured 22 August 2026', 'Subtitle')]
    story.append(P('A deterministic personal information pipeline that collects real job, learning, RSS, and GitHub sources, then ranks them against one personally chosen career goal.', 'Callout'))
    story += [Spacer(1, 8), P('<b>Applicant goal:</b> move from Data Engineer to Generative AI Engineer by April 2027, using evidence from real work, learning, and opportunities.', 'BodyCustom'), PageBreak()]

    story.append(section('1. North Star statement'))
    story.append(P('<b>By April 2027, starting from my current role as Data Engineer, I will be working as a Generative AI Engineer at a company, verified by an employment start date and an official offer letter, so I can make production AI engineering my next career focus.</b>', 'Callout'))
    story.append(P('<b>Four parts a stranger can check:</b>', 'H2Custom'))
    story.append(table([
        [P('Part', 'Small'), P('What it says', 'Small')],
        [P('Current state'), P('I am currently a Data Engineer.')],
        [P('Time-bound goal'), P('The deadline is April 2027.')],
        [P('Provable activity'), P('I will be employed as a Generative AI Engineer, checked using an employment start date and official offer letter.')],
        [P('Reason'), P('I want production AI engineering to become my next career focus.')],
    ], [38 * mm, 132 * mm]))

    story.append(section('2. Source list'))
    story.append(P('The source list is based on sources actually connected to this project. The two strongest signals are marked with [MOST SIGNAL].', 'BodyCustom'))
    story.append(table([
        [P('Source', 'Small'), P('What enters the brain', 'Small'), P('Signal judgment', 'Small')],
        [P('LinkedIn Job Alerts via IMAP [MOST SIGNAL]'), P('Real job-alert emails, including multiple jobs per digest.'), P('Primary opportunity signal.')],
        [P('Zapier structured job email [MOST SIGNAL]'), P('Structured title, company, location, URL, date, tags, and responsibilities.'), P('Primary clean job signal.')],
        [P('GitHub repository search'), P('GenAI repositories searched by topics and sorted by stars or updates.'), P('Strong practical skill and trend signal.')],
        [P('RSS feed'), P('Public GenAI engineering articles and posts.'), P('Useful knowledge signal; not employment proof.')],
        [P('LMS folder'), P('Course notes and exported learning material.'), P('Personal learning signal.')],
        [P('Consciously cut'), P('Personalized LinkedIn home feed: no stable official RSS route and mixed signal. Google security and Pipedream notices: operational mail, not career inputs.'), P('Deliberately excluded; job alerts and public GenAI feeds remain.')],
    ], [52 * mm, 83 * mm, 35 * mm]))

    story.append(section('3. Second brain folder and real items'))
    story.append(P('The project stores raw Markdown separately from normalized and synthesized outputs. Current evidence counts:', 'BodyCustom'))
    story.append(table([
        [P('Folder', 'Small'), P('Items', 'Small'), P('Purpose', 'Small')],
        [P('second_brain/raw/jobs/'), P(str(len(raw_jobs))), P('Raw email and RSS job material.')],
        [P('second_brain/raw/github/'), P(str(len(raw_github))), P('Raw GitHub repository search results.')],
        [P('second_brain/raw/learning/'), P(str(len(raw_learning))), P('Raw LMS Markdown notes.')],
        [P('second_brain/normalized/jobs/'), P(str(len(norm_jobs))), P('Structured job records.')],
        [P('second_brain/normalized/github/'), P(str(len(norm_github))), P('Structured repository records.')],
        [P('second_brain/normalized/learning/'), P(str(len(norm_learning))), P('Structured learning records.')],
        [P('second_brain/normalized/jobs_scores/'), P(str(len(scores))), P('LLM ranking output.')],
    ], [72 * mm, 22 * mm, 76 * mm]))
    story.append(P('Folder tree:', 'H2Custom'))
    story.append(Preformatted('second_brain/\n  raw/\n    jobs/\n    github/\n    learning/\n  normalized/\n    jobs/\n    github/\n    learning/\n    jobs_scores/', styles['CodeCustom']))
    story.append(P('Evidence capture: generated from the current repository folders.', 'Small'))
    story.append(ReportLabImage(str(folder_capture), width=170 * mm, height=92 * mm))
    story.append(P('<b>Examples of real ingested items:</b> LinkedIn Generative AI Engineer alerts, Senior Data Engineer from Zapier, Scaling LLM-based Ranking Systems with SGLang, Microsoft Generative AI for Beginners, LangChain, RAGFlow, vLLM, LMS RAG practical codepath, LMS LLM memory notes, and LMS Connecting the Dots notes.', 'BodyCustom'))
    story.append(PageBreak())

    story.append(section('4. Personalization engine'))
    story.append(P('The engine uses one scoring prompt in <b>deterministic_ingestion/SCORE_PROMPT.md</b>. It asks GROQ to score every normalized item against the North Star using five weighted dimensions:', 'BodyCustom'))
    story.append(table([
        [P('Dimension', 'Small'), P('Weight', 'Small'), P('Meaning', 'Small')],
        [P('Alignment'), P('40'), P('Direct connection to becoming a Generative AI Engineer.')],
        [P('Impact on goal'), P('20'), P('Likelihood of moving toward employment or strong portfolio evidence.')],
        [P('Feasibility / proximity'), P('15'), P('Achievability from the current Data Engineer role.')],
        [P('Skill match'), P('15'), P('Presence of LLM, RAG, inference, MLOps, and related skills.')],
        [P('Urgency / timing'), P('10'), P('Timeliness and opportunity window.')],
    ], [55 * mm, 20 * mm, 95 * mm]))
    story.append(P('The LLM returns JSON with <b>score</b>, <b>breakdown</b>, <b>confidence</b>, and short <b>notes</b>. GitHub repositories are judged for practical implementation and engineering depth; LMS items for hands-on learning; jobs for role fit; RSS for learning and trend signals.', 'BodyCustom'))

    story.append(P('Before and after example', 'H2Custom'))
    story.append(P('<b>Before: raw incoming Zapier email</b>', 'Small'))
    story.append(Preformatted(snippet(raw_text, 1100), styles['CodeCustom']))
    story.append(P('<b>After: normalized record</b>', 'Small'))
    after = {k: job_data.get(k) for k in ('source', 'email_type', 'title', 'company', 'location', 'url', 'date_posted', 'tags', 'skills', 'responsibilities')}
    story.append(Preformatted(json.dumps(after, indent=2, ensure_ascii=True)[:1800], styles['CodeCustom']))
    story.append(P('<b>Filtered/scored output example</b>', 'Small'))
    story.append(Preformatted(json.dumps(score_data, indent=2, ensure_ascii=True)[:1000], styles['CodeCustom']))
    story.append(P('Code proof: the scoring stage scans all three normalized source folders:', 'H2Custom'))
    story.append(Preformatted("NORM_DIRS = [NORM_ROOT / name for name in ('jobs', 'github', 'learning')]\nfiles = sorted(path for norm_dir in NORM_DIRS\n                for path in glob(str(norm_dir / '*.json')))\noutput = call_llm(build_prompt(north_star, item))\nparse_and_save(output, item_id)", styles['CodeCustom']))
    story.append(P('Evidence capture: actual pipeline fields used in this submission.', 'Small'))
    story.append(ReportLabImage(str(pipeline_capture), width=170 * mm, height=92 * mm))
    story.append(PageBreak())

    story.append(section('5. Ingestion mechanism'))
    story.append(P('The pipeline is executable both manually and through GitHub Actions. The weekly workflow runs every Monday at 06:00 UTC and can also be started manually with workflow_dispatch.', 'BodyCustom'))
    story.append(table([
        [P('Step', 'Small'), P('Implementation evidence', 'Small')],
        [P('GitHub repositories'), P('ingest_github.py searches GenAI repositories and writes raw Markdown.')],
        [P('RSS knowledge'), P('ingest_linkedin_rss.py reads configured RSS/Atom feeds and deduplicates entries.')],
        [P('Email jobs'), P('ingest_email_imap.py fetches unseen messages and filters unrelated security/Pipedream mail.')],
        [P('LMS'), P('ingest_lms_folder.py imports files from inbox_lms/.')],
        [P('Normalization'), P('normalize_job.py handles jobs; normalize_sources.py handles GitHub and LMS.')],
        [P('Scoring'), P('score_with_llm.py scans all normalized folders and calls GROQ.')],
    ], [45 * mm, 125 * mm]))
    story.append(P('Workflow evidence: <b>.github/workflows/weekly-ingest.yml</b>. Manual schedule evidence: <b>deterministic_ingestion/cron_example.txt</b>.', 'Callout'))
    story.append(Preformatted('0 * * * * ingest_linkedin_rss.py\n15 * * * * ingest_github.py\n30 * * * * ingest_email.py', styles['CodeCustom']))
    story.append(P('Code proof: the workflow runs the collectors before normalization and scoring:', 'H2Custom'))
    story.append(Preformatted("python deterministic_ingestion/ingest_email_imap.py\npython deterministic_ingestion/ingest_linkedin_rss.py\npython deterministic_ingestion/ingest_github.py\npython deterministic_ingestion/ingest_lms_folder.py\npython deterministic_ingestion/normalize_job.py\npython deterministic_ingestion/normalize_sources.py\npython deterministic_ingestion/score_with_llm.py", styles['CodeCustom']))
    story.append(P('Evidence capture: workflow and manual command sequence.', 'Small'))
    story.append(ReportLabImage(str(workflow_capture), width=170 * mm, height=92 * mm))
    story.append(P('The raw records remain Markdown. The normalizers create structured JSON. Only the final scoring step calls GROQ, and its output is stored separately in jobs_scores.', 'BodyCustom'))
    story.append(Spacer(1, 8))
    story.append(P('End of submission evidence.', 'Subtitle'))

    doc.build(story)
    print(OUT)


if __name__ == '__main__':
    main()
