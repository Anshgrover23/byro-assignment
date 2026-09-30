"""Local API for the browser extension. Binds to this machine only."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engage.decide import decide
from engage.gemini import GeminiModel
from engage.harness import list_memories, resolve_author, update_memory
from engage.models import Author, EngageError, Post
from engage.propose import propose
from engage.store import author_path, load_author, write_json
from engage.voice import card_from_summary, looks_sensitive, summarize

HOST = "127.0.0.1"
PORT = 8787


def serve(data_dir: Path, fixtures_dir: Path, port: int = PORT) -> None:
    handler = _handler_factory(data_dir, fixtures_dir)
    server = ThreadingHTTPServer((HOST, port), handler)
    print(f"Engage is listening on http://{HOST}:{port}")
    print("Load extension/ as an unpacked extension. Open a LinkedIn profile and the voice memory updates. Open a post to draft. Nothing is posted.")
    print("Nothing is posted. Ctrl-C stops the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def _handler_factory(data_dir: Path, fixtures_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_OPTIONS(self) -> None:  # noqa: N802
            self._send(204, b"")

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/health":
                self._send_json({"ok": True})
                return
            if path == "/voices":
                self._send_json({"voices": _voice_list(data_dir, fixtures_dir)})
                return
            if path == "/memories":
                self._send_json({"memories": list_memories(data_dir)})
                return
            self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            try:
                body = self._read_json()
                if path == "/capture":
                    self._send_json(_capture(fixtures_dir, body))
                    return
                if path == "/harness":
                    self._send_json(_harness(data_dir, fixtures_dir, body))
                    return
                if path == "/voices/save":
                    self._send_json(_save(fixtures_dir, body))
                    return
                if path == "/draft":
                    self._send_json(_draft(data_dir, fixtures_dir, body))
                    return
                if path == "/review":
                    self._send_json(_review(data_dir, body))
                    return
            except EngageError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            except (json.JSONDecodeError, ValueError) as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json({"error": "not found"}, status=404)

        def log_message(self, fmt: str, *args) -> None:
            return

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise EngageError("capture is too large")
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise EngageError("expected an object")
            return payload

        def _send_json(self, payload: dict, status: int = 200) -> None:
            body = (json.dumps(payload) + "\n").encode("utf-8")
            self._send(status, body, "application/json")

        def _send(self, status: int, body: bytes, content_type: str = "text/plain") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            if body:
                self.wfile.write(body)

    return Handler


def _capture(fixtures_dir: Path, body: dict) -> dict:
    texts = body.get("texts")
    if not isinstance(texts, list) or not all(isinstance(item, str) for item in texts):
        raise EngageError("texts must be a list of strings")
    name = body.get("name") if isinstance(body.get("name"), str) else ""
    profile_url = body.get("profile_url") if isinstance(body.get("profile_url"), str) else ""
    if "linkedin.com" not in profile_url:
        raise EngageError("capture only accepts an open LinkedIn page")
    summary = summarize(name, profile_url, texts)
    existing = _existing(fixtures_dir, summary["id"])
    card = card_from_summary(summary, existing)
    return {
        "summary": summary,
        "card": card.to_dict(),
        "saved": False,
    }


def _harness(data_dir: Path, fixtures_dir: Path, body: dict) -> dict:
    texts = body.get("texts")
    if not isinstance(texts, list) or not all(isinstance(item, str) for item in texts):
        raise EngageError("texts must be a list of strings")
    name = body.get("name") if isinstance(body.get("name"), str) else ""
    profile_url = body.get("profile_url") if isinstance(body.get("profile_url"), str) else ""
    bio = body.get("bio") if isinstance(body.get("bio"), str) else ""
    use_model = body.get("live", True)
    result = update_memory(
        data_dir,
        name=name,
        profile_url=profile_url,
        texts=texts,
        bio=bio,
        drafter=_voice_drafter() if use_model else None,
    )
    author_id = result["id"]
    if result.get("updated") and "summary" in result:
        card = card_from_summary(result["summary"], None)
        if result["name"] and result["name"] != "Unknown":
            card.name = result["name"]
        write_json(data_dir / "authors" / f"{card.id}.json", card.to_dict())
        result["claims"] = 0
    else:
        result["claims"] = 0
    result.pop("summary", None)
    return result


def _voice_drafter():
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        return None
    try:
        return GeminiModel().draft
    except EngageError:
        return None


def _save(fixtures_dir: Path, body: dict) -> dict:
    card = body.get("card")
    if not isinstance(card, dict):
        raise EngageError("card is required")
    confirmed = Author.from_dict(card)
    write_json(author_path(fixtures_dir, confirmed.id), confirmed.to_dict())
    return {"saved": True, "id": confirmed.id, "name": confirmed.name}


def _draft(data_dir: Path, fixtures_dir: Path, body: dict) -> dict:
    author_id = body.get("author_id")
    text = body.get("text")
    if not isinstance(author_id, str) or not author_id.strip():
        raise EngageError("author_id is required")
    if not isinstance(text, str) or len(text.strip()) < 20:
        raise EngageError("the open post is too short to draft from")
    from engage.harness import author_from_memory

    author = author_from_memory(data_dir, author_id.strip())
    if author is None:
        raise EngageError("No recorded voice yet. Open their profile, then Activity, and scroll.")
    topic = author.topics[0] if author.topics else "general"
    post = Post(
        id="open_post",
        text=text.strip()[:4000],
        topic=topic,
        sensitivity="high" if looks_sensitive(text) else "normal",
        synthetic=False,
        note="Read from the LinkedIn page the person had open.",
    )
    inbox = data_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / "open_post.json"
    write_json(path, post.to_dict())
    proposal = propose(
        author.id,
        path,
        data_dir=data_dir,
        fixtures_dir=fixtures_dir,
        live=bool(body.get("live")),
        from_memory=True,
    )
    return proposal.to_dict()


def _review(data_dir: Path, body: dict) -> dict:
    proposal_id = body.get("proposal_id")
    action = body.get("action")
    if not isinstance(proposal_id, str) or not proposal_id.strip():
        raise EngageError("proposal_id is required")
    if not isinstance(action, str):
        raise EngageError("action is required")
    text = body.get("text") if isinstance(body.get("text"), str) else None
    rule = body.get("rule") if isinstance(body.get("rule"), str) else None
    decision, rule_row, handoff = decide(
        proposal_id.strip(),
        action.strip(),
        data_dir=data_dir,
        text=text,
        rule_text=rule,
    )
    return {
        "decision": decision.to_dict(),
        "rule": rule_row.to_dict() if rule_row else None,
        "handoff": handoff.to_dict() if handoff else None,
    }


def _existing(fixtures_dir: Path, author_id: str):
    try:
        return load_author(fixtures_dir, author_id)
    except EngageError:
        return None


def _existing_any(data_dir: Path, fixtures_dir: Path, author_id: str):
    try:
        return resolve_author(data_dir, fixtures_dir, author_id)
    except EngageError:
        return None


def _voice_list(data_dir: Path, fixtures_dir: Path) -> list[dict]:
    ids: list[str] = []
    for folder in (fixtures_dir / "authors", data_dir / "authors"):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            if path.stem not in ids:
                ids.append(path.stem)
    voices = []
    for author_id in ids:
        author = _existing_any(data_dir, fixtures_dir, author_id)
        if author is None:
            continue
        voices.append({"id": author.id, "name": author.name, "goal": author.goal})
    voices.sort(key=lambda item: item["name"].lower())
    return voices
