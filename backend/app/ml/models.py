"""Arsitektur model klasifikasi (NumPy murni).

Semua model memakai antarmuka yang sama:

    model = create_model(arch, n_classes, hyperparams)
    model.fit(X_train, y_train, X_val, y_val, progress=callback, should_stop=fn)
    proba = model.predict_proba(X)          # N × C, baris berjumlah 1
    model.save(dir_path) / Model.load(dir_path)

``X`` adalah matriks N × 784 float32 (fitur 28×28 dari ``features.py``).

Arsitektur:
- ``template`` : template matching chamfer (baseline on-device, tanpa training)
- ``centroid`` : nearest class-mean (baseline statistik, sangat cepat)
- ``knn``      : k-nearest neighbours berbobot jarak
- ``logreg``   : regresi logistik multinomial (softmax) + Adam
- ``mlp``      : jaringan saraf 1 lapisan tersembunyi (ReLU) + Adam + dropout
- ``cnn``      : CNN kecil (conv3×3-8 → pool → conv3×3-16 → pool → FC64 → softmax)
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np

from .features import FEATURE_SIZE, N_FEATURES

ProgressFn = Callable[[Dict], None]
StopFn = Callable[[], bool]

ARCHITECTURES: List[Dict] = [
    {
        "id": "template",
        "name": "Template Matching (Chamfer)",
        "family": "Baseline non-parametrik",
        "trainable": False,
        "description": (
            "Metode yang sama dengan classifier on-device di peramban: glyph dirender dari font "
            "Noto Sans Balinese lalu dibandingkan dengan tinta memakai chamfer distance dua arah. "
            "Tidak belajar dari dataset — berguna sebagai pembanding (baseline)."
        ),
        "pros": ["Tanpa training", "Deterministik & mudah diaudit"],
        "cons": ["Tidak beradaptasi ke tulisan tangan nyata", "Aksara mirip (na/da/ta) sering tertukar"],
        "hyperparams": [],
    },
    {
        "id": "centroid",
        "name": "Nearest Centroid",
        "family": "Statistik klasik",
        "trainable": True,
        "description": (
            "Menghitung rata-rata piksel tiap kelas (centroid) lalu memilih kelas dengan jarak "
            "Euclidean terdekat. Latih dalam < 1 detik; cocok untuk sanity-check dataset."
        ),
        "pros": ["Instan", "Model sangat kecil"],
        "cons": ["Batas keputusan linear & kaku", "Akurasi terbatas"],
        "hyperparams": [],
    },
    {
        "id": "knn",
        "name": "k-Nearest Neighbours",
        "family": "Instance-based",
        "trainable": True,
        "description": (
            "Menyimpan seluruh sampel latih; prediksi = voting k tetangga terdekat (berbobot 1/jarak). "
            "Kuat untuk dataset kecil, tetapi ukuran model & waktu inferensi tumbuh sejalan data."
        ),
        "pros": ["Tanpa asumsi bentuk", "Baik untuk data sedikit"],
        "cons": ["Inferensi lambat bila data besar", "Model besar"],
        "hyperparams": [{"key": "k", "label": "k tetangga", "type": "int", "default": 5, "min": 1, "max": 25}],
    },
    {
        "id": "logreg",
        "name": "Regresi Logistik (Softmax)",
        "family": "Linear",
        "trainable": True,
        "description": (
            "Model linear multinomial 784 → C dengan optimizer Adam dan regularisasi L2. "
            "Cepat, ringan, dan probabilitasnya terkalibrasi cukup baik."
        ),
        "pros": ["Cepat & stabil", "Probabilitas terkalibrasi"],
        "cons": ["Hanya batas keputusan linear"],
        "hyperparams": [
            {"key": "epochs", "label": "Epoch", "type": "int", "default": 30, "min": 1, "max": 200},
            {"key": "learning_rate", "label": "Learning rate", "type": "float", "default": 0.005, "min": 0.00001, "max": 1},
            {"key": "batch_size", "label": "Batch size", "type": "int", "default": 64, "min": 8, "max": 512},
            {"key": "weight_decay", "label": "Weight decay (L2)", "type": "float", "default": 0.0005, "min": 0, "max": 0.1},
        ],
    },
    {
        "id": "mlp",
        "name": "Multi-Layer Perceptron",
        "family": "Jaringan saraf",
        "trainable": True,
        "description": (
            "Jaringan saraf 784 → hidden (ReLU, dropout) → C. Mampu memodelkan batas non-linear; "
            "biasanya jauh lebih akurat dari model linear pada tulisan tangan."
        ),
        "pros": ["Non-linear", "Masih cepat dilatih di CPU"],
        "cons": ["Perlu tuning epoch/lr", "Rentan overfit bila data sedikit"],
        "hyperparams": [
            {"key": "epochs", "label": "Epoch", "type": "int", "default": 40, "min": 1, "max": 300},
            {"key": "learning_rate", "label": "Learning rate", "type": "float", "default": 0.002, "min": 0.00001, "max": 1},
            {"key": "batch_size", "label": "Batch size", "type": "int", "default": 64, "min": 8, "max": 512},
            {"key": "hidden_units", "label": "Neuron tersembunyi", "type": "int", "default": 128, "min": 8, "max": 1024},
            {"key": "dropout", "label": "Dropout", "type": "float", "default": 0.2, "min": 0, "max": 0.9},
            {"key": "weight_decay", "label": "Weight decay (L2)", "type": "float", "default": 0.0005, "min": 0, "max": 0.1},
        ],
    },
    {
        "id": "cnn",
        "name": "Convolutional Neural Network",
        "family": "Jaringan saraf konvolusi",
        "trainable": True,
        "description": (
            "CNN kecil: conv3×3×8 → maxpool → conv3×3×16 → maxpool → FC-64 → softmax. "
            "Paling tahan terhadap pergeseran & distorsi goresan; akurasi tertinggi, training paling lama."
        ),
        "pros": ["Akurasi terbaik", "Tahan translasi/distorsi"],
        "cons": ["Training paling lama (CPU)", "Model lebih besar"],
        "hyperparams": [
            {"key": "epochs", "label": "Epoch", "type": "int", "default": 15, "min": 1, "max": 100},
            {"key": "learning_rate", "label": "Learning rate", "type": "float", "default": 0.004, "min": 0.00001, "max": 1},
            {"key": "batch_size", "label": "Batch size", "type": "int", "default": 64, "min": 8, "max": 256},
            {"key": "conv1_filters", "label": "Filter conv-1", "type": "int", "default": 8, "min": 2, "max": 32},
            {"key": "conv2_filters", "label": "Filter conv-2", "type": "int", "default": 16, "min": 2, "max": 64},
            {"key": "hidden_units", "label": "Neuron FC", "type": "int", "default": 64, "min": 8, "max": 512},
            {"key": "dropout", "label": "Dropout", "type": "float", "default": 0.25, "min": 0, "max": 0.9},
        ],
    },
]

ARCH_BY_ID = {a["id"]: a for a in ARCHITECTURES}


def default_hyperparams(arch: str) -> Dict:
    spec = ARCH_BY_ID.get(arch)
    if not spec:
        raise ValueError(f"Arsitektur tidak dikenal: {arch}")
    return {h["key"]: h["default"] for h in spec["hyperparams"]}


def coerce_hyperparams(arch: str, given: Optional[Dict]) -> Dict:
    """Gabungkan default + input pengguna, jepit ke rentang yang diizinkan."""
    spec = ARCH_BY_ID.get(arch)
    if not spec:
        raise ValueError(f"Arsitektur tidak dikenal: {arch}")
    out = default_hyperparams(arch)
    given = given or {}
    for h in spec["hyperparams"]:
        if h["key"] not in given or given[h["key"]] is None:
            continue
        try:
            v = int(given[h["key"]]) if h["type"] == "int" else float(given[h["key"]])
        except (TypeError, ValueError):
            continue
        v = max(h["min"], min(h["max"], v))
        out[h["key"]] = v
    return out


# ── util numerik ───────────────────────────────────────────────────────────

def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def one_hot(y: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros((y.size, n), dtype=np.float32)
    out[np.arange(y.size), y.astype(int)] = 1.0
    return out


def _accuracy(model: "BaseModel", X: Optional[np.ndarray], y: Optional[np.ndarray]) -> Optional[float]:
    if X is None or y is None or len(y) == 0:
        return None
    return float((model.predict_proba(X).argmax(axis=1) == y).mean())


class Adam:
    def __init__(self, params: List[np.ndarray], lr: float, weight_decay: float = 0.0):
        self.params = params
        self.lr = lr
        self.wd = weight_decay
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
        self.t = 0
        self.b1, self.b2, self.eps = 0.9, 0.999, 1e-8

    def step(self, grads: List[np.ndarray]) -> None:
        self.t += 1
        lr_t = self.lr * math.sqrt(1 - self.b2 ** self.t) / (1 - self.b1 ** self.t)
        for p, g, m, v in zip(self.params, grads, self.m, self.v):
            if self.wd and p.ndim > 1:
                g = g + self.wd * p
            m *= self.b1
            m += (1 - self.b1) * g
            v *= self.b2
            v += (1 - self.b2) * (g * g)
            p -= lr_t * m / (np.sqrt(v) + self.eps)


# ── kelas dasar ────────────────────────────────────────────────────────────

class BaseModel:
    arch: str = "base"

    def __init__(self, n_classes: int, hyperparams: Optional[Dict] = None):
        self.n_classes = int(n_classes)
        self.hp = coerce_hyperparams(self.arch, hyperparams)
        self.mean: Optional[np.ndarray] = None
        self.std: float = 1.0
        self.history: List[Dict] = []

    # -- normalisasi fitur (mean per-piksel, std global) --
    def _fit_scaler(self, X: np.ndarray) -> None:
        self.mean = X.mean(axis=0).astype(np.float32)
        self.std = float(X.std()) or 1.0

    def _scale(self, X: np.ndarray) -> np.ndarray:
        if self.mean is None:
            return X.astype(np.float32)
        return ((X - self.mean) / self.std).astype(np.float32)

    def fit(self, X, y, X_val=None, y_val=None, progress: Optional[ProgressFn] = None,
            should_stop: Optional[StopFn] = None) -> None:
        raise NotImplementedError

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def n_params(self) -> int:
        return 0

    # -- persistensi --
    def _arrays(self) -> Dict[str, np.ndarray]:
        return {}

    def _load_arrays(self, arrays: Dict[str, np.ndarray]) -> None:
        pass

    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        arrays = dict(self._arrays())
        if self.mean is not None:
            arrays["_mean"] = self.mean
        np.savez_compressed(folder / "model.npz", **arrays)
        (folder / "model.json").write_text(json.dumps({
            "arch": self.arch,
            "n_classes": self.n_classes,
            "hyperparams": self.hp,
            "std": self.std,
            "history": self.history,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, folder: Path) -> "BaseModel":
        meta = json.loads((folder / "model.json").read_text(encoding="utf-8"))
        model = create_model(meta["arch"], meta["n_classes"], meta.get("hyperparams"))
        model.std = float(meta.get("std", 1.0))
        model.history = meta.get("history", [])
        with np.load(folder / "model.npz", allow_pickle=False) as data:
            arrays = {k: data[k] for k in data.files}
        model.mean = arrays.pop("_mean", None)
        model._load_arrays(arrays)
        return model


# ── Template matching (chamfer) ────────────────────────────────────────────

def _chamfer_dt(mask: np.ndarray) -> np.ndarray:
    """Distance transform chamfer (1, √2) dua-pass pada maska boolean 2D."""
    big = 1e6
    d = np.where(mask, 0.0, big).astype(np.float64)
    h, w = mask.shape
    s2 = math.sqrt(2.0)
    for i in range(h):
        row = d[i]
        if i > 0:
            prev = d[i - 1]
            row = np.minimum(row, prev + 1.0)
            row[1:] = np.minimum(row[1:], prev[:-1] + s2)
            row[:-1] = np.minimum(row[:-1], prev[1:] + s2)
        for j in range(1, w):  # sapuan kiri→kanan
            if row[j - 1] + 1.0 < row[j]:
                row[j] = row[j - 1] + 1.0
        d[i] = row
    for i in range(h - 1, -1, -1):
        row = d[i]
        if i < h - 1:
            nxt = d[i + 1]
            row = np.minimum(row, nxt + 1.0)
            row[1:] = np.minimum(row[1:], nxt[:-1] + s2)
            row[:-1] = np.minimum(row[:-1], nxt[1:] + s2)
        for j in range(w - 2, -1, -1):  # sapuan kanan→kiri
            if row[j + 1] + 1.0 < row[j]:
                row[j] = row[j + 1] + 1.0
        d[i] = row
    return d


class TemplateModel(BaseModel):
    """Baseline chamfer: template = render font bersih per kelas (diberikan saat fit)."""

    arch = "template"
    SCALE = FEATURE_SIZE * 0.14

    def __init__(self, n_classes: int, hyperparams: Optional[Dict] = None):
        super().__init__(n_classes, hyperparams)
        self.templates: Optional[np.ndarray] = None   # C × 784 (0/1)
        self.template_dt: Optional[np.ndarray] = None  # C × 784

    def set_templates(self, templates: np.ndarray) -> None:
        masks = (templates.reshape(-1, FEATURE_SIZE, FEATURE_SIZE) > 0.5)
        self.templates = masks.reshape(len(masks), -1).astype(np.float32)
        self.template_dt = np.stack([_chamfer_dt(m).reshape(-1) for m in masks]).astype(np.float32)

    def fit(self, X, y, X_val=None, y_val=None, progress=None, should_stop=None) -> None:
        # Bila template belum di-set (mis. tanpa font), pakai rata-rata kelas sebagai template.
        if self.templates is None:
            cents = np.zeros((self.n_classes, N_FEATURES), dtype=np.float32)
            for c in range(self.n_classes):
                sel = X[y == c]
                if len(sel):
                    cents[c] = sel.mean(axis=0)
            self.set_templates(cents)
        self.history.append({"epoch": 1, "loss": None, "train_acc": _accuracy(self, X, y), "val_acc": _accuracy(self, X_val, y_val)})
        if progress:
            progress(self.history[-1])

    def scores(self, X: np.ndarray) -> np.ndarray:
        assert self.templates is not None and self.template_dt is not None
        n = X.shape[0]
        out = np.zeros((n, self.n_classes), dtype=np.float32)
        t_cnt = self.templates.sum(axis=1) + 1e-9
        for i in range(n):
            mask = X[i].reshape(FEATURE_SIZE, FEATURE_SIZE) > 0.5
            a = mask.reshape(-1).astype(np.float32)
            cnt_a = a.sum()
            if cnt_a == 0:
                continue
            dt_a = _chamfer_dt(mask).reshape(-1)
            # a → template  dan  template → a
            d_ab = (self.template_dt * a[None, :]).sum(axis=1) / cnt_a
            d_ba = (self.templates * dt_a[None, :]).sum(axis=1) / t_cnt
            avg = (d_ab + d_ba) / 2.0
            out[i] = np.clip(1.0 - avg / self.SCALE, 0.0, 1.0)
        return out

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        s = self.scores(X)
        return softmax(s * 12.0)  # temperatur: skor 0..1 → distribusi tajam tapi tidak ekstrem

    def n_params(self) -> int:
        return int(self.templates.size) if self.templates is not None else 0

    def _arrays(self):
        return {"templates": self.templates, "template_dt": self.template_dt}

    def _load_arrays(self, arrays):
        self.templates = arrays["templates"]
        self.template_dt = arrays["template_dt"]


# ── Nearest centroid ───────────────────────────────────────────────────────

class CentroidModel(BaseModel):
    arch = "centroid"

    def __init__(self, n_classes: int, hyperparams: Optional[Dict] = None):
        super().__init__(n_classes, hyperparams)
        self.centroids: Optional[np.ndarray] = None

    def fit(self, X, y, X_val=None, y_val=None, progress=None, should_stop=None) -> None:
        self.centroids = np.zeros((self.n_classes, X.shape[1]), dtype=np.float32)
        for c in range(self.n_classes):
            sel = X[y == c]
            if len(sel):
                self.centroids[c] = sel.mean(axis=0)
        self.history.append({"epoch": 1, "loss": None, "train_acc": _accuracy(self, X, y), "val_acc": _accuracy(self, X_val, y_val)})
        if progress:
            progress(self.history[-1])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        assert self.centroids is not None
        d2 = ((X[:, None, :] - self.centroids[None, :, :]) ** 2).sum(axis=2)
        return softmax(-d2 / (2.0 * max(np.median(d2), 1e-6) * 0.15))

    def n_params(self) -> int:
        return int(self.centroids.size) if self.centroids is not None else 0

    def _arrays(self):
        return {"centroids": self.centroids}

    def _load_arrays(self, arrays):
        self.centroids = arrays["centroids"]


# ── k-NN ───────────────────────────────────────────────────────────────────

class KNNModel(BaseModel):
    arch = "knn"

    def __init__(self, n_classes: int, hyperparams: Optional[Dict] = None):
        super().__init__(n_classes, hyperparams)
        self.X: Optional[np.ndarray] = None
        self.y: Optional[np.ndarray] = None

    def fit(self, X, y, X_val=None, y_val=None, progress=None, should_stop=None) -> None:
        self.X = X.astype(np.float32)
        self.y = y.astype(np.int64)
        self.history.append({"epoch": 1, "loss": None, "train_acc": None, "val_acc": _accuracy(self, X_val, y_val)})
        if progress:
            progress(self.history[-1])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        assert self.X is not None and self.y is not None
        k = int(min(self.hp["k"], len(self.y)))
        out = np.zeros((X.shape[0], self.n_classes), dtype=np.float32)
        train_sq = (self.X ** 2).sum(axis=1)
        for start in range(0, X.shape[0], 256):
            chunk = X[start:start + 256].astype(np.float32)
            d2 = (chunk ** 2).sum(axis=1)[:, None] + train_sq[None, :] - 2.0 * chunk @ self.X.T
            d2 = np.maximum(d2, 0.0)
            idx = np.argpartition(d2, k - 1, axis=1)[:, :k]
            for r in range(chunk.shape[0]):
                nn = idx[r]
                w = 1.0 / (np.sqrt(d2[r, nn]) + 1e-3)
                np.add.at(out[start + r], self.y[nn], w)
        out = out / np.maximum(out.sum(axis=1, keepdims=True), 1e-9)
        return out

    def n_params(self) -> int:
        return int(self.X.size) if self.X is not None else 0

    def _arrays(self):
        return {"X": self.X, "y": self.y}

    def _load_arrays(self, arrays):
        self.X = arrays["X"]
        self.y = arrays["y"]


# ── Regresi logistik & MLP ─────────────────────────────────────────────────

def _iterate_minibatches(n: int, batch: int, rng: np.random.Generator):
    perm = rng.permutation(n)
    for s in range(0, n, batch):
        yield perm[s:s + batch]


class LogRegModel(BaseModel):
    arch = "logreg"

    def __init__(self, n_classes: int, hyperparams: Optional[Dict] = None):
        super().__init__(n_classes, hyperparams)
        self.W: Optional[np.ndarray] = None
        self.b: Optional[np.ndarray] = None

    def fit(self, X, y, X_val=None, y_val=None, progress=None, should_stop=None) -> None:
        rng = np.random.default_rng(int(self.hp.get("seed", 0)) if "seed" in self.hp else 0)
        self._fit_scaler(X)
        Xs = self._scale(X)
        d = Xs.shape[1]
        self.W = (rng.standard_normal((d, self.n_classes)) * 0.01).astype(np.float32)
        self.b = np.zeros(self.n_classes, dtype=np.float32)
        opt = Adam([self.W, self.b], lr=float(self.hp["learning_rate"]), weight_decay=float(self.hp["weight_decay"]))
        Y = one_hot(y, self.n_classes)
        epochs = int(self.hp["epochs"])
        bs = int(self.hp["batch_size"])
        for ep in range(1, epochs + 1):
            t0 = time.time()
            losses = []
            for idx in _iterate_minibatches(len(Xs), bs, rng):
                xb, yb = Xs[idx], Y[idx]
                p = softmax(xb @ self.W + self.b)
                losses.append(float(-(yb * np.log(p + 1e-9)).sum(axis=1).mean()))
                g = (p - yb) / len(idx)
                opt.step([xb.T @ g, g.sum(axis=0)])
            rec = {"epoch": ep, "loss": round(float(np.mean(losses)), 5),
                   "train_acc": _accuracy(self, X, y), "val_acc": _accuracy(self, X_val, y_val),
                   "seconds": round(time.time() - t0, 3)}
            self.history.append(rec)
            if progress:
                progress(rec)
            if should_stop and should_stop():
                break

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return softmax(self._scale(X) @ self.W + self.b)

    def n_params(self) -> int:
        return int(self.W.size + self.b.size) if self.W is not None else 0

    def _arrays(self):
        return {"W": self.W, "b": self.b}

    def _load_arrays(self, arrays):
        self.W = arrays["W"]
        self.b = arrays["b"]


class MLPModel(BaseModel):
    arch = "mlp"

    def __init__(self, n_classes: int, hyperparams: Optional[Dict] = None):
        super().__init__(n_classes, hyperparams)
        self.W1 = self.b1 = self.W2 = self.b2 = None

    def _forward(self, Xs: np.ndarray, train: bool, rng: Optional[np.random.Generator] = None):
        z1 = Xs @ self.W1 + self.b1
        h = np.maximum(z1, 0.0)
        mask = None
        p_drop = float(self.hp["dropout"])
        if train and p_drop > 0 and rng is not None:
            mask = (rng.random(h.shape, dtype=np.float32) >= p_drop).astype(np.float32) / (1.0 - p_drop)
            h = h * mask
        p = softmax(h @ self.W2 + self.b2)
        return z1, h, mask, p

    def fit(self, X, y, X_val=None, y_val=None, progress=None, should_stop=None) -> None:
        rng = np.random.default_rng(0)
        self._fit_scaler(X)
        Xs = self._scale(X)
        d, hdim = Xs.shape[1], int(self.hp["hidden_units"])
        self.W1 = (rng.standard_normal((d, hdim)) * math.sqrt(2.0 / d)).astype(np.float32)
        self.b1 = np.zeros(hdim, dtype=np.float32)
        self.W2 = (rng.standard_normal((hdim, self.n_classes)) * math.sqrt(2.0 / hdim)).astype(np.float32)
        self.b2 = np.zeros(self.n_classes, dtype=np.float32)
        opt = Adam([self.W1, self.b1, self.W2, self.b2], lr=float(self.hp["learning_rate"]),
                   weight_decay=float(self.hp["weight_decay"]))
        Y = one_hot(y, self.n_classes)
        epochs, bs = int(self.hp["epochs"]), int(self.hp["batch_size"])
        for ep in range(1, epochs + 1):
            t0 = time.time()
            losses = []
            for idx in _iterate_minibatches(len(Xs), bs, rng):
                xb, yb = Xs[idx], Y[idx]
                z1, h, mask, p = self._forward(xb, True, rng)
                losses.append(float(-(yb * np.log(p + 1e-9)).sum(axis=1).mean()))
                g2 = (p - yb) / len(idx)
                dW2 = h.T @ g2
                db2 = g2.sum(axis=0)
                dh = g2 @ self.W2.T
                if mask is not None:
                    dh = dh * mask
                dz1 = dh * (z1 > 0)
                opt.step([xb.T @ dz1, dz1.sum(axis=0), dW2, db2])
            rec = {"epoch": ep, "loss": round(float(np.mean(losses)), 5),
                   "train_acc": _accuracy(self, X, y), "val_acc": _accuracy(self, X_val, y_val),
                   "seconds": round(time.time() - t0, 3)}
            self.history.append(rec)
            if progress:
                progress(rec)
            if should_stop and should_stop():
                break

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._forward(self._scale(X), False)[3]

    def n_params(self) -> int:
        if self.W1 is None:
            return 0
        return int(self.W1.size + self.b1.size + self.W2.size + self.b2.size)

    def _arrays(self):
        return {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2}

    def _load_arrays(self, arrays):
        self.W1, self.b1, self.W2, self.b2 = arrays["W1"], arrays["b1"], arrays["W2"], arrays["b2"]


# ── CNN kecil ──────────────────────────────────────────────────────────────

def _im2col3(xp: np.ndarray) -> np.ndarray:
    """xp: N×C×(H+2)×(W+2) (sudah dipad) → (N*H*W) × (C*9)."""
    n, c, hp, wp = xp.shape
    h, w = hp - 2, wp - 2
    win = np.lib.stride_tricks.sliding_window_view(xp, (3, 3), axis=(2, 3))  # N,C,H,W,3,3
    return win.transpose(0, 2, 3, 1, 4, 5).reshape(n * h * w, c * 9)


def _col2im3(dcols: np.ndarray, n: int, c: int, h: int, w: int) -> np.ndarray:
    d6 = dcols.reshape(n, h, w, c, 3, 3).transpose(0, 3, 1, 2, 4, 5)  # N,C,H,W,3,3
    dxp = np.zeros((n, c, h + 2, w + 2), dtype=np.float32)
    for i in range(3):
        for j in range(3):
            dxp[:, :, i:i + h, j:j + w] += d6[:, :, :, :, i, j]
    return dxp[:, :, 1:-1, 1:-1]


def _conv3(x: np.ndarray, Wm: np.ndarray, b: np.ndarray):
    """Konvolusi 3×3 'same'. x: N×C×H×W, Wm: F×(C*9)."""
    n, c, h, w = x.shape
    xp = np.pad(x, ((0, 0), (0, 0), (1, 1), (1, 1)))
    cols = _im2col3(xp)
    out = cols @ Wm.T + b
    return out.reshape(n, h, w, -1).transpose(0, 3, 1, 2), cols


def _maxpool2(x: np.ndarray):
    n, f, h, w = x.shape
    xr = x.reshape(n, f, h // 2, 2, w // 2, 2)
    out = xr.max(axis=(3, 5))
    mask = (xr == out[:, :, :, None, :, None]).astype(np.float32)
    return out, mask


def _maxpool2_back(dout: np.ndarray, mask: np.ndarray):
    n, f, h2, _, w2, _ = mask.shape
    return (mask * dout[:, :, :, None, :, None]).reshape(n, f, h2 * 2, w2 * 2)


class CNNModel(BaseModel):
    arch = "cnn"

    def __init__(self, n_classes: int, hyperparams: Optional[Dict] = None):
        super().__init__(n_classes, hyperparams)
        self.params: Dict[str, np.ndarray] = {}

    def _init(self, rng: np.random.Generator) -> None:
        f1, f2, hdim = int(self.hp["conv1_filters"]), int(self.hp["conv2_filters"]), int(self.hp["hidden_units"])
        s = FEATURE_SIZE // 4
        P = {
            "W1": rng.standard_normal((f1, 9)) * math.sqrt(2.0 / 9),
            "b1": np.zeros(f1),
            "W2": rng.standard_normal((f2, f1 * 9)) * math.sqrt(2.0 / (f1 * 9)),
            "b2": np.zeros(f2),
            "W3": rng.standard_normal((f2 * s * s, hdim)) * math.sqrt(2.0 / (f2 * s * s)),
            "b3": np.zeros(hdim),
            "W4": rng.standard_normal((hdim, self.n_classes)) * math.sqrt(2.0 / hdim),
            "b4": np.zeros(self.n_classes),
        }
        self.params = {k: v.astype(np.float32) for k, v in P.items()}

    def _forward(self, Xs: np.ndarray, train: bool, rng: Optional[np.random.Generator] = None):
        P = self.params
        n = Xs.shape[0]
        x = Xs.reshape(n, 1, FEATURE_SIZE, FEATURE_SIZE)
        z1, cols1 = _conv3(x, P["W1"], P["b1"])
        a1 = np.maximum(z1, 0)
        p1, m1 = _maxpool2(a1)
        z2, cols2 = _conv3(p1, P["W2"], P["b2"])
        a2 = np.maximum(z2, 0)
        p2, m2 = _maxpool2(a2)
        flat = p2.reshape(n, -1)
        z3 = flat @ P["W3"] + P["b3"]
        h = np.maximum(z3, 0)
        mask = None
        p_drop = float(self.hp["dropout"])
        if train and p_drop > 0 and rng is not None:
            mask = (rng.random(h.shape, dtype=np.float32) >= p_drop).astype(np.float32) / (1.0 - p_drop)
            h = h * mask
        out = softmax(h @ P["W4"] + P["b4"])
        cache = (x, z1, cols1, m1, p1, z2, cols2, m2, p2, flat, z3, h, mask)
        return out, cache

    def _backward(self, out: np.ndarray, Y: np.ndarray, cache) -> List[np.ndarray]:
        P = self.params
        x, z1, cols1, m1, p1, z2, cols2, m2, p2, flat, z3, h, mask = cache
        n = out.shape[0]
        g = (out - Y) / n
        dW4, db4 = h.T @ g, g.sum(axis=0)
        dh = g @ P["W4"].T
        if mask is not None:
            dh = dh * mask
        dz3 = dh * (z3 > 0)
        dW3, db3 = flat.T @ dz3, dz3.sum(axis=0)
        dflat = dz3 @ P["W3"].T
        dp2 = dflat.reshape(p2.shape)
        da2 = _maxpool2_back(dp2, m2)
        dz2 = da2 * (z2 > 0)
        f2 = dz2.shape[1]
        dz2_flat = dz2.transpose(0, 2, 3, 1).reshape(-1, f2)
        dW2, db2 = dz2_flat.T @ cols2, dz2_flat.sum(axis=0)
        dcols2 = dz2_flat @ P["W2"]
        dp1 = _col2im3(dcols2, n, p1.shape[1], p1.shape[2], p1.shape[3])
        da1 = _maxpool2_back(dp1, m1)
        dz1 = da1 * (z1 > 0)
        f1 = dz1.shape[1]
        dz1_flat = dz1.transpose(0, 2, 3, 1).reshape(-1, f1)
        dW1, db1 = dz1_flat.T @ cols1, dz1_flat.sum(axis=0)
        return [dW1, db1, dW2, db2, dW3, db3, dW4, db4]

    def fit(self, X, y, X_val=None, y_val=None, progress=None, should_stop=None) -> None:
        rng = np.random.default_rng(0)
        self._fit_scaler(X)
        Xs = self._scale(X)
        self._init(rng)
        keys = ["W1", "b1", "W2", "b2", "W3", "b3", "W4", "b4"]
        opt = Adam([self.params[k] for k in keys], lr=float(self.hp["learning_rate"]), weight_decay=1e-4)
        Y = one_hot(y, self.n_classes)
        epochs, bs = int(self.hp["epochs"]), int(self.hp["batch_size"])
        for ep in range(1, epochs + 1):
            t0 = time.time()
            losses = []
            for idx in _iterate_minibatches(len(Xs), bs, rng):
                xb, yb = Xs[idx], Y[idx]
                out, cache = self._forward(xb, True, rng)
                losses.append(float(-(yb * np.log(out + 1e-9)).sum(axis=1).mean()))
                grads = self._backward(out, yb, cache)
                opt.step([g.astype(np.float32) for g in grads])
                if should_stop and should_stop():
                    break
            rec = {"epoch": ep, "loss": round(float(np.mean(losses)), 5),
                   "train_acc": _accuracy(self, X, y), "val_acc": _accuracy(self, X_val, y_val),
                   "seconds": round(time.time() - t0, 3)}
            self.history.append(rec)
            if progress:
                progress(rec)
            if should_stop and should_stop():
                break

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        Xs = self._scale(X)
        outs = []
        for s in range(0, len(Xs), 512):
            outs.append(self._forward(Xs[s:s + 512], False)[0])
        return np.concatenate(outs, axis=0) if outs else np.zeros((0, self.n_classes), dtype=np.float32)

    def n_params(self) -> int:
        return int(sum(v.size for v in self.params.values()))

    def _arrays(self):
        return dict(self.params)

    def _load_arrays(self, arrays):
        self.params = {k: arrays[k] for k in ["W1", "b1", "W2", "b2", "W3", "b3", "W4", "b4"]}


MODEL_CLASSES = {
    "template": TemplateModel,
    "centroid": CentroidModel,
    "knn": KNNModel,
    "logreg": LogRegModel,
    "mlp": MLPModel,
    "cnn": CNNModel,
}


def create_model(arch: str, n_classes: int, hyperparams: Optional[Dict] = None) -> BaseModel:
    cls = MODEL_CLASSES.get(arch)
    if cls is None:
        raise ValueError(f"Arsitektur tidak dikenal: {arch}")
    return cls(n_classes, hyperparams)
