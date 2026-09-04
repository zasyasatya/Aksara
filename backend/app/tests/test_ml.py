"""Test fitur ML: dataset, labeling, retraining, evaluasi, registry, prediksi.

Semua test memakai direktori data ML sementara (monkeypatch path di ``store``)
agar tidak menyentuh artefak nyata di ``backend/app/data/ml``.
"""

import base64
import io
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.core.config import settings
from app.main import app
from app.ml import features, metrics, models, store, synthetic, training

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_ml_dir(tmp_path, monkeypatch):
    """Arahkan semua path store ke direktori sementara + bersihkan cache inferensi."""
    ml = tmp_path / "ml"
    monkeypatch.setattr(store, "ML_DIR", ml)
    monkeypatch.setattr(store, "DATASET_DIR", ml / "dataset")
    monkeypatch.setattr(store, "IMAGES_DIR", ml / "dataset" / "images")
    monkeypatch.setattr(store, "INDEX_PATH", ml / "dataset" / "index.json")
    monkeypatch.setattr(store, "MODELS_DIR", ml / "models")
    monkeypatch.setattr(store, "REGISTRY_PATH", ml / "models" / "registry.json")
    monkeypatch.setattr(store, "CLASSES_PATH", ml / "classes.json")
    from app.ml import inference
    inference.invalidate()
    yield


@pytest.fixture
def prod_mode(monkeypatch):
    monkeypatch.setattr(settings, "mode", "prod")
    yield
    monkeypatch.setattr(settings, "mode", "dev")


def _admin_headers():
    r = client.post("/auth/login", json={"role": "admin", "username": settings.admin_username, "password": settings.admin_password})
    assert r.json()["ok"], r.text
    return {"Authorization": f"Bearer {r.json()['session_token']}"}


def _png_data_url(draw_fn=None, size=120, mode="RGBA"):
    """Gambar uji: goresan hitam di kanvas transparan (seperti canvas browser)."""
    img = Image.new(mode, (size, size), (0, 0, 0, 0) if mode == "RGBA" else 255)
    d = ImageDraw.Draw(img)
    if draw_fn:
        draw_fn(d)
    else:
        d.line([(20, 90), (50, 20), (80, 90)], fill=(0, 0, 0, 255) if mode == "RGBA" else 0, width=7)
        d.line([(35, 60), (65, 60)], fill=(0, 0, 0, 255) if mode == "RGBA" else 0, width=7)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _wait_job(job_id, timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        j = client.get(f"/api/ml/train/jobs/{job_id}").json()
        if j["status"] in ("done", "failed", "cancelled"):
            return j
        time.sleep(0.05)
    raise AssertionError("job tidak selesai tepat waktu")


# ── fitur & metrik (unit) ──────────────────────────────────────────────────

def test_feature_pipeline_normalizes_to_28x28():
    data = features.decode_base64_image(_png_data_url())
    ink = features.ink_from_bytes(data)
    assert features.has_ink(ink)
    f = features.features_from_ink(ink)
    assert f.shape == (784,)
    assert 0.0 <= f.min() and f.max() <= 1.0
    # roundtrip PNG kanonik
    png = features.to_storage_png(ink)
    back = features.ink_from_storage_png(png)
    assert back.shape == (64, 64) and back.max() > 0.9


def test_feature_pipeline_handles_dark_background_and_transparent():
    # latar gelap, tinta terang → dibalik otomatis
    img = Image.new("L", (100, 100), 0)
    ImageDraw.Draw(img).ellipse([20, 20, 80, 80], outline=255, width=6)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    ink = features.ink_from_bytes(buf.getvalue())
    assert features.has_ink(ink)
    with pytest.raises(features.ImageDecodeError):
        features.decode_base64_image("")
    with pytest.raises(features.ImageDecodeError):
        features.ink_from_bytes(b"bukan gambar sama sekali....")


def test_classification_report_metrics():
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 1, 1, 1, 2, 0])
    rep = metrics.classification_report(y_true, y_pred, ["a", "b", "c"])
    assert rep["accuracy"] == pytest.approx(4 / 6, abs=1e-4)
    pa = next(p for p in rep["per_class"] if p["label"] == "a")
    assert pa["precision"] == pytest.approx(0.5) and pa["recall"] == pytest.approx(0.5)
    pb = next(p for p in rep["per_class"] if p["label"] == "b")
    assert pb["recall"] == 1.0 and pb["precision"] == pytest.approx(2 / 3, abs=1e-4)
    assert rep["confusion_matrix"] == [[1, 1, 0], [0, 2, 0], [1, 0, 1]]
    assert 0 < rep["macro_f1"] < 1
    assert rep["top_confusions"][0]["count"] == 1


