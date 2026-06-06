#!/bin/bash
# tdd-green-gate.sh
# テストがパスしない限り次の実装ファイルへの移動をブロック
#
# PreToolUse (Write|Edit) フック
# 別の実装ファイルに切り替わる際、前のファイルのテストを実行し、
# パスしていなければブロックする

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')

# ファイルパスが空の場合はスキップ
[[ -z "$FILE_PATH" ]] && exit 0

# TDD_GREEN_GATE_ENABLED=0 で無効化可能
[[ "${TDD_GREEN_GATE_ENABLED:-1}" == "0" ]] && exit 0

# --- 対象判定 ---

# テスト関連ファイルはスキップ (テストを書く行為は常に許可)
[[ "$FILE_PATH" == *.test.ts ]] && exit 0
[[ "$FILE_PATH" == *.test.tsx ]] && exit 0
[[ "$FILE_PATH" == *.spec.ts ]] && exit 0
[[ "$FILE_PATH" == *.spec.tsx ]] && exit 0
[[ "$FILE_PATH" == *__tests__/* ]] && exit 0
[[ "$FILE_PATH" == *__mocks__/* ]] && exit 0

# TS/TSX 以外はスキップ
[[ "$FILE_PATH" != *.ts ]] && [[ "$FILE_PATH" != *.tsx ]] && exit 0

# 型定義・設定ファイルはスキップ
[[ "$FILE_PATH" == *.d.ts ]] && exit 0
[[ "$FILE_PATH" == *.config.* ]] && exit 0

# 特定ファイル名はスキップ
BASENAME=$(basename "$FILE_PATH")
case "$BASENAME" in
  index.ts|index.tsx) exit 0 ;;
  layout.tsx|page.tsx|loading.tsx|error.tsx|not-found.tsx|template.tsx|default.tsx) exit 0 ;;
  types.ts|types.tsx|constants.ts) exit 0 ;;
  *.stories.tsx|*.stories.ts) exit 0 ;;
esac

# 特定ディレクトリはスキップ
[[ "$FILE_PATH" == */types/* ]] && exit 0
[[ "$FILE_PATH" == */constants/* ]] && exit 0
[[ "$FILE_PATH" == */mocks/* ]] && exit 0
[[ "$FILE_PATH" == */generated/* ]] && exit 0
# providers/ はビジネスロジックを持つ場合があるためスキップしない

# --- 状態管理 ---

# セッション ID をファイル名に安全な文字列へサニタイズ
SANITIZED_ID=$(echo "$SESSION_ID" | tr -c 'A-Za-z0-9._-' '_')

# セッション固有の状態ファイル (SESSION_ID が空の場合は PID でフォールバック)
if [[ -z "$SANITIZED_ID" ]]; then
  STATE_FILE="/tmp/claude-tdd-state-$$"
else
  STATE_FILE="/tmp/claude-tdd-state-${SANITIZED_ID}"
fi

# 状態ファイルが存在しない場合は初期化
if [[ ! -f "$STATE_FILE" ]]; then
  echo "$FILE_PATH" > "$STATE_FILE"
  exit 0
fi

LAST_FILE=$(cat "$STATE_FILE")

# 同じファイルを編集中 → 許可
[[ "$LAST_FILE" == "$FILE_PATH" ]] && exit 0

# 前のファイルが削除されている場合 → テスト実行不可のため警告して許可
if [[ ! -f "$LAST_FILE" ]]; then
  echo "  [tdd-green-gate] 前のファイルが削除されています: $LAST_FILE" >&2
  echo "  テストの実行を確認できませんでした。" >&2
  echo "$FILE_PATH" > "$STATE_FILE"
  exit 0
fi

# --- 前のファイルのテストファイル探索 ---

find_test_file() {
  local src_file="$1"
  local ext="${src_file##*.}"
  local dir
  dir=$(dirname "$src_file")
  local name
  name=$(basename "$src_file" ".$ext")

  local candidates=(
    "${dir}/${name}.test.ts"
    "${dir}/${name}.test.tsx"
    "${dir}/${name}.spec.ts"
    "${dir}/${name}.spec.tsx"
    "${dir}/__tests__/${name}.test.ts"
    "${dir}/__tests__/${name}.test.tsx"
    "${dir}/__tests__/${name}.spec.ts"
    "${dir}/__tests__/${name}.spec.tsx"
  )

  # apps/dashboard: src/ → __tests__/
  if [[ "$src_file" == */apps/dashboard/src/* ]]; then
    local rel="${src_file#*apps/dashboard/src/}"
    local root
    root=$(echo "$src_file" | sed 's|/src/.*||')
    local rel_dir
    rel_dir=$(dirname "$rel")
    candidates+=("${root}/__tests__/${rel_dir}/${name}.test.ts")
    candidates+=("${root}/__tests__/${rel_dir}/${name}.test.tsx")
    candidates+=("${root}/__tests__/${rel_dir}/${name}.spec.ts")
    candidates+=("${root}/__tests__/${rel_dir}/${name}.spec.tsx")
  fi

  # apps/api: src/foo → src/__tests__/foo
  if [[ "$src_file" == */apps/api/src/* ]] && [[ "$src_file" != */apps/api/src/__tests__/* ]]; then
    local rel="${src_file#*apps/api/src/}"
    local root
    root=$(echo "$src_file" | sed 's|/src/.*||')
    local rel_dir
    rel_dir=$(dirname "$rel")
    candidates+=("${root}/src/__tests__/${rel_dir}/${name}.test.ts")
    candidates+=("${root}/src/__tests__/${rel_dir}/${name}.spec.ts")
  fi

  # apps/lambda-authorizer: src/foo → src/__tests__/foo
  if [[ "$src_file" == */apps/lambda-authorizer/src/* ]] && [[ "$src_file" != */apps/lambda-authorizer/src/__tests__/* ]]; then
    local rel="${src_file#*apps/lambda-authorizer/src/}"
    local root
    root=$(echo "$src_file" | sed 's|/src/.*||')
    local rel_dir
    rel_dir=$(dirname "$rel")
    candidates+=("${root}/src/__tests__/${rel_dir}/${name}.test.ts")
    candidates+=("${root}/src/__tests__/${rel_dir}/${name}.spec.ts")
  fi

  for c in "${candidates[@]}"; do
    if [[ -f "$c" ]]; then
      echo "$c"
      return 0
    fi
  done

  return 1
}

# パッケージルート検索 (package.json のあるディレクトリ)
find_package_root() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "${dir}/package.json" ]]; then
      echo "$dir"
      return 0
    fi
    dir=$(dirname "$dir")
  done
  return 1
}

# 前のファイルのテストファイルを探す
TEST_FILE=$(find_test_file "$LAST_FILE" 2>/dev/null || true)

# テストファイルが見つからない → tdd-test-first.sh が対処するので、ここではスキップ
if [[ -z "$TEST_FILE" ]]; then
  echo "$FILE_PATH" > "$STATE_FILE"
  exit 0
fi

# パッケージルートを特定
PKG_ROOT=$(find_package_root "$(dirname "$TEST_FILE")" 2>/dev/null || true)

if [[ -z "$PKG_ROOT" ]]; then
  echo "$FILE_PATH" > "$STATE_FILE"
  exit 0
fi

# --- テスト実行 ---

TEST_REL_PATH="${TEST_FILE#${PKG_ROOT}/}"

# パッケージの test スクリプトを実行 (vitest/jest 差分を吸収)
TEST_OUTPUT=$(cd "$PKG_ROOT" && mise exec -- pnpm -s test -- "$TEST_REL_PATH" 2>&1) || TEST_EXIT=$?
TEST_EXIT=${TEST_EXIT:-0}

if [[ "$TEST_EXIT" -eq 0 ]]; then
  # テスト成功 → 状態更新して許可
  echo "$FILE_PATH" > "$STATE_FILE"
  exit 0
fi

# --- テスト失敗 → ブロック ---
{
  echo "TDD違反: 前の実装のテストがパスしていません"
  echo ""
  echo "  前の実装ファイル: $LAST_FILE"
  echo "  テストファイル:   $TEST_FILE"
  echo ""
  echo "  次のファイル ($FILE_PATH) に進む前に、"
  echo "  テストがパスするよう実装を完了してください。"
  echo ""
  echo "--- テスト実行結果 ---"
  echo "$TEST_OUTPUT" | tail -20
} >&2

exit 2
