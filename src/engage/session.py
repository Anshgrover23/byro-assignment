"""A numbered menu. The person never has to type a record id."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from pathlib import Path

from engage.decide import decide
from engage.gate import evaluate
from engage.models import Author, Claim, EngageError, Proposal
from engage.propose import propose
from engage.rules import load_rules, revert_rule
from engage.store import author_path, load_author, load_post, write_json

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


class Session:
    def __init__(
        self,
        data_dir: Path,
        fixtures_dir: Path,
        input_fn: InputFn = input,
        output: OutputFn = print,
    ) -> None:
        self.data_dir = data_dir
        self.fixtures_dir = fixtures_dir
        self.input_fn = input_fn
        self.output = output

    def run(self) -> None:
        self.say("Engage. Pick a number. Nothing is posted to LinkedIn.")
        self.say("")
        while True:
            choice = self.choose(
                "What do you want to do?",
                [
                    "Comment on a post",
                    "See a voice",
                    "Add a voice",
                    "Turn off a remembered rule",
                    "Quit",
                ],
            )
            if choice is None or choice == 4:
                self.say("Done.")
                return
            if choice == 0:
                self.comment()
            elif choice == 1:
                self.show_voice()
            elif choice == 2:
                self.add_voice()
            elif choice == 3:
                self.turn_off_rule()

    def comment(self) -> None:
        author = self.pick_author("Who is commenting?")
        if author is None:
            return
        post_path = self.pick_post()
        if post_path is None:
            return
        post = load_post(post_path)
        if not evaluate(post, author).eligible:
            proposal = propose(
                author.id,
                post_path,
                data_dir=self.data_dir,
                fixtures_dir=self.fixtures_dir,
            )
            self.review(proposal, post.text)
            return
        if not self.yes_no("This post is worth a comment. Ask Gemini to write it?"):
            self.say("Nothing written. Say yes next time if you want a sentence.")
            return
        try:
            proposal = propose(
                author.id,
                post_path,
                data_dir=self.data_dir,
                fixtures_dir=self.fixtures_dir,
                live=True,
            )
        except EngageError as exc:
            self.say(str(exc))
            return
        self.review(proposal, post.text)

    def review(self, proposal: Proposal, post_text: str) -> None:
        self.say("")
        self.say(post_text)
        self.say("")
        if proposal.status == "skipped":
            self.say("Say nothing.")
            self.say(_SKIP_REASONS.get(proposal.reason, proposal.reason))
            return
        if proposal.status == "blocked":
            self.say("That wording was refused.")
            self.say(proposal.reason)
            if proposal.comment:
                self.say(proposal.comment)
            return
        self.say("Draft:")
        self.say(proposal.comment or "")
        self.say("")
        choice = self.choose(
            "What do you want to do with it?",
            ["Keep it", "Change the wording", "Drop it", "Leave it"],
        )
        if choice is None:
            return
        if choice == 0:
            decide(proposal.id, "accept", data_dir=self.data_dir)
            self.say("Ready to paste. Nothing was posted.")
            self.say(proposal.comment or "")
            return
        if choice == 1:
            sentence = self.ask("Sentence to paste: ")
            if not sentence:
                self.say("No sentence, so nothing was saved.")
                return
            rule = self.ask("Rule to remember (press enter to skip): ")
            _, saved, handoff = decide(
                proposal.id,
                "edit",
                data_dir=self.data_dir,
                text=sentence,
                rule_text=rule or None,
            )
            self.say("Ready to paste. Nothing was posted.")
            self.say(handoff.text if handoff else sentence)
            if saved is not None:
                self.say(f"Remembered for {saved.author_id}: {saved.text}")
            return
        if choice == 2:
            rule = self.ask("Rule to remember (press enter to skip): ")
            decide(proposal.id, "reject", data_dir=self.data_dir, rule_text=rule or None)
            self.say("Draft dropped.")
            if rule:
                self.say(f"Remembered for {proposal.author_id}: {rule}")
            return
        decide(proposal.id, "skip", data_dir=self.data_dir)
        self.say("Left this post alone.")

    def show_voice(self) -> None:
        author = self.pick_author("Whose voice?")
        if author is None:
            return
        self.say("")
        self.say(author.name)
        self.say(f"Goal: {author.goal}")
        self.say("Sounds like:")
        for example in author.voice_examples:
            self.say(f"- {plain_example(example)}")
        self.say("May say:")
        for claim in author.allowed_claims:
            self.say(f"- {claim.text}")
        self.say("Will not say:")
        for phrase in author.prohibited_phrases:
            self.say(f"- {phrase}")
        rules = [rule for rule in load_rules(self.data_dir, author.id) if rule.active]
        self.say("Remembered:")
        if not rules:
            self.say("- nothing yet")
            return
        for rule in rules:
            self.say(f"- {rule.text}")

    def add_voice(self) -> None:
        name = self.ask("Name: ")
        if not name:
            self.say("No name, so no voice was added.")
            return
        slug = slugify(name)
        if not slug:
            self.say("Use a name with letters.")
            return
        if author_path(self.fixtures_dir, slug).exists():
            self.say(f"{name} is already here.")
            return
        goal = self.ask("What should they be known for? ")
        example = self.ask("One sentence that sounds like them: ")
        claim = self.ask("One thing they are willing to say: ")
        banned = self.ask("One thing they will not say: ")
        topics_raw = self.ask("Topics, separated by commas: ")
        if not all([goal, example, claim, banned, topics_raw]):
            self.say("A voice needs a goal, a sentence, a claim, a limit, and a topic.")
            return
        topics = [part.strip().lower().replace(" ", "_") for part in topics_raw.split(",") if part.strip()]
        author = Author(
            id=slug,
            name=name,
            goal=goal,
            topics=topics,
            voice_examples=[example],
            allowed_claims=[Claim(id=f"{slug}_claim", text=claim)],
            prohibited_phrases=[banned],
            recent_points=[],
            evidence_note="Added by this person in the setup menu.",
        )
        write_json(author_path(self.fixtures_dir, slug), author.to_dict())
        self.say(f"Added {name}. They can comment on: {', '.join(topics)}.")

    def turn_off_rule(self) -> None:
        rules = [rule for rule in load_rules(self.data_dir) if rule.active]
        if not rules:
            self.say("No rules to turn off.")
            return
        labels = []
        for rule in rules:
            try:
                person = load_author(self.fixtures_dir, rule.author_id).name
            except EngageError:
                person = rule.author_id
            labels.append(f"{person}: {rule.text}")
        choice = self.choose("Which rule should turn off?", labels)
        if choice is None:
            return
        revert_rule(self.data_dir, rules[choice].id)
        self.say(f"Turned off: {labels[choice]}")

    def pick_author(self, title: str) -> Author | None:
        authors = list_authors(self.fixtures_dir)
        if not authors:
            self.say("No voices yet. Add one first.")
            return None
        choice = self.choose(title, [author.name for author in authors])
        if choice is None:
            return None
        return authors[choice]

    def pick_post(self) -> Path | None:
        paths = sorted((self.fixtures_dir / "posts").glob("*.json"))
        if not paths:
            self.say("No posts to read.")
            return None
        labels = []
        for path in paths:
            post = load_post(path)
            labels.append(post.text if len(post.text) <= 90 else post.text[:87] + "...")
        choice = self.choose("Which post?", labels)
        if choice is None:
            return None
        return paths[choice]

    def yes_no(self, label: str) -> bool:
        raw = self.ask(f"{label} Type yes or no: ")
        return raw is not None and raw.lower() in {"y", "yes"}

    def choose(self, title: str, options: list[str]) -> int | None:
        self.say(title)
        for index, option in enumerate(options, start=1):
            self.say(f"  {index}. {option}")
        while True:
            raw = self.ask("Number: ")
            if raw is None or raw.lower() in {"q", "quit"}:
                return None
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return int(raw) - 1
            self.say(f"Type a number from 1 to {len(options)}.")

    def ask(self, label: str) -> str | None:
        try:
            value = self.input_fn(label)
        except EOFError:
            return None
        if value is None:
            return None
        return value.strip()

    def say(self, text: str) -> None:
        self.output(text)


def list_authors(fixtures_dir: Path) -> list[Author]:
    folder = fixtures_dir / "authors"
    if not folder.is_dir():
        return []
    authors = []
    for path in sorted(folder.glob("*.json")):
        authors.append(load_author(fixtures_dir, path.stem))
    authors.sort(key=lambda author: author.name.lower())
    return authors


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def plain_example(text: str) -> str:
    prefix = "Hypothesis, not a real quote: "
    if text.startswith(prefix):
        return text[len(prefix) :].strip()
    return text


def scripted_input(answers: list[str]) -> InputFn:
    remaining: Iterator[str] = iter(answers)

    def _read(_label: str) -> str:
        try:
            return next(remaining)
        except StopIteration as exc:
            raise EOFError from exc

    return _read


_SKIP_REASONS = {
    "sensitive": "This post is sensitive.",
    "injection": "This post tries to give the model orders.",
    "off_goal": "This topic is outside their goal.",
    "prohibited_claim": "Replying would repeat a claim they will not make.",
    "repeats_point": "They already said this.",
}
