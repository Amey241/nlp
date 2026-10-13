"""Repository-level NLP features built from README text and commit messages."""

import re
from collections import Counter

from analysis.nlp import (
    STOP_WORDS,
    _tfidf_ranked,
    commit_message_insights,
    lda_topics,
    sentiment_analysis,
)


PROJECT_TYPE_RULES = {
    "Machine learning / AI": {"model", "machine learning", "neural", "training", "inference", "embedding", "dataset", "llm", "artificial intelligence"},
    "Command-line tool": {"command line", "cli", "terminal", "shell", "argparse", "typer", "click"},
    "Developer library": {"library", "package", "sdk", "api", "import", "pip install", "npm install"},
    "Data / analytics": {"analytics", "visualization", "dashboard", "data analysis", "reporting", "etl", "pipeline"},
    "Web application": {"web app", "web application", "frontend", "backend", "website", "streamlit", "react", "django", "flask"},
}

def analyze_repository_text(readme: str, commits: list[dict]) -> dict:
    """Extract interpretable NLP signals from a repository README and its commits."""
    readme = readme or ""
    messages = [str(c.get("message", "")).strip() for c in commits if str(c.get("message", "")).strip()]
    corpus = "\n".join(part for part in (readme, *messages) if part)
    words = re.findall(r"(?u)\b[\w]+(?:[-'][\w]+)*\b", corpus.lower())
    terms = [word for word in words if word not in STOP_WORDS and len(word) > 1]
    frequencies = Counter(terms)
    bigrams = Counter(zip(terms, terms[1:]))

    keywords = [
        {"term": term, "score": round(score, 3)}
        for term, score in _tfidf_ranked([readme, *messages], limit=15, max_features=500)
    ]

    lowered = corpus.lower()
    project_types = []
    if corpus:
        type_scores = {
            name: sum(1 for phrase in phrases if phrase in lowered)
            for name, phrases in PROJECT_TYPE_RULES.items()
        }
        total = sum(type_scores.values())
        if total:
            project_types = [
                {"type": name, "percent": round(score / total * 100)}
                for name, score in sorted(type_scores.items(), key=lambda item: (-item[1], item[0]))
                if score
            ]

    headings = []
    section_text = []
    for line in readme.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            if headings:
                headings[-1]["words"] = len(re.findall(r"\b\w+\b", " ".join(section_text)))
            headings.append({"heading": match.group(1).strip(), "words": 0})
            section_text = []
        elif headings:
            section_text.append(line)
    if headings:
        headings[-1]["words"] = len(re.findall(r"\b\w+\b", " ".join(section_text)))

    named_terms = Counter(
        phrase.strip()
        for phrase in re.findall(r"\b(?:[A-Z][a-zA-Z0-9.+#-]*)(?:\s+[A-Z][a-zA-Z0-9.+#-]*){0,2}", readme)
        if len(phrase.strip()) > 1 and phrase.strip().lower() not in {"readme", "installation", "usage", "contributing", "license"}
    )
    commit_summary = commit_message_insights(messages)
    return {
        "keywords": keywords,
        "word_frequency": [{"word": word, "count": count} for word, count in frequencies.most_common(15)],
        "bigrams": [{"phrase": f"{pair[0]} {pair[1]}", "count": count} for pair, count in bigrams.most_common(8) if count > 1],
        "project_types": project_types,
        "readme_outline": headings,
        "named_terms": [{"term": term, "count": count} for term, count in named_terms.most_common(12)],
        "commit_activity": commit_summary["intent_counts"],
        "commit_summary": commit_summary,
        "sentiment": sentiment_analysis(messages),
        "topics": lda_topics(messages),
        "readme_word_count": len(re.findall(r"\b\w+\b", readme)),
        "commit_count": len(messages),
    }
