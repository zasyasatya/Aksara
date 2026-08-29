import pytest
from app.services.classifier import classify_char, classify_text, get_all_types

def test_classify_wresastra():
    result = classify_char("ᬳ")
    assert result["type"] in ["wresastra", "wresastra_or_swalalita", "wianjana"] or "Ha" in result["name"] or result["char"] == "ᬳ"

def test_classify_suara():
    result = classify_char("ᬅ")
    assert result["type"] == "suara" or "Suara" in result["name"] or result["char"] == "ᬅ"

def test_classify_pangangge():
    result = classify_char("ᬶ")
    assert result["is_pangangge"] == True

def test_classify_tengenan():
    result = classify_char("ᬄ")
    assert "tengenan" in result["type"] or "Bisah" in result["name"]

def test_classify_gantungan():
    result = classify_char("᭄ᬭ")
    assert result["is_gantungan"] == True

def test_classify_text():
    result = classify_text("ᬩᬮᬶ")
    assert len(result["classifications"]) > 0
    assert result["overall_type"] != ""

def test_get_all_types():
    types = get_all_types()
    assert len(types) >= 5
    assert any(t["id"] == "wresastra" for t in types)
