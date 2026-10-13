"""Streamlit section for repository NLP and repository-grounded Q&A."""

import html

import plotly.express as px
import streamlit as st

from analysis.commit_quality import score_commits
from analysis.repo_qa import answer_repository_question
from analysis.repository_nlp import analyze_repository_text
from data.repo_fetcher import fetch_repository_text, normalize_repository_name


def _bar_chart(rows: list[dict], label: str, value: str, alt: str, height: int = 280) -> None:
    if not rows:
        st.info("Not enough text to show this analysis.")
        return
    fig = px.bar(rows, x=value, y=label, orientation="h", text=value)
    fig.update_layout(
        height=height,
        margin=dict(l=5, r=10, t=10, b=5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(fig, alt=alt)


def render_repository_nlp(owner: str, repos: list[dict], github_token: str = "") -> None:
    """Let a profile viewer select one of the developer's repositories and analyze it."""
    if not repos:
        return

    state_prefix = f"repo_nlp_{owner.lower()}"
    names = sorted({repo["name"] for repo in repos if repo.get("name")})
    if not names:
        return

    st.divider()
    st.markdown('<div class="section-header">Repository NLP & Q&A</div>', unsafe_allow_html=True)
    st.caption("Choose one of this developer's repositories or paste another public GitHub repository link.")

    col_select, col_link, col_action = st.columns([1, 1.4, 0.8])
    with col_select:
        selected_name = st.selectbox("Developer repository", names, key=f"{state_prefix}_select")
    with col_link:
        pasted_repo = st.text_input("Or paste a repository URL", key=f"{state_prefix}_url", placeholder="owner/name or github.com/owner/name")
    with col_action:
        st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        analyze_clicked = st.button("Analyze repo", type="primary", key=f"{state_prefix}_analyze")

    target = pasted_repo.strip() or f"{owner}/{selected_name}"
    try:
        normalized_target = normalize_repository_name(target).lower()
    except ValueError:
        normalized_target = target.lower().removesuffix(".git").rstrip("/")
    result_key = f"{state_prefix}_result"
    chat_key = f"{state_prefix}_chat_v2_{normalized_target}"
    if analyze_clicked:
        try:
            with st.spinner(f"Fetching README and recent commits for {target}..."):
                repository = fetch_repository_text(target, github_token)
                metrics = analyze_repository_text(repository["readme"], repository["commits"])
                quality = score_commits([commit["message"].split("\n", 1)[0] for commit in repository["commits"]])
            st.session_state[result_key] = {
                "target": repository["full_name"].lower(),
                "repository": repository,
                "metrics": metrics,
                "quality": quality,
            }
            st.session_state.pop(chat_key, None)
        except Exception as error:
            st.error(f"Could not analyze this repository: {error}")

    result = st.session_state.get(result_key)
    if not result or result["target"] != normalized_target:
        return

    repository, metrics, quality = result["repository"], result["metrics"], result["quality"]
    st.markdown(f"### [{repository['full_name']}]({repository['url']})")
    if repository["description"]:
        st.write(repository["description"])
    summary_cols = st.columns(4)
    summary_cols[0].metric("Language", repository["language"])
    summary_cols[1].metric("Stars", f"{repository['stars']:,}")
    summary_cols[2].metric("README words", f"{metrics['readme_word_count']:,}")
    summary_cols[3].metric("Commits analyzed", f"{metrics['commit_count']:,}")

    readme_tab, commits_tab, qa_tab = st.tabs(["README analysis", "Commit analysis", "Ask about this repo"])
    with readme_tab:
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.subheader("Project type")
                if metrics["project_types"]:
                    for item in metrics["project_types"]:
                        st.write(f"{item['type']} | {item['percent']}%")
                        st.progress(item["percent"] / 100)
                else:
                    st.info("Not enough README text to estimate the project type.")
            with st.container(border=True):
                st.subheader("README outline")
                _bar_chart(metrics["readme_outline"], "heading", "words", "README section word counts.")
        with right:
            with st.container(border=True):
                st.subheader("Key terms (TF-IDF)")
                if metrics["keywords"]:
                    st.markdown(" ".join(f"`{html.escape(item['term'])}`" for item in metrics["keywords"]))
                else:
                    st.info("Not enough distinct README terms to calculate TF-IDF.")
            with st.container(border=True):
                st.subheader("Word frequency (after stop-words)")
                rows = [{"word": item["word"], "count": item["count"]} for item in metrics["word_frequency"][:12]]
                _bar_chart(rows, "word", "count", "Most frequent README and commit terms.")
                st.markdown("**Bigrams**")
                if metrics["bigrams"]:
                    st.markdown(" | ".join(f"`{html.escape(item['phrase'])}` ({item['count']})" for item in metrics["bigrams"]))
                else:
                    st.caption("No repeated word pairs found.")
        if metrics["named_terms"]:
            st.caption("Named terms: " + " | ".join(item["term"] for item in metrics["named_terms"]))

    with commits_tab:
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.subheader("Commit activity")
                activity = [{"intent": key, "commits": count} for key, count in metrics["commit_activity"].items()]
                if activity:
                    fig = px.bar(activity, x="intent", y="commits", color="intent", text="commits")
                    fig.update_layout(showlegend=False, height=280, margin=dict(l=5, r=5, t=10, b=5),
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font_color="#e2e8f0", xaxis_title="Commit intent", yaxis_title="Commits")
                    st.plotly_chart(fig, alt="Commit counts grouped by inferred intent.")
                else:
                    st.info("No commit messages to classify.")
                st.metric("Commit tone", metrics["sentiment"]["mood"], f"Polarity {metrics['sentiment']['avg_polarity']:.3f}")
                for topic in metrics["topics"].get("topics", []):
                    st.caption(f"{topic['label'].title()} topic: {', '.join(topic['top_words'])}")
        with right:
            with st.container(border=True):
                st.subheader("Commit message quality")
                st.metric("Average score", f"{quality['avg_score']} / 100", f"Grade {quality['grade']}")
                for label, field in (("Conventional format", "conventional_avg"), ("Imperative wording", "imperative_avg"), ("Clear length", "length_avg"), ("Issue references", "reference_avg")):
                    st.write(f"{label}: {quality.get(field, 0)}")
                for tip in quality.get("top_tips", [])[:3]:
                    st.caption(f"- {tip}")

    with qa_tab:
        st.caption(f"Ask me anything about {repository['full_name']}. Answers search repository text and include source labels; no AI API key is needed.")
        history = st.session_state.setdefault(chat_key, [])
        for message in history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input(
            "e.g. How do I install it?",
            key=f"{chat_key}_input",
        )
        if question:
            history.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Searching repository evidence..."):
                        answer = answer_repository_question(question, repository)
                    st.markdown(answer)
                except Exception as error:
                    answer = f"I couldn't search this repository: {error}"
                    st.error(answer)
            history.append({"role": "assistant", "content": answer})
