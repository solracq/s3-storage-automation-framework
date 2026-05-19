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


def _get_log_level(env_var: str, default: str) -> int:
    """
    Resolve a logging level from an environment variable.

    Args:
        env_var (str): Environment variable name to inspect.
        default (str): Fallback logging level name.
    Returns:
        int: Logging level constant understood by the logging module.
    """
    level_name = os.getenv(env_var, default).upper()
    return getattr(logging, level_name, getattr(logging, default.upper()))


def pytest_configure(config):
    """
    Configure project-wide logging for pytest runs.

    Args:
        config: Pytest config object provided by the hook system.
    """
    _ = config

    # Keep test logs inside the tests folder by default, but allow CI to override
    # the destination path for artifact collection.
    log_dir_setting = Path(os.getenv("PYTEST_LOG_DIR", str(TESTS_DIR / "logs")))
    log_dir = log_dir_setting if log_dir_setting.is_absolute() else ROOT / log_dir_setting
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_name = os.getenv("PYTEST_LOG_FILE", "S3TestLog.txt")
    log_file = log_dir / log_file_name

    root_level = logging.DEBUG
    console_level = _get_log_level("PYTEST_CONSOLE_LOG_LEVEL", "INFO")
    file_level = _get_log_level("PYTEST_FILE_LOG_LEVEL", "DEBUG")

    logger = logging.getLogger()
    logger.setLevel(root_level)

    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(console_level)
    console.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    # Reset any existing root handlers so repeated test runs do not duplicate logs.
    logger.handlers.clear()

    logger.addHandler(console)
    logger.addHandler(file_handler)

    # Capture warnings emitted through the warnings module into the configured logs.
    logging.captureWarnings(True)

    # Keep common third-party libraries from flooding CI logs while still preserving
    # useful application-level debug messages in the file log.
    logging.getLogger("botocore").setLevel(_get_log_level("PYTEST_BOTOCORE_LOG_LEVEL", "INFO"))
    logging.getLogger("boto3").setLevel(_get_log_level("PYTEST_BOTO3_LOG_LEVEL", "INFO"))
    logging.getLogger("urllib3").setLevel(_get_log_level("PYTEST_URLLIB3_LOG_LEVEL", "INFO"))
    logging.getLogger("s3transfer").setLevel(_get_log_level("PYTEST_S3TRANSFER_LOG_LEVEL", "INFO"))

    logger.info(
        "Pytest logging configured. console=%s file=%s log_file=%s",
        logging.getLevelName(console_level),
        logging.getLevelName(file_level),
        log_file,
    )
