from engage.checker import check_draft
from engage.models import EngageError, Handoff
from engage.propose import propose
from engage.store import load_author

from helpers import FIXTURES, RICO_CLAIM, RICO_COMMENT, post, scripted


def test_checker_blocks_ungrounded_unknown_prohibited_and_unsupported_metric():
    author = load_author(FIXTURES, "rico")
    cases = [
        ("So true.", [], "ungrounded"),
        ("We are the category leader.", ["category_leader"], "unknown_claim"),
        ("We already have 20 paying customers.", RICO_CLAIM, "prohibited_phrase"),
        ("Pipeline conversion hit 40% last quarter.", RICO_CLAIM, "unsupported_metric"),
    ]
    for comment, claim_ids, reason in cases:
        result = check_draft(comment, claim_ids, author, [])
        assert result.ok is False
        assert result.reason == reason


def test_model_draft_with_a_prohibited_phrase_is_blocked_and_cannot_be_accepted(data_dir):
    from engage.decide import decide

    proposal = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted("We already have 20 paying customers.", RICO_CLAIM),
    )
    assert proposal.status == "blocked"
    assert proposal.reason == "prohibited_phrase"
    assert proposal.model_output is not None

    try:
        decide(proposal.id, "accept", data_dir=data_dir)
    except EngageError as exc:
        assert "accept is only valid" in str(exc)
    else:
        raise AssertionError("accept should refuse a blocked draft")

    assert not (data_dir / "handoffs").exists()


def test_handoff_record_rejects_a_posted_status():
    try:
        Handoff.from_dict(
            {
                "id": "h_test",
                "decision_id": "d_test",
                "author_id": "rico",
                "status": "posted",
                "text": RICO_COMMENT,
            }
        )
    except EngageError as exc:
        assert "ready_to_paste" in str(exc)
    else:
        raise AssertionError("posted is not a handoff status")


def test_unparseable_model_output_is_blocked(data_dir):
    proposal = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted_raw("Great post!"),
    )
    assert proposal.status == "blocked"
    assert proposal.reason == "unparseable"
    assert proposal.comment is None
    assert not (data_dir / "handoffs").exists()


def scripted_raw(output: str):
    from engage.model import ScriptedModel

    return ScriptedModel(output)
