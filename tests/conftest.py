import os
import sys
import pytest
import logging
from pathlib import Path

from botocore.exceptions import ClientError


# Make the repository root importable so tests can import from src/ and app/.
ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Provide safe defaults so pydantic settings can initialize during test imports.
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "minioadmin123")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("MINIO_BUCKET_NAME", "test-bucket")


def make_client_error(code: str, operation_name: str = "TestOperation") -> ClientError:
    """Create a botocore ClientError with a minimal error payload."""
    return ClientError(
        {
            "Error": {
                "Code": code,
                "Message": f"{code} failure",
            }
        },
        operation_name,
    )

def pytest_configure(config):
    """
    Configure project-wide logging for pytest runs.

    Args:
        config: Pytest config object provided by the hook system.
    """
    _ = config

    # Keep test logs inside the tests folder, regardless of the invocation cwd.
    log_dir = TESTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "S3TestLog.txt"

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Reset any existing root handlers so repeated test runs do not duplicate logs.
    logger.handlers.clear()

    logger.addHandler(console)
    logger.addHandler(file_handler)
