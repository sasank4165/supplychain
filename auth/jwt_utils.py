"""Lightweight JWT helpers to avoid external dependency in local/test runs."""
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, Dict, Optional


class InvalidTokenError(Exception):
    """Raised when a token cannot be decoded or is malformed."""


class ExpiredSignatureError(InvalidTokenError):
    """Raised when an ``exp`` claim is in the past."""


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def get_unverified_header(token: str) -> Dict[str, Any]:
    """Return the header portion of a JWT without verifying the signature."""
    try:
        header_segment = token.split(".")[0]
        return json.loads(_b64url_decode(header_segment))
    except Exception as exc:  # pragma: no cover - defensive
        raise InvalidTokenError("Invalid token header") from exc


def decode(
    token: str,
    key: Optional[str] = None,
    algorithms: Optional[list[str]] = None,
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Decode a JWT payload.

    Signature verification is intentionally skipped in this lightweight helper,
    but expiration is enforced when present unless ``verify_signature`` is
    explicitly disabled in ``options``.
    """
    verify_signature = True
    if options is not None and options.get("verify_signature") is False:
        verify_signature = False

    try:
        header_segment, payload_segment, *_signature = token.split(".")
        payload = json.loads(_b64url_decode(payload_segment))
    except Exception as exc:  # pragma: no cover - defensive
        raise InvalidTokenError("Invalid token format") from exc

    exp = payload.get("exp")
    if verify_signature and exp is not None:
        if datetime.utcnow().timestamp() > float(exp):
            raise ExpiredSignatureError("Token expired")

    # This helper is primarily for offline testing; full signature
    # verification is handled in production via managed services.
    return payload


class _RSAAlgorithm:
    """Placeholder to mirror the PyJWT API when importing."""

    @staticmethod
    def from_jwk(jwk_json: str) -> Dict[str, Any]:
        return json.loads(jwk_json)


class algorithms:
    """Namespace shim to mimic ``jwt.algorithms`` used in code."""

    RSAAlgorithm = _RSAAlgorithm
