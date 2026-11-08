"""
Optional LLM connector (Stage 4 / 5).

The project works WITHOUT any LLM: question answering then falls back to
"retrieval-only" mode (best passages from the document, no generated text).
If you configure a provider through environment variables, the same code
sends the retrieved passages to that LLM and returns a grounded answer.

Providers (set before starting uvicorn):

  Anthropic (Claude API)
      set LLM_PROVIDER=anthropic
      set ANTHROPIC_API_KEY=your-key
      set ANTHROPIC_MODEL=claude-sonnet-5-5      (optional)

  Any OpenAI-compatible server, e.g. a local Ollama on your laptop
      set LLM_PROVIDER=openai
      set OPENAI_BASE_URL=http://localhost:11434/v1   (default = Ollama)
      set OPENAI_MODEL=llama3.2                        (name of your model)
      set OPENAI_API_KEY=...                           (not needed for Ollama)

Only the standard library is used (urllib), so nothing extra to install.
Note: when a hosted provider is used, the retrieved passages of the
document are sent to that provider. Do not use it for confidential
documents unless that is acceptable to you.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

logger = logging.getLogger("llm")

TIMEOUT_SECONDS = 60
MAX_OUTPUT_TOKENS = 600


class LLMError(Exception):
    """The LLM call failed (network, key, model name...)."""


def provider_name() -> str:
    return os.environ.get("LLM_PROVIDER", "none").strip().lower()


def is_configured() -> bool:
    p = provider_name()
    if p == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    if p == "openai":
        return bool(os.environ.get("OPENAI_MODEL"))
    return False


def describe() -> str:
    """Short label for the UI, e.g. 'anthropic:claude-sonnet-5-5'."""
    p = provider_name()
    if not is_configured():
        return "none"
    if p == "anthropic":
        return f"anthropic:{os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-5-5')}"
    return f"openai-compatible:{os.environ.get('OPENAI_MODEL')}"


def _post(url: str, headers: dict, payload: dict) -> dict:
    # Some API gateways (e.g. Cloudflare in front of Groq) reject the default
    # "Python-urllib" User-Agent with HTTP 403, so send an explicit one.
    headers = {"User-Agent": "legal-document-analyzer/6.0", "Accept": "application/json", **headers}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            detail = ""
        logger.warning("LLM HTTP %s: %s", exc.code, detail)
        hint = f" Service message: {detail}" if detail else ""
        raise LLMError(
            f"The LLM service returned an error (HTTP {exc.code}). Check the API key and model name.{hint}") from exc
    except Exception as exc:
        raise LLMError("The LLM service could not be reached.") from exc


def generate(system: str, user: str) -> str:
    """Send one prompt to the configured provider and return the text reply."""
    if not is_configured():
        raise LLMError("No LLM is configured.")
    p = provider_name()
    if p == "anthropic":
        data = _post(
            "https://api.anthropic.com/v1/messages",
            {"content-type": "application/json",
             "x-api-key": os.environ["ANTHROPIC_API_KEY"],
             "anthropic-version": "2023-06-01"},
            {"model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
             "max_tokens": MAX_OUTPUT_TOKENS, "system": system,
             "messages": [{"role": "user", "content": user}]},
        )
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    else:
        base = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1").rstrip("/")
        headers = {"content-type": "application/json"}
        if os.environ.get("OPENAI_API_KEY"):
            headers["authorization"] = "Bearer " + os.environ["OPENAI_API_KEY"]
        data = _post(
            base + "/chat/completions", headers,
            {"model": os.environ["OPENAI_MODEL"], "max_tokens": MAX_OUTPUT_TOKENS,
             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        )
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LLMError("The LLM service returned an unexpected reply.") from exc
    text = (text or "").strip()
    if not text:
        raise LLMError("The LLM returned an empty answer.")
    return text
