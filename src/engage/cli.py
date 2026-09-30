from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from engage.decide import decide
from engage.model import ScriptedModel
from engage.models import Decision, EngageError, Handoff, Proposal, Rule
from engage.propose import propose
from engage.rules import load_rules, revert_rule
from engage.server import PORT, serve
from engage.session import Session, plain_example
from engage.store import default_fixtures_dir, load_author, load_post


def main(argv: list[str] | None = None) -> int:
    _load_env_file(Path.cwd() / ".env")
    parser = _parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        if sys.stdin.isatty() and sys.stdout.isatty():
            Session(Path("data"), default_fixtures_dir()).run()
            return 0
        _guide()
        return 0
    try:
        args.handler(args)
    except EngageError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="engage",
        description="Decide whether one person should comment, then keep or change the draft.",
    )
    data = argparse.ArgumentParser(add_help=False)
    data.add_argument("--data-dir", type=Path, default=Path("data"))
    fixtures = argparse.ArgumentParser(add_help=False)
    fixtures.add_argument("--fixtures", type=Path, default=default_fixtures_dir())

    commands = parser.add_subparsers(dest="command")

    start_cmd = commands.add_parser("start", parents=[data, fixtures], help="Open the menu")
    start_cmd.set_defaults(handler=_start)

    posts_cmd = commands.add_parser("posts", parents=[fixtures], help="List the sample posts")
    posts_cmd.set_defaults(handler=_posts)

    draft_cmd = commands.add_parser("draft", parents=[data, fixtures], help="Say nothing, or write one comment")
    draft_cmd.add_argument("author", help="rico or fathin")
    draft_cmd.add_argument("post", type=Path, help="Path to a post file")
    draft_cmd.add_argument("--live", action="store_true", help="Ask Gemini for the wording")
    draft_cmd.set_defaults(handler=_draft)

    accept_cmd = commands.add_parser("accept", parents=[data], help="Keep the draft as ready to paste")
    accept_cmd.add_argument("proposal")
    accept_cmd.set_defaults(handler=_accept)

    edit_cmd = commands.add_parser("edit", parents=[data], help="Replace the draft with your own sentence")
    edit_cmd.add_argument("proposal")
    edit_cmd.add_argument("--text", required=True, help="The sentence you would actually paste")
    edit_cmd.add_argument("--rule", help="Remember this for the same person next time")
    edit_cmd.set_defaults(handler=_edit)

    reject_cmd = commands.add_parser("reject", parents=[data], help="Throw the draft away")
    reject_cmd.add_argument("proposal")
    reject_cmd.add_argument("--rule", help="Remember this for the same person next time")
    reject_cmd.set_defaults(handler=_reject)

    skip_cmd = commands.add_parser("skip", parents=[data], help="Leave this post with no comment")
    skip_cmd.add_argument("proposal")
    skip_cmd.set_defaults(handler=_skip)

    voice_cmd = commands.add_parser("voice", parents=[data, fixtures], help="Show one person's voice card and rules")
    voice_cmd.add_argument("author", help="rico or fathin")
    voice_cmd.set_defaults(handler=_voice)

    undo_cmd = commands.add_parser("undo", parents=[data], help="Turn a remembered rule off")
    undo_cmd.add_argument("rule")
    undo_cmd.set_defaults(handler=_undo)

    demo_cmd = commands.add_parser("demo", parents=[data, fixtures], help="Walk through the loop without Gemini")
    demo_cmd.set_defaults(handler=_demo)

    serve_cmd = commands.add_parser("serve", parents=[data, fixtures], help="Local API for the browser extension")
    serve_cmd.add_argument("--port", type=int, default=PORT)
    serve_cmd.set_defaults(handler=_serve)

    propose_cmd = commands.add_parser("propose", parents=[data, fixtures], help="Machine-readable draft. Prefer: engage draft")
    propose_cmd.add_argument("--author", required=True)
    propose_cmd.add_argument("--post", type=Path, required=True)
    propose_cmd.add_argument("--live", action="store_true", help="Draft with Gemini. Default tests do not use this.")
    propose_cmd.set_defaults(handler=_propose)

    decide_cmd = commands.add_parser("decide", parents=[data], help="Record a human decision")
    decide_cmd.add_argument("--proposal", required=True)
    decide_cmd.add_argument("--action", required=True, choices=("accept", "edit", "reject", "skip"))
    decide_cmd.add_argument("--text", help="Required for edit. The person's own sentence.")
    decide_cmd.add_argument("--rule", help="Saved only on edit or reject.")
    decide_cmd.set_defaults(handler=_decide)

    revert_cmd = commands.add_parser("revert-rule", parents=[data], help="Turn a learned rule off")
    revert_cmd.add_argument("--id", required=True)
    revert_cmd.set_defaults(handler=_revert)

    show_cmd = commands.add_parser("show", parents=[data, fixtures], help="Show one author's profile and rules")
    show_cmd.add_argument("--author", required=True)
    show_cmd.set_defaults(handler=_show)
    return parser


