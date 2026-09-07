**1. 矛盾**

- **F-01 — major** — [checkpoint/SKILL.md:49](/Users/ryotaro/claude-research/.claude/skills/checkpoint/SKILL.md:49)  
  古いコンポーネントを含む注記全体を `stale:` 行に置き換える指示は、46行目の「未解決の注意事項・承認境界を保持する」と衝突します。例えば「figure-reviewer の確認待ち。校正失敗が未解決で提出不可」という注記から、後半が消える可能性があります。  
  **修正案:** 古い名称だけを更新し、未解決事項と承認境界は保持すると明記してください。4行制限よりこれらの保持を優先する規定も必要です。

- **F-02 — minor** — [research-integrity.md:15](/Users/ryotaro/claude-research/.claude/rules/research-integrity.md:15)  
  全ての negative/null 結果を `draft.md` / `main.tex` に報告する旧来の指示が残り、17行目の補足資料への配置許可との関係が曖昧です。本文で概要を報告すれば両立しますが、その読み方が明示されていません。  
  **修正案:** 「研究記録には全結果を保持し、各論文では本文の概要と参照先の補足資料を通じて報告する。主要結果・中心的主張を限定する結果は本文に残す」としてください。

その他、簡潔さと科学的完全性の方針は整合しています。

**2. Integrity**

追加の指摘はありません。[scientific-author.md:90](/Users/ryotaro/claude-research/.claude/agents/scientific-author.md:90) は編集による仮説・endpoint・解析区分・多重性判断の変更を禁止し、revision 指示も正当な限界の削除を禁止しています。

提示された **after は文章構成として新方針に適合しますが、before の単なる短縮ではありません**。新たな R-05 の数値主張が加わるため、その裏付けが必要です。また、H2 が未評価であることや vendor baseline と比較していないことが冒頭の改善主張の解釈を変えるなら、その含意は abstract にも必要です。R-08 と除外経緯は Methods 等に残してください。今回、それらの科学的事実・数値自体は検証していません。

**3. Routing と permissions**

- **F-03 — minor** — [checkpoint/SKILL.md:44](/Users/ryotaro/claude-research/.claude/skills/checkpoint/SKILL.md:44)  
  Research Lead が直接行う checkpoint に「履歴を paper changelog に移す」という選択肢がありますが、[CLAUDE.md:75](/Users/ryotaro/claude-research/CLAUDE.md:75) ではその書き込みは scientific-author 所有です。移動の担当が不明確です。  
  **修正案:** checkpoint は Research Lead 所有の task record に履歴を保存し、既存 changelog は参照する、としてください。changelog 更新が必要なら scientific-author に明示的に回します。

役割表、runner 経由の独立した読み取り専用レビュー、人間の承認条件、再現性・metadata 契約そのものは差分で変更されていません。

**4. Workability**

F-01、F-03 以外に指摘はありません。editorial brief の項目と revision 操作は実行可能な粒度です。既存情報と暫定的な仮定を使えるため、追加の計画文書や承認は必須になっていません。`paper_id` 確認は既存の手順です。

**5. Tests**

- **F-04 — minor** — [test_repository_contract.py:146](/Users/ryotaro/claude-research/tests/test_repository_contract.py:146)  
  長い完全一致文と156行目の `consolidation, or relocation` は、改行や句読点に依存します。メモリ内の検証で、意味を変えない改行だけで失敗し、逆に scientific-author の事後変更禁止文を削除しても成功しました。したがって、これは存在確認であり、変更後の振る舞いの検証にはなっていません。  
  **修正案:** 空白を正規化し、操作名は個別に確認してください。テストの対象を構造・マーカーの存在に限定し、意味と読みやすさは before/after と今回のレビューで評価する位置づけを明確にしてください。

検証は契約テスト **9件成功**、Ruff・mypy・Python のメモリ内構文検査・シェル構文検査が成功しました。読み取り専用を維持するため、ファイル生成を伴う全 pytest と通常の compileall は実行していません。ファイル変更はありません。

**Overall verdict: revise**