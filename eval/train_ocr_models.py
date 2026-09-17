#!/usr/bin/env python3
"""Latih model OCR Lens pada dataset aktual & simpan sebagai model bawaan (bundled).

Model hasil skrip ini dikomit ke ``backend/app/data/ml_bundled/<task>/<model_id>/``
sehingga aplikasi **langsung bisa dipakai tanpa training ulang** (Panel Admin tetap
dapat melatih ulang dan memindahkan model produksi kapan saja).

Alur:

1. store sementara → impor paket dataset repo (tulisan tangan nyata + print)
2. latih ``deepcnn`` per tugas (aksara, latin) dengan augmentasi on-the-fly
3. evaluasi pada split test:
   • campuran print+tulisan tangan  • **hanya tulisan tangan nyata** (headline)
   • akurasi, F1 makro, top-3, loss, CER, matriks kebingungan, tabel per kelas
4. salin artefak model + report ke ``backend/app/data/ml_bundled`` + ringkasan
   markdown ke ``eval/results/``

Jalankan dari root repo:

    .venv/bin/python eval/train_ocr_models.py                      # kedua tugas
    .venv/bin/python eval/train_ocr_models.py --task aksara --epochs 60
    .venv/bin/python eval/train_ocr_models.py --quick              # smoke test
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import numpy as np  # noqa: E402

from app.ml import bundled, features, metrics as ml_metrics, models as ml_models, store, training  # noqa: E402

BUNDLED_DIR = BACKEND / "app" / "data" / "ml_bundled"

PACKS = {
    "aksara": ["caraka-aksara-bali-v1", "aksara-bali-print-v1"],
    "latin": ["omniglot-latin-handwriting-v1", "latin-print-v1"],
}
# paket yang berasal dari tulisan tangan manusia (untuk evaluasi terpisah)
REAL_PACKS = {"caraka-aksara-bali-v1", "omniglot-latin-handwriting-v1"}


def load_packs(task: str) -> dict:
    out = {}
    for name in PACKS[task]:
        r = bundled.import_bundled(name, task=task, replace_existing=(name in REAL_PACKS))
        out[name] = r["added"]
    return out


def is_real_sample(meta: dict) -> bool:
    """Sampel berasal dari goresan tangan manusia (bukan render font)?"""
    meta = meta or {}
    return meta.get("kind") == "handwriting-real" or meta.get("dataset") in REAL_PACKS


def real_mask(ids, task: str) -> np.ndarray:
    """Penanda sampel split test yang berasal dari tulisan tangan manusia."""
    return np.array([is_real_sample((store.get_sample(str(sid), task) or {}).get("meta")) for sid in ids], dtype=bool)


TASK = "aksara"


def train_task(task: str, args) -> dict:
    global TASK
    TASK = task
    store.ensure_dirs(task)
    added = load_packs(task)
    stats = store.dataset_stats(task)
    labels = store.class_labels(task)
    print(f"\n=== tugas '{task}' === dataset {stats['labeled']} berlabel · {len(labels)} kelas · {added}")

    hp = {
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "min_learning_rate": args.lr * 0.02,
        "augment": args.augment,
        "class_balance": args.class_balance,
        "hidden_units": args.hidden,
        "conv1_filters": args.f1,
        "conv2_filters": args.f2,
        "label_smoothing": args.label_smoothing,
        "eval_tta": 0,
    }
    if args.quick:
        hp.update({"epochs": 6, "batch_size": 128, "conv1_filters": 8, "conv2_filters": 12, "hidden_units": 48})

    X_tr, y_tr, _ = store.load_matrix("train", labels, task)
    X_va, y_va, _ = store.load_matrix("val", labels, task)
    X_te, y_te, ids_te = store.load_matrix("test", labels, task)
    is_real = real_mask(ids_te, task)
    model = ml_models.create_model(args.arch, len(labels), hp)
    print(f"training {args.arch}: {len(X_tr)} latih · {len(X_va)} val · {len(X_te)} test "
          f"({int(is_real.sum())} tulisan tangan nyata) …", flush=True)
    t0 = time.time()
    last = [0.0]

    def prog(rec):
        el = time.time() - t0
        if rec["epoch"] % max(1, args.log_every) == 0 or rec["epoch"] == hp["epochs"]:
            print(f"  ep {rec['epoch']:>3}/{hp['epochs']}  loss {rec['loss']:.3f}  "
                  f"train {rec['train_acc']:.3f}  val {rec['val_acc']:.3f}  "
                  f"lr {rec.get('lr')}  [{el - last[0]:.0f}s]", flush=True)
            last[0] = el

    model.fit(X_tr, y_tr, X_va, y_va, progress=prog)
    secs = round(time.time() - t0, 1)

    tta = args.tta
    p_all = model.predict_proba(X_te, tta=tta) if tta else model.predict_proba(X_te)
    rep_all = ml_metrics.classification_report(y_te, p_all.argmax(1), labels, p_all)
    rep_all["char_error_rate"] = round(float((p_all.argmax(1) != y_te).mean()), 4)
    real = is_real
    rep_real = (
        ml_metrics.classification_report(y_te[real], p_all[real].argmax(1), labels, p_all[real])
        if real.any() else None
    )
    if rep_real:
        rep_real["char_error_rate"] = round(float((p_all[real].argmax(1) != y_te[real]).mean()), 4)
        rep_real["n"] = int(real.sum())
    rep_all["n"] = int(len(y_te))
    rep_all["train_accuracy"] = round(float((model.predict_proba(X_tr[:1500]).argmax(1) == y_tr[:1500]).mean()), 4)
    rep_all["eval_split"] = "test"
    rep_all["task"] = task
    rep_all["train_seconds"] = secs
    rep_all["history"] = model.history
    rep_all["eval_tta"] = tta
    rep_all["real_handwriting"] = rep_real
    rep_all["misclassified"] = [
        {"sample_id": str(ids_te[i]), "true": labels[int(y_te[i])], "pred": labels[int(p_all[i].argmax())],
         "confidence": round(float(p_all[i].max()), 4), "real": bool(real[i])}
        for i in np.where(p_all.argmax(1) != y_te)[0][:40]
    ]

    model_id = f"lens-{task}-{args.arch}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    folder = BUNDLED_DIR / task / model_id
    folder.mkdir(parents=True, exist_ok=True)
    model.save(folder)
    (folder / "report.json").write_text(json.dumps(rep_all, ensure_ascii=False, indent=2), encoding="utf-8")
    entry = {
        "id": model_id,
        "task": task,
        "name": f"Model OCR Lens — {task} (dilatih pada dataset aktual)",
        "notes": (f"Dilatih oleh eval/train_ocr_models.py pada {stats['labeled']} sampel "
                  f"({', '.join(PACKS[task])}); augmentasi on-the-fly, cosine LR, label smoothing."),
        "arch": args.arch,
        "arch_name": ml_models.ARCH_BY_ID[args.arch]["name"],
        "hyperparams": hp,
        "classes": labels,
        "n_classes": len(labels),
        "n_params": model.n_params(),
        "created_at": store.now_iso(),
        "train_seconds": secs,
        "eval_split": "test",
        "dataset_size": {"train": int(len(y_tr)), "val": int(len(y_va)), "test": int(len(y_te))},
        "metrics": ml_metrics.summarize(rep_all) | {"train_accuracy": rep_all["train_accuracy"]},
        "bundled": True,
    }
    (folder / "entry.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    size = sum(p.stat().st_size for p in folder.glob("*") if p.is_file())
    print(f"  akurasi test   : {rep_all['accuracy'] * 100:.2f}%  (F1 makro {rep_all['macro_f1'] * 100:.2f}%, "
          f"top-3 {rep_all['top3_accuracy'] * 100:.1f}%)")
    if rep_real:
        print(f"  AKTUAL (tangan): {rep_real['accuracy'] * 100:.2f}%  n={rep_real['n']}  "
              f"CER {rep_real['char_error_rate'] * 100:.2f}%  top-3 {rep_real['top3_accuracy'] * 100:.1f}%")
    print(f"  → {folder.relative_to(ROOT)}  ({size / 1024:.0f} KB)")
    return {"model_id": model_id, "entry": entry, "report": rep_all, "real": rep_real, "folder": folder}


def write_summary(results: list[dict], args) -> None:
    out = ROOT / "eval" / "results"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Model OCR Lens — hasil training (diperbarui {stamp})",
        "",
        "Dihasilkan oleh `eval/train_ocr_models.py`. Model-model ini dikomit sebagai",
        "**model bawaan** (`backend/app/data/ml_bundled/`) sehingga halaman Lens langsung",
        "berfungsi tanpa training ulang; Panel Admin tetap dapat melatih ulang.",
        "",
        "| Tugas | Arsitektur | Kelas | Sampel latih | Akurasi test | **Akurasi tulisan tangan nyata** | F1 makro | Top-3 | CER | Waktu |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in results:
        e, rep, real = r["entry"], r["report"], r["real"]
        lines.append(
            f"| {e['task']} | {e['arch_name']} | {e['n_classes']} | "
            f"{e['dataset_size']['train']} | {rep['accuracy'] * 100:.2f}% | "
            + (f"{real['accuracy'] * 100:.2f}% (n={real['n']}) | {real['macro_f1'] * 100:.2f}% | "
               f"{real['top3_accuracy'] * 100:.1f}% | {real['char_error_rate'] * 100:.2f}%"
               if real else "— | — | — | —")
            + f" | {e['train_seconds']} s |"
        )
    lines += ["", "## Konfigurasi", "", "```json", json.dumps({
        "arch": args.arch, "epochs": args.epochs, "batch_size": args.batch_size, "lr": args.lr,
        "augment": args.augment, "class_balance": args.class_balance, "hidden_units": args.hidden,
        "conv1_filters": args.f1, "conv2_filters": args.f2, "label_smoothing": args.label_smoothing,
        "eval_tta": args.tta, "packs": PACKS,
    }, indent=2), "```", ""]
    for r in results:
        real = r["real"] or {}
        per = (real or {}).get("per_class") or r["report"].get("per_class") or []
        if not per:
            continue
        lines += [f"### Tugas `{r['entry']['task']}` — per kelas (tulisan tangan nyata bila tersedia)", "",
                  "| Kelas | Presisi | Recall | F1 | Support |", "| --- | ---: | ---: | ---: | ---: |"]
        for m in per:
            lines.append(f"| `{m.get('label')}` | {m.get('precision', 0) * 100:.1f} | {m.get('recall', 0) * 100:.1f} | "
                         f"{m.get('f1', 0) * 100:.1f} | {m.get('support', 0)} |")
        lines.append("")
    (out / "OCR_LENS_MODELS.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "ocr_lens_models.json").write_text(json.dumps(
        {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "config": vars(args), "results": [
             {"model_id": r["model_id"], "task": r["entry"]["task"], "metrics": r["report"],
              "real_handwriting": r["real"]} for r in results]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ringkasan → {out / 'OCR_LENS_MODELS.md'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", default="both", choices=["aksara", "latin", "both"])
    ap.add_argument("--arch", default="deepcnn")
    ap.add_argument("--epochs", type=int, default=42)
    ap.add_argument("--batch-size", type=int, default=96)
    ap.add_argument("--lr", type=float, default=0.007)
    ap.add_argument("--hidden", type=int, default=112)
    ap.add_argument("--f1", type=int, default=14)
    ap.add_argument("--f2", type=int, default=28)
    ap.add_argument("--augment", type=float, default=1.0)
    ap.add_argument("--class-balance", type=float, default=0.6)
    ap.add_argument("--label-smoothing", type=float, default=0.06)
    ap.add_argument("--tta", type=int, default=4, help="jumlah transformasi TTA saat evaluasi")
    ap.add_argument("--log-every", type=int, default=2)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--keep-store", action="store_true", help="jangan kosongkan store runtime setelah selesai")
    args = ap.parse_args()

    work = Path(tempfile.mkdtemp(prefix="aksara-ocr-train-")) / "ml"
    store.ML_DIR = work
    BUNDLED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"store sementara: {work}")

    results = []
    for task in (["aksara", "latin"] if args.task == "both" else [args.task]):
        results.append(train_task(task, args))
    write_summary(results, args)
    if not args.keep_store:
        shutil.rmtree(work.parent, ignore_errors=True)
    print("\nSelesai.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
