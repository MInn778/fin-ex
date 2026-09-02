import json
import sys
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR / "app"))

import brand_reference
from brand_reference import find_brand_candidates, get_brand_by_name, get_official_domains


def test_reference_json_is_utf8_and_has_required_entries():
    entries = json.loads((SERVICE_DIR / "data" / "brand_reference.json").read_text(encoding="utf-8"))
    assert len(entries) == 23
    assert {"KB국민은행", "토스뱅크", "NH농협카드", "정부24", "금융감독원"}.issubset(
        {entry["brand"] for entry in entries}
    )
    assert all({"brand", "category", "officialDomains", "aliases"} <= entry.keys() for entry in entries)


def test_alias_search_normalizes_case_spaces_and_punctuation():
    result = find_brand_candidates("Kakao-Bank를 사칭한 문구와 KB 국민은행 안내")
    assert {item["brand"] for item in result} >= {"카카오뱅크", "KB국민은행"}


def test_brand_lookup_and_domains():
    assert get_brand_by_name("kb 국민은행")["category"] == "BANK"
    assert get_official_domains("KB국민은행") == ["kbstar.com"]
    assert get_official_domains("없는 기관") == []


def test_missing_reference_has_clear_error(monkeypatch, tmp_path):
    brand_reference.load_brand_reference.cache_clear()
    monkeypatch.setattr(brand_reference, "REFERENCE_PATH", tmp_path / "missing.json")
    with pytest.raises(RuntimeError, match="missing"):
        brand_reference.load_brand_reference()
    brand_reference.load_brand_reference.cache_clear()
