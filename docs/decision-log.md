# Decision log

Approximate times for 30 September 2026. The cap is 10 hours, including sessions and submission prep. Sessions have not been held, so that part of the budget is unused.

- Research and framing, including Byro's public site and how other commenting tools handle review: about 45 minutes
- Product and system design: about 30 minutes
- Implementation, fixtures, and tests: about 60 minutes
- Write-up: about 20 minutes

Running total about 2.5 hours before Fathin's later instruction. The extension, local API, and GitHub submission took about another hour. Running total about 3.5 hours.

## Assumptions

- Rico and Fathin are two authors, not one blended voice. Fathin named both of them when asked for the missing materials. Their goals are still hypotheses.
- A useful comment is one grounded claim in that author's voice, or silence. This follows Byro's public description (goal, supplied evidence, named author, no automatic publish) more than it follows a session.
- Topic and sensitivity can be supplied with the fixture. The proof does not discover posts and does not ask a model to judge sensitivity.
- Learning that a person can inspect is a text rule, not a weight update. Only the "do not end with a question" pattern is enforced in code. Other rule text is added to the next prompt and may be ignored by a live model.
- The named person may override a skip by editing in their own sentence. They may not accept a blocked or skipped model draft unchanged.
- Voice match cannot be proven from the shipped fixtures. They stay labeled as hypotheses until a person confirms a capture.
- Fathin's later message authorizes reading the two profiles and names GitHub as the place to submit. "Scraping" here means reading the DOM of a LinkedIn tab the person already opened. It does not mean an unattended crawler, a login bot, or a cookie export.
- A profile the person opens can refresh a markdown voice memory. A single post cannot. The comment is written into the open box, and the person presses Post.

## Alternatives

- An extension that posts, or a crawler that walks LinkedIn without a click. Fathin allowed reading the pages. He did not allow the tool to act as the author. The extension reads one open tab and stops at `ready_to_paste`.
- Fine-tuning on their posts. It is not inspectable or reversible in this timebox, and we do not have an approved corpus.
- Tone sliders with no memory of an edit. That produces a generic draft and does not learn.
- A web app. The brief does not reward visual polish. The human decision is an explicit command, which the tests can run.
- One shared voice for Rico and Fathin. A rule from one would silently change the other.
- Asking the model whether to skip. Skip reasons would then be untestable. The gate is deterministic. The model only drafts.
- Silent accumulation of every edit into a prompt blob with no off switch. Revert would be a guess. The rule row stays visible and can be turned off.

## AI use

An earlier pass used web search to read [byro.ee](https://byro.ee/) and public descriptions of human-reviewed commenting tools. That supported the boundary: goal, evidence, named author, no autopublish. It was not used as an architecture to copy.

Cursor's coding agent (Grok) wrote the plan and the first implementation of this repo from the brief. It did not interview Rico or Fathin. It did not call Gemini. It did not log into LinkedIn or store a session cookie. After Fathin's message, the same agent added the extension and the local capture API. The extension still does not run until a person loads it and clicks.

Verification is the test run below, not the agent's confidence. The agent also mis-started the first virtualenv with system Python 3.9, which cannot build this package. The verified command uses Python 3.11.

## Verification

On this machine `python3` is 3.9.6. The project requires 3.11. Creating the environment with the command below succeeded. The first `pytest` run in that environment reported 16 passed. One more test was added for a missing Gemini key, and `.venv/bin/pytest` then reported 17 passed.

`python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest`

What those tests cover:

- Skip on sensitive, off-goal, prohibited phrase, and repeated point, without calling a model
- A prompt-injection post cannot become a draft or a handoff
- Ungrounded, unknown, prohibited, and unsupported metric drafts are blocked
- Accept of a blocked or skipped proposal is refused
- A reviewed "do not end with a question" rule blocks the next draft, stays visible, and stops applying after revert
- Rico's rule and voice examples do not appear in Fathin's prompt
- Handoff status is only `ready_to_paste`
- `propose --live` without `GEMINI_API_KEY` exits before writing a proposal

A later run, after the extension, reported 35 passed. The added tests cover the voice summary, the known profile slugs, claim preservation, a capture that does not save until confirm, and an open LinkedIn post that still skips when it is sensitive or tries to instruct the tool.

What they do not cover: a live Gemini sentence, whether Rico or Fathin would send it, whether a free-text rule other than the question pattern actually changes model behavior, and whether LinkedIn's current page markup still exposes the post text to the extension.

The `google-genai` package is an optional `live` extra. The default setup stays offline. Install it with `pip install -e ".[live]"` only when running `propose --live`.

## Deviations from the first plan

The plan's setup line used `python3`. Here that binary is 3.9, so the verified line uses `python3.11`. The plan also listed the Gemini SDK as part of the default install. It is optional so the proof runs with no key and no network. The adapter is still in the repo.