def test_all_architectures_train_and_predict_on_synthetic():
    master = store._master()
    classes = synthetic.build_classes(master, ("wresastra",))[:5]
    names = [c.label for c in classes]
    X, y = [], []
    for cls, ink, _ in synthetic.generate_samples(classes, 12, seed=3):
        X.append(features.features_from_ink(ink)); y.append(names.index(cls.label))
    X, y = np.stack(X), np.array(y)
    for arch in models.MODEL_CLASSES:
        # dataset kecil (60 sampel = 1 batch/epoch) → CNN butuh lebih banyak langkah optimasi
        hp = {"epochs": 3} if arch in ("logreg", "mlp") else ({"epochs": 25, "batch_size": 16} if arch == "cnn" else {})
        m = models.create_model(arch, len(names), hp)
        m.fit(X, y, X, y)
        p = m.predict_proba(X)
        assert p.shape == (len(y), len(names))
        assert np.allclose(p.sum(axis=1), 1.0, atol=1e-4)
        # model harus belajar sesuatu di data latihnya sendiri (jauh di atas chance 20%)
        assert (p.argmax(1) == y).mean() > 0.4, arch


def test_hyperparams_are_clamped_and_unknown_arch_rejected():
    hp = models.coerce_hyperparams("mlp", {"epochs": 99999, "learning_rate": "abc", "hidden_units": 1})
    assert hp["epochs"] == 300 and hp["hidden_units"] == 8 and hp["learning_rate"] == 0.002
    with pytest.raises(ValueError):
        models.coerce_hyperparams("transformer-xl", {})


# ── API: kelas & dataset ───────────────────────────────────────────────────

def test_classes_default_and_update():
    r = client.get("/api/ml/classes").json()
    assert len(r["active"]) == 18 and len(r["available"]) >= 40
    r = client.put("/api/ml/classes", json={"labels": ["ha", "na", "ca"]})
    assert r.status_code == 200 and [c["label"] for c in r.json()["active"]] == ["ha", "na", "ca"]
    r = client.put("/api/ml/classes", json={"labels": ["ha", "zzz"]})
    assert r.status_code == 400


def test_generate_synthetic_and_stats():
    client.put("/api/ml/classes", json={"labels": ["ha", "na", "ca", "ra"]})
    r = client.post("/api/ml/dataset/generate-synthetic", json={"per_class": 6, "seed": 5})
    assert r.status_code == 200, r.text
    assert r.json()["added"] == 24
    st = client.get("/api/ml/dataset/stats").json()
    assert st["total"] == 24 and st["labeled"] == 24 and st["n_classes"] == 4
    assert sum(st["per_split"].values()) == 24
    # generate ulang dengan replace → jumlah tetap
    r = client.post("/api/ml/dataset/generate-synthetic", json={"per_class": 6, "seed": 6, "replace_existing": True})
    assert r.json()["removed"] == 24 and client.get("/api/ml/dataset/stats").json()["total"] == 24


