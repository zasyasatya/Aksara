#!/usr/bin/env python3
"""Evaluasi **tingkat halaman** untuk OCR Lens (segmentasi + klasifikasi + decoding).

``eval/evaluate_handwriting.py`` mengukur akurasi klasifikasi satu aksara pada kotak
potongan bersih. Halaman ini menjawab pertanyaan yang benar-benar penting untuk fitur
kamera: *berapa banyak teks yang berhasil dibaca ulang bila mesin harus mencari sendiri
aksara/huruf pada citra?*

Dua jenis uji:

1. **Halaman render** — teks known dirender dengan font yang sama dengan dataset cetak
   (Noto Sans Balinese / DejaVu) pada beberapa ukuran, lalu di-OCR. Mengukur
   segmentasi + decoding secara terkontrol.
2. **Kata tulisan tangan nyata** — citra kata pada repositori Caraka
   (``test_images/Aksara_Bali/*.png``) whose nama file adalah teks Latin-nya.
   Hasil OCR Aksara ditransliterasi balik ke Latin lalu dibandingkan dengan nama file.

Cara pakai::

    .venv/bin/python eval/evaluate_ocr.py                      # render saja
    .venv/bin/python eval/evaluate_ocr.py --caraka /tmp/caraka/aksara-datasets-main
    .venv/bin/python eval/evaluate_ocr.py --set tta=4 --set script=auto

Keluaran: ``eval/results/OCR_LENS_PAGES.md`` + ``ocr_lens_pages.json``.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.ocr import pipeline, render  # noqa: E402
from app.services.transliterator import transliterate  # noqa: E402

RESULTS = ROOT / "eval" / "results"

PAGES: Dict[str, List[str]] = {
    "aksara": [
        "ᬩᬮᬶ",
        "ᬓᬭ",
        "ᬲᬬ",
        "ᬓᬭ ᬩᬮᬶ",
        "ᬓᬭ\nᬩᬮᬶ",
        "ᬲᬬ ᬓᬭ",
        "ᬤᬢ ᬩᬶ ᬫᬬ",
        "ᬔᬦ ᬘᬬ ᬤᬢ",
        "ᬩᬮᬶ ᬩᬮᬶ ᬩᬮᬶ",
        "ᬓᬭ ᬓᬭ ᬓᬭ ᬩᬮᬶ",
    ],
    "latin": [
        "ok",
        "oo",
        "hello world",
        "balinese script",
        "aksara bali",
        "Aksara Bali\nLearn Balinese Script",
        " read the palm leaf",
        "Tulisan Bali Latin",
        "the quick brown fox",
        "ok0123 456789",
    ],
}


def lev(a: Sequence[str], b: Sequence[str]) -> int:
    n, m = len(a), len(b)
    if n == 0:
        return m
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[m]


def labels_of(text: str, task: str, char_to_label: Dict[str, str]) -> List[str]:
    if task == "aksara":
        return [char_to_label[c] for c in text if c.strip() and c in char_to_label]
    return [c.lower() for c in text if c.strip().isalnum()]


def eval_render(task: str, options: Dict, sizes: List[int]) -> Dict:
    from app.ml import store

    classes = store.get_classes(task)
    c2l = {c["glyph"]: c["label"] for c in classes if c.get("glyph")}
    l2g = {c["label"]: (c.get("glyph") or c["label"]) for c in classes}
    out: Dict = {"task": task, "sizes": {}}
    for fs in sizes:
        rows, n_exact, tot_edit, tot_len, n_lines, n_ref = [], 0, 0, 0, 0, 0
        t0 = time.time()
        for text in PAGES[task]:
            png = render.render_page(text, font_size=fs)
            res = pipeline.scan_bytes(png, options={**options, "script": task})
            ref = labels_of(text, task, c2l)
            hyp: List[str] = []
            for ln in res["lines"]:
                hyp += [g["label"] for g in ln["glyphs"] if g.get("label")]
            d = lev(ref, hyp)
            tot_edit += d
            tot_len += max(1, len(ref))
            n_exact += int(ref == hyp)
            n_lines += len(res["lines"])
            n_ref += text.count("\n") + 1
            rows.append({"text_ref": text.replace("\n", " / "), "text_hyp": "".join(l2g.get(x, "?") for x in hyp),
                         "ref": len(ref), "hyp": len(hyp), "edits": d, "exact": ref == hyp})
        secs = time.time() - t0
        out["sizes"][fs] = {
            "pages": len(PAGES[task]),
            "line_exact_rate": round(n_exact / max(1, len(PAGES[task])), 3),
            "cer": round(tot_edit / max(1, tot_len), 3),
            "line_count_ratio": round(n_lines / max(1, n_ref), 3),
            "ms_per_page": round(1000 * secs / max(1, len(PAGES[task]))),
            "rows": rows,
        }
    return out


def norm_vowel(text: str) -> str:
    """Hapus aksara "a" legya — ejaan Bali tidak menulisnya, jadi "basa" = "bahasa"."""
    return re.sub("a", "", text)


def eval_words(dir_path: Path, options: Dict, limit: int = 40) -> Dict:
    files = sorted(glob.glob(str(dir_path / "test_images" / "Aksara_Bali" / "*.png")))
    if not files:
        return {"available": False, "dir": str(dir_path)}
    rows = []
    for f in files[:limit]:
        gold = re.sub(r"[^a-z]", "", Path(f).stem.lower())
        t0 = time.time()
        try:
            res = pipeline.scan_bytes(Path(f).read_bytes(), options={**options, "script": "aksara"})
        except Exception as exc:  # pragma: no cover
            rows.append({"file": Path(f).name, "gold": gold, "error": str(exc)})
            continue
        aks = res["text"]["aksara"].replace("\n", " ").strip()
        lat = transliterate(aks, "bali-to-latin", True)[0] if aks else ""
        got = re.sub(r"[^a-z]", "", (lat or "").lower())
        d = min(lev(gold, got), lev(norm_vowel(gold), norm_vowel(got)))
        rows.append({"file": Path(f).name, "gold": gold, "aksara": aks, "latin": lat,
                     "glyphs": res["stats"]["glyphs"], "ms": int((time.time() - t0) * 1000),
                     "cer": round(d / max(1, len(gold)), 3),
                     "exact": gold == got or norm_vowel(gold) == norm_vowel(got),
                     "close": d <= max(1, int(0.25 * len(gold)))})
    n = max(1, len(rows))
    return {
        "available": True, "dir": str(dir_path), "n": len(rows),
        "exact_rate": round(sum(r.get("exact", False) for r in rows) / n, 3),
        "close_rate": round(sum(r.get("close", False) for r in rows) / n, 3),
        "mean_cer": round(float(sum(r.get("cer", 1.0) for r in rows) / n), 3),
        "ms_mean": round(float(sum(r.get("ms", 0) for r in rows) / n)),
        "rows": rows,
    }


def write_md(out: Dict) -> None:
    L: List[str] = ["# OCR Lens — evaluasi tingkat halaman", "",
                    f"Dihasilkan `eval/evaluate_ocr.py` (diperbarui {out['created']}).", "",
                    "Angka di bawah mengukur **seluruh pipeline kamera** (praproses → segmentasi →",
                    "klasifikasi → decoding kamus), bukan hanya klasifikasi satu aksara. Oleh karena itu",
                    "nilainya di bawah akurasi per-glyph pada `OCR_LENS_MODELS.md`.", ""]
    L += ["## Halaman render (label space)"]
    for task in ("aksara", "latin"):
        e = out["render"].get(task, {})
        if not e:
            continue
        L += ["", f"### Tugas `{task}`", "", "| Ukuran font | Exact line | CER | Rasio jumlah baris | ms/halaman |",
              "| --- | ---: | ---: | ---: | ---: |"]
        for fs, r in sorted(e["sizes"].items(), key=lambda kv: int(kv[0])):
            L.append(f"| {fs} px | {r['line_exact_rate'] * 100:.1f}% | {r['cer'] * 100:.1f}% | "
                     f"{r['line_count_ratio']:.2f} | {r['ms_per_page']} |")
    w = out.get("words", {})
    L += ["", "## Kata tulisan tangan nyata (Caraka, `test_images/Aksara_Bali`)"]
    if not w.get("available"):
        L += ["", "_Tidak diuji — jalankan dengan `--caraka <folder>` (tarball repositori Caraka)._"]
    else:
        L += ["", f"n={w['n']} · kata tepat **{w['exact_rate'] * 100:.1f}%** (setara setelah huruf a legya "
                  "dilepas) · mendekati (CER≤25%) "
                  f"**{w['close_rate'] * 100:.1f}%** · CER rata-rata {w['mean_cer'] * 100:.1f}% · "
                  f"{w['ms_mean']} ms/kata", "",
              "| Berkas (nama = teks) | OCR (aksara) | OCR → Latin | target | CER |", "| --- | --- | --- | --- | ---: |"]
        for r in w["rows"]:
            if r.get("error"):
                L.append(f"| {r['file']} | error | | {r['gold']} | - |")
                continue
            L.append(f"| {r['file']} | `{r['aksara'][:22]}` | `{r['latin'][:18]}` | {r['gold']} | "
                     f"{r['cer'] * 100:.0f}% |")
    L += ["", "## Catatan", "",
          "- Huruf Bali yang dirangkai *pasangan* (aksara + virama) dibentuk font menjadi satu ligatura;",
          "  kelas pasangan tidak ada di dataset Caraka, sehingga rangkaian itu dibaca",
          "  sebagai kombinasi terdekat. Koreksi pengguna (halaman Lens → „kirim koreksi”) mengisi",
          "  celah ini lewat retraining admin.",
          "- Uji mandiri di Panel Admin memakai mekanisme yang sama (`app/ocr/render.py`).", ""]
    (RESULTS / "OCR_LENS_PAGES.md").write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--caraka", default="/tmp/caraka/aksara-datasets-main", type=Path)
    ap.add_argument("--sizes", default="48,72,96")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--skip-words", action="store_true")
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="K=V",
                    help="opsi pipeline, mis. --set tta=4 --set use_language_model=false")
    args = ap.parse_args()

    options: Dict = {}
    for spec in args.set:
        k, _, v = spec.partition("=")
        v = v.strip()
        if v.lower() in ("true", "false"):
            options[k.strip()] = v.lower() == "true"
        else:
            try:
                options[k.strip()] = float(v) if "." in v else int(v)
            except ValueError:
                options[k.strip()] = v
    RESULTS.mkdir(parents=True, exist_ok=True)
    out: Dict = {"created": time.strftime("%Y-%m-%d %H:%M"), "options": options, "render": {}}

    if not args.skip_render:
        for task in ("aksara", "latin"):
            print(f"render {task} ...", flush=True)
            out["render"][task] = eval_render(task, options, [int(x) for x in args.sizes.split(",")])
            for fs, r in sorted(out["render"][task]["sizes"].items(), key=lambda kv: int(kv[0])):
                print(f"  {fs}px: exact {r['line_exact_rate'] * 100:.1f}%  CER {r['cer'] * 100:.1f}%  "
                      f"lines {r['line_count_ratio']:.2f}  {r['ms_per_page']}ms", flush=True)
    if not args.skip_words:
        print("kata nyata (Caraka) ...", flush=True)
        out["words"] = eval_words(args.caraka, options, args.limit)
        if out["words"].get("available"):
            print(f"  n={out['words']['n']} exact {out['words']['exact_rate'] * 100:.1f}% "
                  f"close {out['words']['close_rate'] * 100:.1f}% CER {out['words']['mean_cer'] * 100:.1f}%",
                  flush=True)
        else:
            print("  dilewati (folder tidak ada)")

    write_md(out)
    (RESULTS / "ocr_lens_pages.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n→ {RESULTS / 'OCR_LENS_PAGES.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
