import os
from pathlib import Path

from app.storage_api.settings import settings

ROOT_DIR = Path(__file__).resolve().parents[2]  # Go up 3 levels until reaching root dir
TEST_ASSETS_DIR = ROOT_DIR / "tests" / "data"

BUCKET = settings.minio_bucket_name
SECONDARY_BUCKET = "test-bucket2"
OBJECT_KEY = "sample.txt"
BASE_URL = os.getenv("S3_PUBLIC_ENDPOINT_URL", "http://127.0.0.1:9000")
CONTENT_DATA = b"Hello from the write_object endpoint"
FILE_PATH = TEST_ASSETS_DIR / "sample.txt"
IMAGE_PATH = TEST_ASSETS_DIR / "image.png"
EMPTY_FILE = TEST_ASSETS_DIR / "empty-sample.txt"
LARGE_FILE = TEST_ASSETS_DIR / "large-sample.txt"
NON_ASCII_FILE = TEST_ASSETS_DIR / "non-ascii-sample.txt"
LARGE_FILE_SIZE_LIMIT_EXEEDED = TEST_ASSETS_DIR / "large-sample-size-limit-exeeded"