def _start(args: argparse.Namespace) -> None:
    Session(args.data_dir, args.fixtures).run()


def _serve(args: argparse.Namespace) -> None:
    serve(args.data_dir, args.fixtures, args.port)


def _propose(args: argparse.Namespace) -> None:
    proposal = propose(
        args.author,
        args.post,
        data_dir=args.data_dir,
        fixtures_dir=args.fixtures,
        live=args.live,
    )
    print(json.dumps(proposal.to_dict(), indent=2))


def _decide(args: argparse.Namespace) -> None:
    decision, rule, handoff = decide(
        args.proposal,
        args.action,
        data_dir=args.data_dir,
        text=args.text,
        rule_text=args.rule,
    )
    payload = {
        "decision": decision.to_dict(),
        "rule_id": rule.id if rule else None,
        "handoff": handoff.to_dict() if handoff else None,
    }
    print(json.dumps(payload, indent=2))


def _revert(args: argparse.Namespace) -> None:
    rule = revert_rule(args.data_dir, args.id)
    print(json.dumps(rule.to_dict(), indent=2))


def _show(args: argparse.Namespace) -> None:
    _print_voice(args.fixtures, args.data_dir, args.author)


def _posts(args: argparse.Namespace) -> None:
    folder = args.fixtures / "posts"
    paths = sorted(folder.glob("*.json"))
    if not paths:
        raise EngageError(f"no posts in {folder}")
    print("Sample posts. These are not from LinkedIn.\n")
    for index, path in enumerate(paths, start=1):
        post = load_post(path)
        shown = _display_path(path)
        person = "fathin" if post.topic in {"agents", "building"} else "rico"
        print(f"{index}. {shown}")
        print(f"   {post.note}")
        print(f"   {post.text}")
        print(f"   Next: engage draft {person} {shown}")
        print()


def _draft(args: argparse.Namespace) -> None:
    post = load_post(args.post)
    proposal = propose(
        args.author,
        args.post,
        data_dir=args.data_dir,
        fixtures_dir=args.fixtures,
        live=args.live,
    )
    _print_proposal(proposal, post.text)


def _accept(args: argparse.Namespace) -> None:
    decision, rule, handoff = decide(args.proposal, "accept", data_dir=args.data_dir)
    _print_decision(decision, rule, handoff)


def _edit(args: argparse.Namespace) -> None:
    decision, rule, handoff = decide(
        args.proposal,
        "edit",
        data_dir=args.data_dir,
        text=args.text,
        rule_text=args.rule,
    )
    _print_decision(decision, rule, handoff)


def _reject(args: argparse.Namespace) -> None:
    decision, rule, handoff = decide(
        args.proposal,
        "reject",
        data_dir=args.data_dir,
        rule_text=args.rule,
    )
    _print_decision(decision, rule, handoff)


def _skip(args: argparse.Namespace) -> None:
    decision, rule, handoff = decide(args.proposal, "skip", data_dir=args.data_dir)
    _print_decision(decision, rule, handoff)


def _voice(args: argparse.Namespace) -> None:
    _print_voice(args.fixtures, args.data_dir, args.author)


def _undo(args: argparse.Namespace) -> None:
    rule = revert_rule(args.data_dir, args.rule)
    print(f"Turned off for {rule.author_id}: {rule.text}")
    print("It stays on file so you can still read it. It will not be used again.")


def _demo(args: argparse.Namespace) -> None:
    import shutil

    data = args.data_dir
    if data == Path("data"):
        data = Path("data/walkthrough")
        if data.exists():
            shutil.rmtree(data)
    print("Walkthrough for Rico. Sample posts only. Nothing is posted.\n")
    sensitive = args.fixtures / "posts" / "03-sensitive.json"
    on_goal = args.fixtures / "posts" / "01-on-goal.json"
    skipped = propose(
        "rico",
        sensitive,
        data_dir=data,
        fixtures_dir=args.fixtures,
    )
    print("1. A sensitive post")
    _print_proposal(skipped, load_post(sensitive).text)
    print()
    drafted = propose(
        "rico",
        on_goal,
        data_dir=data,
        fixtures_dir=args.fixtures,
        model=ScriptedModel(_DEMO_DRAFT),
    )
    print("2. A post that matches his goal")
    _print_proposal(drafted, load_post(on_goal).text)
    print()
    decision, rule, handoff = decide(
        drafted.id,
        "edit",
        data_dir=data,
        text="The named author decides what goes live.",
        rule_text="do not end with a question",
    )
    print("3. He rewrites it and keeps a rule")
    _print_decision(decision, rule, handoff)
    print()
    print("4. His voice")
    _print_voice(args.fixtures, data, "rico")
    print()
    print("5. Fathin does not receive Rico's rule")
    _print_voice(args.fixtures, data, "fathin")
    print()
    if rule is None:
        raise EngageError("demo expected a rule")
    revert_rule(data, rule.id)
    print("6. It is off. The note stays on file.")


