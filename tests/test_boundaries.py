from engage.checker import check_draft
from engage.models import EngageError, Rule
from engage.prompt import build_prompt
from engage.propose import propose
from engage.rules import save_rule
from engage.store import load_author, load_post

from helpers import FIXTURES, post

import pytest


def test_injection_cannot_authorize_a_draft_or_a_handoff(data_dir):
    class ExplodingModel:
        def draft(self, prompt: str) -> str:
            raise AssertionError("injection must not reach the model")

    proposal = propose(
        "rico",
        post("04-injection.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=ExplodingModel(),
    )
    assert proposal.status == "skipped"
    assert proposal.reason == "injection"
    assert proposal.comment is None
    assert "20 paying customers" not in (proposal.comment or "")
    assert not (data_dir / "handoffs").exists()
    assert not (data_dir / "decisions").exists()


def test_rico_rule_does_not_change_fathin(data_dir):
    save_rule(
        data_dir,
        Rule(
            id="r_rico_question",
            author_id="rico",
            source_decision_id="d_seed",
            text="do not end with a question",
            active=True,
        ),
    )
    rico = load_author(FIXTURES, "rico")
    fathin = load_author(FIXTURES, "fathin")
    on_goal = load_post(post("01-on-goal.json"))
    agents = load_post(post("07-agents.json"))
    from engage.rules import load_rules

    rules = load_rules(data_dir)
    rico_prompt = build_prompt(rico, on_goal, rules)
    fathin_prompt = build_prompt(fathin, agents, rules)

    assert "do not end with a question" in rico_prompt
    assert "do not end with a question" not in fathin_prompt
    assert rico.voice_examples[0] in rico_prompt
    assert rico.voice_examples[0] not in fathin_prompt
    assert fathin.voice_examples[0] in fathin_prompt

    fathin_question = "An agent can prepare the next step. The human still chooses the action?"
    fathin_check = check_draft(fathin_question, ["human_sets_the_action"], fathin, rules)
    assert fathin_check.ok is True

    rico_question = "The named author decides what goes live?"
    rico_check = check_draft(rico_question, ["named_author_decides"], rico, rules)
    assert rico_check.ok is False
    assert rico_check.reason == "breaks_rule"


def test_author_id_cannot_escape_the_fixtures_directory():
    with pytest.raises(EngageError, match="slug"):
        load_author(FIXTURES, "../secrets")


def test_live_without_a_key_writes_nothing(data_dir, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(EngageError, match="GEMINI_API_KEY"):
        propose(
            "rico",
            post("01-on-goal.json"),
            data_dir=data_dir,
            fixtures_dir=FIXTURES,
            live=True,
        )
    assert not (data_dir / "proposals").exists()
