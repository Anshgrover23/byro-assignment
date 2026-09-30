from engage.decide import decide
from engage.models import EngageError
from engage.propose import propose
from engage.rules import revert_rule
from engage.store import list_records

from helpers import FIXTURES, RICO_CLAIM, RICO_COMMENT, post, scripted

import pytest

QUESTION = "The named author decides what goes live. Does the source stay attached?"
RULE = "do not end with a question"


def test_reviewed_rule_blocks_the_next_draft_and_revert_clears_it(data_dir):
    model = scripted(QUESTION, RICO_CLAIM)
    first = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=model,
    )
    assert first.status == "draft"

    decision, rule, handoff = decide(
        first.id,
        "edit",
        data_dir=data_dir,
        text=RICO_COMMENT,
        rule_text=RULE,
    )
    assert decision.actor == "human"
    assert decision.final_text == RICO_COMMENT
    assert first.comment == QUESTION
    assert rule is not None and rule.active
    assert handoff is not None
    assert handoff.status == "ready_to_paste"
    assert handoff.text == RICO_COMMENT

    second = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=model,
    )
    assert second.status == "blocked"
    assert second.reason == "breaks_rule"
    assert RULE in (second.prompt or "")

    reverted = revert_rule(data_dir, rule.id)
    assert reverted.active is False

    third = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=model,
    )
    assert third.status == "draft"
    assert RULE not in (third.prompt or "")


def test_accept_writes_only_ready_to_paste_and_a_second_decision_is_refused(data_dir):
    proposal = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted(RICO_COMMENT, RICO_CLAIM),
    )
    decision, rule, handoff = decide(proposal.id, "accept", data_dir=data_dir)
    assert rule is None
    assert handoff is not None
    assert handoff.status == "ready_to_paste"
    stored = list_records(data_dir, "handoffs")
    assert stored == [handoff.to_dict()]
    assert decision.final_text == proposal.comment

    with pytest.raises(EngageError, match="already has a human decision"):
        decide(proposal.id, "reject", data_dir=data_dir)


def test_reject_and_skip_do_not_write_a_handoff(data_dir):
    first = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted(RICO_COMMENT, RICO_CLAIM),
    )
    decide(first.id, "reject", data_dir=data_dir, rule_text="skip generic agreement")
    second = propose(
        "rico",
        post("03-sensitive.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted(RICO_COMMENT, RICO_CLAIM),
    )
    decide(second.id, "skip", data_dir=data_dir)
    assert not (data_dir / "handoffs").exists()
    rules = list_records(data_dir, "rules")
    assert len(rules) == 1
    assert rules[0]["author_id"] == "rico"


def test_a_rule_cannot_be_attached_to_accept(data_dir):
    proposal = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted(RICO_COMMENT, RICO_CLAIM),
    )
    with pytest.raises(EngageError, match="edit or a rejection"):
        decide(proposal.id, "accept", data_dir=data_dir, rule_text=RULE)
    assert not (data_dir / "rules").exists()
    assert not (data_dir / "handoffs").exists()
