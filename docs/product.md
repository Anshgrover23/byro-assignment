# Product definition

Engage helps one named person decide whether a supplied post is worth a comment, and proposes one comment only when it is. The person accepts, edits, or rejects the draft. The program never posts.

The two people in this proof are Rico Soots and Fathin Dosunmu. Each has a separate profile. A correction saved for one does not apply to the other.

## The loop

1. A post is either a local file, or the text of a LinkedIn post the person already has open. It is data, including any instructions written inside it. The extension reads that text only after a click. It does not log in, store cookies, scroll, or crawl.
2. The gate recommends skip or draft.
3. On draft, a model proposes one comment. A checker blocks the proposal if it is ungrounded, uses a claim the author has not allowed, or breaks an active rule.
4. The named person decides: accept, edit, reject, or skip.
5. Accept or edit records a mock handoff, `ready_to_paste`. Reject and skip record no handoff.
6. An edit or a rejection may save a rule for that author. The next prompt includes the rule. Revert turns it off.

## Success signal

The proof can show this: after one reviewed correction, the next proposal for that author obeys the new rule, still refuses a claim they did not allow, and does not create a handoff on its own.

The proof cannot show that the sentence sounds like Rico or Fathin until one of them confirms a voice card captured from their own page. The cards in the repo start as hypotheses. A capture replaces the examples only after Save.

## User evidence

Two design-partner sessions were part of the brief. None has been held. Nothing below is a quote from Rico or Fathin.

What is on the record:

- Fathin sent the challenge and, when asked for founder context and fixtures, said to use him and Rico. That is why the proof has two author profiles instead of a blended voice.
- On 30 September 2026 he replied, in the same chat: "Use github. Do the web web automation stuff required or scraping." That names the submission channel and allows reading the two profiles he already named: `linkedin.com/in/fathindos` and `linkedin.com/in/ricosoots`. It is not a voice interview.
- Byro's public site says the product recommends what to say from an explicit goal and supplied evidence, shows the source, and leaves the named author to approve a LinkedIn handoff. It says the pilot does not publish by itself.
- The brief asks for a judgment about when to engage, a comment in the person's voice, learning from reviewed feedback, and human control of identity, claims, voice, and consequential actions.

Hypotheses, to be replaced after a session:

- Rico would comment to tie a public conversation to evidence the company can stand behind, and would rather say nothing than sound like a generic founder account.
- Fathin would comment as a builder: shorter, more casual, about the human still choosing the action.
- Automation becomes uncomfortable when a tool posts, invents a result, or keeps a preference the person can no longer see or undo.

Voice examples shipped in `fixtures/authors/` are still labeled synthetic. A confirmed capture from the extension overwrites that note and adds the visible posts as examples. It does not invent allowed claims.

## When the system does nothing

`propose` records a skip and does not call a model when:

- the fixture is marked sensitive
- the post text tries to instruct the model
- the topic is outside that author's goal
- the post pushes a phrase the author has prohibited
- the post only repeats a point the author already made

Skip is a finished outcome. A later human edit can still write a sentence, because the named person owns the action. Accept cannot promote a skipped or blocked model draft into a handoff.

## Non-goals

Logging into LinkedIn, storing cookies, an unattended crawl, posting, a feed, a schedule, analytics, fine-tuning, accounts, and billing. Reading a page is a click on a tab the person already opened.
