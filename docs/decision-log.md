# Decision log

Work was done on 30 September 2026. The cap is 10 hours. No design-partner session was held.

The first proof, fixtures, tests, and write-up took about 2.5 hours. The extension, local API, and GitHub repo took about another hour. Later the same day the reader was narrowed to post text, each person got a voice file, and the draft list was switched to those files.

## Decisions

- Silence is a valid result. The gate is ordinary code. The model only drafts.
- Rico and Fathin stay separate. Fathin named both. One shared voice would let a rule for one change the other.
- Learning is a text rule the person can read and turn off. Only "do not end with a question" is enforced in code. Other rule text is prompt-only.
- A skipped or blocked model draft cannot be accepted unchanged. The person can still type their own sentence.
- Sample cards in `fixtures/authors/` stay hypotheses. They exist so `pytest` and `engage demo` run with no key and no LinkedIn login.
- Fathin's message, "Use github. Do the web web automation stuff required or scraping," names the submission channel and allows reading the two profiles he already named. Reading means the DOM of a tab the person opened. It does not mean an unattended crawler, a stored cookie, or a login bot.
- A profile updates `data/voices/{id}.md`. A single post cannot. The draft list is those files. The comment is typed into the open box. The person presses Post.
- The whole page is not scraped. An early reader saved ads, inline script, and the extension's own panel, and Gemini described that junk as the voice. Post text now comes from commentary nodes. The person scrolls. The tool does not.
- Voice files stay off git. They contain posts from the open page, including an email address and some posts that were on screen but were not written by that person.

## Alternatives rejected

An extension that posts, or a crawler that walks LinkedIn alone. Fine-tuning on their posts. One blended voice. Asking the model whether to skip. A prompt blob with no off switch.

## AI use

Web search on [byro.ee](https://byro.ee/) supported the boundary: goal, evidence, named author, no automatic publish. It was not copied as an architecture.

Cursor's coding agent wrote the implementation from the brief. It did not interview Rico or Fathin, did not log into LinkedIn, and did not store a cookie. The extension does nothing until a person loads it.

## Verification

`python3` on this machine is 3.9. The verified command uses Python 3.11:

`python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest`

The latest run reported 44 passed. The tests cover skip without a model call, injection, ungrounded and prohibited drafts, a refused accept of a skip, a question rule that applies to one author and then turns off, isolation between the two prompts, handoff status `ready_to_paste`, a missing Gemini key, a voice file that drops page junk, and a draft that uses the recorded file rather than the sample card.

They do not cover a live sentence Rico or Fathin would send, a free-text rule other than the question pattern, or LinkedIn markup after a redesign.

The plan's setup line used `python3`. Here that binary is too old, so the verified line uses `python3.11`. Gemini stays an optional extra so the proof runs offline.
