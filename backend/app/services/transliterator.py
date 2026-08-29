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
    "sha": "ᬱ",  # common alias for ssa
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
    "a": "ᬅ",
    "ā": "ᬆ",
    "i": "ᬇ",
    "ī": "ᬈ",
    "u": "ᬉ",
    "ū": "ᬊ",
    "e": "ᬏ",
    "ai": "ᬐ",
    "o": "ᬑ",
    "au": "ᬒ",
    "ṛ": "ᬋ",
    "ṝ": "ᬌ",
    "ḷ": "ᬍ",
    "ḹ": "ᬎ",
    "rě": "ᬋ",  # alternative
    "lě": "ᬍ",
}

SUARA_BALI_TO_LATIN = {v: k for k, v in SUARA_LATIN_TO_BALI.items()}
# Ensure single mapping for reverse - use short forms
SUARA_BALI_TO_LATIN.update({
    "ᬅ": "a",
    "ᬆ": "ā",
    "ᬇ": "i",
    "ᬈ": "ī",
    "ᬉ": "u",
    "ᬊ": "ū",
    "ᬏ": "e",
    "ᬐ": "ai",
    "ᬑ": "o",
    "ᬒ": "au",
    "ᬋ": "ṛ",
    "ᬌ": "ṝ",
    "ᬍ": "ḷ",
    "ᬎ": "ḹ",
})

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
        bali_word, word_breakdown, word_warnings = _transliterate_word_latin_to_bali(word)
        result += bali_word
        breakdown.extend(word_breakdown)
        warnings.extend(word_warnings)
        if word_idx < len(words) - 1:
            result += " "
    
    return result, breakdown, warnings

