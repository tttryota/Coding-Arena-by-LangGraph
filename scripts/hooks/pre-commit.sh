#!/bin/sh

set -eu

. "$(dirname "$0")/common.sh"

changed_files=$(get_staged_files)

if [ -z "$changed_files" ] || is_docs_or_config_only "$changed_files"; then
  exit 0
fi

if has_match '^backend/' "$changed_files"; then
  run_backend_lint
fi

if has_match '^frontend/' "$changed_files"; then
  run_frontend_lint
fi
