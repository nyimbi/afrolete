pid_file = "/run/pjs/afrolete.agent.pid"

vault {
  address = "https://vault.lindela.io"
}

auto_auth {
  method "approle" {
    config = {
      role_id_file_path = "/etc/openbao-agent/afrolete.role_id"
      secret_id_file_path = "/run/pjs/afrolete.secret_id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink "file" {
    config = {
      path = "/run/pjs/afrolete.token"
    }
  }
}

template {
  destination = "/run/pjs/afrolete-backend.env"
  perms = "0600"
  contents = <<-EOT
    {{ with secret "secret/data/pjs/apps/afrolete/backend" }}
    AFROLETE_ENV={{ .Data.data.env }}
    AFROLETE_DATABASE_URL={{ .Data.data.database_url }}
    AFROLETE_CORS_ORIGINS={{ .Data.data.cors_origins }}
    {{ end }}
    {{ with secret "secret/data/pjs/auth/keycloak" }}
    AFROLETE_KEYCLOAK_ISSUER={{ .Data.data.issuer }}
    AFROLETE_KEYCLOAK_AUDIENCE=afrolete-api
    {{ end }}
    {{ with secret "secret/data/pjs/auth/spicedb" }}
    AFROLETE_SPICEDB_ENDPOINT={{ .Data.data.endpoint }}
    AFROLETE_SPICEDB_KEY={{ .Data.data.preshared_key }}
    AFROLETE_SPICEDB_INSECURE=true
    {{ end }}
  EOT
}

