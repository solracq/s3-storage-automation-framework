import os
import sys
from pathlib import Path

from botocore.exceptions import ClientError


# Make the repository root importable so tests can import from src/ and app/.
ROOT = Path(__file__).resolve().parents[1]
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
