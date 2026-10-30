"""Shared keyboard helpers."""


def truncate(text: str, limit: int = 40) -> str:
    """Cut long text with an ellipsis so it fits a Telegram button."""
    return text if len(text) <= limit else text[: limit - 1] + "…"
