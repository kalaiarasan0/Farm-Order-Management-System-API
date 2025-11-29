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

	- If `phonenumbers` is installed: parse, validate and return E.164 format.
	- If not installed: perform a permissive cleanup (digits and leading +)
	  and ensure a plausible length.

	Raises `ValueError` on invalid input.
	"""
	if value is None:
		return value
	v = str(value).strip()
	if not v:
		raise ValueError("empty phone number")

	if phonenumbers is None:
		# Lightweight fallback: keep digits and optional leading '+', then validate length
		cleaned = "+" + "".join(ch for ch in v if ch.isdigit()) if v.lstrip().startswith("+") else "".join(ch for ch in v if ch.isdigit())
		if cleaned.startswith("+"):
			digits = cleaned[1:]
		else:
			digits = cleaned
		if 7 <= len(digits) <= 15:
			return ("+" + digits) if not cleaned.startswith("+") and len(digits) <= 15 else cleaned
		raise ValueError("invalid phone number format; install 'phonenumbers' for robust validation")

	# Use phonenumbers for robust parsing/validation
	try:
		pn = phonenumbers.parse(v, None)
	except phonenumbers.NumberParseException as exc:
		raise ValueError("invalid phone number") from exc

	if not phonenumbers.is_valid_number(pn):
		raise ValueError("invalid phone number")

	return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)