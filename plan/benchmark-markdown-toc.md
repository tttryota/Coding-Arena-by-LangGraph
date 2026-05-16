---
profile: backend
scope: benchmark/markdown-toc
spec: docs/spec/benchmark/markdown-toc.md
test_cases: tests/test-cases/benchmark/markdown-toc.md
---

## 今回やること
markdown-toc の全 Phase（Phase 1-3）を一括実装する。
ハーネスのベンチマーク実行として、TDD フロー全体の動作確認とコスト計測を行う。
実装先モジュールは backend/benchmark/markdown_toc.py とする。

## 対象テストケース
1. 空文字列 → headings空リスト、markdown空文字列
2. 見出しなし本文 → headings空リスト、markdown空文字列
3. H1が1つ → text/level/anchor/markdownが正しい
4. H1,H2,H3混在 → 4件のheadingsとインデント階層が正しい
5. バッククォートコードブロック内はスキップ
6. チルダコードブロック内はスキップ、バッククォートとチルダは互いに閉じない
7. 同名見出し3つ → anchor付番 section, section-1, section-2、markdownも対応
8. min_level=2,max_level=3 → H2,H3のみ抽出、インデント正しい
9. **bold**,`code`,[link](url)除去 → text/anchor/markdownが正しい
10. foo_bar_baz → アンダースコア保持、text/anchor正しい
11. ひらがな見出し → anchor保持
12. カタカナ見出し → anchor保持
13. 漢字見出し → anchor保持
14. H2とH4のみ → 相対インデント（深さ差2）が正しい
15. ATX末尾クロージング除去 → text/anchor/markdown正しい
16. 日本語重複見出し → anchor付番 はじめに-1、markdownも対応

## やらないこと
- Setext 形式の見出し対応
- HTML 見出しの認識
- ファイル I/O
- CommonMark バックスラッシュエスケープ
- 全 Unicode カテゴリのスラッグ対応
- インデント付きコードフェンス
- 他モジュールとの連携

## 完了条件
- 上記17個のテストが GREEN
- ruff / mypy がパス
- レビュー完了

## 設計判断
- ベンチマーク用ダミー機能のため、他モジュールへの依存は持たない
- 標準ライブラリのみ使用（外部パッケージ不使用）
- Markdown 装飾除去は正規表現の最短マッチで実装し、完全なパーサーは作らない
