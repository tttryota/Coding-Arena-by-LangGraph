#!/bin/sh

set -eu

. "$(dirname "$0")/common.sh"

changed_files=$(get_push_files)

if [ -z "$changed_files" ] || is_docs_or_config_only "$changed_files"; then
  exit 0
fi

run_backend=0
run_frontend=0

if has_match '^backend/' "$changed_files"; then
  run_backend=1
fi

if has_match '^frontend/' "$changed_files"; then
  run_frontend=1
fi

if has_match '^backend/api/' "$changed_files" || has_match '^frontend/src/types/api\.ts$' "$changed_files"; then
  run_backend=1
  run_frontend=1
fi

if [ "$run_backend" -eq 1 ]; then
  run_backend_push
fi

if [ "$run_frontend" -eq 1 ]; then
  run_frontend_push
fi
