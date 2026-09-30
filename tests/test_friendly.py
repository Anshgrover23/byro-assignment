from engage.cli import main

from helpers import FIXTURES, post


def test_no_command_prints_the_plain_guide(capsys):
    code = main([])
    assert code == 0
    guide = capsys.readouterr().out
    assert "engage demo" in guide
    assert "engage draft rico" in guide
    assert "Nothing is posted" in guide


def test_draft_skip_reads_as_a_sentence(data_dir, capsys):
    code = main(
        [
            "draft",
            "rico",
            str(post("03-sensitive.json")),
            "--data-dir",
            str(data_dir),
            "--fixtures",
            str(FIXTURES),
        ]
    )
    assert code == 0
    text = capsys.readouterr().out
    assert "Say nothing." in text
    assert "This post is sensitive." in text


def test_demo_walks_the_loop_in_plain_language(data_dir, capsys):
    code = main(
        [
            "demo",
            "--data-dir",
            str(data_dir),
            "--fixtures",
            str(FIXTURES),
        ]
    )
    assert code == 0
    text = capsys.readouterr().out
    assert "Say nothing." in text
    assert "Ready to paste. Nothing was posted." in text
    assert "Remembered for rico: do not end with a question" in text
    assert "Fathin Dosunmu" in text
    assert "do not end with a question" not in text.split("Fathin Dosunmu", 1)[1]
    assert "It is off." in text