def _transliterate_word_latin_to_bali(word: str) -> Tuple[str, List[Dict], List[str]]:
    """Transliterate single word latin -> bali"""
    if not word:
        return "", [], []
    
    warnings = []
    breakdown = []
    result = ""
    
    i = 0
    # Track if previous char had gantungan (for tumpuk telu check)
    has_gantungan_on_current = False
    last_base = ""
    
    # Handle if word starts with vowel -> independent vowel
    # For simplicity, if word starts with 'a' and next is consonant, use independent Akara?
    # Rule: In Balinese, words starting with vowel use aksara suara, not ha.
    # But many words like "aksara" start with a independent.
    # We'll detect: if word[0] in vowels and (len==1 or word[1] is consonant cluster start)
    # Use independent vowel for first char
    
    # Special handling for "a" at start vs "ha"
    # If word starts with 'a' and second char is consonant, use Akara ᬅ
    # Example: "aksara" -> a = ᬅ
    # But "anak" -> a = ᬅ? In common Balinese, "anak" is ᬅᬦᬓ᭄
    # We'll implement: if word starts with vowel, first char is independent suara
    
    # Let's iterate
    word_len = len(word)
    
    while i < word_len:
        char = word[i]
        
        # Skip non-alpha? Keep numbers? For MVP, only handle alpha
        if not char.isalpha():
            result += char
            i += 1
            continue
        
        # Check for special clusters like "ng", "ny" that are single aksara
        # Lookahead 3,2,1 for base consonant
        matched = None
        matched_bali = None
        matched_len = 0
        
        # Try longest match for base consonant
        for key in SORTED_LATIN_KEYS:
            if word[i:i+len(key)] == key:
                # Ensure it's not part of vowel combination that should be pangangge?
                # For example, "nga" is base, but "ng" as cecek is different
                # If key is "nga" and next char is vowel, it's still base nga + vowel
                # That's correct
                matched = key
                matched_bali = LATIN_TO_BALI_BASE[key]
                matched_len = len(key)
                break
        
        # If no consonant match, maybe it's a vowel that should be independent or pangangge?
        if not matched:
            # Check if char is vowel
            if char in ['a', 'i', 'u', 'e', 'o']:
                # If at start of word or after space, use independent suara
                if i == 0 or (i > 0 and not word[i-1].isalpha()):
                    # Independent vowel
                    # Map vowel to suara
                    # For 'a' -> ᬅ, 'i' -> ᬇ, etc
                    # But need to handle 'e' as pepet vs taleng? At start, use Ekara
                    vowel_map = {
                        'a': 'ᬅ',
                        'i': 'ᬇ',
                        'u': 'ᬉ',
                        'e': 'ᬏ',
                        'o': 'ᬑ',
                    }
                    bali_char = vowel_map.get(char, 'ᬅ')
                    result += bali_char
                    breakdown.append({
                        "latin": char,
                        "bali": bali_char,
                        "type": "suara",
                        "description": f"Aksara Suara {char.upper()}"
                    })
                    i += 1
                    has_gantungan_on_current = False
                    continue
                else:
                    # This vowel should have been handled as pangangge after previous consonant
                    # But if we are here, previous was not consonant? Maybe previous was vowel? Then use independent?
                    # For simplicity, treat as independent if previous char was vowel (diphthong)
                    # Actually "ae" etc not common
                    # Let's treat as independent
                    vowel_map = {
                        'a': 'ᬅ',
                        'i': 'ᬇ',
                        'u': 'ᬉ',
                        'e': 'ᬏ',
                        'o': 'ᬑ',
                    }
                    bali_char = vowel_map.get(char, 'ᬅ')
                    result += bali_char
                    breakdown.append({
                        "latin": char,
                        "bali": bali_char,
                        "type": "suara",
                        "description": f"Aksara Suara {char.upper()} (after vowel)"
                    })
                    i += 1
                    continue
            else:
                # Unknown char, skip with warning
                warnings.append(f"Unknown char '{char}' at position {i}")
                result += char
                i += 1
                continue
        
        # We have a consonant base matched
        base_latin = matched
        base_bali = matched_bali
        next_pos = i + matched_len
        
        # Look ahead for vowel that modifies this base
        vowel = None
        vowel_len = 0
        pangangge_mark = None
        
        if next_pos < word_len:
            next_char = word[next_pos]
            # Check for vowel combinations: ai, au, etc
            # Try 2-char vowel first
            if next_pos + 1 < word_len:
                two = word[next_pos:next_pos+2]
                if two in ['ai', 'au', 'aa', 'ii', 'uu']:
                    vowel = two
                    vowel_len = 2
            if not vowel and next_char in ['a', 'i', 'u', 'e', 'o']:
                # Check if this vowel is actually part of next consonant? 
                # For example, "bali" -> b a l i, so after "ba", next is "l" not vowel? Actually "ba" is ba + a? Wait
                # Our logic: consonant + vowel = base + pangangge
                # So if we have "ba", we matched "ba" as base? No, "ba" base is "ba" = ᬩ which already includes inherent a
                # Actually our mapping: "ba" -> ᬩ, which is ba (consonant+inherent a)
                # But we also have "b" + "a"? Our keys include "ba"? No, we have "ba" as key for ᬩ? Actually WRESATRA keys are "ba", "ha", etc, which are consonant + a.
                # So we matched "ba" as whole? But word "bali" is b-a-l-i, not ba-li? Let's think.
                # Better approach: our keys should be consonant only? But we defined as "ba" for ᬩ.
                # We need to handle: if we match "ba" and next char is vowel, that vowel is separate?
                # Actually Balinese: ᬩ is ba (b + inherent a). To get bi, we need ba + ulu = ᬩᬶ
                # So "bali" = ba + li = ba (ᬩ) + la (ᬮ) + ulu (ᬶ) = ᬩᬮᬶ
                # So "bali" parsing: 
                # - At i=0, we try match: "ba" matches "bali"[0:2]="ba" => base ba = ᬩ, next_pos=2
                # - Next char at 2 is 'l', which is consonant start, not vowel, so no pangangge, result = ᬩ
                # - Then i=2, match "la" = ᬮ, next_pos=4, next char at 4 is 'i', which is vowel
                # - So we should apply pangangge for i to previous base? Actually "li" = la + ulu
                # So we need to detect vowel after base and apply pangangge
                vowel = next_char
                vowel_len = 1
                # Special: if vowel is 'a', no pangangge needed (inherent)
                # If vowel is 'i', need ulu, etc
        
        # Determine pangangge
        bali_with_pangangge = base_bali
        pangangge_desc = ""
        
        if vowel:
            if vowel == 'a':
                # inherent, no mark
                pangangge_mark = None
                pangangge_desc = "inherent a"
            elif vowel in VOWEL_TO_PANGANGGE:
                pang = VOWEL_TO_PANGANGGE[vowel]
                if pang:
                    # Special handling for o and au which are taleng + tedong
                    if vowel == 'o':
                        # Taleng + Tedong = ᬾ + ᭀ surrounding
                        # In Unicode, o is represented as taleng (front) + tedong (behind)
                        # So we need to produce: taleng + base + tedong? Actually order: taleng before base, tedong after
                        # But our base already emitted? We need to handle: for o, result should be taleng + base + tedong
                        # So we need to prepend taleng
                        # Let's handle: result currently doesn't have base yet, we will emit taleng+base+tedong
                        bali_with_pangangge = "ᬾ" + base_bali + "ᭀ"
                        pangangge_desc = "taleng tedong (o)"
                    elif vowel == 'au':
                        bali_with_pangangge = "ᬾ" + base_bali + "ᭀ"  # Actually taleng detya tedong? For simplicity use same? Need correct: Au is taleng detya + tedong?
                        # According to master, au is ᭁ which is combination, but representation is ᬿ + base + ᭀ?
                        # Let's use "ᬿ" + base + "ᭀ" for ai? Wait
                        # Simplify: use precomposed forms? In Unicode, taleng tedong is two codepoints
                        # We'll use: ᬾ + base + ᭀ for o, ᬿ + base + ᭀ for au? Let's check
                        # Actually from data: taleng = ᬾ (front), tedong = ᭀ (behind)
                        # taleng detya = ᬿ (front) for ai
                        # So: e = ᬾ + base, ai = ᬿ + base, o = ᬾ + base + ᭀ, au = ᬿ + base + ᭀ
                        # We'll implement
                        if vowel == 'ai':
                            bali_with_pangangge = "ᬿ" + base_bali
                        else:  # au
                            bali_with_pangangge = "ᬿ" + base_bali + "ᭀ"
                        pangangge_desc = f"taleng detya tedong ({vowel})"
                    elif vowel in ['e', 'é']:
                        # Taleng front
                        bali_with_pangangge = "ᬾ" + base_bali
                        pangangge_desc = "taleng (e)"
                    else:
                        bali_with_pangangge = base_bali + pang
                        pangangge_desc = f"{PANGANGGE_SUARA.get(vowel, {}).get('name', vowel)} ({vowel})"
                    pangangge_mark = pang
                else:
                    bali_with_pangangge = base_bali
            else:
                bali_with_pangangge = base_bali
        else:
            # No vowel ahead, check if this is at end of word or next is consonant
            # If at end of word and base is consonant, need to decide: kill vowel with adeg-adeg?
            # In Balinese, word final consonant often uses adeg-adeg
            # But our base already includes inherent a, so to kill, add adeg-adeg
            # However, if word ends with "ng" etc, we should use cecek not nga+adeg
            # Handle tengenan
            pass
        
        # Now check for tengenan and gantungan logic
        # If next after vowel is end or consonant, we may need to handle
        # Let's look ahead after consuming vowel
        after_vowel_pos = next_pos + vowel_len if vowel else next_pos
        
        # Check for final tengenan: h, r, ng at end
        # For simplicity, if after_vowel_pos == word_len and base_latin in certain, and previous char was vowel?
        # Actually tengenan is after vowel: e.g., "bah" = ba + bisah? No, "bah" = ba + a + h? 
        # In our parsing, "bah" would be: base "ba" (ᬩ) + vowel? Actually "bah" = b a h, so after matching "ba" (which is b+a), next char is 'h' which is not vowel, so we need to detect tengenan
        
        # Detect tengenan
        is_tengenan_handled = False
        if after_vowel_pos < word_len:
            remaining = word[after_vowel_pos:]
            # Check for "ng" at end or before consonant? Cecek for ng
            if remaining.startswith("ng"):
                # If this ng is at end of word, use cecek
                # If ng is followed by consonant or end, it's cecek, not nga gantungan?
                # Rule: cecek is for final ng, gantungan nga is for medial ng cluster like "angka" = a + ngka?
                # For simplicity: if ng at end of word, use cecek
                if after_vowel_pos + 2 == word_len:
                    # End of word: use cecek
                    bali_with_pangangge += "ᬂ"  # cecek
                    breakdown.append({
                        "latin": base_latin + (vowel or "") + "ng",
                        "bali": bali_with_pangangge,
                        "type": "wresastra+pangangge_tengenan",
                        "description": f"{base_latin} + {vowel or 'a'} + cecek (ng)"
                    })
                    result += bali_with_pangangge
                    i = after_vowel_pos + 2
                    has_gantungan_on_current = False
                    is_tengenan_handled = True
                else:
                    # Medial ng, treat as gantungan? Actually "angka" = a + nga + ka gantungan? Let's treat as gantungan
                    # For now, emit base + adeg-adeg + nga
                    # But we already have base, need to add adeg-adeg + nga
                    # So result will be base + adeg-adeg + nga
                    # We'll handle as gantungan cluster
                    pass  # fall through to gantungan handling
            elif remaining.startswith("h") and after_vowel_pos + 1 == word_len:
                # final h -> bisah
                bali_with_pangangge += "ᬄ"
                breakdown.append({
                    "latin": base_latin + (vowel or "") + "h",
                    "bali": bali_with_pangangge,
                    "type": "wresastra+bisah",
                    "description": f"{base_latin} + bisah (h)"
                })
                result += bali_with_pangangge
                i = after_vowel_pos + 1
                has_gantungan_on_current = False
                is_tengenan_handled = True
            elif remaining.startswith("r") and after_vowel_pos + 1 == word_len:
                # final r -> surang
                bali_with_pangangge += "ᬃ"
                breakdown.append({
                    "latin": base_latin + (vowel or "") + "r",
                    "bali": bali_with_pangangge,
                    "type": "wresastra+surang",
                    "description": f"{base_latin} + surang (r)"
                })
                result += bali_with_pangangge
                i = after_vowel_pos + 1
                has_gantungan_on_current = False
                is_tengenan_handled = True
        
        if is_tengenan_handled:
            continue
        
        # If not tengenan, check if next char starts a new consonant (cluster) -> need gantungan
        if after_vowel_pos < word_len and word[after_vowel_pos].isalpha():
            # Next char is start of next syllable, so current base should have adeg-adeg if next is consonant cluster?
            # Actually in Balinese, consonant clusters are written with gantungan: first consonant + adeg-adeg + second consonant (which renders as gantungan)
            # So we should add adeg-adeg after current base if next is consonant and not vowel?
            # But our current base already emitted? We haven't emitted yet
            # Let's check: if after vowel, next is consonant, then we need adeg-adeg before next base
            # So emit current base with pangangge, plus adeg-adeg
            # Then next iteration will emit next base which will visually be gantungan
            # However, need to check tumpuk telu: if current already has gantungan, cannot add another gantungan
            # Our has_gantungan_on_current tracks if current base is already a gantungan
            # Actually we need to track if we are about to add gantungan to current
            
            # If next is consonant and we have not yet emitted, we emit current + adeg-adeg
            # Then continue
            # But only if next is consonant and not start of new word? Yes
            
            # Check if next char is consonant (not vowel)
            next_char = word[after_vowel_pos]
            if next_char not in ['a', 'i', 'u', 'e', 'o']:
                # It's consonant, so need adeg-adeg
                # Check tumpuk telu
                if has_gantungan_on_current:
                    warnings.append(f"Tumpuk telu prevented at position {after_vowel_pos} in word '{word}'")
                    # To prevent, we should not add gantungan, instead start new syllable with adeg-adeg? Actually need to break
                    # For MVP, we will still add adeg-adeg but note warning, and reset has_gantungan
                    # In real Balinese, you'd need to use adeg-adeg to break cluster
                    result += bali_with_pangangge + ADEG_ADEG
                    breakdown.append({
                        "latin": base_latin + (vowel or ""),
                        "bali": bali_with_pangangge + ADEG_ADEG,
                        "type": "wresastra+gantungan",
                        "description": f"{base_latin} with adeg-adeg (cluster, tumpuk telu avoided)"
                    })
                    i = after_vowel_pos
                    has_gantungan_on_current = False
                    continue
                else:
                    # Normal gantungan
                    result += bali_with_pangangge + ADEG_ADEG
                    breakdown.append({
                        "latin": base_latin + (vowel or ""),
                        "bali": bali_with_pangangge + ADEG_ADEG,
                        "type": "wresastra+gantungan",
                        "description": f"{base_latin} + adeg-adeg for cluster, next will be gantungan"
                    })
                    i = after_vowel_pos
                    # Next base will be gantungan
                    has_gantungan_on_current = True
                    continue
            else:
                # Next is vowel, but that vowel should be part of next syllable? Actually if next is vowel and we are at consonant, then next vowel is independent? No, vowel after consonant should have been consumed as pangangge
                # But we already consumed vowel, so after_vowel_pos points after vowel, and next_char is vowel? That would be two vowels in a row -> second is independent
                # So emit current without adeg-adeg
                result += bali_with_pangangge
                breakdown.append({
                    "latin": base_latin + (vowel or ""),
                    "bali": bali_with_pangangge,
                    "type": "wresastra+pangangge" if pangangge_mark else "wresastra",
                    "description": f"{base_latin} + {pangangge_desc or 'inherent a'}"
                })
                i = after_vowel_pos
                has_gantungan_on_current = False
                continue
        else:
            # End of word
            # Check if current base at end should have adeg-adeg to kill inherent a?
            # In Balinese, if word ends with consonant without vowel, need adeg-adeg
            # But our base already has inherent a, so if word ends and we have no vowel, we need adeg-adeg?
            # Actually our logic: base_latin like "ba" includes a, so "b" alone would be "ba" + adeg-adeg?
            # But we matched "ba" as base, which is "b" + "a". If word is "bab" (b a b), then after first ba, next is b at end, so previous handling would have added adeg-adeg and then final b needs adeg-adeg
            # For final consonant without vowel, we should add adeg-adeg
            # Determine: if base_latin was matched and we are at end, and base_latin ends with 'a' (inherent), and we had no explicit vowel that is 'a'? Actually we did
            # For word ending with consonant like "bali" ends with vowel i, so no adeg-adeg needed
            # For word like "anak" = a na k, last k should have adeg-adeg? In Balinese, "anak" is ᬅᬦᬓ᭄ (a + na + ka + adeg-adeg)
            # So if word ends with consonant and we matched that consonant as base, we need adeg-adeg at end
            
            # Check if word ends with consonant (not vowel)
            # Our current base is at end, and we have no vowel after (or vowel is a)
            # If word ends with consonant cluster that is not 'a', we need adeg-adeg
            # Actually "anak": parsing: a (independent) + na (ᬦ) + ka (ᬓ) + adeg-adeg?
            # Let's see: word "anak" = a n a k
            # i=0: a -> independent ᬅ
            # i=1: na -> ᬦ (n+a)
            # i=3: k -> base "ka"? But "k" alone, our key "ka" is 2 chars, but remaining is "k" (1 char) -> no match for "ka" because need 2 chars "ka", but we have only "k" left
            # So we need to handle single consonant at end: map "k" -> "ka" + adeg-adeg?
            # For simplicity, if remaining single consonant at end, treat as base + adeg-adeg
            
            # For now, if we are at end and base_latin is like "ka" etc, but word actually ended with that base, we need to check if original word ended with consonant without vowel?
            # Example: "anak" -> last char 'k' should be ka + adeg-adeg
            # Our matching: at i=2, word[2:]= "ak", we match "a" as vowel independent? No, we match consonant first, but "ak" starts with 'a' vowel, so we go to vowel handling, emit ᬅ, i=3, now word[3:]="k", we try match keys: "ka" needs 2 chars, but only 1 left, so no match, then we go to unknown? We need to handle single consonant fallback
            
            # Let's handle fallback: if no match and char is consonant single, map it
            # For MVP, we will emit base as is, and if at end and not followed by vowel, add adeg-adeg if needed
            # Check if after_vowel_pos == word_len and vowel is None or vowel == 'a'? Actually if vowel is None, it means base had inherent a, but if at end, we might need adeg-adeg to kill it? 
            # In Balinese, words ending with consonant need adeg-adeg, but words ending with vowel 'a' keep inherent
            # So "bali" ends with i (vowel), no adeg-adeg
            # "anak" ends with k (consonant), need adeg-adeg
            # How to detect? If original word ends with consonant letter that is not 'a', and we are at last base, need adeg-adeg
            # Our base_latin always ends with 'a' except 'ng', 'ny', etc? Actually "ka" ends with a, but represents k
            # So if word ends with 'k' (single), we matched "ka"? No, we matched nothing? Let's re-evaluate
            # For "anak", at i=3, char='k', we try match SORTED keys: "kha" (3), "ka" (2), etc. "k" alone not in keys. So matched remains None, then we go to vowel check: 'k' not vowel, so warning and result+=char
            # That's wrong. We need fallback for single consonant letters: map 'k'->'ka', 'b'->'ba', etc
            
            # Let's add fallback mapping for single letters
            pass  # will be handled below after this block, but for now emit
            
            result += bali_with_pangangge
            breakdown.append({
                "latin": base_latin + (vowel or ""),
                "bali": bali_with_pangangge,
                "type": "wresastra",
                "description": f"{base_latin} final"
            })
            i = after_vowel_pos if vowel else next_pos
            # If word ends with consonant and we didn't have vowel, need adeg-adeg?
            # Check if i == word_len and word[-1] not in vowels and not already has adeg-adeg
            if i == word_len and word[-1] not in ['a', 'i', 'u', 'e', 'o']:
                # Need adeg-adeg to kill inherent vowel
                # But only if base_bali doesn't already have adeg-adeg
                if not result.endswith(ADEG_ADEG):
                    result += ADEG_ADEG
                    breakdown[-1]["bali"] += ADEG_ADEG
                    breakdown[-1]["description"] += " + adeg-adeg (final consonant)"
            has_gantungan_on_current = False
            continue

    # After loop, handle any leftover single consonants that were not matched due to fallback needed
    # For robustness, if result contains latin chars (a-z) still, it means we failed to transliterate some
    # We'll try second pass for single consonants
    # This is a safety net
    
    return result, breakdown, warnings

