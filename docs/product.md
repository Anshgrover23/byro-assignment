# Product definition

Engage is a Chrome extension. It saves how one person writes from the LinkedIn profile already on screen, then drafts one comment in that voice on a post the person opened. The person presses Post.

Rico Soots and Fathin Dosunmu are separate voices. A correction for one does not apply to the other.

## The loop

1. The person opens a profile and scrolls Activity. The page panel saves the posts already on screen into `data/voices/{id}.md`. That file is style. It is not a list of claims.
2. The person opens someone else's post and clicks Comment.
3. A gate recommends skip or draft. Skip does not call a model.
4. On draft, the model writes one sentence from the saved voice file. A checker blocks invented metrics, banned phrases, and a broken rule.
5. The sentence is placed in the comment box. Enter is not pressed. The person presses Post.
6. An edit or a rejection can save a rule for that person. Revert turns the rule off. It stays readable.

## When it says nothing

The gate skips, and does not call a model, when the post is sensitive, tries to instruct the model, sits outside that person's goal, uses a prohibited phrase, or only repeats a point already made.

Skip is a finished result. The person can still write their own sentence. A skipped or blocked model draft cannot be accepted as-is.

## What is known

No voice interview was held. Fathin named himself and Rico, then said to use GitHub and to read the two profiles. That is permission to read an open tab. It is not a quote about how they comment, and it is not permission to post.

The sample cards in `fixtures/authors/` are hypotheses. They keep the offline tests working. A live draft uses the voice file on this machine, not those cards. The voice files are not in the GitHub repo.

## Non-goals

Logging in, storing cookies, scrolling or crawling on its own, posting, a feed, a schedule, analytics, fine-tuning, accounts, and billing.
