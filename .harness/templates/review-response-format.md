## 回答形式
JSON のみを返してください。JSON の外にテキストを一切含めないでください。
返却形式は次のどちらかのみです。

指摘あり:
{"issues":[{"file":"src/foo.py","line":87,"severity":"major","description":"何が問題か、なぜ問題か、影響、修正方針を簡潔に含める"}]}

指摘なし:
{"issues":[]}
