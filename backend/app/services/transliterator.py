"""
Advanced Balinese Script Transliterator
Handles Wresastra, Swalalita, Pangangge, Gantungan, Gempelan
Based on Unicode Balinese U+1B00-U+1B7F and academic sources
"""

import json
import re
import unicodedata
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Tuple, Optional

# Load master data
DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "aksara_master.json", "r", encoding="utf-8") as f:
    MASTER = json.load(f)

with open(DATA_DIR / "dictionary.json", "r", encoding="utf-8") as f:
    DICTIONARY = json.load(f)

# === MAPPING TABLES ===

# Wresastra mapping latin -> bali char
WRESATRA_LATIN_TO_BALI = {
    "ha": "ᬳ",
    "na": "ᬦ",
    "ca": "ᬘ",
    "ra": "ᬭ",
    "ka": "ᬓ",
    "da": "ᬤ",
    "ta": "ᬢ",
    "sa": "ᬲ",
    "wa": "ᬯ",
    "la": "ᬮ",
    "ma": "ᬫ",
    "ga": "ᬕ",
    "ba": "ᬩ",
    "nga": "ᬗ",
    "pa": "ᬧ",
    "ja": "ᬚ",
    "ya": "ᬬ",
    "nya": "ᬜ",
}

# Extra Swalalita
SWALALITA_LATIN_TO_BALI = {
    "kha": "ᬔ",
    "gha": "ᬖ",
    "cha": "ᬙ",
    "jha": "ᬛ",
    "ṭa": "ᬝ",
    "ṭha": "ᬞ",
    "ḍa": "ᬟ",
    "ḍha": "ᬠ",
    "ṇa": "ᬡ",
    "tha": "ᬣ",
    "dha": "ᬥ",
    "pha": "ᬨ",
    "bha": "ᬪ",
    "śa": "ᬰ",  # sa saga
    "ṣa": "ᬱ",  # sa sapa
    "sha": "ᬰ",  # sha = śa (sa saga)
    "ssa": "ᬱ",
}

# Combined mapping for latin->bali base
LATIN_TO_BALI_BASE = {**WRESATRA_LATIN_TO_BALI, **SWALALITA_LATIN_TO_BALI}
# Sort by length descending for longest match
SORTED_LATIN_KEYS = sorted(LATIN_TO_BALI_BASE.keys(), key=lambda x: len(x), reverse=True)

# Reverse mapping bali -> latin base
BALI_TO_LATIN_BASE = {v: k for k, v in LATIN_TO_BALI_BASE.items()}
# Add wresastra only reverse for simple
BALI_TO_LATIN_BASE.update({
    "ᬳ": "ha",
    "ᬦ": "na",
    "ᬘ": "ca",
    "ᬭ": "ra",
    "ᬓ": "ka",
    "ᬤ": "da",
    "ᬢ": "ta",
    "ᬲ": "sa",
    "ᬯ": "wa",
    "ᬮ": "la",
    "ᬫ": "ma",
    "ᬕ": "ga",
    "ᬩ": "ba",
    "ᬗ": "nga",
    "ᬧ": "pa",
    "ᬚ": "ja",
    "ᬬ": "ya",
    "ᬜ": "nya",
    "ᬔ": "kha",
    "ᬖ": "gha",
    "ᬙ": "cha",
    "ᬛ": "jha",
    "ᬝ": "ṭa",
    "ᬞ": "ṭha",
    "ᬟ": "ḍa",
    "ᬠ": "ḍha",
    "ᬡ": "ṇa",
    "ᬣ": "tha",
    "ᬥ": "dha",
    "ᬨ": "pha",
    "ᬪ": "bha",
    "ᬰ": "śa",
    "ᬱ": "ṣa",
})

# Aksara Suara independent vowels
SUARA_LATIN_TO_BALI = {
    "a": "ᬅ",        # akara
    "ā": "ᬆ",      # akara + tedung
    "i": "ᬇ",        # ikara
    "ī": "ᬇᬷ",     # ikara + ulu melik
    "u": "ᬉ",        # ukara
    "ū": "ᬉᬹ",    # ukara + suku ilut
    "e": "ᬏ",        # ekara
    "ai": "ᬐ",      # aikara
    "o": "ᬑ",        # okara
    "au": "ᬐᬵ",       # aikara + tedung
    "ṛ": "ᬋ",
    "ṝ": "ᬌ",
    "ḷ": "ᬍ",
    "ḹ": "ᬎ",
    "rě": "ᬋ",  # alternative
    "lě": "ᬍ",
}

