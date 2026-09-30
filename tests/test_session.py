import shutil

from engage.propose import propose
from engage.session import Session, scripted_input
from engage.store import load_author

from helpers import FIXTURES, RICO_CLAIM, RICO_COMMENT, post, scripted


def test_menu_changes_a_draft_without_an_id(data_dir):
    proposal = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted(RICO_COMMENT, RICO_CLAIM),
    )
    lines: list[str] = []
    session = Session(
        data_dir,
        FIXTURES,
        input_fn=scripted_input(
            [
                "2",
                "The named author decides what goes live.",
                "do not end with a question",
            ]
        ),
        output=lines.append,
    )
    session.review(proposal, "A post about evidence.")
    text = "\n".join(lines)
    assert "Ready to paste. Nothing was posted." in text
    assert "Remembered for rico: do not end with a question" in text
    assert "r_" not in text


def test_menu_can_add_a_voice(tmp_path):
    fixtures = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, fixtures)
    lines: list[str] = []
    session = Session(
        tmp_path / "data",
        fixtures,
        input_fn=scripted_input(
            [
                "3",
                "Ada Example",
                "Careful public writing",
                "Short lines.",
                "We ship the work.",
                "invented revenue",
                "writing",
                "5",
            ]
        ),
        output=lines.append,
    )
    session.run()
    saved = load_author(fixtures, "adaexample")
    assert saved.name == "Ada Example"
    assert saved.topics == ["writing"]
    assert "Added Ada Example." in "\n".join(lines)


def test_menu_skips_a_sensitive_post_by_number(data_dir):
    lines: list[str] = []
    session = Session(
        data_dir,
        FIXTURES,
        input_fn=scripted_input(["1", "2", "3", "5"]),
        output=lines.append,
    )
    session.run()
    text = "\n".join(lines)
    assert "Say nothing." in text
    assert "This post is sensitive." in text
    assert "Done." in text