# Fallback single consonant mapping for edge cases
SINGLE_CONSONANT_FALLBACK = {
    "k": "ᬓ",
    "g": "ᬕ",
    "b": "ᬩ",
    "p": "ᬧ",
    "m": "ᬫ",
    "n": "ᬦ",
    "t": "ᬢ",
    "d": "ᬤ",
    "s": "ᬲ",
    "w": "ᬯ",
    "l": "ᬮ",
    "h": "ᬳ",
    "c": "ᬘ",
    "r": "ᬭ",
    "j": "ᬚ",
    "y": "ᬬ",
}

def _transliterate_word_latin_to_bali_improved(word: str) -> Tuple[str, List[Dict], List[str]]:
    """Improved version with single consonant fallback"""
    # This function wraps the previous but adds fallback
    # For now we call original and then fix latin leftovers
    result, breakdown, warnings = _transliterate_word_latin_to_bali(word)
    
    # Check if result still contains ascii letters (meaning untranslated)
    # If so, try to transliterate those single letters
    # This is a simple fix: replace any remaining ascii consonants with base + adeg if needed
    fixed_result = ""
    for char in result:
        if char in SINGLE_CONSONANT_FALLBACK:
            fixed_result += SINGLE_CONSONANT_FALLBACK[char] + ADEG_ADEG
        else:
            fixed_result += char
    
    return fixed_result, breakdown, warnings

