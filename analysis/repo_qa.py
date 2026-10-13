"""Evidence-grounded questions over the README and recent commit messages."""

import re

_QUESTION_FILLER = {
    "a", "about", "are", "can", "could", "does", "do", "for", "from", "how",
    "i", "is", "it", "me", "of", "on", "please", "the", "this", "to", "what",
    "when", "where", "which", "who", "why", "would", "you", "repo", "repository",
    "project", "code", "github", "tell", "show", "explain",
}
_TERM_NORMALIZATION = {
    "installation": "install",
    "installing": "install",
    "installed": "install",
    "setup": "install",
    "require": "install",
    "requires": "install",
    "required": "install",
    "dependencies": "install",
    "dependency": "install",
    "requirements": "install",
    "quickstart": "start",
    "usage": "run",
    "running": "run",
}
_QUERY_EXPANSIONS = {
    "install": {"setup", "dependencies", "dependency", "requirements", "pip", "npm", "quick", "start", "run"},
    "run": {"start", "usage", "command", "launch"},
}
_INSTALL_QUESTION = re.compile(r"\b(install|installation|setup|set up|get started|requirements?|dependencies)\b", re.I)
_INSTALL_DETAILS = re.compile(
    r"\b(install(?:ation|ing|ed)?|pip|npm|pnpm|yarn|cargo|poetry|uv|requirements?|"
    r"dependenc(?:y|ies)|setup|quick ?start|get(?:ting)? started|python\s+\S+|node\s+\S+)\b",
    re.I,
)


def _tokens(text: str) -> set[str]:
    return {
        _TERM_NORMALIZATION.get(token.lower(), token.lower())
        for token in re.findall(r"[A-Za-z0-9_+-]{2,}", text)
        if token.lower() not in _QUESTION_FILLER
    }


def _readme_sections(readme: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = [("README.md", [])]
    for line in readme.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            sections.append((f"README.md > {heading.group(1).strip()}", []))
        else:
            sections[-1][1].append(line)
    return [(title, "\n".join(lines).strip()) for title, lines in sections if "\n".join(lines).strip()]


def retrieve_evidence(question: str, repository: dict, limit: int = 8) -> list[dict]:
    """Rank README sections and commit messages by useful question-term overlap."""
    query = _tokens(question)
    query.update(term for token in tuple(query) for term in _QUERY_EXPANSIONS.get(token, set()))
    candidates = []
    for source, text in _readme_sections(repository.get("readme", "")):
        for paragraph in re.split(r"\n\s*\n", text):
            paragraph = paragraph.strip()
            if len(paragraph) >= 25:
                candidates.append({"source": source, "text": paragraph[:1200]})
    for commit in repository.get("commits", []):
        message = commit.get("message", "").strip()
        if message:
            candidates.append({"source": f"commit {commit.get('sha', '')}", "text": message[:500]})
    description = str(repository.get("description", "")).strip()
    if description:
        candidates.append({"source": "GitHub repository description", "text": description[:500]})

    def rank(item: dict) -> tuple[int, int]:
        matched = len(query & _tokens(item["text"]))
        return matched, -len(item["text"])

    candidates.sort(key=rank, reverse=True)
    return [item for item in candidates if rank(item)[0] > 0][:limit]


def answer_repository_question(question: str, repository: dict) -> str:
    """Return matching repository excerpts with citations, without an LLM call."""
    if _INSTALL_QUESTION.search(question):
        setup_lines = []
        for section, text in _readme_sections(repository.get("readme", "")):
            for line in text.splitlines():
                line = line.strip()
                if len(line) > 3 and _INSTALL_DETAILS.search(line):
                    item = {"source": section, "text": line[:800]}
                    if item not in setup_lines:
                        setup_lines.append(item)
        if setup_lines:
            lines = ["The README contains these setup details:"]
            lines.extend(f"- {item['text']} [{item['source']}]" for item in setup_lines[:5])
            return "\n\n".join(lines)

    evidence = retrieve_evidence(question, repository)
    if not evidence:
        return (
            "I couldn't find matching README or commit text for that question. "
            "Try a more specific term from the repository."
        )
    excerpts = evidence[:4]
    lines = ["Here are the closest matches from the repository:"]
    lines.extend(f"- {item['text']} [{item['source']}]" for item in excerpts)
    return "\n\n".join(lines)
