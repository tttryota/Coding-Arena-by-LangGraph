#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
env_file="$repo_root/.env"

if [ ! -f "$env_file" ]; then
    cp "$repo_root/.env.example" "$env_file"
fi

random_hex() {
    openssl rand -hex "$1"
}

ensure_value() {
    key=$1
    value=$2
    if ! grep -q "^${key}=" "$env_file"; then
        printf '%s=%s\n' "$key" "$value" >> "$env_file"
    fi
}

ensure_value LANGFUSE_TRACING_ENABLED true
ensure_value LANGFUSE_PUBLIC_KEY "lf_pk_$(random_hex 16)"
ensure_value LANGFUSE_SECRET_KEY "lf_sk_$(random_hex 24)"
ensure_value LANGFUSE_POSTGRES_PASSWORD "$(random_hex 24)"
ensure_value LANGFUSE_CLICKHOUSE_PASSWORD "$(random_hex 24)"
ensure_value LANGFUSE_REDIS_PASSWORD "$(random_hex 24)"
ensure_value LANGFUSE_MINIO_PASSWORD "$(random_hex 24)"
ensure_value LANGFUSE_NEXTAUTH_SECRET "$(random_hex 32)"
ensure_value LANGFUSE_SALT "$(random_hex 32)"
ensure_value LANGFUSE_ENCRYPTION_KEY "$(random_hex 32)"
ensure_value LANGFUSE_INIT_USER_EMAIL "local@obsidian.invalid"
ensure_value LANGFUSE_INIT_USER_PASSWORD "$(random_hex 16)"
ensure_value LANGFUSE_TRACING_ENVIRONMENT local
ensure_value LANGFUSE_RELEASE dev
ensure_value LANGFUSE_SAMPLE_RATE 1.0
ensure_value LANGFUSE_CAPTURE_CONTENT true

printf '%s\n' "Langfuse local credentials are ready in $env_file"
printf '%s\n' "Start with: docker compose --profile observability up --build"
printf '%s\n' "Open: http://localhost:3000"
