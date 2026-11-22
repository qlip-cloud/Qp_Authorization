"""Redaction helpers for request diagnostics.

This module is intentionally free of Frappe imports so it can be unit tested
without a site context. Callers must never pass raw secrets to the log; the
helpers below only expose structural metadata (keys, sizes, status codes).
"""

import json

try:
    from urllib.parse import urlsplit
except ImportError:  # pragma: no cover - Python 2 compatibility fallback
    from urlparse import urlsplit


REDACTED = "***"

SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "session",
    "code",
)

ERROR_DETAIL_KEYS = (
    "error",
    "error_codes",
    "correlation_id",
    "trace_id",
)


def is_sensitive_key(key):
    """Return True when a mapping key may contain a credential or token."""

    normalized = str(key or "").lower().replace("-", "_")

    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def redact(value):
    """Return a copy of value with sensitive mapping entries redacted."""

    if isinstance(value, dict):
        return {
            key: (REDACTED if is_sensitive_key(key) else redact(item))
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]

    return value


def sanitize_url(url):
    """Return scheme, host, port and path only (no query, userinfo or fragment)."""

    try:
        parts = urlsplit(str(url or ""))
    except Exception:
        return "<invalid-url>"

    if not parts.scheme or not parts.hostname:
        return "<invalid-url>"

    host = parts.hostname

    try:
        port = parts.port
    except ValueError:
        port = None

    if port:
        host = "{0}:{1}".format(host, port)

    return "{0}://{1}{2}".format(parts.scheme, host, parts.path or "/")


def summarize_headers(headers):
    """Return header names only; values may contain credentials."""

    return sorted(str(name) for name in (headers or {}).keys())


def summarize_payload(payload):
    """Return structural metadata only, never payload values."""

    if isinstance(payload, dict):
        return {
            "type": "mapping",
            "keys": sorted(str(key) for key in payload.keys()),
            "bytes": len(_serialize(payload)),
        }

    if isinstance(payload, (list, tuple)):
        return {"type": "sequence", "length": len(payload)}

    return {"type": type(payload).__name__, "bytes": len(str(payload or ""))}


def summarize_response(response):
    """Return status, reason, body size and JSON key names only."""

    body = getattr(response, "text", "") or ""
    status = getattr(response, "status_code", None)
    reason = getattr(response, "reason", "") or ""

    return {
        "status": status,
        "reason": str(reason)[:200],
        "bytes": len(body),
        "json_keys": _json_keys(body),
    }


def summarize_error_response(payload):
    """Extract safe OAuth/API error fields without tokens or raw bodies."""

    if not isinstance(payload, dict):
        return "sin detalle"

    parts = []

    for key in ERROR_DETAIL_KEYS:
        value = payload.get(key)

        if value:
            parts.append("{0}={1}".format(key, str(value)[:200]))

    return "; ".join(parts) or "sin detalle"


def describe_http_error(response):
    """Describe an HTTP error using status plus safe JSON error fields."""

    status = getattr(response, "status_code", None)
    body = getattr(response, "text", "") or ""

    try:
        payload = json.loads(body)
    except Exception:
        return "HTTP {0}".format(status)

    return "HTTP {0}: {1}".format(status, summarize_error_response(payload))


def build_request_log(method, url, payload=None, headers=None, response=None, error=None):
    """Build a redacted diagnostic message for the Error Log."""

    lines = [
        "method={0}".format(method or ""),
        "url={0}".format(sanitize_url(url)),
        "payload={0}".format(
            json.dumps(summarize_payload(payload), sort_keys=True)
        ),
        "headers={0}".format(
            json.dumps(summarize_headers(headers), sort_keys=True)
        ),
    ]

    if response is not None:
        lines.append(
            "response={0}".format(
                json.dumps(summarize_response(response), sort_keys=True)
            )
        )

    if error is not None:
        lines.append("error={0}".format(type(error).__name__))

    return "\n".join(lines)


def _json_keys(body):
    if not body:
        return []

    try:
        payload = json.loads(body)
    except Exception:
        return []

    if isinstance(payload, dict):
        return sorted(str(key) for key in payload.keys())

    return ["<non-mapping>"]


def _serialize(value):
    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)
