from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from .service import run_graph_response


load_dotenv()
load_dotenv(Path(__file__).with_name(".env"))


async def run_query(user_input: str) -> str:
    return await run_graph_response(user_input)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph LLM Ad Engine runtime.")
    parser.add_argument("query", help="User request to route through the graph.")
    args = parser.parse_args()
    response = asyncio.run(run_query(args.query))
    print(response)


if __name__ == "__main__":
    main()