SUARA_BALI_TO_LATIN = {
    # Aksara suara independen. Vokal panjang (ā/ī/ū/au) dibaca parser
    # saat menemukan tanda length di belakang aksara suara.
    "ᬅ": "a",
    "ᬇ": "i",
    "ᬉ": "u",
    "ᬏ": "e",
    "ᬐ": "ai",
    "ᬑ": "o",
    "ᬋ": "ṛ",
    "ᬌ": "ṝ",
    "ᬍ": "ḷ",
    "ᬎ": "ḹ",
}

# Pangangge Suara marks (vowel diacritics)
# These are applied to base consonant
PANGANGGE_SUARA = {
    "i": {"mark": "ᬶ", "name": "ulu", "unicode": "U+1B36", "position": "above"},
    "ī": {"mark": "ᬷ", "name": "ulu sari", "unicode": "U+1B37"},
    "u": {"mark": "ᬸ", "name": "suku", "unicode": "U+1B38", "position": "below"},
    "ū": {"mark": "ᬹ", "name": "suku ilut", "unicode": "U+1B39"},
    "e": {"mark": "ᬾ", "name": "taleng", "unicode": "U+1B3E", "position": "front"},  # é
    "é": {"mark": "ᬾ", "name": "taleng"},
    "ai": {"mark": "ᬿ", "name": "taleng detya", "unicode": "U+1B3F"},
    "o": {"mark": "ᭀ", "name": "taleng tedong", "unicode": "U+1B40", "combined": True},  # actually taleng + tedong
    "au": {"mark": "ᭁ", "name": "taleng detya tedong", "unicode": "U+1B41", "combined": True},
    "ě": {"mark": "ᭂ", "name": "pepet", "unicode": "U+1B42", "forbidden_with": ["cakra"]},
    "ê": {"mark": "ᭂ", "name": "pepet"},
    "a_long": {"mark": "ᭀ", "name": "tedong", "unicode": "U+1B40", "position": "behind"},  # ā
}

# Simplified mapping for Latin vowel to pangangge
VOWEL_TO_PANGANGGE = {
    "a": None,  # inherent, no mark
    "i": "ᬶ",
    "ī": "ᬷ",
    "u": "ᬸ",
    "ū": "ᬹ",
    "e": "ᬾ",  # taleng for é
    "é": "ᬾ",
    "è": "ᭂ",  # pepet
    "ě": "ᭂ",
    "ê": "ᭂ",
    "ai": "ᬿ",
    "o": "ᭀ",  # will be handled as taleng+tedong combination
    "au": "ᭁ",
    "ā": "ᭀ",  # tedong
}

# Pangangge Tengenan (final consonants)
TENGENAN = {
    "h": {"mark": "ᬄ", "name": "bisah", "unicode": "U+1B04"},
    "r": {"mark": "ᬃ", "name": "surang", "unicode": "U+1B03"},
    "ng": {"mark": "ᬂ", "name": "cecek", "unicode": "U+1B02"},
    # adeg-adeg is handled separately as virama
}

# Adege-adeg
ADEG_ADEG = "᭄"  # U+1B44

# Pangangge Aksara (gantungan forms) - special
PANGANGGE_AKSARA = {
    "ra": {"form": "᭄ᬭ", "name": "cakra", "mark": "◌᭄ᬭ"},
    "ya": {"form": "᭄ᬬ", "name": "nania", "mark": "◌᭄ᬬ"},
    "wa": {"form": "᭄ᬯ", "name": "suku kembung", "mark": "◌᭄ᬯ"},
    "la": {"form": "᭄ᬮ", "name": "gantungan la", "mark": "◌᭄ᬮ"},
}

