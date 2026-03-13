-- Runs once on first DB initialization (docker-entrypoint-initdb.d).
-- Enables the pgvector extension so the backend can use vector columns.
CREATE EXTENSION IF NOT EXISTS vector;
