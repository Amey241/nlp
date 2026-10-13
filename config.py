"""Shared configuration constants for GitHub Profile Analyzer."""

import os

# Cache settings
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_TTL_HOURS = 1

# Performance Settings
API_WORKERS = 10
MAX_REPOS_TO_ANALYZE = 20
REPO_COMMIT_CAP = 60
TOTAL_COMMIT_CAP = 600

# LDA settings
LDA_N_TOPICS = 4
TOPIC_LABELS = ["bug", "feature", "refactor", "docs"]

# Personality badge thresholds
NIGHT_OWL_THRESHOLD = 0.25        # >25% commits between midnight and 4am
DOC_LOVER_THRESHOLD = 0.70         # >70% repos have a README
PROLIFIC_COMMITTER_THRESHOLD = 50  # avg commits per repo
WEEKEND_WARRIOR_THRESHOLD = 0.35   # >35% commits on Sat/Sun

# Colors
ACCENT_COLORS = [
    "#6C63FF", "#FF6584", "#43DDE6", "#F9A826",
    "#7ED957", "#FF8C42", "#A855F7", "#EC4899",
]
