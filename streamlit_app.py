"""
app.py — GitHub Profile Analyzer
Main Streamlit application entry point.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------ #
#  Page config — MUST be first Streamlit call
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="GitHub Profile Analyzer",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
#  Custom CSS
# ------------------------------------------------------------------ #
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1040 40%, #24243e 100%);
    color: #FFFFFF;
  }

  section[data-testid="stSidebar"] {
    background: #1a1040 !important;
    border-right: 1px solid rgba(255,255,255,0.15);
    backdrop-filter: blur(20px);
  }

  .glass-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(12px);
    color: #FFFFFF;
  }

  .profile-header {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(108,99,255,0.20), rgba(236,72,153,0.10));
    border: 1px solid rgba(108,99,255,0.3);
    border-radius: 20px;
    margin-bottom: 1.5rem;
  }
  .profile-header img {
    width: 90px; height: 90px;
    border-radius: 50%;
    border: 3px solid #6C63FF;
    box-shadow: 0 0 20px rgba(108,99,255,0.4);
  }
  .profile-name {
    font-size: 1.8rem; font-weight: 800;
    color: #FFFFFF;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
  }

  .stat-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem; }
  .stat-pill {
    background: rgba(108,99,255,0.25);
    border: 1px solid rgba(108,99,255,0.45);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: #DDD6FE;
    font-weight: 600;
  }

  .badge-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: transform 0.2s;
  }
  .badge-card:hover {
    transform: translateY(-2px);
    border-color: #6C63FF;
  }
  .badge-title { font-size: 1.1rem; font-weight: 700; color: #FFFFFF; }
  .badge-desc  { font-size: 0.85rem; color: #CBD5E1; margin-top: 0.2rem; }

  .section-header {
    font-size: 1.25rem; font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 0.02em;
    margin-bottom: 0.6rem;
    border-left: 5px solid #6C63FF;
    padding-left: 0.75rem;
  }

  .sentiment-bar-wrap {
    height: 12px; border-radius: 999px;
    background: rgba(255,255,255,0.1);
    overflow: hidden; margin: 0.5rem 0;
  }
  .sentiment-bar { height: 100%; border-radius: 999px; }

  .topic-pill {
    display: inline-block;
    background: rgba(168,85,247,0.2);
    border: 1px solid rgba(168,85,247,0.4);
    border-radius: 8px;
    padding: 0.15rem 0.6rem;
    font-size: 0.75rem;
    color: #E9D5FF;
    margin: 0.15rem;
    font-weight: 600;
  }

  /* Comparison Styles */
  .comp-label {
    font-size: 0.8rem; color: #CBD5E1; margin-bottom: 0.2rem; font-weight: 600;
  }
  .comp-value {
    font-size: 1.2rem; font-weight: 800; color: #FFFFFF;
  }

  #MainMenu, footer { visibility: hidden; }

  input[type=text], .stTextInput input {
    background: rgba(0, 0, 0, 0.5) !important;
    border: 1px solid rgba(108,99,255,0.6) !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
    font-size: 1.1rem !important;
    padding: 0.75rem 1rem !important;
  }
  
  .stTextInput input:focus {
    border: 1px solid #6C63FF !important;
    box-shadow: 0 0 15px rgba(108,99,255,0.3) !important;
  }

  input[type="password"]::-ms-reveal,
  input[type="password"]::-ms-clear {
    display: none !important;
  }
  div[data-baseweb="input"] button[aria-label*="password"],
  div[data-baseweb="input"] button[aria-label*="Password"],
  div[data-baseweb="input"] button[aria-label*="Show"],
  div[data-baseweb="input"] button[aria-label*="Hide"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
  }

  /* Specific Button Contrast Fixes */
  .stDownloadButton button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    font-weight: 700 !important;
  }
  .stButton button {
    background-color: rgba(108, 99, 255, 0.2) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(108, 99, 255, 0.5) !important;
    font-weight: 600 !important;
  }

  /* Sidebar Visibility Fixes */
  section[data-testid="stSidebar"] {
    color: #FFFFFF !important;
  }
  section[data-testid="stSidebar"] p, 
  section[data-testid="stSidebar"] span, 
  section[data-testid="stSidebar"] label {
    color: #FFFFFF !important;
    font-weight: 500 !important;
  }
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: #FFFFFF !important;
  }

  /* Remove Streamlit white header bar */
  header[data-testid="stHeader"], 
  .stAppHeader {
    background: transparent !important;
  }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #
def _topic_emoji(label: str) -> str:
    return {"bug": "🐛", "feature": "🚀", "refactor": "🥷", "docs": "📖"}.get(label, "💡")


def _render_topics(topics_data: dict) -> None:
    if not topics_data.get("topics"):
        return
    dominant = topics_data["dominant_topic"]
    emoji = _topic_emoji(dominant)
    topic_rows = []
    for topic in topics_data["topics"]:
        words_html = " ".join(f'<span class="topic-pill">{word}</span>' for word in topic["top_words"])
        topic_rows.append(
            f'<div style="margin-bottom:0.4rem;">'
            f'<span style="color:#CBD5E1;font-size:0.8rem;">Topic {topic["index"]+1} ({topic["label"]}):</span><br>'
            f'{words_html}</div>'
        )
    topics_html = "".join(topic_rows)
    st.markdown(f"""
    <div class="glass-card">
      <div style="font-weight:600;color:#CBD5E1;margin-bottom:0.5rem;text-transform:uppercase;font-size:0.75rem;">🗂 Dominant Commit Theme</div>
      <div style="font-size:1.5rem;font-weight:800;color:#FFFFFF;margin-bottom:0.75rem;">{emoji} {dominant.title()}</div>
      {topics_html}
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------ #
#  Imports
# ------------------------------------------------------------------ #
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from datetime import datetime
import nltk

