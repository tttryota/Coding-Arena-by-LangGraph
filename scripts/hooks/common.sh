#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
ZERO_SHA=0000000000000000000000000000000000000000

cd "$ROOT_DIR"

get_staged_files() {
  if [ -n "${HOOK_CHANGED_FILES:-}" ]; then
    printf '%s\n' "$HOOK_CHANGED_FILES"
    return
  fi
  git diff --cached --name-only --diff-filter=ACMR
}

get_push_files() {
  if [ -n "${HOOK_CHANGED_FILES:-}" ]; then
    printf '%s\n' "$HOOK_CHANGED_FILES"
    return
  fi

  updates=$(cat)
  if [ -z "$updates" ]; then
    if git rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
      git diff --name-only '@{upstream}'...HEAD
    fi
    return
  fi

  printf '%s\n' "$updates" | while read -r local_ref local_sha remote_ref remote_sha; do
    [ -z "${local_sha:-}" ] && continue
    [ "$local_sha" = "$ZERO_SHA" ] && continue

    if [ "$remote_sha" = "$ZERO_SHA" ]; then
      if git rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
        base=$(git merge-base "$local_sha" '@{upstream}')
      elif git rev-parse --verify refs/remotes/origin/HEAD >/dev/null 2>&1; then
        base=$(git merge-base "$local_sha" refs/remotes/origin/HEAD)
      else
        base=$(git rev-list --max-parents=0 "$local_sha" | tail -n 1)
      fi
    else
      base=$remote_sha
    fi

    git diff --name-only "$base" "$local_sha"
  done | sort -u
}

has_match() {
  pattern=$1
  files=$2
  printf '%s\n' "$files" | grep -Eq "$pattern"
}

is_docs_or_config_only() {
  files=$1
  if [ -z "$files" ]; then
    return 0
  fi

  ! printf '%s\n' "$files" | grep -Ev \
    '^(README\.md|frontend/README\.md|docs/|mise\.toml$|lefthook\.yml$|scripts/hooks/|.+\.(png|jpg|jpeg|gif|svg|webp))$' \
    >/dev/null
}

run_or_echo() {
  label=$1
  shift
  if [ "${HOOK_DRY_RUN:-0}" = "1" ]; then
    printf '%s\n' "$label"
    return
  fi
  "$@"
}

run_in_repo_env() {
  if command -v pnpm >/dev/null 2>&1; then
    sh -lc "$1"
    return
  fi

  if command -v mise >/dev/null 2>&1; then
    mise exec -- sh -lc "$1"
    return
  fi

  printf 'Missing required toolchain environment: pnpm or mise\n' >&2
  return 127
}

run_backend_lint() {
  run_or_echo "backend:lint" run_in_repo_env 'cd backend && uv run ruff check . && uv run mypy .'
}

run_backend_push() {
  run_or_echo "backend:push" run_in_repo_env 'cd backend && uv run ruff check . && uv run mypy . && uv run pytest'
}

run_frontend_lint() {
  run_or_echo "frontend:lint" run_in_repo_env 'cd frontend && pnpm run lint'
}

run_frontend_push() {
  run_or_echo "frontend:push" run_in_repo_env 'cd frontend && pnpm run lint && pnpm test'
}
