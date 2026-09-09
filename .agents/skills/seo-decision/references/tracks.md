# 三轨说明（seo-decision）

## 主题轨（写库）

- 时态：`cutoff_date` = 昨天及以前。
- 动作：存量 `weight` / `target_total` / `extra.writing_hints`。
- 门禁：Gate → 决策 → **独立审查**（≥0.90）→ 写前 SELECT（含 24h 互斥）→ `full` 才 COMMIT。
- 审计：`source=seo_decision`。

## Prompt 轨（提案，不直接改 Prompt）

- 读 `prompt-surfaces.md`。
- 出 `bundle_plans`（≤2）。
- 无失败样本 / `evidence/`：禁止 `patch_prompt`；允许 `writing_hints_only`、`adjust_scoring_rubric`、`no_change`。
- `writing_hints_only` 并入主题轨 hints。
- 评分知识提案只写 `proposals/pending/`，本轮仍用冻结评分文件。

## 知识进化轨（自进化边界）

- **可提案**：`scoring-decision.md` 软权重/阈值、collector 抽样上限、`decision-rules` 软规则。
- **不可本轮改**：任何 `SKILL.md`、write-invariants 破坏性护栏（done/钉住/互斥小时）、正在使用的评分文件。
- 人审合入后**下一轮**生效。

## 与 seo-topic-learning

| | topic-learning | seo-decision |
|---|---|---|
| 日期 | 今天 `run_date` | 昨天 `cutoff_date` |
| source | `topic_learning` | `seo_decision` |
| 排产/新建 | 可 | 禁止 |
| 互斥 | 写入供对方 24h 跳过 | 读对方 24h 跳过 |
