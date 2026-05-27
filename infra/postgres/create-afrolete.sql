-- Run as a PostgreSQL admin on db.lindela.io.
-- Replace the password out-of-band; never commit real credentials.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'afrolete') THEN
    CREATE ROLE afrolete LOGIN PASSWORD 'replace-outside-git';
  END IF;
END
$$;

SELECT 'CREATE DATABASE afrolete OWNER afrolete'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'afrolete')\gexec

\connect afrolete

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;

GRANT ALL ON SCHEMA public TO afrolete;

