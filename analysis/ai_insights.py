"""
analysis/ai_insights.py
AI-powered insights using Anthropic Claude.
"""

import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

class AIInsights:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.model = "claude-3-haiku-20240307"

    def _call_claude(self, prompt: str, system_prompt: str) -> str:
        if not self.client:
            return ""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def get_job_role_suggestions(self, user_stats: dict, lang_df: any) -> list:
        """Suggest top 3 job roles based on developer profile."""
        if not self.client:
            return ["Full Stack Developer", "Software Engineer", "Open Source Contributor"]
        
        langs = lang_df["language"].tolist() if not lang_df.empty else []
        prompt = f"""
        Analyze this developer profile and suggest the top 3 job roles they are best suited for.
        Languages: {', '.join(langs)}
        Dominant Topic: {user_stats.get('dominant_topic')}
        Avg Sentiment: {user_stats.get('avg_sentiment')}
        PRs Authored: {user_stats.get('prs_authored')}
        
        Return ONLY a JSON list of strings.
        """
        system = "You are a specialized technical recruiter assistant. Provide concise, accurate job role titles."
        
        res = self._call_claude(prompt, system)
        try:
            return json.loads(res)
        except:
            return ["Backend Architect", "Product Engineer", "DevOps Specialist"]

    def suggest_commit_rewrites(self, low_quality_commits: list) -> list:
        """Suggest better commit messages for low-quality commits."""
        if not self.client or not low_quality_commits:
            return []
        
        commits_str = "\n".join([f"- {c}" for c in low_quality_commits[:5]])
        prompt = f"""
        Suggest professional and descriptive rewrites for these low-quality commit messages.
        Messages:
        {commits_str}
        
        Return a JSON list of objects with "old" and "new" keys.
        """
        system = "You are a senior software engineer who values clear git history. Rewrite vague commits into Conventional Commits format."
        
        res = self._call_claude(prompt, system)
        try:
            return json.loads(res)
        except:
            return []