def test_sample_crud_labeling_flow():
    client.put("/api/ml/classes", json={"labels": ["ha", "na"]})
    # tambah tanpa label → antrean labeling
    r = client.post("/api/ml/dataset/samples", json={"image": _png_data_url(), "source": "canvas"})
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["status"] == "unlabeled" and s["label"] is None
    # gambar tersedia
    img = client.get(f"/api/ml/dataset/samples/{s['id']}/image")
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    # filter unlabeled
    lst = client.get("/api/ml/dataset/samples", params={"label": "__none__"}).json()
    assert lst["total"] == 1
    # beri label
    r = client.patch(f"/api/ml/dataset/samples/{s['id']}", json={"label": "ha", "split": "train", "note": "tangan"})
    assert r.status_code == 200 and r.json()["status"] == "labeled" and r.json()["label"] == "ha"
    # label tak dikenal
    assert client.patch(f"/api/ml/dataset/samples/{s['id']}", json={"label": "xx"}).status_code == 400
    # bulk label + hapus label
    r = client.post("/api/ml/dataset/bulk-label", json={"ids": [s["id"]], "label": "na", "status": "review"})
    assert r.json()["updated"] == 1
    detail = client.get(f"/api/ml/dataset/samples/{s['id']}").json()
    assert detail["label"] == "na" and detail["status"] == "review" and detail["feature_preview"].startswith("data:image/png")
    r = client.patch(f"/api/ml/dataset/samples/{s['id']}", json={"clear_label": True})
    assert r.json()["status"] == "unlabeled"
    # hapus
    assert client.delete(f"/api/ml/dataset/samples/{s['id']}").status_code == 200
    assert client.get(f"/api/ml/dataset/samples/{s['id']}").status_code == 404


def test_bulk_upload_skips_invalid_and_empty():
    client.put("/api/ml/classes", json={"labels": ["ha", "na"]})
    empty = _png_data_url(draw_fn=lambda d: None)
    r = client.post("/api/ml/dataset/samples/bulk", json={"items": [
        {"image": _png_data_url(), "label": "ha", "source": "upload"},
        {"image": empty, "label": "ha", "source": "upload"},
        {"image": "data:image/png;base64,QUJDRA==", "label": "na", "source": "upload"},
    ]})
    assert r.status_code == 201
    assert r.json()["added"] == 1 and r.json()["skipped"] == 2


def test_rebalance_splits_stratified():
    client.put("/api/ml/classes", json={"labels": ["ha", "na", "ca"]})
    client.post("/api/ml/dataset/generate-synthetic", json={"per_class": 10, "seed": 1})
    r = client.post("/api/ml/dataset/rebalance", json={"val_ratio": 0.2, "test_ratio": 0.2, "seed": 3})
    assert r.status_code == 200
    assert r.json()["per_split"] == {"train": 18, "val": 6, "test": 6}
    st = client.get("/api/ml/dataset/stats").json()
    for lbl in ("ha", "na", "ca"):
        assert st["per_label"][lbl] == {"train": 6, "val": 2, "test": 2, "total": 10}


# ── API: training, evaluasi, registry, prediksi ────────────────────────────

def test_training_requires_enough_data():
    client.put("/api/ml/classes", json={"labels": ["ha", "na"]})
    r = client.post("/api/ml/train", json={"arch": "logreg"})
    assert r.status_code == 400 and "terlalu sedikit" in r.json()["detail"]
    r = client.post("/api/ml/train", json={"arch": "nope"})
    assert r.status_code == 400


def test_full_retraining_flow_with_evaluation_and_production():
    client.put("/api/ml/classes", json={"labels": ["ha", "na", "ca", "ra", "ka"]})
    client.post("/api/ml/dataset/generate-synthetic", json={"per_class": 16, "seed": 11})
    client.post("/api/ml/dataset/rebalance", json={"val_ratio": 0.2, "test_ratio": 0.2})

    r = client.post("/api/ml/train", json={"arch": "logreg", "hyperparams": {"epochs": 8}, "name": "LogReg uji"})
    assert r.status_code == 202, r.text
    job = _wait_job(r.json()["id"])
    assert job["status"] == "done", job
    assert job["model_id"] and job["metrics"]["accuracy"] > 0.5
    assert len(job["history"]) == 8

    # registry + laporan lengkap
    models_list = client.get("/api/ml/models").json()
    assert len(models_list["models"]) == 1 and models_list["production_model_id"] is None
    mid = job["model_id"]
    detail = client.get(f"/api/ml/models/{mid}").json()
    rep = detail["report"]
    for key in ("accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_f1", "confusion_matrix",
                "per_class", "top3_accuracy", "log_loss", "history", "train_accuracy", "eval_split"):
        assert key in rep, key
    assert rep["eval_split"] == "test" and len(rep["per_class"]) == 5
    assert len(rep["confusion_matrix"]) == 5 and sum(map(sum, rep["confusion_matrix"])) == rep["n_samples"]

    # sebelum promosi: predict tanpa model_id → 409
    assert client.post("/api/ml/predict", json={"image": _png_data_url()}).status_code == 409
    # promosi ke produksi
    r = client.put("/api/ml/models/production", json={"model_id": mid})
    assert r.status_code == 200
    assert client.get("/api/ml/status").json()["production_model"]["id"] == mid
    # prediksi publik memakai model produksi
    r = client.post("/api/ml/predict", json={"image": _png_data_url()})
    assert r.status_code == 200
    body = r.json()
    assert body["model_id"] == mid and body["label"] in ("ha", "na", "ca", "ra", "ka")
    assert len(body["top"]) == 5 and abs(sum(t["probability"] for t in body["top"]) - 1) < 0.01
    assert body["preview"].startswith("data:image/png")
    # model produksi tidak boleh dihapus
    assert client.delete(f"/api/ml/models/{mid}").status_code == 409
    # rename
    assert client.patch(f"/api/ml/models/{mid}", json={"name": "Produksi v1"}).json()["name"] == "Produksi v1"
    # nonaktifkan produksi lalu hapus
    assert client.put("/api/ml/models/production", json={"model_id": None}).status_code == 200
    assert client.delete(f"/api/ml/models/{mid}").status_code == 200
    assert client.get("/api/ml/models").json()["models"] == []


