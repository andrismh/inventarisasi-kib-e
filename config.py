import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{INSTANCE_DIR / 'inventory.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXCEL_SEED_PATH = BASE_DIR / "assets" / "templates" / "Format_Excel_KIBE.xlsx"
    FOTO_UPLOAD_DIR = BASE_DIR / "app" / "static" / "foto"
    MAX_FOTO_UPLOAD_BYTES = int(os.environ.get("MAX_FOTO_UPLOAD_BYTES", 5 * 1024 * 1024))
    FOTO_MAX_DIMENSION = int(os.environ.get("FOTO_MAX_DIMENSION", 1920))
    FOTO_JPEG_QUALITY = float(os.environ.get("FOTO_JPEG_QUALITY", 0.8))
    FOTO_ALLOWED_MIME_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
