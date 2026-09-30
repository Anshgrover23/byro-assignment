from engage.models import EngageError
from engage.propose import propose

from helpers import FIXTURES, RICO_CLAIM, RICO_COMMENT, post, scripted

import pytest


class ExplodingModel:
    def draft(self, prompt: str) -> str:
        raise AssertionError("the model must not be called on a skip")


def test_sensitive_off_goal_prohibited_and_repeat_skip_without_a_model(data_dir):
    cases = [
        ("03-sensitive.json", "sensitive"),
        ("02-off-goal.json", "off_goal"),
        ("05-prohibited.json", "prohibited_claim"),
        ("06-repeat.json", "repeats_point"),
    ]
    for filename, reason in cases:
        proposal = propose(
            "rico",
            post(filename),
            data_dir=data_dir,
            fixtures_dir=FIXTURES,
            model=ExplodingModel(),
        )
        assert proposal.status == "skipped", filename
        assert proposal.reason == reason
        assert proposal.prompt is None
        assert proposal.model_output is None
        assert proposal.comment is None


def test_eligible_post_without_a_model_does_not_write_a_proposal(data_dir):
    with pytest.raises(EngageError):
        propose(
            "rico",
            post("01-on-goal.json"),
            data_dir=data_dir,
            fixtures_dir=FIXTURES,
        )
    assert not (data_dir / "proposals").exists()


def test_scripted_draft_keeps_model_output_out_of_the_decision_store(data_dir):
    model = scripted(RICO_COMMENT, RICO_CLAIM)
    proposal = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=model,
    )
    assert proposal.status == "draft"
    assert proposal.comment == RICO_COMMENT
    assert proposal.model_output is not None
    assert "<untrusted_post>" in model.prompts[0]
    assert not (data_dir / "decisions").exists()
    assert not (data_dir / "handoffs").exists()
