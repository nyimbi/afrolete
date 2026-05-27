# SpiceDB Setup

`afrolete.zed` is the AfroLete authorization schema for the shared PJS SpiceDB
service.

## Backend Runtime

Use the in-memory authorization service only for local tests and trusted local
tools:

```env
AFROLETE_AUTHZ_MODE=memory
```

Use SpiceDB in deployed environments:

```env
AFROLETE_AUTHZ_MODE=spicedb
AFROLETE_SPICEDB_ENDPOINT=62.84.181.55:50051
AFROLETE_SPICEDB_KEY=<from OpenBao>
AFROLETE_SPICEDB_INSECURE=true
AFROLETE_SPICEDB_REQUEST_TIMEOUT_SECONDS=3
```

AfroLete writes relationships with `TOUCH` semantics so repeated API operations
are idempotent. Permission checks fail closed if SpiceDB is unavailable.
