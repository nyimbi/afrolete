# MinIO Setup

Create an `afrolete` bucket in the shared PJS MinIO service.

Planned object prefixes:

```text
afrolete/
  <organization-id>/<resource-id>/<checksum>-<filename>
  ai-artifacts/
  compliance/
```

The backend owns MinIO credentials. Browser uploads should continue to flow
through backend endpoints or backend-issued presigned URLs; the frontend must
not hold MinIO credentials.

Backend settings for the shared PJS MinIO service:

```env
AFROLETE_OBJECT_STORAGE_MODE=s3
AFROLETE_OBJECT_STORAGE_ENDPOINT=https://minio.lindela.io
AFROLETE_OBJECT_STORAGE_REGION=us-east-1
AFROLETE_OBJECT_STORAGE_BUCKET=afrolete
AFROLETE_OBJECT_STORAGE_ACCESS_KEY=...
AFROLETE_OBJECT_STORAGE_SECRET_KEY=...
AFROLETE_OBJECT_STORAGE_PUBLIC_URL=https://minio.lindela.io/afrolete
```

Local development can leave `AFROLETE_OBJECT_STORAGE_MODE=local`; report
artifacts and equipment files then stay under `data/report-artifacts` and
`data/equipment-files`.
