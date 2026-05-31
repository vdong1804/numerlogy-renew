"""Build the system + user prompt sent to Gemini.

Keeps the system instruction as a CONSTANT string so Gemini's prompt cache
can deduplicate across requests. Variable parts (KB excerpts + history +
user question) go into the user message.

Returns a tuple (system, contents, chunks) where `chunks` is the ordered list
used for citation mapping later — index `i` in the list maps to `[i+1]` in
the prompt.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from app.config import settings
from app.db.models.chat.message import ChatMessage
from app.schemas.chat.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

# Constant system prompt — cacheable by Gemini after first call.
# Admin can override at runtime via ChatSystemSetting (key=chat_system_prompt);
# when no override row exists, this constant is used so the Gemini explicit
# prompt cache stays stable for the common path.
SYSTEM_PROMPT = """You are a numerology expert assistant. Answer ONLY based on the provided KNOWLEDGE BASE excerpts below.

RULES:
1. Cite sources inline using [1], [2]... matching the numbered excerpts.
2. If KNOWLEDGE BASE has insufficient information, reply EXACTLY: "Tôi không có đủ thông tin để trả lời câu hỏi này."
3. Answer in Vietnamese unless the user writes in English.
4. Be concise but complete. Use bullet points for lists.
5. Do not invent numerology meanings not present in the excerpts.
"""


def resolve_system_prompt(override: Optional[str]) -> str:
    """Return the override when it's a non-empty, non-whitespace string;
    otherwise fall back to the in-code SYSTEM_PROMPT constant.

    Centralized so build_prompt and prompt-cache key computation use the same
    resolution rule.
    """
    if override is not None and override.strip():
        return override
    return SYSTEM_PROMPT

# Rough budget warning thresholds (tiktoken cl100k approximation).
FLASH_BUDGET = 16_000
PRO_BUDGET = 32_000


@dataclass
class BuiltPrompt:
    system: str
    user_content: str
    chunks: list[RetrievedChunk]
    approx_tokens: int


def sanitize_user_text(text: str) -> str:
    """Strip role-injection tokens so a hostile user can't impersonate system."""
    bad = ("<|system|>", "<|assistant|>", "<|user|>", "<|im_start|>", "<|im_end|>")
    out = text
    for tok in bad:
        out = out.replace(tok, "")
    return out.strip()


def build_prompt(
    user_message: str,
    chunks: list[RetrievedChunk],
    history: Optional[list[ChatMessage]] = None,
    history_max: Optional[int] = None,
    system_prompt_override: Optional[str] = None,
) -> BuiltPrompt:
    """Assemble system + KB excerpts + history + user question.

    ``system_prompt_override`` (Phase 07) lets an admin-tuned prompt take the
    place of the in-code constant. Empty / whitespace falls back to constant.
    """
    user_message = sanitize_user_text(user_message)
    max_hist = history_max if history_max is not None else settings.history_max_messages
    recent = (history or [])[-max_hist:] if max_hist > 0 else []
    system = resolve_system_prompt(system_prompt_override)

    parts: list[str] = []
    if chunks:
        parts.append("KNOWLEDGE BASE:")
        for i, c in enumerate(chunks, start=1):
            ref = f"{c.source_type}/{c.source_ref}"
            parts.append(f"[{i}] (source: {ref}) {c.content}")
        parts.append("")
    else:
        parts.append("KNOWLEDGE BASE: (no relevant excerpts found)\n")

    if recent:
        parts.append("CONVERSATION HISTORY:")
        for m in recent:
            role = "User" if m.role == "user" else "Assistant"
            parts.append(f"{role}: {m.content}")
        parts.append("")

    parts.append(f"USER QUESTION:\n{user_message}")
    user_content = "\n".join(parts)
    approx = _rough_token_count(system) + _rough_token_count(user_content)

    if approx > PRO_BUDGET:
        logger.warning("prompt approx %d tokens exceeds Pro budget %d", approx, PRO_BUDGET)
    elif approx > FLASH_BUDGET:
        logger.info("prompt approx %d tokens exceeds Flash budget", approx)

    return BuiltPrompt(
        system=system,
        user_content=user_content,
        chunks=chunks,
        approx_tokens=approx,
    )


def _rough_token_count(text: str) -> int:
    """~4 chars per token heuristic — fast, no tiktoken dep at runtime."""
    return max(1, len(text) // 4)
