from __future__ import annotations

import json
import uuid
from pathlib import Path

from engage.checker import check_draft
from engage.gate import evaluate
from engage.gemini import GeminiModel
from engage.model import ModelAdapter
from engage.models import EngageError, Proposal
from engage.prompt import build_prompt
from engage.rules import load_rules
from engage.store import list_records, load_author, load_post, save_record


def propose(
    author_id: str,
    post_path: Path,
    *,
    data_dir: Path,
    fixtures_dir: Path,
    model: ModelAdapter | None = None,
    live: bool = False,
) -> Proposal:
    author = load_author(fixtures_dir, author_id)
    post = load_post(post_path)
    rules = load_rules(data_dir, author.id)
    gate = evaluate(post, author)

    if not gate.eligible:
        proposal = Proposal(
            id=_new_id("p"),
            author_id=author.id,
            post_id=post.id,
            status="skipped",
            reason=gate.reason,
            comment=None,
            claim_ids=[],
            prompt=None,
            model_output=None,
        )
        save_record(data_dir, "proposals", proposal.id, proposal.to_dict())
        return proposal

    drafter = _resolve_model(model, live)
    prompt = build_prompt(author, post, rules)
    raw = drafter.draft(prompt)
    parsed = parse_model_output(raw)

    if parsed is None:
        proposal = Proposal(
            id=_new_id("p"),
            author_id=author.id,
            post_id=post.id,
            status="blocked",
            reason="unparseable",
            comment=None,
            claim_ids=[],
            prompt=prompt,
            model_output=raw,
        )
        save_record(data_dir, "proposals", proposal.id, proposal.to_dict())
        return proposal

    comment, claim_ids, model_reason = parsed
    checked = check_draft(comment, claim_ids, author, rules)
    if checked.ok:
        proposal = Proposal(
            id=_new_id("p"),
            author_id=author.id,
            post_id=post.id,
            status="draft",
            reason=model_reason,
            comment=comment,
            claim_ids=claim_ids,
            prompt=prompt,
            model_output=raw,
        )
    else:
        proposal = Proposal(
            id=_new_id("p"),
            author_id=author.id,
            post_id=post.id,
            status="blocked",
            reason=checked.reason,
            comment=comment,
            claim_ids=claim_ids,
            prompt=prompt,
            model_output=raw,
        )
    save_record(data_dir, "proposals", proposal.id, proposal.to_dict())
    return proposal


def parse_model_output(raw: str) -> tuple[str, list[str], str] | None:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    comment = payload.get("comment")
    claim_ids = payload.get("claim_ids", [])
    reason = payload.get("reason", "")
    if not isinstance(comment, str):
        return None
    if not isinstance(claim_ids, list) or not all(isinstance(item, str) for item in claim_ids):
        return None
    if not isinstance(reason, str) or not reason.strip():
        reason = "model_draft"
    return comment, claim_ids, reason


def proposal_was_acted_on(data_dir: Path, proposal_id: str) -> bool:
    for record in list_records(data_dir, "decisions"):
        if record.get("proposal_id") == proposal_id:
            return True
    return False


def _resolve_model(model: ModelAdapter | None, live: bool) -> ModelAdapter:
    if model is not None and live:
        raise EngageError("pass either a model adapter or --live, not both")
    if model is not None:
        return model
    if live:
        return GeminiModel()
    raise EngageError(
        "This post is eligible for a draft. Re-run with --live, or call propose with a scripted model."
    )


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
