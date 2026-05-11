import boto3
from src.storage_automation.interfaces.s3 import S3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.storage_api.settings import Settings


class S3Client(S3):

    def __init__(self) -> None:
        self.bucket_name = Settings.minio_bucket_name
        self.s3_client = boto3.client( # customizing how the S3 client talks to the MinIO service.
            "s3", # AWS service identifier, 's3' as the low-level client to build.
            endpoint_url=Settings.s3_endpoint_url,
            aws_access_key_id=Settings.aws_access_key_id,
            aws_secret_access_key=Settings.aws_secret_access_key,
            region_name=Settings.aws_region,
            config=Config(signature_version="s3v4"), # signing S3 API calls with AWS Signature Ver 4.
        )

    @property
    def access_type(self):
        return "S3 Client"

    def bucket_exists(self, bucket_name: str) -> bool:
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as error:
            self.s3_client.create_bucket(Bucket=bucket_name)

    def create_bucket(self, bucket_name: str) -> dict:
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            return {"message": "Bucket created successfully"}
        except ClientError as error:
            return {"message": "Bucket already exists"}