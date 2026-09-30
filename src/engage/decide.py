from __future__ import annotations

import uuid
from pathlib import Path

from engage.models import HANDOFF_STATUS, Decision, EngageError, Handoff, Rule
from engage.propose import proposal_was_acted_on
from engage.rules import load_proposal, save_decision, save_handoff, save_rule

_RULE_ACTIONS = {"edit", "reject"}
_HANDOFF_ACTIONS = {"accept", "edit"}


def decide(
    proposal_id: str,
    action: str,
    *,
    data_dir: Path,
    text: str | None = None,
    rule_text: str | None = None,
) -> tuple[Decision, Rule | None, Handoff | None]:
    if action not in ("accept", "edit", "reject", "skip"):
        raise EngageError("action must be accept, edit, reject, or skip")

    proposal = load_proposal(data_dir, proposal_id)
    if proposal_was_acted_on(data_dir, proposal.id):
        raise EngageError("this proposal already has a human decision")

    cleaned_rule = rule_text.strip() if isinstance(rule_text, str) else None
    if cleaned_rule == "":
        cleaned_rule = None
    if cleaned_rule and action not in _RULE_ACTIONS:
        raise EngageError("a rule can only be saved from an edit or a rejection")

    final_text: str | None
    handoff: Handoff | None = None

    if action == "accept":
        if proposal.status != "draft" or not proposal.comment:
            raise EngageError("accept is only valid for a draft that passed the checker")
        final_text = proposal.comment
    elif action == "edit":
        if not isinstance(text, str) or not text.strip():
            raise EngageError("edit needs the person's own text")
        final_text = text.strip()
    else:
        final_text = None

    decision = Decision(
        id=_new_id("d"),
        proposal_id=proposal.id,
        author_id=proposal.author_id,
        action=action,  # type: ignore[arg-type]
        final_text=final_text,
        rule_text=cleaned_rule,
        actor="human",
    )
    save_decision(data_dir, decision)

    rule: Rule | None = None
    if cleaned_rule:
        rule = Rule(
            id=_new_id("r"),
            author_id=proposal.author_id,
            source_decision_id=decision.id,
            text=cleaned_rule,
            active=True,
        )
        save_rule(data_dir, rule)

    if action in _HANDOFF_ACTIONS:
        if final_text is None:
            raise EngageError("handoff requires text")
        handoff = Handoff(
            id=_new_id("h"),
            decision_id=decision.id,
            author_id=proposal.author_id,
            status=HANDOFF_STATUS,
            text=final_text,
        )
        save_handoff(data_dir, handoff)

    return decision, rule, handoff


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
