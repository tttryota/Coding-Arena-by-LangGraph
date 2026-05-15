---
profile: backend
benchmark: generation
scope: benchmark/markdown-toc
spec: docs/spec/benchmark/markdown-toc.md
test_cases: tests/test-cases/benchmark/markdown-toc.md
---

## 今回やること
markdown-toc を generation benchmark として実行する。
開始時点で ALREADY_GREEN なら失格とし、既存実装の review-only benchmark と混在させない。

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
17. 未閉鎖コードフェンス → 開始行以降の見出しはすべて無視
18. min_level > max_level → headings空リスト、markdown空文字列
19. 先頭スペース付き見出し → 見出しとして認識しない
20. `#` 7個以上の行 → 見出しとして認識しない
21. 空 slug 見出し `## !!!` → anchor空文字列、markdownは `- [!!!](#)`
22. URL内に `)` を含むリンク → 最初の `)` でリンク終了した既知制限どおりに text/anchor が決まる
23. 仕様書の具体例全体 → headings/markdown が spec 記載どおり

## やらないこと
- 既存実装あり benchmark の品質比較

## 完了条件
- generation benchmark が RED スタート前提でのみ実行される
- ALREADY_GREEN の場合は失格として終了する
