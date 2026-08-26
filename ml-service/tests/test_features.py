import pytest

from src.features import FEATURE_NAMES, extract_features, feature_vector


def test_extracts_security_signals():
    result = extract_features("http://xn--secure-bank-9za.xyz:8080/login?verify=1")
    assert result["has_punycode"] == 1.0
    assert result["has_suspicious_tld"] == 1.0
    assert result["has_financial_term"] == 1.0
    assert result["uses_nonstandard_port"] == 1.0
    assert result["uses_https"] == 0.0


def test_vector_schema_is_stable():
    assert len(feature_vector("https://example.com")) == len(FEATURE_NAMES)


def test_detects_financial_brand_domain_mismatch():
    result = extract_features("http://kb-login-security.xyz/verify")
    assert result["has_financial_term"] == 1.0
    assert result["official_financial_domain"] == 0.0
    assert result["brand_domain_mismatch"] == 1.0


def test_recognizes_official_financial_domain():
    result = extract_features("https://www.kbstar.com/")
    assert result["official_financial_domain"] == 1.0
    assert result["brand_domain_mismatch"] == 0.0


def test_blank_url_is_rejected():
    with pytest.raises(ValueError):
        extract_features("   ")
