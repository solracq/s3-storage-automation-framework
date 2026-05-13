# Exploratory Test Document:

## Purpose
Document to show the initial manual testing activity to understand and validate the product.

## API Endpoints
- `GET /health` : service health check
- `POST /buckets/bootstrap?bucket_name=...` : ensure a bucket exists
- `POST /buckets?bucket_name=...` : create a bucket
- `DELETE /buckets/{bucket_name}` : delete a bucket
- `GET /buckets` : list buckets
- `POST /files/{object_key}` : upload a file to the default configured bucket
- `GET /files?bucket_name=...` : list objects in a bucket
- `GET /files/{object_key}` : download a file from the default configured bucket
- `DELETE /files/{object_key}?bucket_name=...` : delete an object from a bucket
- `GET /objects/{object_key}/metadata?bucket_name=...` : get object metadata
- `GET /objects/{object_key}/size?bucket_name=...` : get object size
- `PUT /objects/{object_key}?bucket_name=...` : write raw object content
- `GET /objects/{object_key}?bucket_name=...` : read raw object content

## Notes
- Quote URLs that contain query parameters when using `zsh`, for example: `curl "http://localhost:8000/files?bucket_name=test-bucket"`.
- The `/files/{object_key}` routes use the default configured bucket, while the `/objects/...` routes require an explicit `bucket_name` query parameter.

## Test Scenarios
### Scenario 1: Check FastAPI health:
```text
curl http://localhost:8000/health
```

**Output**
```text
portfolio-storage-api  | INFO:  "GET /health HTTP/1.1" 200 OK
{"status":"ok","service":"storage-api"}
```

### Scenario 2: Bootstrap the S3 bucket:
```text
curl -X POST "http://localhost:8000/buckets/bootstrap?bucket_name=test-bucket"
```

**Output**
```text
portfolio-storage-api  | INFO:  - "POST /buckets/bootstrap?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","status":"ready"}
```

### Scenario 3: Create and upload a file to a bucket, then apply file/object related operations such as list, download, compare and delete file.

#### 3.1 Create a sample file:
```text
echo "Hello from local MinIO S3 automation framework" > sample.txt
```

#### 3.2 Upload the file
```text
curl -X POST \
  -F "file=@sample.txt" \
  http://localhost:8000/files/sample.txt
```

**Output**
```text
portfolio-storage-api  | INFO: - "POST /files/sample.txt HTTP/1.1" 200 OK

{"message":"Object uploaded successfully","bucket":"test-bucket","object_key":"sample.txt","content_type":"text/plain"}
```

#### 3.3 List files:
```text
curl "http://localhost:8000/files?bucket_name=test-bucket"
```

**Output**
```text
portfolio-storage-api  | INFO: - "GET /files?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","objects":[{"key":"sample.txt","size":47,"last_modified":"2026-05-13T03:35:45.022000+00:00"}]}
```

#### 3.4 Download the file:
```text
curl http://localhost:8000/files/sample.txt -o downloaded-sample.txt
```

**Output**
```text
portfolio-storage-api  | INFO: - "GET /files/sample.txt HTTP/1.1" 200 OK

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    47  100    47    0     0   3523      0 --:--:-- --:--:-- --:--:--  3615
```

```text
cat downloaded-sample.txt:
Hello from local MinIO S3 automation framework
```

#### 3.5 Compare files:
```text
diff sample.txt downloaded-sample.txt
```

**Note**: If there is no output from diff, the files match.

#### 3.6 Delete the file:
```text
curl -X DELETE "http://localhost:8000/files/sample.txt?bucket_name=test-bucket"
```

**Output**
```text
portfolio-storage-api  | INFO: - "DELETE /files/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

{"message":"Object deleted successfully","bucket_name":"test-bucket","object_key":"sample.txt"}
```

### Additional Scenarios
List buckets:
```text
curl "http://localhost:8000/buckets"
```

Create bucket:
```text
curl -X POST "http://localhost:8000/buckets?bucket_name=test-bucket"
```

Delete bucket:
```text
curl -X DELETE "http://localhost:8000/buckets/test-bucket"
```

Get Object Metadata:
```text
curl "http://localhost:8000/objects/sample.txt/metadata?bucket_name=test-bucket"
```

Get Object Size:
```text
curl "http://localhost:8000/objects/sample.txt/size?bucket_name=test-bucket"
```

Write Object:
```text
curl -X PUT "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" --data-binary @sample.txt
```

Read Object:
```text
curl "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket"
```
