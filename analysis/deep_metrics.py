"""
analysis/deep_metrics.py
Commit streak and inactive repository metrics.
"""

from datetime import datetime, timedelta

def calculate_streaks(commits: list[dict]) -> dict:
    """
    Calculate commit streaks.
    """
    if not commits:
        return {"current": 0, "longest": 0}

    date_strings = []
    for commit in commits:
        raw_date = commit.get("date") or commit.get("timestamp")
        if not raw_date:
            continue
        raw_date = str(raw_date)
        normalized = raw_date.split("T")[0].split(" ")[0]
        if normalized:
            date_strings.append(normalized)

    dates = sorted(list(set(date_strings)), reverse=True)
    if not dates:
        return {"current": 0, "longest": 0}

    # Current streak
    current = 0
    today = datetime.now().date()
    # Check if first commit is within 1 day of today
    last_commit_date = datetime.strptime(dates[0], "%Y-%m-%d").date()
    if (today - last_commit_date).days <= 1:
        current = 1
        for i in range(len(dates) - 1):
            d1 = datetime.strptime(dates[i], "%Y-%m-%d").date()
            d2 = datetime.strptime(dates[i+1], "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                current += 1
            else:
                break
    
    # Longest streak
    longest = 0
    temp = 1
    for i in range(len(dates) - 1):
        d1 = datetime.strptime(dates[i], "%Y-%m-%d").date()
        d2 = datetime.strptime(dates[i+1], "%Y-%m-%d").date()
        if (d1 - d2).days == 1:
            temp += 1
        else:
            longest = max(longest, temp)
            temp = 1
    longest = max(longest, temp)
    
    return {"current": current, "longest": longest}

def ghost_repo_audit(repos: list[dict]) -> list:
    """
    Detect zombie repos (no activity for 1 year).
    """
    ghosts = []
    one_year_ago = datetime.now() - timedelta(days=365)
    for r in repos:
        updated_at = datetime.strptime(r["updated_at"][:19], "%Y-%m-%d %H:%M:%S")
        if updated_at < one_year_ago:
            ghosts.append({
                "name": r["name"],
                "last_updated": r["updated_at"][:10],
                "stars": r["stars"]
            })
    return sorted(ghosts, key=lambda x: x["stars"], reverse=True)
