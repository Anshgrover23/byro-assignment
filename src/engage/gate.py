from __future__ import annotations

from dataclasses import dataclass

from engage.models import Author, Post

# Checked in order. First match wins.
INJECTION_MARKERS = (
    "ignore previous",
    "ignore all instructions",
    "disregard your",
    "system:",
    "you are now",
    "approve and post",
)


@dataclass(frozen=True)
class GateResult:
    eligible: bool
    reason: str


def evaluate(post: Post, author: Author) -> GateResult:
    if post.sensitivity == "high":
        return GateResult(False, "sensitive")

    lowered = post.text.lower()
    if any(marker in lowered for marker in INJECTION_MARKERS):
        return GateResult(False, "injection")

    if post.topic not in author.topics:
        return GateResult(False, "off_goal")

    for phrase in author.prohibited_phrases:
        if phrase.lower() in lowered:
            return GateResult(False, "prohibited_claim")

    for point in author.recent_points:
        if point.lower() in lowered:
            return GateResult(False, "repeats_point")

    return GateResult(True, "eligible")
