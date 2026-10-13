"""Optional JSON API for repository analysis and repository-grounded Q&A."""

from collections import OrderedDict
import os
import uuid

from flask import Flask, jsonify, request
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

from analysis.repo_qa import answer_repository_question, retrieve_evidence
from analysis.repository_nlp import analyze_repository_text
from data.repo_fetcher import fetch_repository_text

load_dotenv()


app = Flask(__name__)
SESSIONS: OrderedDict[str, dict] = OrderedDict()
MAX_SESSIONS = 128


def _json_body() -> dict:
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Send a JSON object in the request body.")
    return body


def _commit_list(value) -> list[dict]:
    if isinstance(value, str):
        return [{"message": line.strip()} for line in value.splitlines() if line.strip()]
    if isinstance(value, list):
        return [({"message": item} if isinstance(item, str) else item)
                for item in value if isinstance(item, (str, dict))]
    if value is None:
        return []
    raise ValueError("`commits` must be a string or a list of commit messages.")


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(Exception)
def unexpected_error(error):
    if isinstance(error, HTTPException):
        return jsonify(error=error.description), error.code
    app.logger.exception("API request failed")
    return jsonify(error="Unexpected server error."), 500


@app.post("/api/analyze")
def analyze():
    body = _json_body()
    url = body.get("url", "")
    if not isinstance(url, str):
        raise ValueError("`url` must be a string.")

    if url.strip():
        repository = fetch_repository_text(url, os.getenv("GITHUB_TOKEN", ""))
    else:
        readme = body.get("readme", "")
        if not isinstance(readme, str):
            raise ValueError("`readme` must be a string.")
        commits = _commit_list(body.get("commits", []))
        metadata = body.get("meta", {})
        if not isinstance(metadata, dict):
            raise ValueError("`meta` must be a JSON object.")
        repository = {
            **metadata,
            "full_name": str(metadata.get("full_name") or metadata.get("name") or "Pasted repository"),
            "readme": readme[:100_000],
            "commits": commits[:300],
        }

    analysis = analyze_repository_text(repository["readme"], repository["commits"])
    session_id = uuid.uuid4().hex
    SESSIONS[session_id] = repository
    while len(SESSIONS) > MAX_SESSIONS:
        SESSIONS.popitem(last=False)

    public_meta = {key: repository.get(key) for key in ("full_name", "description", "url", "stars", "language")}
    return jsonify(id=session_id, meta=public_meta, analysis=analysis)


@app.post("/api/chat")
def chat():
    body = _json_body()
    session_id = body.get("id", "")
    question = body.get("question", "")
    if not isinstance(session_id, str) or session_id not in SESSIONS:
        return jsonify(error="Analyze a repository first or start a new analysis session."), 400
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Enter a question first.")
    if len(question) > 1000:
        raise ValueError("Keep the question under 1,000 characters.")

    repository = SESSIONS.pop(session_id)
    SESSIONS[session_id] = repository
    evidence = retrieve_evidence(question, repository)
    answer = answer_repository_question(question, repository)
    return jsonify(answer=answer, how=[item["source"] for item in evidence])


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
