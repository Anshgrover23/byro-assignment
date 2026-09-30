from __future__ import annotations

import json
from pathlib import Path

from engage.model import ScriptedModel
from engage.store import default_fixtures_dir

FIXTURES = default_fixtures_dir()
RICO_COMMENT = "The named author decides what goes live."
RICO_CLAIM = ["named_author_decides"]


def post(name: str) -> Path:
    return FIXTURES / "posts" / name


def scripted(comment: str, claim_ids: list[str], reason: str = "fits the goal") -> ScriptedModel:
    return ScriptedModel(json.dumps({"comment": comment, "claim_ids": claim_ids, "reason": reason}))
