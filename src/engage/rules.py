from __future__ import annotations

from pathlib import Path

from engage.models import Decision, Handoff, Proposal, Rule
from engage.store import list_records, load_record, save_record


def load_rules(data_dir: Path, author_id: str | None = None) -> list[Rule]:
    rules = [Rule.from_dict(record) for record in list_records(data_dir, "rules")]
    if author_id is None:
        return rules
    return [rule for rule in rules if rule.author_id == author_id]


def load_proposal(data_dir: Path, proposal_id: str) -> Proposal:
    return Proposal.from_dict(load_record(data_dir, "proposals", proposal_id))


def save_decision(data_dir: Path, decision: Decision) -> None:
    save_record(data_dir, "decisions", decision.id, decision.to_dict())


def save_rule(data_dir: Path, rule: Rule) -> None:
    save_record(data_dir, "rules", rule.id, rule.to_dict())


def save_handoff(data_dir: Path, handoff: Handoff) -> None:
    save_record(data_dir, "handoffs", handoff.id, handoff.to_dict())


def revert_rule(data_dir: Path, rule_id: str) -> Rule:
    rule = Rule.from_dict(load_record(data_dir, "rules", rule_id))
    rule.active = False
    save_rule(data_dir, rule)
    return rule
