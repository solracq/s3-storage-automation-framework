from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    s3_endpoint_url: str
    s3_public_endpoint_url: str = "http://localhost:9000"
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    minio_bucket_name: str = "test-bucket"


settings = Settings()