# For Bali -> Latin parsing
BALI_PANGANGGE_SUARA_TO_LATIN = {
    "ᬶ": "i",
    "ᬷ": "ī",
    "ᬸ": "u",
    "ᬹ": "ū",
    "ᬾ": "e",  # taleng, need context for o/au
    "ᬿ": "ai",
    "ᭀ": "o",  # tedong, but also ā, o depending
    "ᭁ": "au",
    "ᭂ": "ě",
    "ᬺ": "rě",  # guwung macelek
}

BALI_TENGENAN_TO_LATIN = {
    "ᬄ": "h",
    "ᬃ": "r",
    "ᬂ": "ng",
}

# Regex for tokenization
VOWELS = set(['a', 'i', 'u', 'e', 'o', 'ā', 'ī', 'ū', 'é', 'è', 'ě', 'ê', 'ö', 'ô'])
# We'll use simple latin vowels: a,i,u,e,o plus combined

def normalize_latin(text: str) -> str:
    """Normalize latin input"""
    text = text.lower().strip()
    # Replace common variants
    text = text.replace("ö", "o").replace("é", "e").replace("è", "e")
    return text

@lru_cache(maxsize=2000)
def transliterate_latin_to_bali(text: str, use_dictionary: bool = True) -> Tuple[str, List[Dict], List[str]]:
    """
    Advanced Latin to Balinese transliteration
    Returns: (bali_text, breakdown, warnings)
    """
    warnings = []
    breakdown = []
    
    if not text:
        return "", [], []
    
    original = text
    text = normalize_latin(text)
    
    # Check dictionary first for whole phrase
    if use_dictionary:
        # Exact match
        if text in DICTIONARY:
            entry = DICTIONARY[text]
            breakdown.append({
                "latin": text,
                "bali": entry["bali"],
                "type": "dictionary",
                "description": entry.get("meaning", ""),
                "note": entry.get("note", "")
            })
            return entry["bali"], breakdown, warnings
        
        # Check if text contains dictionary words? For now handle word by word later
    
    result = ""
    words = text.split()
    latin_words = []
    
    for word_idx, word in enumerate(words):
        # Check dictionary per word
        if use_dictionary and word in DICTIONARY:
            bali_word = DICTIONARY[word]["bali"]
            result += bali_word
            breakdown.append({
                "latin": word,
                "bali": bali_word,
                "type": "dictionary",
                "description": DICTIONARY[word].get("meaning", "")
            })
            if word_idx < len(words) - 1:
                result += " "
            continue
        
        # Process word via rule engine
        bali_word, word_breakdown, word_warnings = _transliterate_word_latin_to_bali_improved(word)
        result += bali_word
        breakdown.extend(word_breakdown)
        warnings.extend(word_warnings)
        if word_idx < len(words) - 1:
            result += " "
    
    return result, breakdown, warnings

# ---------------------------------------------------------------------------
# Latin -> Bali (word level) — parse silabis dengan aturan onset/koda.
#
# Implementasi mengikuti Unicode Balinese U+1B00-U+1B7F, Nala (2006)
# Pedoman Aksara Bali, dan LOC Balinese Romanization Table (2025).
# Prinsip utama:
#   * Stem konsonan di-match terpanjang-terlebih dahulu (ng, ny, kh, gh, ...).
#   * Konsonan yang diikuti VOKAL = onset -> vokal jadi pangangge
#     (i=ulu, u=suku, e=taleng, o=taleng+tedong, ai/au, a=inheren).
#   * Konsonan yang diikuti KONSONAN lain, atau di akhir kata = CODA
#     -> adeg-adeg (virama) mematikan vokal inheren (cluster/gantungan).
#   * >=3 coda beruntun = tumpuk telu (dilarang) -> warning.
#   * h/r/ng di akhir kata -> tengenan bisah/surang/cecek.
#   * Vokal di awal kata (atau setelah vokal) -> aksara suara independen.
#   * TIDAK ADA huruf Latin yang bocor ke hasil: setiap huruf dipetakan ke
#     aksara; f/v/x/z (tanpa padanan native) dipekatkan + warning.
# ---------------------------------------------------------------------------


