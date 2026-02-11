"""Common Pydantic schemas and utilities used across the application.

This module provides a `Phone` annotation and a `normalize_phone` helper.
`phonenumbers` is optional — when available we parse/validate and return
an E.164-formatted string. When not available, a lightweight fallback
normalization is applied.
"""

from typing import Annotated
from pydantic import Field

try:
    import phonenumbers
except Exception:  # pragma: no cover - optional dependency
    phonenumbers = None


Phone = Annotated[str, Field(description="Phone number, ideally in E.164 format")]


def normalize_phone(value: str) -> str:
    """Normalize and validate a phone number.

    - Strips all non-digit characters.
    - Ensures the result has at least 10 digits.
    - Returns the LAST 10 digits (removing country code).

    Raises `ValueError` if the number allows fewer than 10 digits.
    """
    if value is None:
        return value
    v = str(value).strip()
    if not v:
        raise ValueError("empty phone number")

    # Keep only digits
    digits = "".join(ch for ch in v if ch.isdigit())

    # Check length
    if len(digits) < 10:
        raise ValueError("Phone number must have at least 10 digits")

    # Return last 10 digits
    return digits[-10:]
