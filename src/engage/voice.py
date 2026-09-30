"""Turn visible writing into a voice card a person can read before it is saved."""

from __future__ import annotations

import re
import statistics
from datetime import date

from engage.models import Author
from engage.session import slugify

_KNOWN_SLUGS = {
    "ricosoots": "rico",
    "fathindos": "fathin",
}

_SENSITIVE = ("laid off", "let people go", "passed away", "suicide", "died")


def author_id_for(profile_url: str, name: str) -> str:
    match = re.search(r"linkedin\.com/in/([^/?#]+)", profile_url or "", re.I)
    slug = (match.group(1) if match else slugify(name)).lower().strip("/")
    return _KNOWN_SLUGS.get(slug, slugify(slug) or slugify(name))


def summarize(name: str, profile_url: str, texts: list[str]) -> dict:
    samples = _clean_samples(texts)
    if not samples:
        raise ValueError("no writing was captured")
    words = [len(sample.split()) for sample in samples]
    median = int(statistics.median(words))
    question_rate = sum(sample.rstrip().endswith("?") for sample in samples) / len(samples)
    lowercase_rate = sum(sample[:1].islower() for sample in samples) / len(samples)
    examples = _pick_examples(samples)
    observations = [
        f"{len(samples)} visible posts",
        f"typical length about {median} words",
    ]
    if question_rate >= 0.5:
        observations.append("often ends with a question")
    elif question_rate == 0:
        observations.append("does not end with a question in these posts")
    if lowercase_rate >= 0.6:
        observations.append("often starts in lowercase")
    return {
        "id": author_id_for(profile_url, name),
        "name": name.strip() or "Unknown",
        "profile_url": profile_url,
        "voice_examples": examples,
        "observations": observations,
        "median_words": median,
        "question_rate": round(question_rate, 2),
        "evidence_note": (
            f"Captured from posts visible on the open LinkedIn page on {date.today().isoformat()}. "
            "Saved only after the person confirms."
        ),
    }


def card_from_summary(summary: dict, existing: Author | None) -> Author:
    examples = list(summary["voice_examples"])
    claims = list(existing.allowed_claims) if existing else []
    prohibited = list(existing.prohibited_phrases) if existing else []
    topics = list(existing.topics) if existing else ["general"]
    recent = list(existing.recent_points) if existing else []
    goal = existing.goal if existing else f"Sound like {summary['name']} in public comments."
    if existing:
        for example in existing.voice_examples:
            if example not in examples:
                examples.append(example)
    note = summary["evidence_note"]
    if existing:
        note += " Earlier examples stay until you remove them. Allowed claims were not taken from the page."
    return Author(
        id=summary["id"],
        name=existing.name if existing else summary["name"],
        goal=goal,
        topics=topics,
        voice_examples=examples[:8],
        allowed_claims=claims,
        prohibited_phrases=prohibited,
        recent_points=recent,
        evidence_note=note,
    )


def looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in _SENSITIVE)


def _clean_samples(texts: list[str]) -> list[str]:
    seen: set[str] = set()
    samples = []
    for raw in texts:
        text = " ".join(raw.split())
        if len(text) < 40:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        samples.append(text[:600])
    return samples


def _pick_examples(samples: list[str]) -> list[str]:
    ranked = sorted(samples, key=lambda sample: len(sample.split()))
    picked = ranked[:3] if len(ranked) >= 3 else ranked
    return picked