def _build_stem_table():
    """Stem = kunci romanisasi tanpa 'a' inheren (semua kunci berakhiran a).

    Turun langsung dari LATIN_TO_BALI_BASE agar tidak ada typo manual;
    diurutkan terpanjang lebih dulu untuk longest-match.
    """
    table = []
    for key, base in LATIN_TO_BALI_BASE.items():
        assert key.endswith("a"), f"kunci romanisasi harus berakhiran a: {key}"
        table.append((key[:-1], base, key))
    table.sort(key=lambda t: len(t[0]), reverse=True)
    # Pemekatan fonetis untuk huruf tanpa padanan native (dengan warning).
    table.append(("f", "ᬧ", "f~pa"))   # /f/ ~ /p/
    table.append(("v", "ᬯ", "v~wa"))   # /v/ ~ /w/
    table.append(("q", "ᬓ", "q~ka"))   # /k/ (huruf q pada serapan)
    table.append(("x", "ᬲ", "x~sa"))   # /ks/ ~ /s/
    table.append(("z", "ᬓ", "z~ka"))   # /z/ ~ /k/
    return table


_CONSONANT_STEMS = _build_stem_table()

# Unit vokal, terpanjang lebih dulu (diftong, vokal panjang, vokal pendek).
_VOWEL_UNITS = ["ai", "au", "ā", "ī", "ū", "a", "i", "u", "e", "o"]


def _match_stem(word: str, pos: int):
    """(stem, base, nama latin) terpanjang yang cocok di `pos`, atau None."""
    for stem, base, name in _CONSONANT_STEMS:
        if word[pos:pos + len(stem)] == stem:
            return stem, base, name
    return None


def _match_vowel(word: str, pos: int):
    """Unit vokal terpanjang yang cocok di `pos`, atau None."""
    for v in _VOWEL_UNITS:
        if word[pos:pos + len(v)] == v:
            return v
    return None


def _apply_pangangge(base: str, vowel: str):
    """Pangangge untuk vokal `vowel` pada `base` -> (string, deskripsi).

    Urutan Unicode standar: AKSARA DASAR DIKUTI tanda pangangge
    (konvensi Noto Sans Balinese / Pedoman Aksara Bali), contoh:
    ka+e = "\u1b13\u1b3e" (ke), ka+o = "\u1b13\u1b40" (ko), ka+ā = "\u1b13\u1b35" (kā).
    """
    if vowel == "a":
        return base, "a inheren"
    if vowel == "ā":
        return base + "ᬵ", "tedung (ā)"
    if vowel == "i":
        return base + "ᬶ", "ulu (i)"
    if vowel == "ī":
        return base + "ᬷ", "ulu sari (ī)"
    if vowel == "u":
        return base + "ᬸ", "suku (u)"
    if vowel == "ū":
        return base + "ᬹ", "suku ilut (ū)"
    if vowel == "e":
        return base + "ᬾ", "taleng (e)"
    if vowel == "ai":
        return base + "ᬿ", "taling detya (ai)"
    if vowel == "o":
        return base + "ᭀ", "taling tedung (o)"
    if vowel == "au":
        return base + "ᭁ", "taling detya tedung (au)"
    return base, vowel


