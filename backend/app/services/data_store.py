"""Penyimpanan JSON thread-safe untuk konten yang bisa diedit guru.

Semua pembaca/pengguna konten dinamis (lessons, quiz, dictionary) harus
melalui modul ini agar editan guru langsung terlihat tanpa restart server.
Penulisan dilakukan atomik (file sementara + os.replace).
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).parent.parent / "data"

_lock = threading.RLock()


def _read(name: str) -> Any:
    with _lock:
        with open(DATA_DIR / name, "r", encoding="utf-8") as f:
            return json.load(f)


def _write(name: str, data: Any) -> None:
    with _lock:
        tmp = DATA_DIR / f"{name}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_DIR / name)


# ── Lessons (materi) ────────────────────────────────────────────────────

def get_lessons() -> List[Dict[str, Any]]:
    return _read("lessons.json")


def save_lessons(lessons: List[Dict[str, Any]]) -> None:
    _write("lessons.json", lessons)


def get_lesson(lesson_id: str) -> Dict[str, Any] | None:
    return next((l for l in get_lessons() if l.get("id") == lesson_id), None)


# ── Quizzes (kuis) ──────────────────────────────────────────────────────

def get_quizzes() -> List[Dict[str, Any]]:
    return _read("quiz.json")


def save_quizzes(quizzes: List[Dict[str, Any]]) -> None:
    _write("quiz.json", quizzes)


def get_quiz(quiz_id: str) -> Dict[str, Any] | None:
    return next((q for q in get_quizzes() if q.get("id") == quiz_id), None)


# ── Dictionary (kamus kata khusus) ──────────────────────────────────────

def get_dictionary() -> Dict[str, Dict[str, Any]]:
    return _read("dictionary.json")


def save_dictionary(data: Dict[str, Dict[str, Any]]) -> None:
    _write("dictionary.json", data)


# ── Aksara master (read-only reference untuk form guru) ─────────────────

def get_aksara_master() -> Dict[str, Any]:
    return _read("aksara_master.json")


# ── Engagement (counter & sekolah mitra) ───────────────────────────────
# Data "proof of concept": kunjungan, twibbon yang dibuat, dan daftar
# sekolah/sanggar yang mendaftar kemitraan. Dipakai di paper & landing.

def get_engagement() -> Dict[str, Any]:
    data = _read("engagement.json")
    data.setdefault("visits", 0)
    data.setdefault("twibbons", 0)
    data.setdefault("schools", [])
    return data


def save_engagement(data: Dict[str, Any]) -> None:
    _write("engagement.json", data)


def bump_engagement(key: str) -> Dict[str, Any]:
    """Tambahkan 1 pada counter (visits/twibbons) dan kembalikan data terbaru."""
    with _lock:
        data = _read("engagement.json")
        data.setdefault("visits", 0)
        data.setdefault("twibbons", 0)
        data.setdefault("schools", [])
        data[key] = int(data.get(key, 0)) + 1
        tmp = DATA_DIR / "engagement.json.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_DIR / "engagement.json")
        return data


# ── Pengaturan aplikasi (tema/palet warna) ─────────────────────────────

def get_app_settings() -> Dict[str, Any]:
    path = DATA_DIR / "settings.json"
    if not path.is_file():
        return {"theme": "native"}
    data = _read("settings.json")
    data.setdefault("theme", "native")
    return data


def save_app_settings(data: Dict[str, Any]) -> None:
    _write("settings.json", data)
