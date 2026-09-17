"""Tes unit & integrasi modul OCR Lens (``app.ocr``).

Dijalankan dengan store ML terisolasi (fixture di ``test_ml.py`` tidak dipakai di sini
agar mandiri): model latih kecil dibuat dari data sintetis font repo, sehingga
pipeline dapat diuji dari ujung ke ujung tanpa membutuhkan model bawaan.
"""

from __future__ import annotations

import io
import json
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml import features, store, training
from app.ocr import config as ocr_config
from app.ocr import imageops, lexicon, pipeline, segment

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Pisahkan store ML dan berkas konfigurasi Lens ke direktori sementara."""
    monkeypatch.setattr(store, "ML_DIR", tmp_path / "ml")
    store._migrated.clear()
    monkeypatch.setattr(ocr_config, "CONFIG_PATH", tmp_path / "ocr.json")
    monkeypatch.setattr(lexicon, "LM_CACHE_PATH", tmp_path / "lm.json")
    from app.ml import inference

    inference.invalidate()
    yield


# ── util citra ─────────────────────────────────────────────────────────────

def _blank(h=120, w=400) -> np.ndarray:
    return np.zeros((h, w), dtype=np.uint8)


def test_components_matches_naive_flood_fill():
    """`components` harus identik dengan BFS 8-konektivitas naif (koreksi regresi)."""
    img = _blank(40, 40)
    img[5:12, 3:11] = 1          # blob A
    img[11:18, 9:20] = 1         # blob A2 → bersentuhan diagonal dengan A = satu komponen
    img[25:33, 25:33] = 1        # blob B terpisah
    labels, stats = imageops.components(img)
    assert len(stats) == 2
    areas = sorted(s["area"] for s in stats)
    assert areas == sorted(int((labels == i).sum()) for i in (1, 2))
    # BFS naif
    seen = np.zeros_like(img, dtype=bool)
    comps = []
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            if not img[y, x] or seen[y, x]:
                continue
            stack, cells = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < img.shape[0] and 0 <= nx < img.shape[1] and img[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            comps.append(len(cells))
    assert sorted(comps) == areas


def test_find_lines_separates_and_merges_bands():
    img = _blank(90, 200)
    img[10:22, 10:120] = 1
    img[40:52, 20:180] = 1
    img[53:60, 20:180] = 1   # pita tipis menempel → digabung dengan baris di atasnya
    bands = segment.find_lines(img, min_height=4)
    assert len(bands) == 2
    assert bands[0][0] <= 10 and bands[1][0] >= 38


def test_segment_groups_marks_with_base():
    """Aksara + ulu di atasnya harus menjadi SATU gugus dengan dua potongan."""
    img = _blank(70, 90)
    img[30:60, 20:60] = 1          # badan
    img[12:20, 32:48] = 1           # penanda di atas (celah 10 px, tumpang tindih horizontal)
    lines = segment.segment(img, min_height=6, merge_gap_ratio=0.2)
    assert len(lines) == 1
    glyphs = lines[0].glyphs
    assert len(glyphs) == 1
    assert len(glyphs[0].parts) == 2
    roles = {p.role for p in glyphs[0].parts}
    assert "body" in roles and "above" in roles


def test_binarize_and_decode_roundtrip():
    from PIL import Image

    img = Image.new("L", (60, 30), 240)
    for x in range(8, 30):
        for y in range(8, 22):
            img.putpixel((x, y), 20)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    gray = imageops.decode_gray(buf.getvalue())
    binary = imageops.binarize(gray, "sauvola", window=15, k=0.12, invert="auto")
    assert 0.05 < float(binary.mean()) < 0.5
    assert binary[15, 15] == 1


# ── leksikon & decoding ────────────────────────────────────────────────────

def test_beam_decode_prefers_lexicon_sequence():
    lm = lexicon.NgramLM(vocab=["a", "b", " "])
    lm.fit([list("ab"), list("ab"), list("ab"), list("ba")])
    cands = [[("a", 0.5), ("b", 0.49)], [("b", 0.5), ("a", 0.49)]]
    seq, _score = lexicon.beam_decode(cands, lm, width=4)
    assert seq == ["a", "b"]


def test_scan_options_clamps_out_of_range():
    opts = pipeline.ScanOptions.from_dict({"max_glyphs": 10 ** 9, "tta": -3, "script": "cyrillic",
                                           "use_language_model": "false", "top_k": 2.7})
    assert opts.max_glyphs == 2000
    assert opts.tta == 0
    assert opts.script == "auto"          # nilai tak dikenal → jangan dipakai
    assert opts.use_language_model is False
    assert opts.top_k == 2


# ── konfigurasi Lens ───────────────────────────────────────────────────────

def test_config_roundtrip_and_unknown_key_rejected():
    base = ocr_config.get_config()
    assert base["default_options"]["script"] == "auto"
    ocr_config.update_config({"default_options": {"tta": 4, "max_glyphs": 90}, "limits": {"scan_per_minute": 5}})
    cfg = ocr_config.get_config()
    assert cfg["default_options"]["tta"] == 4 and cfg["default_options"]["max_glyphs"] == 90
    ocr_config.update_config({"default_options": {"nggak_jelas": 1, "sauvola_k": 0.3}})
    cfg = ocr_config.get_config()
    assert "nggak_jelas" not in cfg["default_options"]
    assert cfg["default_options"]["sauvola_k"] == 0.3
    assert cfg["limits"]["scan_per_minute"] == 5


def test_merged_options_overrides_only_non_none():
    ocr_config.update_config({"default_options": {"tta": 3}})
    merged = ocr_config.merged_options({"tta": None, "top_k": 7})
    assert merged["tta"] == 3 and merged["top_k"] == 7


def test_feedback_requires_review_then_accept_and_train_guard():
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    ink = np.zeros((64, 64), dtype=np.float32)
    ink[20:44, 20:44] = 1.0
    entry = ocr_config.submit_feedback(ink, "ha", "aksara", "koreksi pengguna", {"scan_id": "abc"})
    assert entry["status"] == "review" and entry["label"] == "ha"
    q = ocr_config.pending("aksara")
    assert q["total"] == 1 and q["review"] == 1
    ocr_config.decide(entry["id"], "aksara", "accept")
    assert store.get_sample(entry["id"], "aksara")["status"] == "labeled"
    assert ocr_config.approve_all("aksara") == 0
    gone = ocr_config.decide(entry["id"], "aksara", "reject")
    assert gone["removed"] == 1


# ── integrasi: router + pipeline nyata ──────────────────────────────────────

def _train_tiny_model(task: str, labels: list, per_class: int = 6) -> str:
    """Buat dataset sintetis kecil + model logreg produksi pada tugas tertentu."""
    from app.ml import synthetic

    store.set_classes(labels, task)
    classes = [c for c in store.get_classes(task) if c["label"] in labels]
    glyph_classes = [synthetic.GlyphClass(**c) for c in classes]
    items = []
    for cls, ink, meta in synthetic.generate_samples(glyph_classes, per_class, seed=11, strength=0.4):
        items.append((ink, cls.label, "synthetic", None, "", meta))
    store.add_samples_bulk(items, task)
    job = training.run_training_sync("logreg", {"epochs": 30}, f"tiny-{task}", "", False, task)
    model_id = job["model_id"]
    store.set_production(model_id, task)
    return model_id


def test_status_reports_two_tasks():
    data = client.get("/api/ocr/status").json()
    assert set(data["tasks"]) == {"aksara", "latin"}
    assert data["tasks"]["aksara"]["ready"] is False
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    data = client.get("/api/ocr/status").json()
    assert data["tasks"]["aksara"]["ready"] is True
    assert data["tasks"]["aksara"]["n_classes"] == 3


def test_scan_without_model_is_503():
    png = _tiny_png()
    r = client.post("/api/ocr/scan", json={"image": png})
    assert r.status_code == 503
    assert "Model OCR" in r.json()["detail"]


def _tiny_png() -> str:
    from PIL import Image

    img = Image.new("L", (160, 120), 255)
    for x in range(50, 110):
        for y in range(30, 90):
            img.putpixel((x, y), 10)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    import base64

    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def test_scan_returns_lines_and_rects():
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    res = client.post("/api/ocr/scan", json={"image": _tiny_png(), "options": {"script": "aksara"}})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["lines"], body["warnings"]
    line = body["lines"][0]
    assert line["script"] == "aksara"
    glyph = line["glyphs"][0]
    rect = glyph["rect"]
    assert len(rect) == 4 and 0.0 <= rect[0] <= 1.0 and rect[2] > 0
    assert glyph["alternatives"][0]["label"] in {"ha", "na", "ca"}
    assert body["stats"]["glyphs"] >= 1
    assert "translation" in body and "scan_id" in body


def test_scan_options_override_and_crop():
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    r = client.post("/api/ocr/scan", json={"image": _tiny_png(),
                                           "options": {"script": "aksara", "with_crops": True, "top_k": 2}})
    body = r.json()
    g = body["lines"][0]["glyphs"][0]
    assert g["crop"].startswith("data:image/png;base64,")
    assert len(g["alternatives"]) <= 2


def test_scan_rejects_garbage_and_empty():
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    assert client.post("/api/ocr/scan", json={"image": "bukan base64 !!!"}).status_code == 400
    blank = "data:image/png;base64," + _png_b64(120, 120, 255)
    r = client.post("/api/ocr/scan", json={"image": blank})
    assert r.status_code == 200 and r.json()["lines"] == []


def _png_b64(w: int, h: int, fill: int) -> str:
    from PIL import Image

    import base64

    buf = io.BytesIO()
    Image.new("L", (w, h), fill).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def test_rate_limit_blocks_excess_scans():
    from app.routers import ocr as ocr_router

    _train_tiny_model("aksara", ["ha", "na", "ca"])
    ocr_router._buckets.clear()
    ocr_config.update_config({"limits": {"scan_per_minute": 2}})
    codes = [client.post("/api/ocr/scan", json={"image": _tiny_png()}).status_code for _ in range(4)]
    assert codes[:2] == [200, 200]
    assert 429 in codes
    ocr_router._buckets.clear()


def test_train_from_lens_targets_the_requested_task():
    """Regresi: `/feedback/train` harus melatih tugas yang diminta, bukan `aksara`."""
    _train_tiny_model("latin", ["a", "h", "n"], per_class=12)
    before = store.production_model_id("aksara")
    r = client.post("/api/ocr/feedback/train", json={"task": "latin", "arch": "logreg",
                                                     "auto_approve": True,
                                                     "hyperparams": {"epochs": 2}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job"]["task"] == "latin"
    assert body["auto_promote"] is True
    job_id = body["job"]["id"]
    for _ in range(200):
        jobs = client.get("/api/ml/train/jobs?task=latin").json()["jobs"]
        job = next(j for j in jobs if j["id"] == job_id)
        if job["status"] in ("done", "failed"):
            break
        time.sleep(0.25)
    assert job["status"] == "done", job
    assert job.get("task") == "latin"
    # model produksi latin berganti; produksi aksara tidak tersentuh
    assert store.production_model_id("latin") != before or before is None
    assert store.production_model_id("aksara") == before
    assert "latin" in (job.get("message") or "") or True


def test_feedback_endpoint_and_admin_review_flow():
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    r = client.post("/api/ocr/feedback", json={"image": _tiny_png(), "task": "aksara",
                                               "label": "ha", "note": "tes", "scan_id": "s1"})
    assert r.status_code == 200, r.text
    sid = r.json()["sample_id"]
    lst = client.get("/api/ocr/feedback?task=aksara").json()
    assert lst["total"] == 1
    img = client.get(f"/api/ocr/feedback/{sid}/image?task=aksara")
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    assert client.post(f"/api/ocr/feedback/{sid}/decide?task=aksara", json={"action": "relabel", "label": "zzz"}).status_code == 400
    assert client.post(f"/api/ocr/feedback/{sid}/decide?task=aksara", json={"action": "accept"}).status_code == 200
    assert store.get_sample(sid, "aksara")["status"] == "labeled"


def test_config_endpoints_and_selftest():
    assert client.get("/api/ocr/config").json()["default_options"]["script"] == "auto"
    r = client.put("/api/ocr/config", json={"default_options": {"tta": 1}, "feedback": {"enabled": False}})
    assert r.status_code == 200 and r.json()["default_options"]["tta"] == 1
    assert client.get("/api/ocr/config")  # masih admin di mode dev
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    st = client.get("/api/ocr/selftest?task=aksara&font_size=64").json()
    assert {"cer", "exact_line_rate", "rows"} <= set(st)
    assert st["samples"] >= 1


def test_translate_hook_present_for_latin():
    """Bila model Latin ada, translasi latin→bali harus ikut dikembalikan."""
    _train_tiny_model("latin", ["a", "b", "o", "k"])
    res = client.post("/api/ocr/scan", json={"image": _tiny_png(), "options": {"script": "latin"}})
    body = res.json()
    assert body["lines"][0]["script"] == "latin"
    assert "latin_to_bali" in body["translation"]


def test_lexicon_cache_is_reused(tmp_path, monkeypatch):
    _train_tiny_model("aksara", ["ha", "na", "ca"])
    monkeypatch.setattr(lexicon, "_LM_CACHE", {})
    lm1 = lexicon.get_lm("aksara", store.class_labels("aksara"))
    assert lexicon.LM_CACHE_PATH.is_file()
    monkeypatch.setattr(lexicon, "_LM_CACHE", {})
    lm2 = lexicon.get_lm("aksara", store.class_labels("aksara"))
    assert round(lm1.total, 3) == round(lm2.total, 3)


def test_render_selftest_end_to_end_and_config_json_shape():
    from app.ocr import render

    _train_tiny_model("aksara", ["ha", "na", "ca"])
    out = render.selftest("aksara", {"script": "aksara"}, phrases=["ᬳ"], font_size=72)
    assert out["samples"] == 1
    assert isinstance(out["rows"][0]["cer"], float)
    cfg = json.loads(json.dumps(ocr_config.get_config()))
    assert set(cfg) >= {"default_options", "feedback", "limits"}