def _transliterate_word_latin_to_bali(word: str) -> Tuple[str, List[Dict], List[str]]:
    """Transliterasi satu kata Latin -> Bali (parse silabis onset/koda).

    Mengembalikan (bali_text, breakdown, warnings). Hasil tidak pernah
    mengandung huruf Latin.
    """
    if not word:
        return "", [], []

    warnings: List[str] = []
    breakdown: List[Dict] = []
    result = ""
    i = 0
    n = len(word)
    coda_run = 0  # coda beruntun (deteksi tumpuk telu)

    while i < n:
        ch = word[i]

        # Karakter non-huruf (angka, tanda baca) dilewati apa adanya.
        if not ch.isalpha():
            result += ch
            i += 1
            continue

        # 1) Posisi vokal -> aksara suara independen.
        v = _match_vowel(word, i)
        if v is not None:
            bali_v = SUARA_LATIN_TO_BALI.get(v)
            if bali_v is None:
                warnings.append(f"Vokal '{v}' tidak dikenal; dilewati")
                i += len(v)
                continue
            result += bali_v
            breakdown.append({
                "latin": v, "bali": bali_v, "type": "suara",
                "description": f"Aksara Suara {v}",
            })
            i += len(v)
            coda_run = 0
            continue

        # 2) Stem konsonan.
        m = _match_stem(word, i)
        if m is None:
            warnings.append(f"Karakter '{ch}' tidak punya padanan aksara")
            result += ch
            i += 1
            coda_run = 0
            continue

        stem, base, name = m
        i += len(stem)

        approx = "~" in name
        latin_label = name.split("~")[0]
        if approx:
            warnings.append(
                f"'{latin_label}' tidak ada dalam Aksara Bali; "
                f"dipekati sebagai {name.split('~')[1]}"
            )

        # 2a) Akhir kata.
        if i == n:
            if stem == "ng":
                if result:
                    unit = "ᬂ"
                    breakdown.append({
                        "latin": "ng", "bali": "ᬂ", "type": "tengenan",
                        "description": "cecek (ng final)",
                    })
                else:
                    unit = base + ADEG_ADEG
                    breakdown.append({
                        "latin": "ng", "bali": unit, "type": "wresastra+gantungan",
                        "description": "nga + adeg-adeg (kata hanya 'ng')",
                    })
            elif stem == "h":
                unit = "ᬄ"
                breakdown.append({
                    "latin": "h", "bali": "ᬄ", "type": "tengenan",
                    "description": "bisah (h final)",
                })
            elif stem == "r":
                unit = "ᬃ"
                breakdown.append({
                    "latin": "r", "bali": "ᬃ", "type": "tengenan",
                    "description": "surang (r final)",
                })
            else:
                unit = base + ADEG_ADEG
                breakdown.append({
                    "latin": latin_label, "bali": unit,
                    "type": "wresastra+gantungan",
                    "description": f"{latin_label} + adeg-adeg (konsonan akhir kata)",
                })
            result += unit
            coda_run = 0
            continue

        # 2b) Onset: vokal berikutnya jadi pangangge.
        v_after = _match_vowel(word, i)
        if v_after is not None:
            unit, p_desc = _apply_pangangge(base, v_after)
            result += unit
            breakdown.append({
                "latin": latin_label + v_after, "bali": unit,
                "type": "wresastra+pangangge" if v_after != "a" else "wresastra",
                "description": f"{latin_label} + {p_desc}",
            })
            i += len(v_after)
            coda_run = 0
            continue

        # 2c) Coda: konsonan berikutnya -> adeg-adeg (cluster/gantungan).
        coda_run += 1
        if coda_run >= 3:
            warnings.append(
                f"Tumpuk telu terdeteksi pada '{word}' (>=3 konsonan beruntun); "
                f"dilarang dalam Aksara Bali"
            )
        unit = base + ADEG_ADEG
        result += unit
        breakdown.append({
            "latin": latin_label, "bali": unit,
            "type": "wresastra+gantungan",
            "description": f"{latin_label} + adeg-adeg (cluster/gantungan)",
        })

    return result, breakdown, warnings


# Jaring pengaman: huruf Latin apa pun yang lolos dipaksa ke dasar terdekat.
SINGLE_CONSONANT_FALLBACK = {
    "k": "ᬓ", "g": "ᬕ", "b": "ᬩ", "p": "ᬧ", "m": "ᬫ", "n": "ᬦ",
    "t": "ᬢ", "d": "ᬤ", "s": "ᬲ", "w": "ᬯ", "l": "ᬮ", "h": "ᬳ",
    "c": "ᬘ", "r": "ᬭ", "j": "ᬚ", "y": "ᬬ",
    "f": "ᬧ", "v": "ᬯ", "q": "ᬓ", "x": "ᬲ", "z": "ᬓ",
}


def _transliterate_word_latin_to_bali_improved(word: str) -> Tuple[str, List[Dict], List[str]]:
    """Jaring pengaman: pastikan 100% hasil bebas huruf Latin."""
    result, breakdown, warnings = _transliterate_word_latin_to_bali(word)

    if any(c.isalpha() and c.isascii() for c in result):
        fixed = []
        for char in result:
            if char in SINGLE_CONSONANT_FALLBACK:
                fixed.append(SINGLE_CONSONANT_FALLBACK[char] + ADEG_ADEG)
                warnings.append(f"Jaring pengaman: '{char}' dipaksa ke aksara")
            else:
                fixed.append(char)
        result = "".join(fixed)

    return result, breakdown, warnings

