"""LLM cost logging — used by app.lib.llm."""

import structlog

log = structlog.get_logger()


def log_llm_cost(model: str, input_tokens: int, output_tokens: int) -> None:
    """Record token usage for a completion (billing / observability)."""
    log.info(
        "llm.cost",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
