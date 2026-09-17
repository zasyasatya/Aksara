"""Evaluasi CER pipeline OCR latin pada berbagai kondisi kamera (in-proses)."""
import sys
import zlib
import unicodedata

sys.path.insert(0, "."); sys.path.insert(0, "eval")
from backend.app.ocr import pipeline, render
from camera_sim import to_camera

TEXTS = [
    "om swastiastu\nsareng sami",
    "rahajeng semeng\nratu ajeng",
    "basa bali mawit\nsaking jaman dulu",
    "titiang nunas\nicang kerahayuan",
]

CAM = [
    ("ringan ", dict(blur=0.8, shadow=0.78, noise=5, jpeg_q=84, downscale=0.9, seed=11)),
    ("sedang ", dict(blur=1.1, shadow=0.6, noise=9, jpeg_q=76, downscale=0.7, seed=23)),
    ("gelap  ", dict(blur=1.3, shadow=0.45, noise=13, jpeg_q=70, downscale=0.9, seed=37)),
    ("jauh   ", dict(blur=1.5, shadow=0.62, noise=10, jpeg_q=72, downscale=0.45, seed=41)),
    ("kecil  ", dict(blur=0.9, shadow=0.7, noise=8, jpeg_q=75, downscale=0.3, seed=53)),
    ("sangat jauh", dict(blur=1.2, shadow=0.68, noise=7, jpeg_q=78, downscale=0.22, seed=67)),
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s.lower())
    return " ".join("".join(ch if ch.isalnum() else " " for ch in s).split())


def cer(ref: str, hyp: str) -> float:
    ref, hyp = norm(ref), norm(hyp)
    if not ref:
        return 0.0
    # Levenshtein (mantap untuk string pendek)
    dp = list(range(len(hyp) + 1))
    for i, rc in enumerate(ref, 1):
        prev, dp[0] = dp[0], i
        for j, hc in enumerate(hyp, 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (rc != hc))
            prev = cur
    return dp[-1] / len(ref)


def run(script="latin", tta=2, **opt):
    total, n, worst = 0.0, 0, []
    for text in TEXTS:
        page = render.render_page(text, font_size=44, rotate=1.0, noise=0, seed=zlib.crc32(text.encode()) % 1000)
        for cam, kw in CAM:
            data = to_camera(page, **kw)
            res = pipeline.scan_bytes(data, options={"script": script, "tta": tta, **opt})
            hyp = res["text"]["all"]
            c = cer(text.replace("\n", " "), hyp)
            total += c
            n += 1
            worst.append((c, cam, text.split("\n")[0], hyp.replace("\n", " | ")))
    worst.sort(reverse=True)
    per_cam: dict = {}
    for c, cam, t, h in worst:
        per_cam.setdefault(cam.strip(), []).append(c)
    breakdown = "  ".join(f"{k}={sum(v) / len(v):.2f}" for k, v in per_cam.items())
    print(f"=== script={script} opt={opt} → CER rata-rata {total / n:.3f} atas {n} kasus | {breakdown}")
    for c, cam, t, h in worst[:10]:
        print(f"  {c:4.2f} [{cam.strip():11}] {t!r} → {h!r}")
    return total / n


if __name__ == "__main__":
    opt = {}
    for a in sys.argv[1:]:
        k, _, v = a.partition("=")
        opt[k] = v if k in ("binarize", "script") else float(v)
    run(**opt)
