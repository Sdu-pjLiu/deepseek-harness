# 采集 lane 与子 Agent 任务模板

父 Agent 派发子 Agent 时，将对应 lane 的 brief 整段复制进 prompt，并填入 `run_date`、`article_language`、实际 MCP 工具名。
子 Agent **只读**；禁止写 `seo_ai`。只返回 digest JSON，禁止回传大段原表。

## 统一 digest 外壳

每个 lane 返回：

```json
{
  "lane": "pool_schedule",
  "run_date": "YYYY-MM-DD",
  "article_language": "zh",
  "available": true,
  "reason": null,
  "summary": {},
  "signals": [],
  "errors": []
}
```

- `available=false` 时 `reason` 必填（如 `no_rows`、`query_failed`），`signals` 可为空。
- `signals` 每条建议 ≤ 30 条；单条字段尽量短。

---

## Lane: pool_schedule（必派）

**表**：`seo_ai.seo_sub_topic`、`seo_topic_publish_plan`、近日 `seo_sub_topic_change_log`（只读）

**任务**：

1. `search_objects` 探上述表列与唯一键。
2. 读 `status=active` 主题池：id、pillar、key、title、weight、target_total、published_count、notes、status。
3. 算 remaining、同语种 weight 的 p10/p50/p75/p90（用于后续钳制参考）。
4. 读排产窗口 `[run_date, run_date+1]` 内 planned/dispatched/done：按日占槽、按平台占槽、按 pillar 占槽。
5. 每题 min_gap：窗口外最近 planned/dispatched/done 的 `planned_write_date`。
6. 列出 notes 以 `split:` 或 `auto:faq_expand:` 开头的钉住行（只报告，不修改）。

**summary 建议字段**：`active_count`、`remaining_total_sum`、`weight_percentiles`、`slot_occupancy_by_day`、`platform_occupancy_by_day`、`pinned_plan_count`

---

## Lane: search_queries（必派）

**表**（按语种）：

- zh：`geo_collect_db.seo_daily_search_baidu`
- en：`geo_collect_db.gsc_query_stats`

**窗口**：run_date 起回溯约 30 天。

**任务**：

1. 探表后聚合，不要导出全量 query 行。
2. zh：排除 `is_promotion=1`；映射 query≈`simple_searchword_title`，展现≈`pv_count`，点击≈`visit_count`。
3. 产出信号类型示例：`zero_click`（有展现无/低点击）、`high_impressions_low_ctr`、词质量（zh 可含 bounce/dwell）。
4. 每条 signal：`signal_type`、`query_or_label`、`pillar_hint`（若能从 query 推断）、`metrics`（聚合数字）、`suggested_topic_keys`（与池标题子串匹配到的 key，可为空）。

**上限**：signals ≤ 30。

---

## Lane: site_trend（必派）

**表**：

- zh：`geo_collect_db.la51_trend_stats`
- en：`geo_collect_db.gsc_daily_trend`

**任务**：窗口内站点/session 趋势；en 可算 WoW delta。无数据则 `available=false`。

**summary**：`sum_sessions` 或等价、`wow_delta_pct`、`site_bounce_rate`（若有）

---

## Lane: page_engagement（必派）

**表**：

- zh：`la51_entry_stats`、`la51_interview_stats`
- en：`gsc_page_stats`

**任务**：聚合 Top 页面问题（高跳出、低深度、高展现低 CTR 等），每条带 `path_or_page`、`signal_type`、`metrics`。

**上限**：signals ≤ 20。

---

## Lane: geo（可选）

**表**：`geo_visibility_data`、`geo_visibility_question`、`geo_visibility_question_pool`

**窗口**：约 14 天。先 COUNT；0 则 `available=false`。

**summary**：按 pillar 的 `visibility_rate`、`probe_count`；零可见 pillar 列表。

---

## Lane: autocomplete（可选）

**表**：`seo_search_autocomplete_suggestion`

**窗口**：约 7 天。先 COUNT。

**signals**：未覆盖池的高价值联想词（≤ 20），带 `suggestion_text`、`engine`、`pillar_hint`。

---

## Lane: competitor（可选）

**表**：`seo_competitor_page`

**summary**：pillar gap 摘要（gap_ratio、gap_score 高的 pillar）。

---

## Lane: delivery（可选）

**表**：`seo_writing_prompt_delivery`

**summary**：官网系列/回收相关：哪些 sub_topic 交付已全部 submitted、可回收候选（只读报告）。

---

## 父 Agent 汇总后

合并各 lane digest → 形成「分析摘要」→ 决策 JSON（见 SKILL.md）。
若某 lane 子 Agent 失败，父 Agent 可自己跑该 lane 或标记不可用后继续。

## DeepBI 审查子 Agent（可选，决策后）

**输入**：拟新建 `sub_topics` + 拟继续 active 的越界嫌疑存量题（key、title、pillar、notes）。

**输出**：见 [deepbi-and-pillars.md](deepbi-and-pillars.md) 审查 JSON。

**禁止**：写库、改 weight。
