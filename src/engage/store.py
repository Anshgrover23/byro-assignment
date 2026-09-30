from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from engage.models import Author, EngageError, Post

_SLUG = re.compile(r"^[a-z0-9_-]+$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_fixtures_dir() -> Path:
    return repo_root() / "fixtures"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EngageError(f"missing file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EngageError(f"expected an object in {path}")
    return payload


def author_path(fixtures_dir: Path, author_id: str) -> Path:
    if not _SLUG.fullmatch(author_id):
        raise EngageError("author id must be a slug of letters, numbers, _ or -")
    return fixtures_dir / "authors" / f"{author_id}.json"


def load_author(fixtures_dir: Path, author_id: str) -> Author:
    return Author.from_dict(read_json(author_path(fixtures_dir, author_id)))


def load_post(path: Path) -> Post:
    return Post.from_dict(read_json(path))


def save_record(data_dir: Path, collection: str, record_id: str, payload: dict[str, Any]) -> Path:
    if not _SLUG.fullmatch(record_id):
        raise EngageError(f"unsafe id for {collection}: {record_id}")
    path = data_dir / collection / f"{record_id}.json"
    write_json(path, payload)
    return path


def load_record(data_dir: Path, collection: str, record_id: str) -> dict[str, Any]:
    if not _SLUG.fullmatch(record_id):
        raise EngageError(f"unsafe id for {collection}: {record_id}")
    return read_json(data_dir / collection / f"{record_id}.json")


def list_records(data_dir: Path, collection: str) -> list[dict[str, Any]]:
    folder = data_dir / collection
    if not folder.is_dir():
        return []
    records = []
    for path in sorted(folder.glob("*.json")):
        records.append(read_json(path))
    return records