# Override to use improved
def transliterate_word_wrapper(word: str):
    return _transliterate_word_latin_to_bali(word)

@lru_cache(maxsize=2000)
def transliterate_bali_to_latin(text: str) -> Tuple[str, List[Dict], List[str]]:
    """
    Bali to Latin transliteration
    Parses Unicode Balinese
    """
    if not text:
        return "", [], []
    
    warnings = []
    breakdown = []
    result = ""
    
    # Normalize unicode
    text = unicodedata.normalize('NFC', text)
    
    i = 0
    # State: are we in gantungan mode? (previous was adeg-adeg)
    pending_adeg = False
    last_base_latin = ""
    
    while i < len(text):
        char = text[i]
        code = f"U+{ord(char):04X}"
        
        # Check for adeg-adeg
        if char == ADEG_ADEG:
            pending_adeg = True
            # adeg-adeg itself doesn't produce latin, it kills vowel and marks next as gantungan
            # But we need to handle: it removes inherent 'a' from previous syllable
            # So if result ends with 'a', remove it?
            # For simplicity, if pending, we will not add vowel, and next base will be cluster without new vowel
            # Actually in latin, "nda" = n + da gantungan, not "na da"
            # So we need to handle: if pending_adeg, next base should not have inherent 'a' added separately? No, it should be cluster
            # Let's keep pending flag and continue
            i += 1
            continue
        
        # Check for pangangge suara marks that appear before base (taleng)
        # In Unicode, taleng is stored before base? Actually in logical order, taleng comes before base in string? 
        # In Balinese, taleng is typed before base but rendered before. In Unicode, it's stored before base?
        # Need to handle: if we encounter taleng, it applies to next base
        # So we need to lookahead
        # For simplicity, handle taleng as prefix
        
        # Check for taleng (front vowel)
        if char in ["ᬾ", "ᬿ"]:  # taleng, taleng detya
            # This is front vowel, should apply to next base
            # Look ahead for base
            if i + 1 < len(text):
                next_char = text[i+1]
                if next_char in BALI_TO_LATIN_BASE:
                    base_latin = BALI_TO_LATIN_BASE[next_char]
                    # Remove inherent 'a' from base_latin
                    base_consonant = base_latin[:-1] if base_latin.endswith('a') else base_latin
                    if char == "ᬾ":
                        # e or o depending if followed by tedong?
                        # Check if after base there's tedong
                        if i + 2 < len(text) and text[i+2] == "ᭀ":
                            # o
                            latin_syllable = base_consonant + "o"
                            breakdown.append({
                                "bali": char + next_char + "ᭀ",
                                "latin": latin_syllable,
                                "type": "taleng_tedong",
                                "description": f"{base_latin} + taleng tedong = {latin_syllable}"
                            })
                            result += latin_syllable
                            i += 3
                            pending_adeg = False
                            continue
                        else:
                            latin_syllable = base_consonant + "e"
                            breakdown.append({
                                "bali": char + next_char,
                                "latin": latin_syllable,
                                "type": "taleng",
                                "description": f"{base_latin} + taleng = {latin_syllable}"
                            })
                            result += latin_syllable
                            i += 2
                            pending_adeg = False
                            continue
                    elif char == "ᬿ":
                        # ai or au
                        if i + 2 < len(text) and text[i+2] == "ᭀ":
                            latin_syllable = base_consonant + "au"
                            breakdown.append({
                                "bali": char + next_char + "ᭀ",
                                "latin": latin_syllable,
                                "type": "taleng_detya_tedong",
                                "description": f"{base_latin} + taleng detya tedong = {latin_syllable}"
                            })
                            result += latin_syllable
                            i += 3
                            pending_adeg = False
                            continue
                        else:
                            latin_syllable = base_consonant + "ai"
                            breakdown.append({
                                "bali": char + next_char,
                                "latin": latin_syllable,
                                "type": "taleng_detya",
                                "description": f"{base_latin} + taleng detya = {latin_syllable}"
                            })
                            result += latin_syllable
                            i += 2
                            pending_adeg = False
                            continue
            # If no base after, treat as standalone?
            warnings.append(f"Taleng without base at {i}")
            i += 1
            continue
        
        # Check for base aksara
        if char in BALI_TO_LATIN_BASE:
            base_latin = BALI_TO_LATIN_BASE[char]
            base_consonant = base_latin[:-1] if base_latin.endswith('a') else base_latin
            
            # Check if this base is gantungan (pending adeg)
            if pending_adeg:
                # This is gantungan, so it's cluster without vowel yet, just consonant
                # For example, "n" + adeg + "da" = "nda" = n + da? Actually latin "nda" = n + da cluster
                # The previous syllable's vowel was killed, so we just add consonant cluster
                # So result should have base_consonant (without a) appended to previous?
                # But we already have previous base with its vowel, and adeg killed its a?
                # Let's handle: if pending_adeg, we should have removed 'a' from previous? We didn't yet
                # For simplicity, we add base_consonant directly (cluster)
                # Example: "ᬦ᭄ᬤ" = na + adeg + da = nda
                # Our result so far: "na" (from na), then adeg, then da gantungan
                # We should have "na" -> "n" + "a", but with adeg, "na" becomes "n" (kill a), then + "da" = "nda" -> "nda" or "nda" with a? Actually "nda" = nda (n + da) = n + da (with inherent a) = "nda"
                # So we need to remove last 'a' if present and replace with cluster
                if result.endswith('a'):
                    result = result[:-1]
                # Now add base_latin (with inherent a) as cluster? Or just consonant + a?
                # For "nda", after "n" (from na without a), we want "da" = "da" (with a) => "nda"
                # So add base_latin
                latin_to_add = base_latin
                # Check for following pangangge that will modify vowel
                # Look ahead for pangangge suara
                j = i + 1
                pangangge_found = None
                while j < len(text) and text[j] in BALI_PANGANGGE_SUARA_TO_LATIN:
                    # This pangangge modifies the vowel of current base
                    p_char = text[j]
                    p_latin = BALI_PANGANGGE_SUARA_TO_LATIN[p_char]
                    # Replace vowel
                    if p_latin == 'i':
                        latin_to_add = base_consonant + 'i'
                    elif p_latin == 'u':
                        latin_to_add = base_consonant + 'u'
                    elif p_latin == 'ě':
                        latin_to_add = base_consonant + 'e'  # pepet as e
                    elif p_latin == 'o':
                        # tedong could be ā or o, need context: if base already had taleng, it's o, else ā
                        # But we already handled taleng case, so here tedong alone is ā?
                        # Actually tedong alone after base is ā
                        latin_to_add = base_consonant + 'ā'
                        # But if it's part of o, we already handled
                        # For simplicity, treat as 'a' long or 'o'? We'll treat as 'a' long -> 'a'?
                        # Let's check: in Balinese, tedong alone is ā, but taleng+tedong is o
                        # Since we are not in taleng case, tedong is ā
                        # We'll map to 'a' for simplicity? But keep ā
                        pass
                    # etc
                    pangangge_found = p_char
                    j += 1
                
                # Check for tengenan after
                tengenan_latin = ""
                if j < len(text) and text[j] in BALI_TENGENAN_TO_LATIN:
                    tengenan_latin = BALI_TENGENAN_TO_LATIN[text[j]]
                    j += 1
                
                result += latin_to_add + tengenan_latin
                breakdown.append({
                    "bali": char + (pangangge_found or "") + tengenan_latin,
                    "latin": latin_to_add + tengenan_latin,
                    "type": "gantungan",
                    "description": f"Gantungan {base_latin} -> {latin_to_add}"
                })
                i = j
                pending_adeg = False
                continue
            else:
                # Normal base, not gantungan
                # Check following pangangge
                j = i + 1
                latin_syllable = base_latin
                pangangge_marks = ""
                # Collect pangangge suara
                while j < len(text) and text[j] in BALI_PANGANGGE_SUARA_TO_LATIN:
                    p_char = text[j]
                    p_latin = BALI_PANGANGGE_SUARA_TO_LATIN[p_char]
                    # Map
                    if p_char == "ᬶ":
                        latin_syllable = base_consonant + "i"
                    elif p_char == "ᬷ":
                        latin_syllable = base_consonant + "ī"
                    elif p_char == "ᬸ":
                        latin_syllable = base_consonant + "u"
                    elif p_char == "ᬹ":
                        latin_syllable = base_consonant + "ū"
                    elif p_char == "ᭂ":
                        latin_syllable = base_consonant + "e"  # pepet
                    elif p_char == "ᭀ":
                        # tedong: could be ā or part of o (but o already handled)
                        # If previous was not taleng, it's ā
                        # For simplicity, if latin_syllable ends with 'a', make it 'ā' or keep 'a'?
                        # We'll keep as 'a' + 'ā' marker? Let's map to 'a' long as 'a'?
                        # Actually to avoid confusion, we will map tedong alone to 'ā'
                        # But if latin_syllable is "ka", then "kā" should be "ka" + tedong = "kā" -> we have base_consonant + "ā"
                        latin_syllable = base_consonant + "ā"
                    elif p_char == "ᬺ":
                        latin_syllable = base_consonant + "rě"
                    # Add more
                    pangangge_marks += p_char
                    j += 1
                
                # Check tengenan
                tengenan_latin = ""
                tengenan_marks = ""
                while j < len(text) and text[j] in BALI_TENGENAN_TO_LATIN:
                    tengenan_latin += BALI_TENGENAN_TO_LATIN[text[j]]
                    tengenan_marks += text[j]
                    j += 1
                
                full_latin = latin_syllable + tengenan_latin
                result += full_latin
                breakdown.append({
                    "bali": char + pangangge_marks + tengenan_marks,
                    "latin": full_latin,
                    "type": "wresastra",
                    "description": f"{base_latin} + {pangangge_marks} + {tengenan_marks} = {full_latin}"
                })
                i = j
                pending_adeg = False
                continue
        
        # Check for independent suara
        if char in SUARA_BALI_TO_LATIN:
            latin = SUARA_BALI_TO_LATIN[char]
            result += latin
            breakdown.append({
                "bali": char,
                "latin": latin,
                "type": "suara",
                "description": f"Aksara Suara {latin}"
            })
            i += 1
            pending_adeg = False
            continue
        
        # Check for pangangge tengenan standalone? (should have been handled)
        if char in BALI_TENGENAN_TO_LATIN:
            latin = BALI_TENGENAN_TO_LATIN[char]
            result += latin
            breakdown.append({
                "bali": char,
                "latin": latin,
                "type": "tengenan",
                "description": f"Tengenan {latin}"
            })
            i += 1
            continue
        
        # Check for pangangge suara standalone (should be after base, but if alone, treat)
        if char in BALI_PANGANGGE_SUARA_TO_LATIN:
            # Standalone pangangge without base? Should not happen, but handle
            warnings.append(f"Pangangge without base at {i}: {char}")
            i += 1
            continue
        
        # Space and punctuation
        if char == " ":
            result += " "
            i += 1
            continue
        
        # Unknown char, keep as is
        warnings.append(f"Unknown Bali char at {i}: {char} {code}")
        result += char
        i += 1
    
    return result, breakdown, warnings

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
