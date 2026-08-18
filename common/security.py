"""Helpers for keeping credentials out of logs and test reports."""

import json
import re
from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SENSITIVE_KEYS = {
    'access_token',
    'authorization',
    'cookie',
    'password',
    'passwd',
    'secret',
    'sign',
    'token',
}


def _is_sensitive_key(key):
    normalized = str(key).casefold().replace('-', '_')
    return any(part in normalized for part in SENSITIVE_KEYS)


def redact_sensitive(value):
    """Return a redacted copy of nested request or response data."""
    if isinstance(value, Mapping):
        return {
            key: '<redacted>' if _is_sensitive_key(key) else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    return value


def redact_url(url):
    """Redact sensitive query-string values without changing other URL parts."""
    if not isinstance(url, str):
        return url
    split_url = urlsplit(url)
    safe_query = urlencode([
        (key, '<redacted>' if _is_sensitive_key(key) else value)
        for key, value in parse_qsl(split_url.query, keep_blank_values=True)
    ])
    return urlunsplit((split_url.scheme, split_url.netloc, split_url.path, safe_query, split_url.fragment))


def redact_text(text):
    """Redact structured JSON and common credential patterns in plain text."""
    if not isinstance(text, str):
        return text
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        redacted = re.sub(r'(?i)Bearer\s+[^\s,;]+', 'Bearer <redacted>', text)
        return re.sub(
            r'(?i)(access_token|authorization|cookie|password|passwd|secret|sign|token)'
            r'(["\s:=]+)([^&\s,;}]+)',
            r'\1\2<redacted>',
            redacted,
        )
    return json.dumps(redact_sensitive(parsed), ensure_ascii=False)
