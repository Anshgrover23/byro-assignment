from __future__ import annotations

import re
from dataclasses import dataclass

from engage.models import Author, Rule
from engage.prompt import active_rules_for

# A percent, a dollar amount, or a counted customer claim.
_METRIC = re.compile(
    r"\d+(?:\.\d+)?\s*%|\$\d[\d,]*|\d+\s+paying customers",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    reason: str


def recognized_effects(author: Author, rules: list[Rule]) -> set[str]:
    effects: set[str] = set()
    for rule in active_rules_for(author, rules):
        lowered = rule.text.lower()
        if "end with a question" in lowered or "end with question" in lowered:
            effects.add("no_trailing_question")
    return effects


def check_draft(
    comment: str | None,
    claim_ids: list[str],
    author: Author,
    rules: list[Rule],
) -> CheckResult:
    if comment is None or not comment.strip():
        return CheckResult(False, "empty")

    allowed = {claim.id: claim.text for claim in author.allowed_claims}
    if not claim_ids:
        return CheckResult(False, "ungrounded")
    for claim_id in claim_ids:
        if claim_id not in allowed:
            return CheckResult(False, "unknown_claim")

    lowered = comment.lower()
    for phrase in author.prohibited_phrases:
        if phrase.lower() in lowered:
            return CheckResult(False, "prohibited_phrase")

    cited_text = "\n".join(allowed[claim_id] for claim_id in claim_ids).lower()
    for match in _METRIC.finditer(comment):
        if match.group(0).lower() not in cited_text:
            return CheckResult(False, "unsupported_metric")

    if "no_trailing_question" in recognized_effects(author, rules):
        if comment.rstrip().endswith("?"):
            return CheckResult(False, "breaks_rule")

    return CheckResult(True, "ok")
