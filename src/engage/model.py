from __future__ import annotations

from typing import Protocol


class ModelAdapter(Protocol):
    def draft(self, prompt: str) -> str: ...


class ScriptedModel:
    """Returns a fixed string. Tests use this so the proof needs no API key."""

    def __init__(self, output: str) -> None:
        self.output = output
        self.prompts: list[str] = []

    def draft(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.output
