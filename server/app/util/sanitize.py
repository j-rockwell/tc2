from typing import Union, List
import re

_allowed_pattern = re.compile(r"[^a-zA-Z0-9\-]+")

def _sanitize_str(value: str) -> str:
    cleaned = value.lower()
    cleaned = _allowed_pattern.sub("", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip("-")

def sanitize_str(text: str) -> str:
    return _sanitize_str(text)

def sanitize_str_list(text: List[str]) -> List[str]:
    return [_sanitize_str(t) for t in text if isinstance(t, str)]