from engage.models import Author
from engage.store import load_author
from engage.voice import author_id_for, card_from_summary, looks_sensitive, summarize

from helpers import FIXTURES

import pytest


LONG = "The named author still decides what goes live, and the draft stays a draft until they say so."
SHORTER = "A useful comment names one operational point and then it stops there."
QUESTION = "Would you rather say nothing than invent a number you cannot stand behind today?"


def test_known_profiles_keep_their_ids():
    assert author_id_for("https://www.linkedin.com/in/ricosoots/", "Rico Soots") == "rico"
    assert author_id_for("https://www.linkedin.com/in/fathindos/?trk=public", "Fathin") == "fathin"
    assert author_id_for("https://www.linkedin.com/in/ada-example/", "Ada Example") == "adaexample"


def test_summary_describes_visible_writing_and_drops_short_lines():
    summary = summarize(
        "Rico Soots",
        "https://www.linkedin.com/in/ricosoots/",
        ["too short", LONG, LONG, SHORTER, QUESTION],
    )
    assert summary["id"] == "rico"
    assert summary["observations"][0] == "3 visible posts"
    assert "often ends with a question" not in summary["observations"]
    assert LONG in summary["voice_examples"]
    assert "too short" not in summary["voice_examples"]


def test_capture_keeps_existing_claims_and_does_not_invent_new_ones():
    existing = load_author(FIXTURES, "rico")
    summary = summarize("Someone Else", "https://www.linkedin.com/in/ricosoots/", [LONG, SHORTER, QUESTION])
    card = card_from_summary(summary, existing)
    assert card.name == "Rico Soots"
    assert [claim.id for claim in card.allowed_claims] == [claim.id for claim in existing.allowed_claims]
    assert card.prohibited_phrases == existing.prohibited_phrases
    assert LONG in card.voice_examples
    assert "Allowed claims were not taken from the page." in card.evidence_note


def test_new_person_starts_with_no_claims():
    summary = summarize("Ada Example", "https://www.linkedin.com/in/ada-example/", [LONG, SHORTER])
    card = card_from_summary(summary, None)
    assert isinstance(card, Author)
    assert card.allowed_claims == []
    assert card.topics == ["general"]


def test_a_short_real_post_is_kept():
    summary = summarize(
        "Rico Soots",
        "https://www.linkedin.com/in/ricosoots/recent-activity/all/",
        ["Byro is now five people.", "looking for six and seven."],
    )
    assert summary["id"] == "rico"
    assert "Byro is now five people." in summary["voice_examples"]


def test_empty_capture_is_refused():
    with pytest.raises(ValueError, match="no writing"):
        summarize("Rico", "https://www.linkedin.com/in/ricosoots/", ["hi", "   "])


def test_sensitive_phrasing():
    assert looks_sensitive("We laid off the team last week and I am still sitting with it.")
    assert not looks_sensitive(LONG)
