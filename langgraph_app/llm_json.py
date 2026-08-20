from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .json_utils import parse_json_object
from .models import get_llm


async def invoke_json(system_prompt: str, user_input: str, schema_hint: dict[str, Any]) -> dict[str, Any]:
    """Ask the model for JSON and parse the response into a dictionary."""

    llm = get_llm()
    schema_text = json.dumps(schema_hint, indent=2)
    response = await llm.ainvoke(
        [
            SystemMessage(
                content=(
                    f"{system_prompt}\n\n"
                    "Return only a JSON object with no prose before or after it.\n"
                    f"JSON schema example:\n{schema_text}"
                )
            ),
            HumanMessage(content=user_input),
        ]
    )
    return parse_json_object(response.text)