# Override to use improved
def transliterate_word_wrapper(word: str):
    return _transliterate_word_latin_to_bali_improved(word)

# ── Tabel tanda untuk parser bali->latin (urutan standar Unicode:
#    aksara dasar DIKUTI tanda) ────────────────────────────────────────────
BALI_VOWEL_MARKS = {
    "ᬶ": "i",        # ulu
    "ᬷ": "ī",        # ulu melik
    "ᬸ": "u",        # suku
    "ᬹ": "ū",        # suku ilut
    "ᬾ": "e",      # taleng
    "ᬿ": "ai",    # taling detya
    "ᬵ": "ā",       # tedung
    "ᭀ": "o",   # taling tedung (e+o precomposed)
    "ᭁ": "au",  # taling detya tedung (ai+o precomposed)
    "ᭂ": "ě",       # pepet
    "ᬺ": "rě",     # guwung macelek
}

# Aksara suara yang bisa diikuti tanda length -> vokal panjang/diftong
_SUARA_LENGTH = {
    "ᬅ": "ā",   # akara + tedung
    "ᬇ": "ī",   # ikara + ulu melik
    "ᬉ": "ū",   # ukara + suku ilut
    "ᬐ": "au",  # aikara + tedung
}

_HA_CHAR = "ᬳ"  # ha — berfungsi ganda: konsonan "h" & vokal tunggal "a"

_PUNCT_KEEP = set("  ,,.;:!?()")


