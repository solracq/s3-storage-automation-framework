from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from botocore.exceptions import ClientError

from s3_lib.s3.s3_client import S3StorageClient

app = FastAPI(
    title="Portfolio S3 Storage API",
    description="A small FastAPI wrapper service for validating S3-compatible object storage with MinIO.",
    version="0.1.0",
)

storage = S3StorageClient()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "storage-api",
    }


@app.post("/buckets/bootstrap")
def bootstrap_bucket():
    storage.ensure_bucket_exists()
    return {
        "bucket": storage.bucket_name,
        "status": "ready",
    }


@app.post("/files/{object_key}")
async def upload_file(object_key: str, file: UploadFile = File(...)):
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="File content cannot be empty")

    result = storage.upload_file(
        object_key=object_key,
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    return {
        "message": "File uploaded successfully",
        **result,
    }


@app.get("/files")
def list_files():
    return {
        "bucket": storage.bucket_name,
        "objects": storage.list_objects(),
    }


@app.get("/files/{object_key}")
def download_file(object_key: str):
    try:
        file_stream, content_type = storage.download_file(object_key)
        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{object_key}"'
            },
        )
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code")

        if error_code in ["NoSuchKey", "404"]:
            raise HTTPException(status_code=404, detail=f"Object not found: {object_key}")

        raise HTTPException(status_code=500, detail="Failed to download object")


@app.delete("/files/{object_key}")
def delete_file(object_key: str):
    return storage.delete_object(object_key)
