path "secret/data/pjs/apps/afrolete/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/pjs/apps/afrolete/*" {
  capabilities = ["read", "list"]
}

path "secret/data/pjs/auth/keycloak" {
  capabilities = ["read"]
}

path "secret/data/pjs/auth/spicedb" {
  capabilities = ["read"]
}

path "secret/data/pjs/infrastructure/minio" {
  capabilities = ["read"]
}

