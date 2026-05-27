# MinIO Setup

Create an `afrolete` bucket in the shared PJS MinIO service.

Planned object prefixes:

```text
afrolete/
  imports/
  media/
  reports/
  exports/
  ai-artifacts/
  compliance/
```

Browser uploads should use backend-issued presigned URLs. The frontend must not
hold MinIO credentials.

