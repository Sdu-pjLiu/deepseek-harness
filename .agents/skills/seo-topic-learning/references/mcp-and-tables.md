# MCP 工具与必读表

## 工具怎么选

dbhub 多数据源时工具名是 `{tool}_{source_id}`，DSH 会话里再加前缀 `mcp__<server>__`。
以**当前工具列表**为准。

| 目的 | 工具 |
|---|---|
| 探 schema / 表 / 列 / 索引 | `search_objects*`：`names` → `summary` → 将查询的表 `full` |
| 跑 SQL | `execute_sql*`；只读源只走只读工具 |

## 采集 lane 与表（见 collector-briefs.md）

| Lane | 数据源 | 表 |
|---|---|---|
| pool_schedule | seo_ai 只读 | `seo_sub_topic`、`seo_topic_publish_plan`、`seo_sub_topic_change_log` |
| search_queries | geo_collect_db | zh：`seo_daily_search_baidu`；en：`gsc_query_stats` |
| site_trend | geo_collect_db | zh：`la51_trend_stats`；en：`gsc_daily_trend` |
| page_engagement | geo_collect_db | zh：`la51_entry_stats`、`la51_interview_stats`；en：`gsc_page_stats` |
| geo（可选） | seo_ai | `geo_visibility_*` 三表 |
| autocomplete（可选） | seo_ai | `seo_search_autocomplete_suggestion` |
| competitor（可选） | seo_ai | `seo_competitor_page` |
| delivery（可选） | seo_ai | `seo_writing_prompt_delivery` |

中文不要查 GSC；英文不要查 51.LA。
停读：`la51_directory_stats`；主库 `seo_daily_search`、`seo_daily_trend`。

## 语种路由

| 语种 | 词级 | 站点趋势 | 页面 |
|---|---|---|---|
| zh | `seo_daily_search_baidu` | `la51_trend_stats` | `la51_entry_stats` / `la51_interview_stats` |
| en | `gsc_query_stats` | `gsc_daily_trend` | `gsc_page_stats` |

窗口默认以 `run_date` 为右端点、回溯约 30 天（GEO 约 14 天）。日期列名以探表为准。

## 百度词 / GSC 列语义

| 外部列 | 映射语义 |
|---|---|
| `simple_searchword_title` | query |
| `SUM(pv_count)` | sum_impressions |
| `SUM(visit_count)` | sum_clicks |

百度词默认：`is_promotion = 0 OR IS NULL`。

## 不在 MySQL 的数据

Google News 不在上述表中。无新闻源则 `news_available: false`，不要编造热点。

## 查询纪律

聚合优先；禁止 30 天原词 dump；列名以 `search_objects` 为准；抽样带 LIMIT。

## 关键唯一键（速查，仍须探表）

- `seo_sub_topic`：`(article_language, sub_topic_key)`
- `seo_topic_publish_plan`：`(sub_topic_id, planned_write_date, daily_sequence)`
