from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ProposalStatus = Literal["skipped", "blocked", "draft"]
DecisionAction = Literal["accept", "edit", "reject", "skip"]
HandoffStatus = Literal["ready_to_paste"]

HANDOFF_STATUS: HandoffStatus = "ready_to_paste"


class EngageError(ValueError):
    """A caller-facing refusal. The CLI prints it and exits."""


@dataclass
class Claim:
    id: str
    text: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Claim:
        return cls(id=_require_str(payload, "id"), text=_require_str(payload, "text"))

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "text": self.text}


@dataclass
class Author:
    id: str
    name: str
    goal: str
    topics: list[str]
    voice_examples: list[str]
    allowed_claims: list[Claim]
    prohibited_phrases: list[str]
    recent_points: list[str]
    evidence_note: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Author:
        claims = payload.get("allowed_claims")
        if not isinstance(claims, list):
            raise EngageError("author.allowed_claims must be a list")
        return cls(
            id=_require_str(payload, "id"),
            name=_require_str(payload, "name"),
            goal=_require_str(payload, "goal"),
            topics=_require_str_list(payload, "topics"),
            voice_examples=_require_str_list(payload, "voice_examples"),
            allowed_claims=[Claim.from_dict(item) for item in claims],
            prohibited_phrases=_require_str_list(payload, "prohibited_phrases"),
            recent_points=_require_str_list(payload, "recent_points"),
            evidence_note=_require_str(payload, "evidence_note"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "topics": self.topics,
            "voice_examples": self.voice_examples,
            "allowed_claims": [claim.to_dict() for claim in self.allowed_claims],
            "prohibited_phrases": self.prohibited_phrases,
            "recent_points": self.recent_points,
            "evidence_note": self.evidence_note,
        }


@dataclass
class Post:
    id: str
    text: str
    topic: str
    sensitivity: Literal["normal", "high"]
    synthetic: bool
    note: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Post:
        sensitivity = payload.get("sensitivity")
        if sensitivity not in ("normal", "high"):
            raise EngageError("post.sensitivity must be normal or high")
        synthetic = payload.get("synthetic")
        if not isinstance(synthetic, bool):
            raise EngageError("post.synthetic must be a boolean")
        return cls(
            id=_require_str(payload, "id"),
            text=_require_str(payload, "text"),
            topic=_require_str(payload, "topic"),
            sensitivity=sensitivity,
            synthetic=synthetic,
            note=_require_str(payload, "note"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "topic": self.topic,
            "sensitivity": self.sensitivity,
            "synthetic": self.synthetic,
            "note": self.note,
        }


@dataclass
class Proposal:
    id: str
    author_id: str
    post_id: str
    status: ProposalStatus
    reason: str
    comment: str | None
    claim_ids: list[str]
    prompt: str | None
    model_output: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "author_id": self.author_id,
            "post_id": self.post_id,
            "status": self.status,
            "reason": self.reason,
            "comment": self.comment,
            "claim_ids": self.claim_ids,
            "prompt": self.prompt,
            "model_output": self.model_output,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Proposal:
        status = payload.get("status")
        if status not in ("skipped", "blocked", "draft"):
            raise EngageError("proposal.status is invalid")
        return cls(
            id=_require_str(payload, "id"),
            author_id=_require_str(payload, "author_id"),
            post_id=_require_str(payload, "post_id"),
            status=status,
            reason=_require_str(payload, "reason"),
            comment=payload.get("comment"),
            claim_ids=_require_str_list(payload, "claim_ids"),
            prompt=payload.get("prompt"),
            model_output=payload.get("model_output"),
        )


@dataclass
class Decision:
    id: str
    proposal_id: str
    author_id: str
    action: DecisionAction
    final_text: str | None
    rule_text: str | None
    actor: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "proposal_id": self.proposal_id,
            "author_id": self.author_id,
            "action": self.action,
            "final_text": self.final_text,
            "rule_text": self.rule_text,
            "actor": self.actor,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Decision:
        action = payload.get("action")
        if action not in ("accept", "edit", "reject", "skip"):
            raise EngageError("decision.action is invalid")
        return cls(
            id=_require_str(payload, "id"),
            proposal_id=_require_str(payload, "proposal_id"),
            author_id=_require_str(payload, "author_id"),
            action=action,
            final_text=payload.get("final_text"),
            rule_text=payload.get("rule_text"),
            actor=_require_str(payload, "actor"),
        )


@dataclass
class Rule:
    id: str
    author_id: str
    source_decision_id: str
    text: str
    active: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "author_id": self.author_id,
            "source_decision_id": self.source_decision_id,
            "text": self.text,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Rule:
        active = payload.get("active")
        if not isinstance(active, bool):
            raise EngageError("rule.active must be a boolean")
        return cls(
            id=_require_str(payload, "id"),
            author_id=_require_str(payload, "author_id"),
            source_decision_id=_require_str(payload, "source_decision_id"),
            text=_require_str(payload, "text"),
            active=active,
        )


@dataclass
class Handoff:
    id: str
    decision_id: str
    author_id: str
    status: HandoffStatus
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "decision_id": self.decision_id,
            "author_id": self.author_id,
            "status": self.status,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Handoff:
        status = payload.get("status")
        if status != HANDOFF_STATUS:
            raise EngageError("handoff.status must be ready_to_paste")
        return cls(
            id=_require_str(payload, "id"),
            decision_id=_require_str(payload, "decision_id"),
            author_id=_require_str(payload, "author_id"),
            status=status,
            text=_require_str(payload, "text"),
        )


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EngageError(f"{key} must be a non-empty string")
    return value


def _require_str_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise EngageError(f"{key} must be a list of strings")
    return value