def test_auto_promote_and_compare():
    client.put("/api/ml/classes", json={"labels": ["ha", "na", "ca"]})
    client.post("/api/ml/dataset/generate-synthetic", json={"per_class": 12, "seed": 2})
    ids = []
    for arch in ("centroid", "knn"):
        r = client.post("/api/ml/train", json={"arch": arch, "auto_promote": arch == "knn"})
        assert r.status_code == 202, r.text
        ids.append(_wait_job(r.json()["id"])["model_id"])
    assert client.get("/api/ml/status").json()["production_model"]["id"] == ids[1]
    r = client.post("/api/ml/predict/compare", json={"image": _png_data_url(), "model_ids": ids + ["hilang"]})
    res = r.json()["results"]
    assert res[0]["arch"] == "centroid" and res[1]["arch"] == "knn" and "error" in res[2]


def test_template_architecture_uses_font_templates():
    client.put("/api/ml/classes", json={"labels": ["ha", "na", "ca", "ra"]})
    client.post("/api/ml/dataset/generate-synthetic", json={"per_class": 8, "seed": 4, "strength": 0.3})
    r = client.post("/api/ml/train", json={"arch": "template"})
    assert r.status_code == 202, r.text
    job = _wait_job(r.json()["id"])
    assert job["status"] == "done"
    assert job["metrics"]["accuracy"] > 0.4


def test_jobs_listing_and_cancel_of_finished_job():
    client.put("/api/ml/classes", json={"labels": ["ha", "na"]})
    client.post("/api/ml/dataset/generate-synthetic", json={"per_class": 6, "seed": 9})
    r = client.post("/api/ml/train", json={"arch": "centroid"})
    job = _wait_job(r.json()["id"])
    assert client.get("/api/ml/train/jobs").json()["jobs"][0]["id"] == job["id"]
    assert client.delete(f"/api/ml/train/jobs/{job['id']}").status_code == 409
    assert client.get("/api/ml/train/jobs/tidak-ada").status_code == 404


# ── otorisasi mode prod ────────────────────────────────────────────────────

def test_prod_mode_requires_admin(prod_mode):
    assert client.get("/api/ml/dataset/stats").status_code == 403
    assert client.post("/api/ml/train", json={"arch": "centroid"}).status_code == 403
    assert client.put("/api/ml/classes", json={"labels": ["ha", "na"]}).status_code == 403
    assert client.get("/api/ml/models").status_code == 403
    # status & predict tetap publik (predict 409 karena belum ada model produksi)
    st = client.get("/api/ml/status")
    assert st.status_code == 200 and st.json()["is_admin"] is False
    assert client.post("/api/ml/predict", json={"image": _png_data_url()}).status_code == 409
    # dengan sesi admin → boleh
    h = _admin_headers()
    assert client.get("/api/ml/dataset/stats", headers=h).status_code == 200
    assert client.get("/api/ml/status", headers=h).json()["is_admin"] is True
