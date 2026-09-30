# Design-partner sessions

No voice session has been held. Fathin assigned the exercise and said to use him and Rico. That names the two authors. It does not answer why they comment, what a useful comment does, or where a draft becomes uncomfortable.

On 30 September 2026 he added, in LinkedIn chat: "Use github. Do the web web automation stuff required or scraping." That is the submission channel, and permission to read the two profile URLs he and the brief already named. It is not feedback on a draft.

Until a session happens, the voice cards in `fixtures/authors/` stay labeled as hypotheses. Do not treat them as quotes.

## How to run one session

Thirty minutes is enough. One person at a time. Rico first, then Fathin. Ask these, and write down the words they use.

1. When did you last comment on someone else's post, and what were you trying to make happen?
2. Show me a comment you would still send. What makes it yours?
3. Show me a comment you would be embarrassed to have under your name. What is the specific failure?
4. Which claims are you willing to make in public right now? Which numbers, customers, or results are off limits?
5. When would you rather say nothing?
6. If a tool remembered one correction from you, what would that correction be?
7. Where does automation become uncomfortable: drafting, choosing the post, remembering a preference, or anything that leaves your account?

After each session, replace that author's `voice_examples`, `allowed_claims`, `prohibited_phrases`, and `recent_points` with what they approved. Keep `evidence_note` honest about the date and that the examples are approved.

## What to do with the answers

Bring five posts they recognize. Ask, for each, "skip" or "I would comment," and one sentence they would actually send. Then run `propose` on synthetic stand-ins of those posts, with `--live` only if they agree the prompt may be sent to Gemini.

The result that matters is disagreement: a skip they would have answered, a draft they would not send, or a rule that did not change the next sentence.

## Feedback so far

There is none. Filling this section with imagined reactions would fake the user evidence the brief asks for.

## Next experiment

1. Load the extension, open `https://www.linkedin.com/in/ricosoots/`, scroll until posts are visible, and click Read visible posts.
2. Save only if the samples are his writing. Do the same for `https://www.linkedin.com/in/fathindos/`.
3. Open five posts one of them would recognize. For each, record skip or comment before looking at the draft.
4. Draft as that person. Count how many labels match, and whether one reviewed rule changes the next sentence into one they would paste.

That is the assumption this repo cannot prove yet: that a reviewed correction makes the next comment one they would send, in their voice, without a claim they did not approve.