# Initialize NLTK data for Streamlit Cloud
@st.cache_resource
def setup_nltk():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('brown', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception:
        pass

setup_nltk()

from config import *
from data.fetcher import GitHubFetcher
from analysis.languages import aggregate_languages, radar_chart, bar_chart
from analysis.activity import build_heatmap_data, activity_heatmap, peak_hours_summary
from analysis.nlp import sentiment_analysis, lda_topics, commit_message_insights
from analysis.personality import classify, generate_narrative, achievement_trophy_case
from analysis.card_generator import generate_card
from analysis.commit_quality import score_commits
from analysis.comparison import overlay_radar, compatibility_score, highlight_differences
from analysis.ai_insights import AIInsights
from analysis.deep_metrics import calculate_streaks, ghost_repo_audit
from utils.repo_nlp_view import render_repository_nlp


# ------------------------------------------------------------------ #
#  Cached Pipeline
# ------------------------------------------------------------------ #
def get_configured_github_token() -> str:
    try:
        secret_token = st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        secret_token = ""
    return (secret_token or os.getenv("GITHUB_TOKEN", "")).strip()


@st.cache_data(ttl=3600, show_spinner=False)
def run_pipeline(username: str, _token_override: str = "") -> dict:
    token = (_token_override or get_configured_github_token()).strip()
    fetcher = GitHubFetcher(token)

    # Pipeline Execution with Progress Tracking
    with st.status("🔍 Analyzing GitHub Profile...") as status:
        status.update(label="📡 Fetching repository & commit data...", state="running")
        raw = fetcher.get_user_data(username)
        
        # Process data for local analysis
        commits = raw["commits"]
        lang_df = aggregate_languages(raw["lang_totals"])
        
        # Analytical Calls (Synced with module names)
        heatmap_pivot = build_heatmap_data(commits)
        activity      = peak_hours_summary(heatmap_pivot)
        sentiment     = sentiment_analysis([c["message"] for c in commits])
        topics        = lda_topics([c["message"] for c in commits])
        message_insights = commit_message_insights([c["message"] for c in commits])
        
        
        # Commit Quality (synced name)
        quality = score_commits([c["message"] for c in commits])
        
        # User Stats for Personality/Narrative/Achievements
        user_stats = {
            "commit_hours":   [c["hour"] for c in commits],
            "commit_weekdays": [c["weekday"] for c in commits],
            "repos":          raw["repos"],
            "dominant_topic": topics["dominant_topic"],
            "avg_sentiment":  sentiment["avg_polarity"],
            "prs_authored":   raw["prs_authored"],
            "issues_authored": raw["issues_authored"],
            "followers":       raw["profile"].get("followers", 0),
        }
        badges = classify(user_stats)
        narrative = generate_narrative(user_stats, raw["profile"])
        achievements = achievement_trophy_case(user_stats, raw["profile"], lang_df)

        status.update(label="🎨 Generating AI Insights...", state="running")
        try:
            ai = AIInsights()
            job_roles = ai.get_job_role_suggestions(user_stats, lang_df)
            low_q_commits = [m for m, s, g in quality.get("worst_examples", [])[:3]]
            rewrites = ai.suggest_commit_rewrites(low_q_commits)
        except Exception:
            job_roles, rewrites = [], []

        try:
            streak_stats = calculate_streaks(commits)
            ghosts = ghost_repo_audit(raw["repos"])
        except Exception:
            streak_stats = {"current": 0, "longest": 0}
            ghosts = []

        status.update(label="✅ Analysis Complete!", state="complete")

    return {
        "profile": raw["profile"],
        "repos": raw["repos"],
        "lang_df": lang_df,
        "heatmap_pivot": heatmap_pivot,
        "activity": activity,
        "sentiment": sentiment,
        "topics": topics,
        "message_insights": message_insights,
        "badges": badges,
        "commits": commits,
        "quality": quality,
        "user_stats": user_stats,
        "narrative": narrative,
        "achievements": achievements,
        "job_roles": job_roles,
        "rewrites": rewrites,
        "streak_stats": streak_stats,
        "ghosts": ghosts,
    }


# ------------------------------------------------------------------ #
#  Sidebar
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## 🔭 GitHub Analyzer")
    st.markdown("Uncover any developer's coding personality through data.")
    st.divider()

    configured_token = get_configured_github_token()
    if configured_token:
        st.text_input(
            "GitHub Personal Access Token",
            value="************",
            type="password",
            disabled=True,
            help="The deployment is using a server-side token. Its real value is hidden from users.",
        )
        token = ""
    else:
        token_input = st.text_input(
            "GitHub Personal Access Token",
            value="",
            type="password",
            placeholder="ghp_xxxxxxxxxxxx",
            help="Generate at github.com/settings/tokens — no scopes needed for public repos.",
        )
        token = token_input.strip()

    st.divider()
    
    # Feature 13: Rate Limit Monitor
    def show_rate_limit(fetcher):
        if not fetcher: return
        rate = fetcher.get_rate_limit()
        if rate:
            rem = rate['remaining']
            total = rate['limit']
            color = "green" if rem > 1000 else "orange" if rem > 200 else "red"
            st.markdown(f"**API Quota:** :{color}[{rem} / {total}]")
            st.progress(rem / total)
            st.caption(f"Resets at: `{rate['reset']}`")
            if rem < 100:
                st.warning("Low API quota — analysis may be capped.")
    
    if 'fetcher' in locals() or 'fetcher' in globals():
        show_rate_limit(fetcher if 'fetcher' in locals() else globals().get('fetcher'))
    
    st.divider()
    mode = st.radio("Analysis Mode", ["Single Profile", "Compare Mode"], index=0)
    
    st.divider()
    st.markdown("**How to use**")
    if configured_token:
        st.markdown("""
1. Enter username(s)  
2. Hit **Enter** — wait ~30 s  
3. Explore the insights!
        """)
    else:
        st.markdown("""
1. Paste your GitHub token above  
2. Enter username(s)  
3. Hit **Enter** — wait ~30 s  
4. Explore the insights!
        """)
    st.divider()
    st.caption("Rate limit: 5,000 req/hr with token. Results cached 1 hr.")


# ------------------------------------------------------------------ #
#  Main header
# ------------------------------------------------------------------ #
st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 1rem;">
  <span style="font-size:2.5rem; font-weight:800;
    background: linear-gradient(90deg, #6C63FF, #EC4899, #F9A826);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;">
    GitHub Profile Analyzer
  </span>
  <p style="color:#94A3B8; margin-top:0.4rem; font-size:0.95rem;">
    Data-driven personality insights from commit history
  </p>
</div>
""", unsafe_allow_html=True)

if mode == "Single Profile":
    username = st.text_input(
        "GitHub Username",
        placeholder="🔍  Enter a GitHub username (e.g. torvalds, gvanrossum)",
        label_visibility="collapsed",
    )
else:
    c1, c2 = st.columns(2)
    with c1:
        u1 = st.text_input("First Developer", placeholder="e.g. torvalds")
    with c2:
        u2 = st.text_input("Second Developer", placeholder="e.g. gvanrossum")
    username = (u1, u2) if (u1 and u2) else None

active_token = configured_token or token

if not active_token:
    st.warning("⚠️ Please add a GitHub Personal Access Token to continue.")
    st.stop()

if not username:
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; justify-content:center; margin-top:2rem;">
      <div class="glass-card" style="text-align:center; min-width:130px;">
        <div style="font-size:2rem;">🐧</div>
        <div style="color:#FFFFFF; font-weight:800;">torvalds</div>
        <div style="color:#CBD5E1; font-size:0.8rem;">Linux kernel</div>
      </div>
      <div class="glass-card" style="text-align:center; min-width:130px;">
        <div style="font-size:2rem;">🐍</div>
        <div style="color:#FFFFFF; font-weight:800;">gvanrossum</div>
        <div style="color:#CBD5E1; font-size:0.8rem;">Python creator</div>
      </div>
      <div class="glass-card" style="text-align:center; min-width:130px;">
        <div style="font-size:2rem;">🦀</div>
        <div style="color:#FFFFFF; font-weight:800;">nikomatsakis</div>
        <div style="color:#CBD5E1; font-size:0.8rem;">Rust core dev</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ------------------------------------------------------------------ #
#  Run analysis
# ------------------------------------------------------------------ #
try:
    if isinstance(username, str):
        with st.spinner(f"🔍 Analysing **{username}**'s GitHub profile…"):
            data = run_pipeline(username.strip(), token)
            data_list = [data]
    else:
        with st.spinner(f"⚔️ Comparing **{username[0]}** vs **{username[1]}**…"):
            data_a = run_pipeline(username[0].strip(), token)
            data_b = run_pipeline(username[1].strip(), token)
            data_list = [data_a, data_b]
except ValueError as e:
    st.error(f"❌ {e}")
    st.stop()
except RuntimeError as e:
    st.error(f"⚠️ {e}")
    st.stop()
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.stop()

if len(data_list) == 2:
    # ── COMPARISON MODE ──────────────────────────────────────────────────────
    d1, d2 = data_list[0], data_list[1]
    p1, p2 = d1["profile"], d2["profile"]

    st.markdown(f"""
    <div style="display:flex; justify-content:space-around; align-items:center; margin-bottom:2rem;">
        <div style="text-align:center;">
            <img src="{p1['avatar_url']}" style="width:100px; height:100px; border-radius:50%; border:3px solid #6C63FF; box-shadow:0 0 15px rgba(108,99,255,0.4); mb:0.5rem;" />
            <div style="font-size:1.4rem; font-weight:800; color:#FFFFFF;">{p1['name']}</div>
            <div style="color:#CBD5E1;">@{p1['login']}</div>
        </div>
        <div style="font-size:3rem; font-weight:900; color:rgba(255,255,255,0.1); font-style:italic;">VS</div>
        <div style="text-align:center;">
            <img src="{p2['avatar_url']}" style="width:100px; height:100px; border-radius:50%; border:3px solid #EC4899; box-shadow:0 0 15px rgba(236,72,153,0.4); mb:0.5rem;" />
            <div style="font-size:1.4rem; font-weight:800; color:#FFFFFF;">{p2['name']}</div>
            <div style="color:#CBD5E1;">@{p2['login']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Compatibility Score
    comp = compatibility_score(d1["user_stats"], d2["user_stats"], d1["lang_df"], d2["lang_df"])
    st.markdown(f"""
    <div class="glass-card" style="text-align:center; border:1px solid rgba(249,168,38,0.4);">
        <div style="color:#CBD5E1; font-size:0.8rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em;">Compatibility Score</div>
        <div style="font-size:3.5rem; font-weight:800; color:#F9A826; margin:0.5rem 0;">{comp['score']}%</div>
        <div style="font-size:1.2rem; font-weight:600; color:#FFFFFF;">{comp['label']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Insights & Radar
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.markdown('<div class="section-header">🔍 Key Differences</div>', unsafe_allow_html=True)
        diffs = highlight_differences(d1["user_stats"], d2["user_stats"], p1["login"], p2["login"])
        for d in diffs:
            st.markdown(f'<div class="badge-card" style="padding:0.75rem 1rem; margin-bottom:0.5rem;">{d}</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header" style="margin-top:1.5rem;">🤝 Team Insights</div>', unsafe_allow_html=True)
        for ins in comp["insights"]:
            st.markdown(f'<div style="color:#FFFFFF; font-size:0.9rem; margin-bottom:0.4rem;">{ins}</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-header">🌐 Language Overlap</div>', unsafe_allow_html=True)
        st.plotly_chart(overlay_radar(d1["lang_df"], d2["lang_df"], p1["login"], p2["login"]), use_container_width=True)

else:
    # ── SINGLE PROFILE MODE ──────────────────────────────────────────────────
    data = data_list[0]
    profile       = data["profile"]
    lang_df       = data["lang_df"]
    heatmap_pivot = data["heatmap_pivot"]
    activity      = data["activity"]
    sentiment     = data["sentiment"]
    topics        = data["topics"]
    badges        = data["badges"]
    repos         = data["repos"]
    commits       = data["commits"]
    quality       = data["quality"]

    # Header with Card Generator
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"""
        <div class="profile-header">
          <img src="{profile['avatar_url']}" alt="avatar" />
          <div>
            <div class="profile-name">{profile['name']}</div>
            <div style="color:#E2E8F0;font-size:0.9rem;">@{profile['login']}</div>
            <div style="color:#CBD5E1;font-size:0.85rem;margin-top:0.2rem;">{profile['bio']}</div>
            <div style="color:#FFFFFF; font-style:italic; font-size:1rem; margin-top:1rem; line-height:1.4;">
              "{data['narrative']}"
            </div>
            <div class="stat-row">
              <span class="stat-pill">📁 {profile['public_repos']} repos</span>
              <span class="stat-pill">👥 {profile['followers']} followers</span>
              <span class="stat-pill">💬 {len(commits)} commits analysed</span>
            </div>
            <div style="display:flex; gap:1.5rem; margin-top:0.8rem;">
               <div style="text-align:center;">
                 <div style="font-size:1.2rem; font-weight:800; color:#EC4899;">{data['streak_stats']['current']}</div>
                 <div style="font-size:0.65rem; color:#CBD5E1; text-transform:uppercase;">Current Streak</div>
               </div>
               <div style="text-align:center;">
                 <div style="font-size:1.2rem; font-weight:800; color:#6C63FF;">{data['streak_stats']['longest']}</div>
                 <div style="font-size:0.65rem; color:#CBD5E1; text-transform:uppercase;">Longest Streak</div>
               </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="height:25px;"></div>', unsafe_allow_html=True)
        card_bytes = generate_card(profile, badges, lang_df, sentiment, commits, profile["login"])
        st.download_button(
            label="🎨 Download Wrapped Card",
            data=card_bytes,
            file_name=f"{profile['login']}_wrapped.png",
            mime="image/png",
            use_container_width=True,
        )

    # Badges
    st.markdown('<div class="section-header">🏅 Personality Badges</div>', unsafe_allow_html=True)
    n_cols = min(len(badges), 3)
    badge_cols = st.columns(n_cols)
    for i, b in enumerate(badges):
        with badge_cols[i % n_cols]:
            st.markdown(f"""
            <div class="badge-card">
              <div class="badge-title">{b['badge']}</div>
              <div class="badge-desc">{b['description']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Feature 12: Hidden Achievements (Always try to show some)
    unlocked = [a for a in data.get("achievements", []) if a["unlocked"]]
    if unlocked:
        achievement_badges = "".join(
            f'<span title="{a["desc"]}" style="background: rgba(249,168,38,0.1); border: 1px solid #F9A826; color: #F9A826; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{a["emoji"]} {a["name"]}</span>'
            for a in unlocked
        )
        st.markdown(
            f'<div style="margin-top: -1rem; margin-bottom: 1.5rem; display: flex; gap: 10px; flex-wrap: wrap;">{achievement_badges}</div>',
            unsafe_allow_html=True,
        )



    # AI Job Matcher (Feature 7)
    st.markdown('<div class="section-header">💼 AI Job Role Matcher</div>', unsafe_allow_html=True)
    role_cols = st.columns(3)
    roles = data.get("job_roles", [])
    if not roles:
        roles = ["Full Stack Developer", "Software Engineer", "Open Source Contributor"] # Fallback
    
    for i, role in enumerate(roles[:3]):
        with role_cols[i]:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding:1.5rem; border-color:#22D3EE;">
                <div style="font-size:0.8rem; color:#22D3EE; font-weight:700;">#{i+1} RECOMMENDATION</div>
                <div style="font-size:1.1rem; font-weight:700; color:#FFFFFF; margin-top:0.5rem;">{role}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()

    # Lang & Activity
    col_left, col_right = st.columns(2, gap="large")
    with col_left:
        st.markdown('<div class="section-header">🌐 Language Distribution</div>', unsafe_allow_html=True)
        if not lang_df.empty:
            tab1, tab2 = st.tabs(["🕸 Radar", "📊 Bar"])
            with tab1: st.plotly_chart(radar_chart(lang_df), use_container_width=True)
            with tab2: st.plotly_chart(bar_chart(lang_df), use_container_width=True)
    with col_right:
        st.markdown('<div class="section-header">⏰ Commit Activity Heatmap</div>', unsafe_allow_html=True)
        if not heatmap_pivot.empty:
            st.plotly_chart(activity_heatmap(heatmap_pivot), use_container_width=True)



    # WordCloud & NLP & Quality
    col_quality, col_nlp = st.columns([1.1, 1], gap="large")
    with col_quality:
        
        # QUALITY SCORE
        st.markdown('<div class="section-header" style="margin-top:1.5rem;">📝 Commit Quality Report</div>', unsafe_allow_html=True)
        q = quality
        c_a, c_b = st.columns([1, 2])
        with c_a:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding:1.5rem 0;">
                <div style="font-size:0.8rem; color:#E2E8F0;">GRADE</div>
                <div style="font-size:4rem; font-weight:800; color:#6C63FF;">{q['grade']}</div>
                <div style="font-size:0.9rem; color:#FFFFFF;">Score: {q['avg_score']}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_b:
            for tip in q["top_tips"]:
                st.markdown(f'<div style="font-size:0.85rem; color:#FFFFFF; margin-bottom:0.4rem;">💡 {tip}</div>', unsafe_allow_html=True)
            
            # AI REWRITER (Feature 8)
            if data["rewrites"]:
                with st.expander("✨ AI Suggested Rewrites"):
                    for rw in data["rewrites"]:
                        st.markdown(f"""
                        <div style="font-size:0.8rem; margin-bottom:0.5rem; padding:0.5rem; border-left:2px solid #6C63FF; background:rgba(108,99,255,0.05);">
                          <div style="color:#94A3B8;"><s>{rw['old']}</s></div>
                          <div style="color:#6C63FF; font-weight:600;">-> {rw['new']}</div>
                        </div>
                        """, unsafe_allow_html=True)


    with col_nlp:
        st.markdown('<div class="section-header">Commit Language Insights</div>', unsafe_allow_html=True)
        insights = data.get("message_insights", {})
        intent_counts = insights.get("intent_counts", {})
        if intent_counts:
            intent_df = pd.DataFrame(
                [{"Intent": name, "Commits": count} for name, count in intent_counts.items()]
            ).sort_values("Commits", ascending=True)
            intent_fig = go.Figure(go.Bar(
                x=intent_df["Commits"], y=intent_df["Intent"], orientation="h",
                marker_color="#A855F7", text=intent_df["Commits"], textposition="outside",
            ))
            intent_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"}, height=260,
                margin=dict(t=10, b=10, l=10, r=35),
                xaxis={"visible": False}, yaxis={"title": ""},
            )
            st.plotly_chart(intent_fig, use_container_width=True)
            st.caption("Intent labels are keyword-based estimates from commit messages.")
            m1, m2 = st.columns(2)
            m1.metric("Avg. words per message", insights.get("avg_words", 0))
            m2.metric("Vocabulary variety", f'{insights.get("vocabulary_richness", 0):.0%}')
            if insights.get("keywords"):
                st.markdown("**Recurring terms**")
                st.markdown(" ".join(f'<span class="topic-pill">{word}</span>' for word in insights["keywords"]), unsafe_allow_html=True)
        else:
            st.info("No commit messages were available for language analysis.")




    render_repository_nlp(profile["login"], repos, get_configured_github_token() or token)

    # Ghost Repo Audit (if any)
    ghosts = data.get("ghosts", [])
    if ghosts:
        st.divider()
        st.markdown('<div class="section-header">👻 Ghost Repo Audit</div>', unsafe_allow_html=True)
        ghost_cols = st.columns(min(len(ghosts), 4))
        for i, g in enumerate(ghosts[:4]):
            with ghost_cols[i]:
                st.markdown(f"""
                <div class="glass-card" style="padding:0.8rem; border-color:#94A3B8;">
                    <div style="font-weight:600; font-size:0.85rem; color:#FFFFFF; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{g['name']}</div>
                    <div style="font-size:0.75rem; color:#94A3B8; margin-top:0.3rem;">Inactive since {g['last_updated']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.info("💡 Pro-tip: Archiving inactive repos makes your GitHub profile look more maintained and focused.")

    st.divider()





    # ------------------------------------------------------------------ #
    #  Footer
    # ------------------------------------------------------------------ #
st.caption("Built with PyGithub, Streamlit, Plotly, TF-IDF, and TextBlob")
