"""Ask Jev (TypeSafe) to pick the right option for a quiz question.

Answers are cached in jev_cache.json, keyed by the question plus its options
(order does not matter), so the same question is only sent to the API once.

Needs the TYPESAFE_API_KEY environment variable.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

from typesafe_sdk import AsyncTypeSafeClient, Choice

MODEL = "jev-latest"
CACHE_FILE = Path(__file__).with_name("jev_cache.json")
INSTRUCTIONS = "Pick the correct answer to this quiz question."

_cache: dict[str, dict] | None = None


def _cache_key(question: str, options: list[str]) -> str:
    # Options are sorted so the same question with shuffled options hits the cache.
    return json.dumps([question, sorted(options)], ensure_ascii=False)


def _load_cache() -> dict[str, dict]:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError:
            _cache = {}
    return _cache


def _save_cache() -> None:
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(_load_cache(), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CACHE_FILE)


async def ask(question: str, options: list[str]) -> str:
    """Return the option Jev considers correct. Uses the cache when possible."""
    if not options:
        raise ValueError("options must not be empty")

    cache = _load_cache()
    key = _cache_key(question, options)
    if key in cache:
        return cache[key]["answer"]

    async with AsyncTypeSafeClient(model=MODEL) as client:
        response = await client.system_one(
            state=question,
            questions={
                "answer": Choice(
                    instructions=INSTRUCTIONS,
                    criteria={option: None for option in options},
                ),
            },
        )

    result = response.choices["answer"]
    cache[key] = {"answer": result.choice, "confidence": result.confidence}
    _save_cache()
    return result.choice


def is_cached(question: str, options: list[str]) -> bool:
    return _cache_key(question, options) in _load_cache()


def cli_entry() -> None:
    parser = argparse.ArgumentParser(description="Ask Jev to pick the right option")
    parser.add_argument("question")
    parser.add_argument("options", nargs="+")
    args = parser.parse_args()

    cached = is_cached(args.question, args.options)
    answer = asyncio.run(ask(args.question, args.options))
    print(f"{answer}{'  (cache)' if cached else ''}")


if __name__ == "__main__":
    cli_entry()
