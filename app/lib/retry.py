# app/lib/retry.py
"""
Retry decorator for all LLM calls.
Exponential backoff with jitter.
Applied via @llm_retry on every agent function that calls an LLM.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import structlog

log = structlog.get_logger()

P = ParamSpec("P")
R = TypeVar("R")


def llm_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """
    Retry decorator for async LLM calls.
    Uses exponential backoff with jitter to avoid thundering herd.

    Usage:
        @llm_retry(max_retries=3)
        async def call_something():
            ...
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        log.error(
                            "llm_retry.exhausted",
                            func=func.__name__,
                            attempts=max_retries,
                            error=str(e),
                        )
                        raise

                    delay = min(
                        base_delay * (2**attempt) + random.uniform(0, 0.5),
                        max_delay,
                    )
                    log.warning(
                        "llm_retry.retrying",
                        func=func.__name__,
                        attempt=attempt + 1,
                        delay=round(delay, 2),
                        error=str(e),
                    )
                    await asyncio.sleep(delay)

            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


# Specific retry configs per use case
standup_retry = llm_retry(max_retries=3, base_delay=1.0)  # fast recovery
sprint_retry = llm_retry(max_retries=2, base_delay=2.0)  # K2 can be slow
voice_retry = llm_retry(max_retries=2, base_delay=0.5)  # voice needs speed
