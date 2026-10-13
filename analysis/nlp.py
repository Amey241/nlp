"""
analysis/nlp.py
NLP analysis on commit messages:
  - TextBlob sentiment (polarity)
  - LDA topic modeling → dominant topic label
"""

import re
import math
import random
from collections import Counter

from textblob import TextBlob
from config import LDA_N_TOPICS

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could", "did",
    "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "will", "with", "would", "you", "your", "yours", "yourself",
    "yourselves",
}

# Word lists that anchor each topic label heuristically
TOPIC_ANCHORS = {
    "bug":     {"fix", "bug", "error", "crash", "null", "issue", "broken", "fail", "patch", "revert"},
    "feature": {"add", "new", "feature", "implement", "create", "introduce", "support", "enable"},
    "refactor":{"refactor", "cleanup", "clean", "rename", "move", "extract", "restructure", "reorganize"},
    "docs":    {"doc", "docs", "readme", "comment", "typo", "update", "changelog", "license"},
}

# Lightweight intent tags for commit subjects. These are heuristic labels,
# since commit messages are usually short and domain-specific.
INTENT_PATTERNS = {
    "Bug fix": r"\b(fix|bug|issue|error|crash|patch|hotfix|resolve)\b",
    "Feature": r"\b(add|feat|feature|implement|introduce|support|enable|create)\b",
    "Documentation": r"\b(doc|docs|readme|documentation|typo|guide)\b",
    "Refactor": r"\b(refactor|cleanup|clean up|restructure|rename|simplify|reorganize)\b",
    "Testing": r"\b(test|tests|testing|spec|coverage)\b",
    "Maintenance": r"\b(chore|build|ci|deps|dependency|upgrade|bump|release|format)\b",
}


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"(?u)\b[a-zA-Z][a-zA-Z0-9_-]*\b", text)]


def _tfidf_ranked(documents: list[str], limit: int = 8, max_features: int = 300) -> list[tuple[str, float]]:
    """Calculate lightweight TF-IDF rankings without compiled dependencies."""
    document_terms = []
    document_frequency = Counter()
    total_frequency = Counter()
    for document in documents:
        tokens = [token for token in _tokens(document) if token not in STOP_WORDS]
        terms = Counter(tokens)
        terms.update(f"{left} {right}" for left, right in zip(tokens, tokens[1:]))
        document_terms.append((terms, max(len(tokens), 1)))
        document_frequency.update(terms.keys())
        total_frequency.update(terms)

    allowed = {term for term, _ in total_frequency.most_common(max_features)}
    scores = Counter()
    count_docs = max(len(document_terms), 1)
    for terms, token_count in document_terms:
        for term, count in terms.items():
            if term in allowed:
                inverse_document_frequency = math.log((1 + count_docs) / (1 + document_frequency[term])) + 1
                scores[term] += (count / token_count) * inverse_document_frequency
    return [(term, score) for term, score in scores.most_common(limit)]


def _tfidf_terms(documents: list[str], limit: int = 8, max_features: int = 300) -> list[str]:
    return [term for term, _ in _tfidf_ranked(documents, limit, max_features)]

def commit_message_insights(messages: list[str]) -> dict:
    """Summarize intent, recurring phrases, and vocabulary in commit messages."""
    usable = [str(message).strip() for message in messages if str(message).strip()]
    if not usable:
        return {"intent_counts": {}, "keywords": [], "avg_words": 0.0, "vocabulary_richness": 0.0}

    from collections import Counter

    intents = Counter()
    for message in usable:
        normalized = message.lower()
        intent = next((label for label, pattern in INTENT_PATTERNS.items()
                       if re.search(pattern, normalized)), "Other")
        intents[intent] += 1

    keywords = _tfidf_terms(usable)

    words = [word for message in usable for word in re.findall(r"[a-zA-Z]+", message.lower())]
    return {
        "intent_counts": dict(intents),
        "keywords": keywords,
        "avg_words": round(sum(len(message.split()) for message in usable) / len(usable), 1),
        "vocabulary_richness": round(len(set(words)) / len(words), 3) if words else 0.0,
    }


def _clean(msg: str) -> str:
    msg = re.sub(r"https?://\S+", "", msg)           # strip URLs
    msg = re.sub(r"[^a-zA-Z\s]", " ", msg).lower()  # keep letters only
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg


def sentiment_analysis(messages: list[str]) -> dict:
    """Return avg polarity, mood label, and percentage breakdowns."""
    if not messages:
        return {
            "avg_polarity": 0.0,
            "mood": "Neutral 😐",
            "pos_pct": 0,
            "neg_pct": 0,
            "neu_pct": 100,
            "total": 0
        }

    polarities = [TextBlob(m).sentiment.polarity for m in messages if m.strip()]
    if not polarities:
        return {"avg_polarity": 0.0, "mood": "Neutral 😐", "pos_pct": 0, "neg_pct": 0, "neu_pct": 100, "total": 0}

    avg = sum(polarities) / len(polarities)
    
    pos = sum(1 for p in polarities if p > 0.1)
    neg = sum(1 for p in polarities if p < -0.1)
    neu = len(polarities) - pos - neg

    if avg > 0.15:
        mood = "Upbeat 😄"
    elif avg < -0.10:
        mood = "Frustrated 😤"
    else:
        mood = "Neutral 😐"

    return {
        "avg_polarity": round(avg, 4),
        "mood": mood,
        "pos_pct": round(pos / len(polarities) * 100),
        "neg_pct": round(neg / len(polarities) * 100),
        "neu_pct": round(neu / len(polarities) * 100),
        "total": len(polarities)
    }


def _label_topic(top_words: list[str]) -> str:
    """Label a topic using the existing lightweight commit vocabulary anchors."""
    words = set(top_words)
    scores = {label: len(words & anchors) for label, anchors in TOPIC_ANCHORS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def lda_topics(messages: list[str], n_topics: int = LDA_N_TOPICS) -> dict:
    """
    Run LDA on commit messages.
    Returns:
        topics: list of {label, top_words} dicts
        dominant_topic: label of the most common topic
        doc_topics: per-message dominant topic label
    """
    cleaned = [_tokens(_clean(message[:500])) for message in messages]
    cleaned = [tokens for tokens in cleaned if len(tokens) >= 2]

    if len(cleaned) < 10:
        return {
            "topics": [],
            "dominant_topic": "unknown",
            "doc_topics": [],
            "topic_counts": {},
        }

    document_frequency = Counter()
    for tokens in cleaned:
        document_frequency.update(set(token for token in tokens if token not in STOP_WORDS))
    vocabulary = [word for word, count in document_frequency.most_common(500) if count >= 2]
    if not vocabulary:
        return {"topics": [], "dominant_topic": "unknown", "doc_topics": [], "topic_counts": {}}

    word_ids = {word: index for index, word in enumerate(vocabulary)}
    docs = [[word_ids[word] for word in tokens if word in word_ids] for tokens in cleaned]
    docs = [doc for doc in docs if doc]
    if not docs:
        return {"topics": [], "dominant_topic": "unknown", "doc_topics": [], "topic_counts": {}}

    # Collapsed Gibbs sampling for a small, deterministic LDA model.
    topic_count = min(max(int(n_topics), 1), len(vocabulary))
    alpha, beta = 0.1, 0.01
    rng = random.Random(42)
    doc_topic = [[0] * topic_count for _ in docs]
    topic_word = [[0] * len(vocabulary) for _ in range(topic_count)]
    topic_total = [0] * topic_count
    assignments = []
    for doc_index, doc in enumerate(docs):
        assigned = []
        for word_id in doc:
            topic = rng.randrange(topic_count)
            assigned.append(topic)
            doc_topic[doc_index][topic] += 1
            topic_word[topic][word_id] += 1
            topic_total[topic] += 1
        assignments.append(assigned)

    for _ in range(30):
        for doc_index, doc in enumerate(docs):
            for token_index, word_id in enumerate(doc):
                old_topic = assignments[doc_index][token_index]
                doc_topic[doc_index][old_topic] -= 1
                topic_word[old_topic][word_id] -= 1
                topic_total[old_topic] -= 1
                weights = [
                    (doc_topic[doc_index][topic] + alpha)
                    * (topic_word[topic][word_id] + beta)
                    / (topic_total[topic] + beta * len(vocabulary))
                    for topic in range(topic_count)
                ]
                draw = rng.random() * sum(weights)
                selected_topic = topic_count - 1
                for topic, weight in enumerate(weights):
                    draw -= weight
                    if draw <= 0:
                        selected_topic = topic
                        break
                assignments[doc_index][token_index] = selected_topic
                doc_topic[doc_index][selected_topic] += 1
                topic_word[selected_topic][word_id] += 1
                topic_total[selected_topic] += 1

    topics = []
    for topic in range(topic_count):
        ranked_ids = sorted(range(len(vocabulary)), key=lambda word_id: topic_word[topic][word_id], reverse=True)
        top_words = [vocabulary[word_id] for word_id in ranked_ids[:8] if topic_word[topic][word_id] > 0]
        topics.append({"index": topic, "label": _label_topic(top_words), "top_words": top_words})

    doc_topics = [
        topics[max(range(topic_count), key=lambda topic: doc_topic[index][topic])]["label"]
        for index in range(len(docs))
    ]
    counts = Counter(doc_topics)
    dominant = counts.most_common(1)[0][0]

    return {
        "topics": topics,
        "dominant_topic": dominant,
        "doc_topics": doc_topics,
        "topic_counts": dict(counts),
    }
