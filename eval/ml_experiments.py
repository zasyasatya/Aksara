#!/usr/bin/env python3
"""Percobaan (eksperimen) retraining classifier Aksara Bali — reproducible.

Skrip ini memakai **kode yang sama persis** dengan Panel Admin → Model ML
(``backend/app/ml``): dataset sintetis dibangkitkan dengan renderer + augmentasi
yang sama, model dilatih lewat ``training.run_training_sync`` (pipeline job yang
sama), dan laporan metrik dihitung oleh ``metrics.classification_report``.

Semua artefak ditulis ke direktori sementara (store di-*patch*), jadi skrip ini
TIDAK menyentuh dataset/model nyata di ``backend/app/data/ml``.

Tiga percobaan:

1. **Benchmark arsitektur** — 6 arsitektur, hyperparameter default, dataset
   sintetis N/kelas (default 60), split 70/15/15 stratified.
   Metrik: accuracy, precision/recall/F1 makro, top-3, log-loss, train acc,
   durasi latih, jumlah parameter, ukuran model.
2. **Uji pergeseran distribusi (shift)** — model yang sama dievaluasi pada set
   sintetis *lebih sulit* (augmentasi lebih kuat, seed berbeda) untuk melihat
   arsitektur mana yang paling tahan terhadap variasi tulisan.
3. **Ablasi ukuran data** (``--ablation``) — akurasi vs jumlah sampel per kelas,
   untuk memperkirakan berapa banyak sampel berlabel yang perlu dikumpulkan.

Jalankan dari root repo (butuh dependensi backend: numpy, Pillow, fastapi):

    backend/.venv/bin/python eval/ml_experiments.py
    backend/.venv/bin/python eval/ml_experiments.py --per-class 80 --ablation \
        --out-md eval/results/ml_experiments.md --out-json eval/results/ml_experiments.json

HASIL ADALAH METRIK PADA DATASET SINTETIS — bukan klaim performa pada tulisan
tangan manusia sungguhan. Gunakan tab Dataset di Panel Admin untuk mengumpulkan
tinta nyata, lalu jalankan retraining dari sana.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import numpy as np  # noqa: E402

from app.ml import features, inference, metrics, models, store, synthetic, training  # noqa: E402

ARCH_ORDER = ["template", "centroid", "knn", "logreg", "mlp", "cnn"]


# ── util ───────────────────────────────────────────────────────────────────

def pct(x: Optional[float]) -> str:
    return "—" if x is None else f"{x * 100:.1f}%"


def fmt_bytes(n: Optional[int]) -> str:
    if n is None:
        return "—"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / 1024 / 1024:.1f} MB"


def md_table(headers: List[str], rows: List[List[str]], align: Optional[List[str]] = None) -> str:
    align = align or (["l"] + ["r"] * (len(headers) - 1))
    sep = {"l": ":--", "r": "--:", "c": ":-:"}
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep[a] for a in align) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def use_temp_store(base: Path) -> None:
    """Arahkan semua path ``store`` ke direktori sementara (sama seperti test)."""
    ml = base / "ml"
    store.ML_DIR = ml
    store.DATASET_DIR = ml / "dataset"
    store.IMAGES_DIR = ml / "dataset" / "images"
    store.INDEX_PATH = ml / "dataset" / "index.json"
    store.MODELS_DIR = ml / "models"
    store.REGISTRY_PATH = ml / "models" / "registry.json"
    store.CLASSES_PATH = ml / "classes.json"
    inference.invalidate()


def reset_dataset() -> None:
    """Kosongkan dataset + registry di store sementara."""
    import shutil

    if store.ML_DIR.exists():
        shutil.rmtree(store.ML_DIR)
    inference.invalidate()


def build_dataset(groups: List[str], per_class: int, seed: int, strength: float) -> Dict:
    classes_all = {c.label: c for c in store.all_available_classes()}
    wanted = synthetic.build_classes(store._master(), tuple(groups))
    store.set_classes([c.label for c in wanted])
    glyph_classes = [classes_all[c.label] for c in wanted]
    items = []
    for cls, ink, meta in synthetic.generate_samples(glyph_classes, per_class, seed, strength):
        items.append((ink, cls.label, "synthetic", None, "", {"seed": seed, **meta}))
    store.add_samples_bulk(items)
    store.rebalance_splits(seed=seed)
    return store.dataset_stats()


def shift_set(groups: List[str], per_class: int, seed: int, strength: float):
    """Set evaluasi 'lebih sulit' (tidak masuk store) → (X, y) dengan urutan label store."""
    labels = store.class_labels()
    idx = {l: i for i, l in enumerate(labels)}
    classes_all = {c.label: c for c in store.all_available_classes()}
    glyph_classes = [classes_all[l] for l in labels]
    X, y = [], []
    for cls, ink, _meta in synthetic.generate_samples(glyph_classes, per_class, seed, strength):
        X.append(features.features_from_ink(ink))
        y.append(idx[cls.label])
    return np.stack(X).astype(np.float32), np.asarray(y, dtype=np.int64)


def train(arch: str, hp: Optional[Dict], name: str) -> Dict:
    t0 = time.time()
    job = training.run_training_sync(arch, hp, name=name)
    if job["status"] != "done":
        raise RuntimeError(f"Job {arch} gagal: {job.get('error') or job.get('message')}")
    entry = store.get_model_entry(job["model_id"])
    report = store.read_report(job["model_id"])
    assert entry and report
    return {"job": job, "entry": entry, "report": report, "wall_seconds": time.time() - t0}


def evaluate_shift(model_id: str, X: np.ndarray, y: np.ndarray) -> Dict:
    model = inference.load_model(model_id)
    proba = model.predict_proba(X)
    rep = metrics.classification_report(y, proba.argmax(axis=1), store.class_labels(), proba)
    return {"accuracy": rep["accuracy"], "macro_f1": rep["macro_f1"], "top3_accuracy": rep.get("top3_accuracy")}


# ── percobaan ──────────────────────────────────────────────────────────────

def experiment_benchmark(args, results: Dict, lines: List[str]) -> List[Dict]:
    stats = build_dataset(args.groups, args.per_class, args.seed, args.strength)
    results["dataset"] = {
        "groups": args.groups, "per_class": args.per_class, "seed": args.seed, "strength": args.strength,
        "labeled": stats["labeled"], "n_classes": stats["n_classes"], "per_split": stats["per_split"],
    }
    lines.append(f"## 1. Benchmark arsitektur\n")
    lines.append(
        f"Dataset sintetis: **{stats['labeled']} sampel**, {stats['n_classes']} kelas "
        f"({', '.join(args.groups)}), {args.per_class}/kelas, augmentasi strength {args.strength}, seed {args.seed}. "
        f"Split train/val/test = {stats['per_split']['train']}/{stats['per_split']['val']}/{stats['per_split']['test']} "
        f"(stratified). Evaluasi pada split **test**.\n"
    )
    Xs, ys = shift_set(args.groups, args.shift_per_class, args.seed + 7919, args.shift_strength)
    lines.append(
        f"Uji pergeseran (shift): {len(ys)} sampel baru dengan augmentasi lebih kuat "
        f"(strength {args.shift_strength}, seed berbeda) — tidak pernah dilihat saat training.\n"
    )

    runs: List[Dict] = []
    for arch in args.archs:
        hp = models.default_hyperparams(arch)
        print(f"[benchmark] melatih {arch} …", flush=True)
        r = train(arch, hp, f"bench-{arch}")
        r["shift"] = evaluate_shift(r["entry"]["id"], Xs, ys)
        r["arch"] = arch
        runs.append(r)
        rep = r["report"]
        print(
            f"           acc {pct(rep['accuracy'])} · F1 {pct(rep['macro_f1'])} · "
            f"shift acc {pct(r['shift']['accuracy'])} · {r['entry']['train_seconds']:.1f}s",
            flush=True,
        )

    headers = ["Arsitektur", "Accuracy", "Precision", "Recall", "F1 (makro)", "Top-3", "Log-loss",
               "Train acc", "Acc (shift)", "F1 (shift)", "Latih", "Param", "Ukuran"]
    rows = []
    for r in runs:
        rep, e = r["report"], r["entry"]
        rows.append([
            f"**{e['arch_name']}** (`{r['arch']}`)", pct(rep["accuracy"]), pct(rep["macro_precision"]),
            pct(rep["macro_recall"]), pct(rep["macro_f1"]), pct(rep.get("top3_accuracy")),
            f"{rep['log_loss']:.3f}" if rep.get("log_loss") is not None else "—",
            pct(rep.get("train_accuracy")), pct(r["shift"]["accuracy"]), pct(r["shift"]["macro_f1"]),
            f"{e['train_seconds']:.1f} s", f"{e['n_params']:,}".replace(",", "."), fmt_bytes(e["size_bytes"]),
        ])
    lines.append(md_table(headers, rows) + "\n")

    best = max(runs, key=lambda r: (r["report"]["macro_f1"], r["shift"]["macro_f1"]))
    lines.append(f"Model terbaik (F1 makro test): **{best['entry']['arch_name']}** — "
                 f"F1 {pct(best['report']['macro_f1'])}, akurasi {pct(best['report']['accuracy'])}.\n")

    # per-kelas untuk model terbaik
    rep = best["report"]
    lines.append(f"### Per kelas — {best['entry']['arch_name']}\n")
    rows = [[p["label"], pct(p["precision"]), pct(p["recall"]), pct(p["f1"]), str(p["support"])]
            for p in rep["per_class"]]
    lines.append(md_table(["Kelas", "Precision", "Recall", "F1", "Support"], rows) + "\n")
    if rep.get("top_confusions"):
        conf = ", ".join(f"{c['true']}→{c['pred']} ×{c['count']}" for c in rep["top_confusions"][:8])
        lines.append(f"Paling sering tertukar: {conf}.\n")

    # hyperparameter yang dipakai
    lines.append("### Hyperparameter (default panel admin)\n")
    rows = [[f"`{r['arch']}`", "`" + json.dumps(r["entry"]["hyperparams"], ensure_ascii=False) + "`"] for r in runs]
    lines.append(md_table(["Arsitektur", "Hyperparameter"], rows, ["l", "l"]) + "\n")

    results["benchmark"] = [
        {
            "arch": r["arch"], "arch_name": r["entry"]["arch_name"], "hyperparams": r["entry"]["hyperparams"],
            "metrics": r["entry"]["metrics"], "shift": r["shift"], "train_seconds": r["entry"]["train_seconds"],
            "n_params": r["entry"]["n_params"], "size_bytes": r["entry"]["size_bytes"],
            "per_class": r["report"]["per_class"], "top_confusions": r["report"].get("top_confusions", []),
        }
        for r in runs
    ]
    return runs


def experiment_ablation(args, results: Dict, lines: List[str]) -> None:
    sizes = args.ablation_sizes
    archs = [a for a in args.ablation_archs if a in args.archs or a in ARCH_ORDER]
    lines.append("## 2. Ablasi ukuran data (sampel per kelas)\n")
    lines.append("Akurasi test / F1 makro saat jumlah sampel per kelas bertambah (hyperparameter default, "
                 "dataset dibangkitkan ulang per ukuran, seed sama).\n")
    table: Dict[str, Dict[int, Dict]] = {a: {} for a in archs}
    for n in sizes:
        reset_dataset()
        build_dataset(args.groups, n, args.seed, args.strength)
        for arch in archs:
            print(f"[ablasi] {arch} @ {n}/kelas …", flush=True)
            r = train(arch, models.default_hyperparams(arch), f"abl-{arch}-{n}")
            table[arch][n] = {"accuracy": r["report"]["accuracy"], "macro_f1": r["report"]["macro_f1"],
                              "train_seconds": r["entry"]["train_seconds"]}
            print(f"         acc {pct(r['report']['accuracy'])} · F1 {pct(r['report']['macro_f1'])}", flush=True)
    headers = ["Arsitektur"] + [f"{n}/kelas" for n in sizes]
    rows = [[f"`{a}`"] + [f"{pct(table[a][n]['accuracy'])} / {pct(table[a][n]['macro_f1'])}" for n in sizes] for a in archs]
    lines.append(md_table(headers, rows) + "\n")
    lines.append("Format sel: akurasi / F1 makro.\n")
    results["ablation"] = {"sizes": sizes, "archs": archs,
                           "table": {a: {str(n): v for n, v in d.items()} for a, d in table.items()}}


# ── main ───────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archs", default=",".join(ARCH_ORDER), help="daftar arsitektur, pisahkan koma")
    ap.add_argument("--groups", default="wresastra", help="kelompok aksara: wresastra,swalalita,suara,angka")
    ap.add_argument("--per-class", type=int, default=60, help="sampel sintetis per kelas (default 60)")
    ap.add_argument("--strength", type=float, default=1.0, help="kekuatan augmentasi dataset latih")
    ap.add_argument("--shift-per-class", type=int, default=20, help="sampel per kelas untuk uji shift")
    ap.add_argument("--shift-strength", type=float, default=1.6, help="kekuatan augmentasi uji shift")
    ap.add_argument("--seed", type=int, default=20260904)
    ap.add_argument("--ablation", action="store_true", help="jalankan juga ablasi ukuran data")
    ap.add_argument("--ablation-sizes", default="10,20,40,80")
    ap.add_argument("--ablation-archs", default="logreg,mlp,cnn")
    ap.add_argument("--out-md", type=Path, help="tulis laporan markdown ke file")
    ap.add_argument("--out-json", type=Path, help="tulis hasil mentah JSON ke file")
    ap.add_argument("--keep-dir", type=Path, help="simpan artefak (dataset+model) ke direktori ini alih-alih temp")
    args = ap.parse_args()
    args.archs = [a.strip() for a in args.archs.split(",") if a.strip()]
    args.groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    args.ablation_sizes = [int(x) for x in args.ablation_sizes.split(",") if x.strip()]
    args.ablation_archs = [a.strip() for a in args.ablation_archs.split(",") if a.strip()]
    unknown = [a for a in args.archs if a not in models.ARCH_BY_ID]
    if unknown:
        ap.error(f"arsitektur tidak dikenal: {unknown}; pilihan: {list(models.ARCH_BY_ID)}")

    started = datetime.now(timezone.utc)
    results: Dict = {
        "generated_at": started.isoformat(timespec="seconds"),
        "python": platform.python_version(), "numpy": np.__version__, "machine": platform.machine(),
        "args": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
    }
    lines: List[str] = [
        "# Hasil percobaan retraining classifier Aksara Bali\n",
        f"Dibangkitkan `{started.strftime('%Y-%m-%d %H:%M UTC')}` oleh `eval/ml_experiments.py` "
        f"(Python {platform.python_version()}, NumPy {np.__version__}, CPU {platform.machine()}). "
        "Semua model murni NumPy di CPU — angka durasi tergantung mesin.\n",
        "> Metrik pada **dataset sintetis** (glyph Noto Sans Balinese + augmentasi), bukan tulisan tangan manusia.\n",
    ]

    def run_all(base: Path) -> None:
        use_temp_store(base)
        t0 = time.time()
        experiment_benchmark(args, results, lines)
        if args.ablation:
            experiment_ablation(args, results, lines)
        results["total_seconds"] = round(time.time() - t0, 1)
        lines.append(f"Total waktu percobaan: {results['total_seconds']:.0f} detik.\n")

    if args.keep_dir:
        args.keep_dir.mkdir(parents=True, exist_ok=True)
        run_all(args.keep_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="aksara-ml-exp-") as tmp:
            run_all(Path(tmp))

    report_md = "\n".join(lines)
    print("\n" + report_md)
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(report_md + "\n", encoding="utf-8")
        print(f"\n→ markdown: {args.out_md}")
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"→ json: {args.out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