def _guide() -> None:
    print(
        """Open the menu. Type a number, then type the sentence and the rule.

  engage

Or walk the loop once, with no API key:

  engage demo

Direct commands, if you already know the step:

  engage posts
  engage draft rico fixtures/posts/03-sensitive.json
  engage draft rico fixtures/posts/01-on-goal.json --live
  engage voice rico

Read a LinkedIn page you already have open, from the browser extension:

  engage serve

Nothing is posted to LinkedIn."""
    )


def _print_proposal(proposal: Proposal, post_text: str) -> None:
    print(f"Person: {proposal.author_id}")
    print(f"Post: {post_text}")
    print()
    if proposal.status == "skipped":
        print("Say nothing.")
        print(_SKIP_REASONS.get(proposal.reason, proposal.reason))
        print(f"Recorded as {proposal.id}.")
        return
    if proposal.status == "blocked":
        print("This draft was refused.")
        print(_BLOCK_REASONS.get(proposal.reason, proposal.reason))
        if proposal.comment:
            print()
            print("Refused wording:")
            print(proposal.comment)
        print()
        print("Write your own sentence instead:")
        print(f"  engage edit {proposal.id} --text \"your sentence\"")
        return
    print("Draft:")
    print(proposal.comment)
    print()
    print("What do you want to do?")
    print(f"  Keep it:    engage accept {proposal.id}")
    print(f"  Change it:  engage edit {proposal.id} --text \"your sentence\" --rule \"what to remember\"")
    print(f"  Drop it:    engage reject {proposal.id}")
    print(f"  Leave it:   engage skip {proposal.id}")


def _print_decision(decision: Decision, rule: Rule | None, handoff: Handoff | None) -> None:
    if handoff is not None:
        print("Ready to paste. Nothing was posted.")
        print()
        print(handoff.text)
    elif decision.action == "reject":
        print("Draft dropped. Nothing to paste.")
    elif decision.action == "skip":
        print("Left this post alone. Nothing to paste.")
    else:
        print("Nothing to paste.")
    if rule is not None:
        print()
        print(f"Remembered for {rule.author_id}: {rule.text}")
        print("The next draft for that person will include this line.")
        print("Turn it off from the menu with: engage")


def _print_voice(fixtures_dir: Path, data_dir: Path, author_id: str) -> None:
    author = load_author(fixtures_dir, author_id)
    rules = load_rules(data_dir, author.id)
    print(author.name)
    print(f"Goal: {author.goal}")
    print()
    print("Sounds like:")
    for example in author.voice_examples:
        print(f"- {plain_example(example)}")
    print()
    print("May say:")
    for claim in author.allowed_claims:
        print(f"- {claim.text}")
    print()
    print("Will not say:")
    for phrase in author.prohibited_phrases:
        print(f"- {phrase}")
    print()
    print("Remembered rules:")
    if not rules:
        print("- none")
        return
    for rule in rules:
        state = "on" if rule.active else "off"
        print(f"- [{state}] {rule.text}")


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


_SKIP_REASONS = {
    "sensitive": "This post is sensitive.",
    "injection": "This post tries to give the model orders.",
    "off_goal": "This topic is outside their goal.",
    "prohibited_claim": "Replying would repeat a claim they will not make.",
    "repeats_point": "They already said this.",
}

_BLOCK_REASONS = {
    "empty": "The model returned no sentence.",
    "ungrounded": "The sentence is not tied to an allowed claim.",
    "unknown_claim": "The sentence cites a claim that is not allowed.",
    "prohibited_phrase": "The sentence uses a phrase they will not say.",
    "unsupported_metric": "The sentence invents a number.",
    "breaks_rule": "The sentence breaks a rule they already saved.",
    "unparseable": "The model did not return a comment the checker could read.",
}

_DEMO_DRAFT = (
    '{"comment": "The named author decides what goes live.", '
    '"claim_ids": ["named_author_decides"], "reason": "demo"}'
)


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os_key = key.strip()
        if os_key and os_key not in os.environ:
            os.environ[os_key] = value.strip().strip("'\"")