@lru_cache(maxsize=2000)
def transliterate_bali_to_latin(text: str) -> Tuple[str, List[Dict], List[str]]:
    """Bali to Latin — parser urutan Unicode standar.

    Aturan (mengikuti Pedoman Aksara Bali & romanisasi LOC):
    * Aksara dasar dibaca dengan vokal inheren "a", diubah tanda
      pangangge suara di belakangnya (ulu=i, suku=u, taleng=e,
      taling tedung=o, taling detya=ai, taling detya tedung=au,
      tedung=ā, pepet=ě, ulu melik=ī, suku ilut=ū, guwung macelek=rě).
      Bentuk terpisah taleng+tedung (=o) dan taling detya+tedung (=au)
      tetap dikenali.
    * Adeg-adeg mematikan vokal -> konsonan menjadi cluster (gantungan);
      vokal penutup cluster datang dari aksara berikutnya.
    * Tengenan (bisah=h, surang=r, cecek=ng) menambah koda pada suku kata.
    * Aksara suara independen (akara/ikara/ukara/ekara/aikara/okara)
      dibaca a/i/u/e/ai/o; + tanda length di belakang = vokal panjang.
    """
    text = unicodedata.normalize("NFC", text)
    warnings: List[str] = []
    breakdown: List[Dict] = []
    result_parts: List[str] = []
    cluster: List[str] = []  # konsonan cluster menunggu vokal penutup
    cluster_bali: List[str] = []
    i = 0
    n = len(text)

    def flush_cluster() -> None:
        """Kata berakhir dengan konsonan cluster (tanpa vokal penutup)."""
        if cluster:
            syl = "".join(cluster)
            result_parts.append(syl)
            breakdown.append({
                "bali": "".join(cluster_bali), "latin": syl,
                "type": "wresastra+gantungan",
                "description": "Cluster konsonan %s (tanpa vokal)" % syl,
            })
            cluster.clear()
            cluster_bali.clear()

    def base_consonant(base_latin: str) -> str:
        return base_latin[:-1] if base_latin.endswith("a") else base_latin

    while i < n:
        ch = text[i]

        # Spasi & tanda baca: batasi cluster, simpan apa adanya.
        if ch in _PUNCT_KEEP:
            flush_cluster()
            result_parts.append(" " if ch == " " else ch)
            i += 1
            continue

        # 1) Aksara suara independen.
        if ch in SUARA_BALI_TO_LATIN:
            flush_cluster()
            reading = SUARA_BALI_TO_LATIN[ch]
            j = i + 1
            # vokal panjang/diftong: akara+tedung, ikara+ulu melik,
            # ukara+suku ilut, aikara+tedung (=au)
            length_mark = None
            if ch == "ᬅ" and j < n and text[j] == "ᬵ":
                length_mark = "ᬵ"
            elif ch == "ᬇ" and j < n and text[j] == "ᬷ":
                length_mark = "ᬷ"
            elif ch == "ᬉ" and j < n and text[j] == "ᬹ":
                length_mark = "ᬹ"
            elif ch == "ᬐ" and j < n and text[j] == "ᬵ":
                length_mark = "ᬵ"
            if length_mark is not None:
                reading = _SUARA_LENGTH[ch]
                result_parts.append(reading)
                breakdown.append({
                    "bali": ch + length_mark, "latin": reading,
                    "type": "suara", "description": "Aksara Suara %s (panjang)" % reading,
                })
                i = j + 1
                continue
            # adeg setelah aksara suara -> vokal jadi koda cluster (mis. okara+adeg = "om")
            if j < n and text[j] == "᭄":
                cluster.append(reading)
                cluster_bali.append(ch + "᭄")
                i = j + 1
                continue
            result_parts.append(reading)
            breakdown.append({
                "bali": ch, "latin": reading,
                "type": "suara", "description": "Aksara Suara %s" % reading,
            })
            i = j
            continue

        # 2) Aksara dasar (wresastra/swalalita, termasuk ha).
        if ch in BALI_TO_LATIN_BASE:
            base_latin = BALI_TO_LATIN_BASE[ch]
            cons = base_consonant(base_latin)
            j = i + 1
            vowel = "a"
            marks = ""
            # Kumpulkan tanda vokal (maks. 2: taleng+tedung / taling detya+tedung).
            while j < n and text[j] in BALI_VOWEL_MARKS:
                mk = text[j]
                if mk == "ᬾ" and j + 1 < n and text[j + 1] == "ᭀ":
                    vowel = "o"
                    marks = mk + "ᭀ"
                    j += 2
                    break
                if mk == "ᬿ" and j + 1 < n and text[j + 1] == "ᭀ":
                    vowel = "au"
                    marks = mk + "ᭀ"
                    j += 2
                    break
                vowel = BALI_VOWEL_MARKS[mk]
                marks += mk
                j += 1
                break  # satu tanda vokal cukup (kecuali kombinasi di atas)
            adeg = False
            if j < n and text[j] == "᭄":
                adeg = True
                marks += "᭄"
                j += 1
            teng = ""
            teng_marks = ""
            while j < n and text[j] in BALI_TENGENAN_TO_LATIN:
                teng += BALI_TENGENAN_TO_LATIN[text[j]]
                teng_marks += text[j]
                j += 1
            if adeg:
                # Koda: konsonan (tanpa vokal) masuk cluster.
                cluster.append(cons + teng)
                cluster_bali.append(ch + marks)
            else:
                bali_syl = "".join(cluster_bali) + ch + marks + teng_marks
                if ch == _HA_CHAR:
                    # ha (ᬳ) dibaca sebagai vokal tunggal "a" (standar LOC &
                    # romanisasi umum); bila diikuti tanda vokal, tanda itu
                    # dibaca langsung (h-nya tidak diucapkan).
                    syl = "".join(cluster) + vowel + teng
                    desc_bits = ["ha sebagai vokal %s" % vowel]
                else:
                    syl = "".join(cluster) + cons + vowel + teng
                    desc_bits = [("%s (a inheren)" % cons) if not marks else ("%s + %s" % (cons, marks))]
                if teng:
                    desc_bits.append("+ %s" % teng)
                breakdown.append({
                    "bali": bali_syl,
                    "latin": syl,
                    "type": "wresastra+gantungan" if cluster_bali else ("wresastra+pangangge" if (marks or teng_marks) else "wresastra"),
                    "description": " ".join(desc_bits) + " = %s" % syl,
                })
                result_parts.append(syl)
                cluster.clear()
                cluster_bali.clear()
            i = j
            continue

        # 3) Tengenan mengambang (tanpa dasar) — tidak valid.
        if ch in BALI_TENGENAN_TO_LATIN:
            warnings.append("Tengenan tanpa aksara dasar (posisi %d)" % i)
            i += 1
            continue

        # 4) Tanda vokal mengambang (tanpa dasar).
        if ch in BALI_VOWEL_MARKS:
            warnings.append("Tanda pangangge tanpa aksara dasar (posisi %d)" % i)
            i += 1
            continue

        # 5) Karakter lain (angka, simbol, dsb.) apa adanya.
        result_parts.append(ch)
        i += 1

    flush_cluster()
    return "".join(result_parts), breakdown, warnings


