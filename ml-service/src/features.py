"""Deterministic URL features with an explicit security rationale."""

from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from urllib.parse import parse_qsl, unquote, urlsplit

SUSPICIOUS_TLDS = {
    "buzz", "click", "country", "fit", "gq", "info", "kim", "link",
    "ml", "online", "rest", "support", "tk", "top", "work", "xyz",
}
FINANCIAL_TERMS = {
    "bank", "banking", "card", "credit", "finance", "kb", "kbank",
    "login", "nh", "pay", "secure", "shinhan", "toss", "verify", "woori",
}
SHORTENERS = {
    "bit.ly", "cutt.ly", "is.gd", "ow.ly", "rebrand.ly", "shorturl.at", "t.co", "tinyurl.com",
}

FEATURE_NAMES = [
    "url_length", "hostname_length", "path_length", "query_length",
    "dot_count", "hyphen_count", "digit_ratio", "special_char_ratio",
    "url_entropy", "subdomain_depth", "query_param_count", "percent_encoding_count",
    "has_ip_host", "has_punycode", "has_at_symbol", "uses_https",
    "uses_nonstandard_port", "has_suspicious_tld", "has_financial_term", "uses_shortener",
]


def _normalized_url(raw_url: str) -> str:
    value = raw_url.strip()
    return value if "://" in value else f"http://{value}"


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    size = len(value)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def extract_features(raw_url: str) -> dict[str, float]:
    if not raw_url or not raw_url.strip():
        raise ValueError("URL must not be blank")

    url = _normalized_url(raw_url)
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise ValueError("URL must contain a hostname")

    try:
        ipaddress.ip_address(hostname.strip("[]"))
        has_ip_host = 1.0
    except ValueError:
        has_ip_host = 0.0

    labels = [label for label in hostname.split(".") if label]
    subdomain_depth = max(0, len(labels) - 2)
    tld = labels[-1] if labels else ""
    decoded = unquote(url).lower()
    alnum = sum(character.isalnum() for character in url)
    digits = sum(character.isdigit() for character in url)
    special = len(url) - alnum

    try:
        port = parsed.port
        nonstandard_port = port is not None and port not in {80, 443}
    except ValueError:
        nonstandard_port = True

    return {
        "url_length": float(len(url)),
        "hostname_length": float(len(hostname)),
        "path_length": float(len(parsed.path)),
        "query_length": float(len(parsed.query)),
        "dot_count": float(url.count(".")),
        "hyphen_count": float(url.count("-")),
        "digit_ratio": digits / max(len(url), 1),
        "special_char_ratio": special / max(len(url), 1),
        "url_entropy": _entropy(url),
        "subdomain_depth": float(subdomain_depth),
        "query_param_count": float(len(parse_qsl(parsed.query, keep_blank_values=True))),
        "percent_encoding_count": float(len(re.findall(r"%[0-9a-fA-F]{2}", url))),
        "has_ip_host": has_ip_host,
        "has_punycode": float("xn--" in hostname),
        "has_at_symbol": float("@" in url),
        "uses_https": float(parsed.scheme.lower() == "https"),
        "uses_nonstandard_port": float(nonstandard_port),
        "has_suspicious_tld": float(tld in SUSPICIOUS_TLDS),
        "has_financial_term": float(any(term in decoded for term in FINANCIAL_TERMS)),
        "uses_shortener": float(hostname in SHORTENERS),
    }


def feature_vector(raw_url: str) -> list[float]:
    features = extract_features(raw_url)
    return [features[name] for name in FEATURE_NAMES]

