from __future__ import annotations

import os

from engage.models import EngageError

# Tried in order when the chosen model answers 429 or 503.
# gemini-2.5-flash is omitted: this key can list it, but new accounts cannot generate with it.
_FALLBACK_MODELS = (
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
)


class GeminiModel:
    """Live drafter. Imported only when propose --live is used."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise EngageError("GEMINI_API_KEY is missing. Add it to the environment or .env.")
        self.api_key = key
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

    def draft(self, prompt: str) -> str:
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError as exc:
            raise EngageError("Gemini support is not installed. Run: pip install -e '.[live]'") from exc
        client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        failures: list[str] = []
        for name in self._candidates():
            try:
                response = client.models.generate_content(
                    model=name,
                    contents=prompt,
                    config=config,
                )
            except errors.APIError as exc:
                if not _overloaded(exc):
                    raise EngageError(f"Gemini request failed for {name}: {exc}") from exc
                failures.append(f"{name}: {exc}")
                continue
            text = getattr(response, "text", None)
            if isinstance(text, str) and text.strip():
                self.model_name = name
                return text
            failures.append(f"{name}: empty draft")
        detail = "; ".join(failures) if failures else "no model was tried"
        raise EngageError(f"Gemini is busy or returned nothing. Tried {detail}")

    def _candidates(self) -> list[str]:
        names = [self.model_name]
        for name in _FALLBACK_MODELS:
            if name not in names:
                names.append(name)
        return names


def _overloaded(exc: Exception) -> bool:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code in (429, 503):
        return True
    text = str(exc)
    return " 503 " in f" {text} " or "429" in text or "UNAVAILABLE" in text or "RESOURCE_EXHAUSTED" in text
