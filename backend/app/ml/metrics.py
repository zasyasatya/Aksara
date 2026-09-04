"""Metrik evaluasi klasifikasi: accuracy, precision, recall, F1, confusion matrix.

Implementasi mandiri (tanpa scikit-learn) agar dependensi tetap ringan.
Semua fungsi menerima label integer ``y_true``/``y_pred`` dalam rentang
``[0, n_classes)``.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> np.ndarray:
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for t, p in zip(y_true.astype(int), y_pred.astype(int)):
        cm[t, p] += 1
    return cm


def _safe_div(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    out = np.zeros_like(num, dtype=np.float64)
    mask = den > 0
    out[mask] = num[mask] / den[mask]
    return out


def classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: List[str],
    proba: Optional[np.ndarray] = None,
) -> Dict:
    """Laporan lengkap: per-kelas + rata-rata makro/berbobot + confusion matrix.

    ``proba`` (N×C) opsional → top-3 accuracy & log-loss.
    """
    n = len(class_names)
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    total = int(y_true.size)
    cm = confusion_matrix(y_true, y_pred, n)

    tp = np.diag(cm).astype(np.float64)
    pred_pos = cm.sum(axis=0).astype(np.float64)   # kolom = prediksi
    actual = cm.sum(axis=1).astype(np.float64)     # baris = label sebenarnya
    precision = _safe_div(tp, pred_pos)
    recall = _safe_div(tp, actual)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    present = actual > 0  # hanya kelas yang ada di data uji masuk rata-rata makro
    if present.any():
        macro_p = float(precision[present].mean())
        macro_r = float(recall[present].mean())
        macro_f1 = float(f1[present].mean())
    else:
        macro_p = macro_r = macro_f1 = 0.0
    weights = actual / actual.sum() if actual.sum() > 0 else np.zeros(n)
    weighted_p = float((precision * weights).sum())
    weighted_r = float((recall * weights).sum())
    weighted_f1 = float((f1 * weights).sum())
    accuracy = float(tp.sum() / total) if total else 0.0

    per_class = []
    for i, name in enumerate(class_names):
        per_class.append({
            "label": name,
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(actual[i]),
            "predicted": int(pred_pos[i]),
            "tp": int(tp[i]),
            "fp": int(pred_pos[i] - tp[i]),
            "fn": int(actual[i] - tp[i]),
        })

    report: Dict = {
        "accuracy": round(accuracy, 4),
        "error_rate": round(1.0 - accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_precision": round(weighted_p, 4),
        "weighted_recall": round(weighted_r, 4),
        "weighted_f1": round(weighted_f1, 4),
        "n_samples": total,
        "n_classes_present": int(present.sum()),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "class_names": list(class_names),
    }

    if proba is not None and total:
        proba = np.asarray(proba, dtype=np.float64)
        k = min(3, n)
        topk = np.argsort(-proba, axis=1)[:, :k]
        report["top3_accuracy"] = round(float((topk == y_true[:, None]).any(axis=1).mean()), 4)
        eps = 1e-12
        p_true = np.clip(proba[np.arange(total), y_true], eps, 1.0)
        report["log_loss"] = round(float(-np.log(p_true).mean()), 4)
        conf = proba.max(axis=1)
        report["mean_confidence"] = round(float(conf.mean()), 4)
        # kalibrasi kasar: akurasi pada prediksi dengan confidence ≥ 0.8
        hi = conf >= 0.8
        report["confident_rate"] = round(float(hi.mean()), 4)
        report["confident_accuracy"] = round(float((y_pred[hi] == y_true[hi]).mean()), 4) if hi.any() else None

    # pasangan kelas yang paling sering tertukar (untuk insight admin)
    off = cm.copy()
    np.fill_diagonal(off, 0)
    pairs = []
    if off.sum() > 0:
        flat = np.argsort(-off, axis=None)[:8]
        for idx in flat:
            i, j = divmod(int(idx), n)
            if off[i, j] <= 0:
                break
            pairs.append({"true": class_names[i], "pred": class_names[j], "count": int(off[i, j])})
    report["top_confusions"] = pairs
    return report


def summarize(report: Dict) -> Dict:
    """Ringkasan kecil untuk registry/tabel (tanpa matriks besar)."""
    keys = [
        "accuracy", "macro_precision", "macro_recall", "macro_f1",
        "weighted_precision", "weighted_recall", "weighted_f1",
        "top3_accuracy", "log_loss", "n_samples",
    ]
    return {k: report.get(k) for k in keys if k in report}
