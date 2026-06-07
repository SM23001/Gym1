#!/usr/bin/env bash
# Start the Postgres MCP server for Cursor using gymdb_test (never production).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

: "${GYM_DB_HOST:=192.168.1.34}"
: "${GYM_DB_PORT:=5432}"
: "${GYM_DB_USER:=gymuser}"
: "${GYM_DB_PASSWORD:=gympass}"

# MCP always uses the test database — tests TRUNCATE tables; never point agents at gymdb.
MCP_DB_NAME="gymdb_test"

export DATABASE_URL="postgresql://${GYM_DB_USER}:${GYM_DB_PASSWORD}@${GYM_DB_HOST}:${GYM_DB_PORT}/${MCP_DB_NAME}"

exec npx -y @henkey/postgres-mcp-server
