from fastapi import FastAPI, File, HTTPException, Request, UploadFile
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
    """
    Return a simple health status for the FastAPI storage service.

    Args:
        None
    Returns:
        dict: Basic service status information.
    Raises:
        None
    """
    return {
        "status": "ok",
        "service": "storage-api",
    }


@app.post("/buckets/bootstrap")
async def bootstrap_bucket(bucket_name: str):
    """
    Ensure that a bucket exists before use.

    Args:
        bucket_name (str): Name of the bucket to verify or create.
    Returns:
        dict: Bucket readiness information.
    Raises:
        ClientError: If the bucket check fails for an unexpected reason.
        RuntimeError: If bucket creation is attempted but does not succeed.
    """
    storage.ensure_bucket_exists(bucket_name)
    return {
        "bucket": storage.bucket_name,
        "status": "ready",
    }


@app.post("/buckets")
async def create_bucket(bucket_name: str):
    """
    Create a bucket through the storage client.

    Args:
        bucket_name (str): Name of the bucket to create.
    Returns:
        dict: Success or failure details for the create operation.
    Raises:
        None
    """
    return storage.create_bucket(bucket_name)


@app.delete("/buckets/{bucket_name}")
async def delete_bucket(bucket_name: str):
    """
    Delete a bucket through the storage client.

    Args:
        bucket_name (str): Name of the bucket to delete.
    Returns:
        dict: Success or failure details for the delete operation.
    Raises:
        None
    """
    return storage.delete_bucket(bucket_name)


@app.get("/buckets")
async def list_buckets():
    """
    List all buckets available to the configured storage client.

    Args:
        None
    Returns:
        dict: Raw bucket listing response or a failure message.
    Raises:
        None
    """
    return storage.list_buckets()


@app.post("/files/{object_key}")
async def upload_file(object_key: str, file: UploadFile = File(...)):
    """
    Upload a multipart file into the default configured bucket.

    Args:
        object_key (str): Key to assign to the uploaded object.
        file (UploadFile): Uploaded multipart file content.
    Returns:
        dict: Success details for the uploaded file.
    Raises:
        HTTPException: If the uploaded file is empty.
    """
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
    """
    List objects stored in a bucket.

    Args:
        bucket_name (str): Name of the bucket to inspect.
    Returns:
        dict: Bucket name plus the list of object summaries.
    Raises:
        None
    """
    return {
        "bucket": storage.bucket_name,
        "objects": storage.list_objects(bucket_name),
    }


@app.get("/objects/{object_key}/metadata")
async def get_object_metadata(bucket_name: str, object_key: str):
    """
    Retrieve metadata for an object in a bucket.

    Args:
        bucket_name (str): Name of the bucket containing the object.
        object_key (str): Key of the object to inspect.
    Returns:
        dict: Metadata response for the requested object.
    Raises:
        None
    """
    return storage.get_object_metadata(bucket_name, object_key)


@app.get("/objects/{object_key}/size")
async def get_object_size(bucket_name: str, object_key: str):
    """
    Retrieve the size of an object in bytes.

    Args:
        bucket_name (str): Name of the bucket containing the object.
        object_key (str): Key of the object to inspect.
    Returns:
        dict: Object size information for the requested object.
    Raises:
        HTTPException: If the object size cannot be retrieved.
    """
    size = storage.get_object_size(bucket_name, object_key)

    if size == -1:
        raise HTTPException(status_code=500, detail=f"Failed to get size for object: {object_key}")

    return {
        "bucket_name": bucket_name,
        "object_key": object_key,
        "size": size,
    }


@app.put("/objects/{object_key}")
async def write_object(bucket_name: str, object_key: str, request: Request):
    """
    Write raw request body bytes to an object in a bucket.

    Args:
        bucket_name (str): Name of the target bucket.
        object_key (str): Key to create or overwrite.
        request (Request): Incoming request containing the raw body to store.
    Returns:
        dict: Success or failure details for the write operation.
    Raises:
        HTTPException: If the request body is empty.
    """
    content = await request.body()

    if not content:
        raise HTTPException(status_code=400, detail="Request body cannot be empty")

    return storage.write_object(bucket_name, object_key, content)


@app.get("/objects/{object_key}")
async def read_object(bucket_name: str, object_key: str):
    """
    Read the raw content of an object from a bucket.

    Args:
        bucket_name (str): Name of the bucket containing the object.
        object_key (str): Key of the object to read.
    Returns:
        Response: HTTP response containing the object body and content type.
    Raises:
        HTTPException: If the object cannot be read.
    """
    result = storage.read_object(bucket_name, object_key)

    if isinstance(result, dict):
        raise HTTPException(
            status_code=500,
            detail=result.get("message", f"Failed to read object: {object_key}"),
        )

    metadata = storage.get_object_metadata(bucket_name, object_key)
    content_type = metadata.get("ContentType", "application/octet-stream")

    return Response(
        content=result,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{object_key}"'
        },
    )


@app.get("/files/{object_key}")
async def download_file(object_key: str):
    """
    Download an object from the default configured bucket.

    Args:
        object_key (str): Key of the object to download.
    Returns:
        Response: HTTP response containing the downloaded object content.
    Raises:
        HTTPException: If the object is missing or cannot be downloaded.
    """
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
    """
    Delete an object from a bucket.

    Args:
        bucket_name (str): Name of the bucket containing the object.
        object_key (str): Key of the object to delete.
    Returns:
        dict: Success or failure details for the delete operation.
    Raises:
        None
    """
    return storage.delete_object(bucket_name, object_key)