def transliterate(text: str, direction: str = "latin-to-bali", use_dictionary: bool = True):
    """Main entry point"""
    if direction == "latin-to-bali":
        return transliterate_latin_to_bali(text, use_dictionary)
    elif direction == "bali-to-latin":
        return transliterate_bali_to_latin(text)
    else:
        raise ValueError(f"Invalid direction: {direction}")

def has_tumpuk_telu(bali_text: str) -> bool:
    """Check if text has tumpuk telu violation (2 gantungan on same base)"""
    # In Unicode, tumpuk telu would be base + adeg + base + adeg + base
    # That's actually allowed in terms of encoding but forbidden in writing
    # We detect pattern: adeg + base + adeg + base without vowel in between?
    # Simplified: count consecutive adeg+base patterns
    # If we have base + adeg + base + adeg + base in a row without intervening vowel killer reset, it's tumpuk telu
    # For MVP, we check if there are 2 adeg in a row with only one base between? Actually need 2 gantungan on same base
    # Pattern: base + adeg + base + adeg + base would be 2 gantungan on first base? No, first base has 1 gantungan (second base), second base has 1 gantungan (third base)
    # But tumpuk telu is when one base has 2 gantungan directly: base + adeg + base + adeg + base where second and third are both gantungan of first? That's not how Unicode works
    # In Unicode, each adeg attaches to previous base, so base + adeg + base is one gantungan, base + adeg + base + adeg + base would be base with gantungan, and that gantungan with another gantungan - which is forbidden
    # So we can detect: if we have adeg + base + adeg + base consecutively, that's 2 levels, which is tumpuk telu if we consider first base having 2 gantungan? Actually second gantungan is on second base, not first, but still 3 layers total
    # Rule: max 1 gantungan per base, so any occurrence of base + adeg + base + adeg + base is forbidden (3 layers)
    # We'll detect regex: \u1B44.\u1B44. (adeg + any + adeg + any) 
    pattern = f"{ADEG_ADEG}.{{1}}{ADEG_ADEG}"
    return bool(re.search(pattern, bali_text))

def analyze_gantungan(text: str, direction: str = "latin-to-bali"):
    """Analyze gantungan usage in text"""
    if direction == "latin-to-bali":
        bali_text, breakdown, warnings = transliterate_latin_to_bali(text)
    else:
        bali_text = text
        _, breakdown, _ = transliterate_bali_to_latin(text)
    
    clusters = []
    # Find all adeg+base occurrences
    for m in re.finditer(f"{ADEG_ADEG}(.)", bali_text):
        gantungan_char = m.group(1)
        latin = BALI_TO_LATIN_BASE.get(gantungan_char, gantungan_char)
        clusters.append({
            "position": m.start(),
            "bali": m.group(0),
            "latin": latin,
            "type": "gantungan",
            "explanation": f"Gantungan {latin}"
        })
    
    return {
        "original": text,
        "bali": bali_text if direction == "latin-to-bali" else text,
        "clusters": clusters,
        "has_gantungan": len(clusters) > 0,
        "gantungan_count": len(clusters),
        "has_tumpuk_telu": has_tumpuk_telu(bali_text),
        "breakdown": breakdown
    }

# For testing
if __name__ == "__main__":
    tests = ["bali", "aksara", "angklung", "bleganjur", "dharma", "om swastyastu", "anak"]
    for t in tests:
        bali, breakdown, warnings = transliterate_latin_to_bali(t)
        print(f"{t} -> {bali} | warnings: {warnings}")
        latin, _, _ = transliterate_bali_to_latin(bali)
        print(f"  back -> {latin}")
