"""OCR Lens — baca Aksara Bali & teks Latin dari kamera, lalu terjemahkan.

Modul ini adalah pipeline tingkat tinggi (praproses → segmentasi → klasifikasi →
decoding → translasi). Model klasifikasinya adalah model yang sama dengan Panel
Admin (``app.ml``) sehingga retraining admin langsung memperbaiki halaman Lens.
"""

from .config import DEFAULT_OPTIONS, feedback_config, get_config, merged_options, update_config
from .pipeline import ScanOptions, crop_glyph, scan_bytes

__all__ = [
    "ScanOptions",
    "scan_bytes",
    "crop_glyph",
    "get_config",
    "update_config",
    "merged_options",
    "feedback_config",
    "DEFAULT_OPTIONS",
]
