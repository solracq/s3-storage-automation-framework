from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from botocore.exceptions import ClientError

from src.storage_automation.s3_client import S3Client

app = FastAPI(
    title="Portfolio S3 Storage API",
    description="A small FastAPI wrapper service for validating S3-compatible object storage with MinIO.",
    version="0.1.0",
)

storage = S3Client()


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "storage-api",
    }


@app.post("/buckets/bootstrap")
async def bootstrap_bucket(bucket_name: str):
    storage.ensure_bucket_exists(bucket_name)
    return {
        "bucket": storage.bucket_name,
        "status": "ready",
    }


@app.post("/files/{object_key}")
async def upload_file(object_key: str, file: UploadFile = File(...)):
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="File content cannot be empty")

    result = storage.upload_bytes(
        object_key=object_key,
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    return {
        "message": "File uploaded successfully",
        **result,
    }


@app.get("/files")
async def list_files(bucket_name: str):
    return {
        "bucket": storage.bucket_name,
        "objects": storage.list_objects(bucket_name),
    }


@app.get("/files/{object_key}")
async def download_file(object_key: str):
    try:
        file_stream, content_type = storage.download_file(object_key)
        return Response(
            content=file_stream.getvalue(),
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
async def delete_file(bucket_name: str, object_key: str):
    return storage.delete_object(bucket_name, object_key)
