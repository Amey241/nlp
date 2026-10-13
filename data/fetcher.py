"""
data/fetcher.py — GitHub Data Integration
Fetches profile, repositories, and commits using PyGithub with parallel processing.
"""

import os
import json
import threading
from datetime import datetime, timezone, timedelta
from github import Github, GithubException, RateLimitExceededException
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    CACHE_DIR, CACHE_TTL_HOURS, REPO_COMMIT_CAP,
    API_WORKERS, MAX_REPOS_TO_ANALYZE, TOTAL_COMMIT_CAP,
)
from utils.sanitize import safe_int

class GitHubFetcher:
    def __init__(self, token: str):
        self.g = Github(token, per_page=100) if token else Github(per_page=100)
        self.lock = threading.Lock()
        self.total_commits_fetched = 0

    @staticmethod
    def _to_int(value, default: int = 0) -> int:
        return safe_int(value, default)

    def get_rate_limit(self):
        """Return rate limit info for the UI."""
        try:
            rate = self.g.get_rate_limit().core
            return {
                "remaining": rate.remaining,
                "limit": rate.limit,
                "reset": rate.reset.strftime("%H:%M:%S")
            }
        except:
            return None

    def _get_recent_repos(self, user, limit: int):
        """
        Fetch only the most recently pushed public repos without materializing the
        user's entire repository list.
        """
        repos = []
        try:
            repo_pages = user.get_repos(type="public", sort="pushed", direction="desc")
        except TypeError:
            repo_pages = user.get_repos(type="public")

        for repo in repo_pages:
            repos.append(repo)
            if len(repos) >= limit:
                break
        return repos

    # ------------------------------------------------------------------ #
    #  Cache helpers
    # ------------------------------------------------------------------ #
    def _cache_path(self, username: str) -> str:
        os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, f"{username}.json")

    def _load_cache(self, username: str):
        path = self._cache_path(username)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        age_hours = (datetime.now(timezone.utc) - cached_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        if age_hours > CACHE_TTL_HOURS:
            return None
        return self._normalize_cached_data(data)

    def _save_cache(self, username: str, data: dict):
        path = self._cache_path(username)
        data["_cached_at"] = datetime.now(timezone.utc).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _normalize_cached_data(self, data: dict) -> dict:
        profile = data.get("profile", {})
        for key in ("public_repos", "followers", "following"):
            profile[key] = self._to_int(profile.get(key, 0))

        normalized_repos = []
        for repo in data.get("repos", []):
            normalized_repo = dict(repo)
            for key in ("stars", "forks", "commit_count", "open_issues_count"):
                normalized_repo[key] = self._to_int(normalized_repo.get(key, 0))
            for key in ("contributor_count", "user_share_all_time", "bus_factor_ready"):
                normalized_repo.pop(key, None)
            normalized_repos.append(normalized_repo)
        data["repos"] = normalized_repos

        normalized_commits = []
        for commit in data.get("commits", []):
            normalized_commit = dict(commit)
            normalized_commit["hour"] = self._to_int(normalized_commit.get("hour", 0))
            timestamp = str(normalized_commit.get("timestamp", "") or normalized_commit.get("date", ""))
            normalized_commit["timestamp"] = timestamp
            normalized_commit["date"] = timestamp
            if "year" not in normalized_commit and len(timestamp) >= 4 and timestamp[:4].isdigit():
                normalized_commit["year"] = int(timestamp[:4])
            normalized_commits.append(normalized_commit)
        data["commits"] = normalized_commits

        data["lang_totals"] = {
            str(lang): self._to_int(value)
            for lang, value in data.get("lang_totals", {}).items()
        }
        data["issues_authored"] = self._to_int(data.get("issues_authored", 0))
        data["prs_authored"] = self._to_int(data.get("prs_authored", 0))
        data.pop("pr_reviews_count", None)
        data.pop("issue_comments_count", None)
        data.pop("all_samples", None)
        data.pop("all_deps", None)
        return data

    # ------------------------------------------------------------------ #
    #  Public entry point
    # ------------------------------------------------------------------ #
    def get_user_data(self, username: str) -> dict:
        """Return rich dict for *username*. Uses cache if fresh."""
        cached = self._load_cache(username)
        if cached:
            return cached

        data = self._fetch(username)
        self._save_cache(username, data)
        return data

    # ------------------------------------------------------------------ #
    #  Fetching
    # ------------------------------------------------------------------ #
    def _fetch(self, username: str) -> dict:
        try:
            user = self.g.get_user(username)
        except GithubException as e:
            if e.status == 404:
                raise ValueError(f"GitHub user '{username}' not found.")
            raise RuntimeError(f"GitHub API error: {e.data.get('message', str(e))}")

        profile = {
            "login": user.login,
            "name": user.name or user.login,
            "bio": user.bio or "",
            "avatar_url": user.avatar_url,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": str(user.created_at),
            "location": user.location or "",
            "blog": user.html_url,
        }

        repos_data = []
        all_commits = []
        lang_totals = {}

        try:
            target_repos = self._get_recent_repos(user, MAX_REPOS_TO_ANALYZE)
        except RateLimitExceededException:
            raise RuntimeError("GitHub rate limit exceeded.")

        self.total_commits_fetched = 0

        def process_repo(repo):
            repo_commits = []
            try:
                # 1. Commits (author specific, capped)
                # Check global cap before starting commit loop
                with self.lock:
                    can_fetch_commits = self.total_commits_fetched < TOTAL_COMMIT_CAP
                
                if can_fetch_commits:
                    commits_iter = repo.get_commits(author=username)
                    for commit in commits_iter[:REPO_COMMIT_CAP]:
                        with self.lock:
                            if self.total_commits_fetched >= TOTAL_COMMIT_CAP:
                                break
                            self.total_commits_fetched += 1
                        
                        ts = commit.commit.author.date
                        repo_commits.append({
                            "message": (commit.commit.message or "").split("\n")[0],
                            "timestamp": str(ts),
                            "date": str(ts),
                            "year": ts.year if ts else None,
                            "hour": ts.hour if ts else 0,
                            "weekday": ts.strftime("%A") if ts else "Monday",
                            "repo_lang": repo.language or "Unknown"
                        })

                # 2. Languages & Basic Stats
                raw_langs = repo.get_languages()
                langs = {}
                for lang, value in raw_langs.items():
                    coerced = self._to_int(value, None)
                    if coerced is None:
                        continue
                    langs[lang] = coerced
                
                # 3. SINGLE-PASS CONTENT PEEK
                root_files = []
                try: 
                    root_files = repo.get_contents("")
                except: pass

                has_readme = any(f.name.lower().startswith("readme") for f in root_files)

                return {
                    "repo_data": {
                        "name": repo.name,
                        "language": repo.language or "Unknown",
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "updated_at": str(repo.updated_at),
                        "has_readme": has_readme,
                        "commit_count": len(repo_commits)
                    },
                    "commits": repo_commits,
                    "languages": langs,
                }
            except:
                return None

        repos_data = []
        all_commits = []
        lang_totals = {}

        # Parallelize repo processing
        with ThreadPoolExecutor(max_workers=API_WORKERS) as executor:
            futures = [executor.submit(process_repo, r) for r in target_repos]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    repos_data.append(res["repo_data"])
                    all_commits.extend(res["commits"])
                    for l, v in res["languages"].items():
                        lang_totals[l] = lang_totals.get(l, 0) + v

        # PRs & Issues (Robust totalCount)
        issues_authored = 0
        prs_authored = 0
        try:
            issue_search = self.g.search_issues(f"author:{username} is:issue is:public")
            prs_search = self.g.search_issues(f"author:{username} is:pr is:public")
            issues_authored = issue_search.totalCount
            prs_authored = prs_search.totalCount
        except: pass

        return {
            "profile": profile,
            "repos": repos_data,
            "commits": all_commits,
            "lang_totals": lang_totals,
            "issues_authored": issues_authored,
            "prs_authored": prs_authored,
        }

