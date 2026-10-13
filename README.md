---
title: GitHub Profile Analyzer
emoji: 🔎
colorFrom: purple
colorTo: pink
sdk: streamlit
---

# GitHub Profile Analyzer

Enter a developer's GitHub username to see their profile, language distribution, activity, personality badges, commit insights and quality, and shareable profile card. Comparison mode can analyze two developers.

The single-profile page also lets you select one of that developer's repositories, or paste another public repository URL. Its NLP workspace analyzes README terms and structure, project type, commit intent, sentiment, topics, and message quality. Repository Q&A retrieves relevant README sections and recent commits, then cites that evidence in its answer.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
python -m streamlit run streamlit_app.py
```

Open the local URL Streamlit prints, usually `http://localhost:8501`.

Repository Q&A uses a chat-style interface with a separate conversation for each analyzed repository. It uses built-in text matching to find relevant README and commit excerpts, then returns those excerpts with source labels; no API key is needed. A GitHub token is optional for public repositories; it raises the GitHub API rate limit. The JSON API also accepts pasted README text and commit messages, so you can analyze them without fetching from GitHub. Put `GITHUB_TOKEN` in `.env` only if you want the higher rate limit. `.env.example` contains placeholders only.

## Optional JSON API

Run `python api.py` to start the local Flask API at `http://127.0.0.1:5000`. `POST /api/analyze` accepts a GitHub repository `url`, or pasted `readme` and `commits`, and returns an analysis plus a session `id`. Send that `id` and a `question` to `POST /api/chat` to get matching repository excerpts and their source labels in `how`. No AI API key is needed. The API keeps up to 128 analysis sessions in memory; restarting it clears them.

```json
{"url": "https://github.com/pallets/flask"}
```

For pasted text instead of a GitHub fetch, send `{"readme": "...", "commits": ["Add request logging", "Fix timeout handling"]}` to `/api/analyze`.

```json
{"id": "analysis-id-from-the-first-response", "question": "How do I install this project?"}
```
