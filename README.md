# Engage

A local loop that helps one named person decide whether a post is worth a comment. It proposes one comment only when the post passes a gate, and only with claims that person has allowed. The person accepts, edits, or rejects. Nothing is posted.

The write-up is the submission:

- [Product definition](docs/product.md)
- [System design](docs/system.md)
- [Decision log](docs/decision-log.md)
- [Sessions, limits, and the next experiment](docs/sessions.md)

Rico and Fathin each have a profile under `fixtures/authors/`. Those voice cards are still hypotheses. A confirmed read from the extension replaces the examples. It does not invent allowed claims. Posts under `fixtures/posts/` are synthetic and keep the offline proof working.

Fathin named GitHub as the place to submit, and said to do the web automation or scraping required for the two profiles he already named.

## Setup

Python 3.11 or newer. On this machine `python3` is 3.9, so the verified command is:

```bash
python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest
```

That installs the package, runs the tests, and does not call a model.

## Browser extension

In the project folder:

```bash
.venv/bin/engage serve
```

That listens on `http://127.0.0.1:8787` and does not open LinkedIn.

In Chrome, open `chrome://extensions`, turn on Developer mode, choose Load unpacked, and select the `extension/` folder.

Log into LinkedIn yourself. Open one of these, scroll until posts are on screen, then click the Engage icon and Read visible posts:

- https://www.linkedin.com/in/fathindos/
- https://www.linkedin.com/in/ricosoots/

Save this voice only if the samples are theirs. Then open a post, pick that voice, and draft. Keep, change, or drop the sentence. Paste it yourself.

The extension reads text already visible in the tab you clicked. It does not store cookies, scroll, walk a profile, or post. If the page layout hides the writing, it reports that no posts were visible.

A live draft needs Gemini:

```bash
.venv/bin/pip install -e ".[live]"
```

Put the key in `.env`. That file stays off git. Leave "Ask Gemini" unchecked and the gate can still say nothing on a sensitive or injected post, with no model call.

## Commands

The menu still walks the fixture proof. You pick a person, pick a post, and type the sentence and the rule.

```bash
.venv/bin/engage
.venv/bin/engage demo
```

`engage demo` plays the loop once, with no API key, and starts from a clean slate every time.

You should see a sensitive post dismissed in a sentence, one draft, your rewrite marked ready to paste, a rule saved for Rico, and that same rule absent from Fathin. The last line says the rule is off.

Look at the sample posts, then try one skip:

```bash
.venv/bin/engage posts
.venv/bin/engage draft rico fixtures/posts/03-sensitive.json
```

You should see `Say nothing.` and `This post is sensitive.`

Ask Gemini for a draft on a post that fits:

```bash
.venv/bin/engage draft rico fixtures/posts/01-on-goal.json --live
```

The reply ends with the next command. Copy the id from that line.

```bash
.venv/bin/engage edit PROPOSAL --text "The named author decides what goes live." --rule "do not end with a question"
.venv/bin/engage voice rico
.venv/bin/engage voice fathin
.venv/bin/engage undo RULE
```

`edit` prints the sentence under `Ready to paste` and says nothing was posted. `voice rico` lists the rule as `[on]`. `voice fathin` does not list it. `undo` turns it `[off]` and leaves it readable.

`accept` keeps the draft unchanged. `reject` drops it. `skip` leaves the post alone. A skipped or blocked draft cannot be accepted.
