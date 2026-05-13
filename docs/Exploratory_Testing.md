# Exploratory Test Document:

## Purpose
Document to show the initial manual testing activity to understand and validate the product.

## Scenarios
Check FastAPI health:
curl http://localhost:8000/health


Bootstrap the S3 bucket:
curl -X POST http://localhost:8000/buckets/bootstrap

Create a sample file:
echo "Hello from local MinIO S3 automation framework" > sample.txt
Upload the file
curl -X POST \
  -F "file=@sample.txt" \
  http://localhost:8000/files/sample.txt
List files:
curl http://localhost:8000/files
Download the file:
curl http://localhost:8000/files/sample.txt -o downloaded-sample.txt
Compare files:
diff sample.txt downloaded-sample.txt
If there is no output from diff, the files match.
Delete the file:
curl -X DELETE http://localhost:8000/files/sample.txt

## Smoke Test Scenario
```text
curl http://localhost:8000/health
curl -X POST http://localhost:8000/buckets/bootstrap

echo "hello s3" > sample.txt

curl -X POST \
  -F "file=@sample.txt" \
  http://localhost:8000/files/sample.txt

curl http://localhost:8000/files

curl http://localhost:8000/files/sample.txt -o downloaded-sample.txt

diff sample.txt downloaded-sample.txt
```text