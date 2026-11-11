from __future__ import annotations

import json
import logging
import os
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from .json_utils import parse_json_object
from .models import get_llm

logger = logging.getLogger(__name__)


class EmptyLLMReply(RuntimeError):
    """The model kept returning no usable text after every retry."""


def _max_attempts() -> int:
    try:
        return max(1, int(os.getenv("LLM_MAX_ATTEMPTS", "3")))
    except ValueError:
        return 3


async def invoke_text(messages: list[BaseMessage]) -> str:
    """Call the model and return its reply text, retrying when the reply is empty.

    Reasoning models on the hosted NVIDIA API sometimes put the whole answer in a
    separate reasoning field and return empty content. Retrying usually gets a
    normal reply.
    """

    llm = get_llm()
    attempts = _max_attempts()
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = await llm.ainvoke(messages)
        except Exception as exc:
            last_error = exc
            logger.warning("LLM call failed (attempt %d of %d): %s", attempt, attempts, type(exc).__name__)
            continue
        text = (response.text or "").strip()
        if text:
            return text
        logger.warning("LLM returned an empty reply (attempt %d of %d)", attempt, attempts)
    if last_error is not None:
        raise EmptyLLMReply(f"No usable reply after {attempts} attempts; last error: {type(last_error).__name__}")
    raise EmptyLLMReply(f"The model returned an empty reply {attempts} times.")


async def invoke_json(system_prompt: str, user_input: str, schema_hint: dict[str, Any]) -> dict[str, Any]:
    """Ask the model for JSON and parse the response into a dictionary.

    Retries when the call fails or times out, or the reply is empty or not a JSON object. Returns an empty
    dict if every attempt fails, so callers fall back to their defaults
    instead of failing the whole request.
    """

    llm = get_llm()
    schema_text = json.dumps(schema_hint, indent=2)
    messages = [
        SystemMessage(
            content=(
                f"{system_prompt}\n\n"
                "Return only a JSON object with no prose before or after it.\n"
                f"JSON schema example:\n{schema_text}"
            )
        ),
        HumanMessage(content=user_input),
    ]

    attempts = _max_attempts()
    for attempt in range(1, attempts + 1):
        try:
            response = await llm.ainvoke(messages)
        except Exception as exc:
            logger.warning("LLM call failed (attempt %d of %d): %s", attempt, attempts, type(exc).__name__)
            continue
        text = (response.text or "").strip()
        if not text:
            logger.warning("LLM returned an empty reply (attempt %d of %d)", attempt, attempts)
            continue
        try:
            return parse_json_object(text)
        except ValueError:
            logger.warning("LLM reply was not a JSON object (attempt %d of %d)", attempt, attempts)

    logger.warning("No usable JSON from the LLM after %d attempts; using defaults", attempts)
    return {}
