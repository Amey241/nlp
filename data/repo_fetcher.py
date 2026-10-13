"""Fetch only public README and commit text needed for repository NLP."""

import re

from github import Github


def normalize_repository_name(value: str) -> str:
    value = (value or "").strip().rstrip("/")
    value = re.sub(r"^https?://(?:www\.)?github\.com/", "", value, flags=re.I)
    value = value.removesuffix(".git")
    parts = [part for part in value.split("/") if part]
    if len(parts) != 2 or any(part in {".", ".."} for part in parts):
        raise ValueError("Enter a GitHub repository URL or owner/repository, such as `pallets/flask`.")
    return "/".join(parts)


def fetch_repository_text(repository: str, token: str = "", commit_limit: int = 300) -> dict:
    """Return repository metadata, README text, and recent commit messages."""
    full_name = normalize_repository_name(repository)
    client = Github(token.strip(), per_page=100) if token and token.strip() else Github(per_page=100)
    repo = client.get_repo(full_name)

    try:
        readme = repo.get_readme().decoded_content.decode("utf-8", errors="replace")
    except Exception:
        readme = ""

    commits = []
    for item in repo.get_commits()[:commit_limit]:
        commit = item.commit
        commits.append({
            "sha": item.sha[:7],
            "message": (commit.message or "").strip()[:2000],
            "date": commit.author.date.isoformat() if commit.author and commit.author.date else "",
        })

    return {
        "full_name": repo.full_name,
        "description": repo.description or "",
        "url": repo.html_url,
        "stars": repo.stargazers_count,
        "language": repo.language or "Unknown",
        "readme": readme[:100_000],
        "commits": commits,
    }
