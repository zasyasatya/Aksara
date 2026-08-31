import json
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "aksara_master.json", "r", encoding="utf-8") as f:
    MASTER = json.load(f)

# Build lookup
LOOKUP = {}

for category, items in MASTER.items():
    for item in items:
        bali_char = item.get("bali", "")
        if bali_char:
            # Handle multi-char like gantungan forms
            LOOKUP[bali_char] = {
                **item,
                "category_group": category
            }
        # Also index by id
        if "id" in item:
            LOOKUP[item["id"]] = item

# Additional manual entries for gantungan forms
GANTUNGAN_EXTRAS = {
    "᭄ᬓ": {"name": "Gantungan Ka", "latin": "ka", "type": "gantungan", "base": "ᬓ"},
    "᭄ᬭ": {"name": "Cakra - Gantungan Ra", "latin": "ra", "type": "pangangge_aksara", "subtype": "cakra"},
    "᭄ᬬ": {"name": "Nania - Gantungan Ya", "latin": "ya", "type": "pangangge_aksara", "subtype": "nania"},
    "᭄ᬯ": {"name": "Suku Kembung - Gantungan Wa", "latin": "wa", "type": "pangangge_aksara"},
    "᭄ᬮ": {"name": "Gantungan La", "latin": "la", "type": "pangangge_aksara"},
}

def classify_char(char: str) -> Dict:
    """Classify single Balinese char or gantungan"""
    if char in LOOKUP:
        item = LOOKUP[char]
        return {
            "char": char,
            "unicode": f"U+{ord(char):04X}" if len(char)==1 else " ".join([f"U+{ord(c):04X}" for c in char]),
            "latin": item.get("latin", ""),
            "name": item.get("name", ""),
            "type": item.get("type", item.get("category_group", "unknown")),
            "category": item.get("category", ""),
            "warga": item.get("warga", ""),
            "description": item.get("description", ""),
            "gantungan_form": item.get("gantungan", ""),
            "is_gantungan": "gantungan" in item.get("type", "") or char.startswith("᭄"),
            "is_pangangge": "pangangge" in item.get("type", "") or item.get("category_group", "").startswith("pangangge"),
            "examples": item.get("examples", []),
        }
    if char in GANTUNGAN_EXTRAS:
        extra = GANTUNGAN_EXTRAS[char]
        return {
            "char": char,
            "unicode": " ".join([f"U+{ord(c):04X}" for c in char]),
            "latin": extra["latin"],
            "name": extra["name"],
            "type": extra["type"],
            "description": extra["name"],
            "is_gantungan": True,
            "is_pangangge": "pangangge" in extra["type"],
        }
    
    # Try to detect by unicode range
    if len(char) == 1:
        cp = ord(char)
        if 0x1B00 <= cp <= 0x1B7F:
            # Balinese block
            if 0x1B13 <= cp <= 0x1B33:
                return {
                    "char": char,
                    "unicode": f"U+{cp:04X}",
                    "latin": "unknown",
                    "name": "Aksara Wianjana",
                    "type": "wresastra_or_swalalita",
                    "description": "Aksara Bali dalam blok Wianjana",
                    "is_gantungan": False,
                    "is_pangangge": False
                }
            elif 0x1B05 <= cp <= 0x1B12:
                return {
                    "char": char,
                    "unicode": f"U+{cp:04X}",
                    "latin": "vowel",
                    "name": "Aksara Suara",
                    "type": "suara",
                    "description": "Aksara Suara (vokal independen)",
                    "is_gantungan": False,
                    "is_pangangge": False
                }
            elif 0x1B35 <= cp <= 0x1B44:
                return {
                    "char": char,
                    "unicode": f"U+{cp:04X}",
                    "latin": "pangangge",
                    "name": "Pangangge",
                    "type": "pangangge",
                    "description": "Pangangge (tanda diakritik)",
                    "is_gantungan": False,
                    "is_pangangge": True
                }
            elif 0x1B00 <= cp <= 0x1B04:
                return {
                    "char": char,
                    "unicode": f"U+{cp:04X}",
                    "latin": "tengenan",
                    "name": "Pangangge Tengenan",
                    "type": "pangangge_tengenan",
                    "description": "Pangangge Tengenan",
                    "is_gantungan": False,
                    "is_pangangge": True
                }
    
    return {
        "char": char,
        "unicode": f"U+{ord(char):04X}" if len(char)==1 else "unknown",
        "latin": "",
        "name": "Unknown",
        "type": "unknown",
        "description": "Karakter tidak dikenal atau bukan Aksara Bali",
        "is_gantungan": False,
        "is_pangangge": False
    }

def classify_text(text: str) -> Dict:
    """Classify entire text"""
    classifications = []
    # Preserve virama + following consonant as one logical grapheme. Iterating
    # Python codepoints used to split ᭄ᬭ into two unrelated predictions, which
    # made pangangge/gantungan disappear in sentence-level results.
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
            continue
        if char == "᭄" and i + 1 < len(text) and not text[i + 1].isspace():
            char = text[i:i + 2]
            i += 2
        else:
            i += 1
        classifications.append(classify_char(char))
    
    # Overall type detection
    types = [c["type"] for c in classifications]
    overall = "mixed"
    if len(set(types)) == 1:
        overall = types[0] if types else "empty"
    elif all("wresastra" in t for t in types):
        overall = "wresastra"
    
    return {
        "input": text,
        "classifications": classifications,
        "overall_type": overall,
        "syllable_count": len([c for c in classifications if not c["is_pangangge"]]),
        "has_gantungan": any(c["is_gantungan"] for c in classifications),
        "has_pangangge": any(c["is_pangangge"] for c in classifications),
    }

def get_all_types():
    """Get all classification types"""
    return [
        {"id": "wresastra", "name": "Wresastra", "count": 18, "description": "Aksara Bali dasar 18 huruf untuk bahasa Bali umum"},
        {"id": "swalalita", "name": "Swalalita", "count": 33, "description": "Aksara lengkap untuk Sanskerta, Kawi, Jawa Kuno"},
        {"id": "suara", "name": "Aksara Suara", "count": 14, "description": "Vokal independen untuk awal kata"},
        {"id": "pangangge_suara", "name": "Pangangge Suara", "count": 11, "description": "Tanda vokal yang menempel pada aksara"},
        {"id": "pangangge_tengenan", "name": "Pangangge Tengenan", "count": 4, "description": "Akhiran konsonan: bisah (h), surang (r), cecek (ng), adeg-adeg"},
        {"id": "pangangge_aksara", "name": "Pangangge Aksara", "count": 5, "description": "Gantungan semi-vokal: cakra (ra), nania (ya), suku kembung (wa), la, repa"},
        {"id": "gantungan", "name": "Gantungan", "count": 33, "description": "Bentuk konsonan yang menggantung untuk cluster"},
        {"id": "angka", "name": "Angka Bali", "count": 10, "description": "Angka 0-9 dalam Aksara Bali"},
    ]
