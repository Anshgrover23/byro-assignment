import json

from engage.cli import main
from engage.propose import propose

from helpers import FIXTURES, RICO_CLAIM, RICO_COMMENT, post, scripted


def test_cli_skip_prints_a_proposal_and_show_lists_a_rule(data_dir, capsys):
    code = main(
        [
            "propose",
            "--author",
            "rico",
            "--post",
            str(post("03-sensitive.json")),
            "--data-dir",
            str(data_dir),
            "--fixtures",
            str(FIXTURES),
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "skipped"
    assert payload["reason"] == "sensitive"

    proposal = propose(
        "rico",
        post("01-on-goal.json"),
        data_dir=data_dir,
        fixtures_dir=FIXTURES,
        model=scripted(RICO_COMMENT, RICO_CLAIM),
    )
    code = main(
        [
            "decide",
            "--proposal",
            proposal.id,
            "--action",
            "edit",
            "--text",
            RICO_COMMENT,
            "--rule",
            "do not end with a question",
            "--data-dir",
            str(data_dir),
        ]
    )
    assert code == 0
    decision_payload = json.loads(capsys.readouterr().out)
    assert decision_payload["handoff"]["status"] == "ready_to_paste"
    rule_id = decision_payload["rule_id"]

    code = main(
        [
            "show",
            "--author",
            "rico",
            "--data-dir",
            str(data_dir),
            "--fixtures",
            str(FIXTURES),
        ]
    )
    assert code == 0
    shown = capsys.readouterr().out
    assert "do not end with a question" in shown
    assert "[on]" in shown

    code = main(["revert-rule", "--id", rule_id, "--data-dir", str(data_dir)])
    assert code == 0
    reverted = json.loads(capsys.readouterr().out)
    assert reverted["active"] is False

    code = main(
        [
            "show",
            "--author",
            "rico",
            "--data-dir",
            str(data_dir),
            "--fixtures",
            str(FIXTURES),
        ]
    )
    assert code == 0
    rico_after = capsys.readouterr().out
    assert "[off]" in rico_after
    assert "do not end with a question" in rico_after

    code = main(
        [
            "show",
            "--author",
            "fathin",
            "--data-dir",
            str(data_dir),
            "--fixtures",
            str(FIXTURES),
        ]
    )
    assert code == 0
    fathin_shown = capsys.readouterr().out
    assert "do not end with a question" not in fathin_shown


def test_cli_refuses_accept_of_a_skipped_proposal(data_dir, capsys):
    code = main(
        [
            "propose",
            "--author",
            "rico",
            "--post",
            str(post("04-injection.json")),
            "--data-dir",
            str(data_dir),
            "--fixtures",
            str(FIXTURES),
        ]
    )
    proposal = json.loads(capsys.readouterr().out)
    assert code == 0
    code = main(
        [
            "decide",
            "--proposal",
            proposal["id"],
            "--action",
            "accept",
            "--data-dir",
            str(data_dir),
        ]
    )
    assert code == 2
    error = capsys.readouterr().err
    assert "accept is only valid" in error
