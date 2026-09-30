# Engage

A Chrome extension. Open a LinkedIn profile, scroll their posts, and it saves how they write. Open someone else's post and it drafts one comment in that voice, in the comment box. You press Post.

Demo: https://youtu.be/sg2BOgRnwdw

Write-up: [product](docs/product.md), [system](docs/system.md), [decision log](docs/decision-log.md), [sessions](docs/sessions.md).

## Run

Python 3.11 or newer.

```bash
python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev,live]" && .venv/bin/pytest
```

Put `GEMINI_API_KEY` in `.env`. That file stays off git.

```bash
.venv/bin/engage serve
```

In Chrome, open `chrome://extensions`, turn on Developer mode, choose Load unpacked, and select the `extension/` folder.

1. Log into LinkedIn yourself.
2. Open a profile, then Activity, and scroll. The panel on the page saves each post into `data/voices/`.
3. Open a post. Click Comment so the box is open.
4. Choose a saved voice and click Write draft. The sentence goes in the box. You press Post.

The extension does not log in, store cookies, scroll for you, or press Enter. After a code change, reload the extension and refresh the LinkedIn tab, then restart `engage serve`.

`engage demo` runs the same loop on the sample posts, with no API key.
