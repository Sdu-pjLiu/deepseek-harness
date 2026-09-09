# MCP 通用纪律

具体库名、表名、语种路由见工作区 manifest 中的 `mcp-and-tables.md`（或等价文件）。

## 工具选择

- 多数据源时工具名可能是 `{tool}_{source_id}`，会话里再加 MCP 前缀；以**当前工具列表**为准。
- 探 schema / 表 / 列 / 索引：用 `search_objects*`（`names` → `summary` → 将查询的表 `full`）。
- 跑 SQL：用 `execute_sql*`；只读数据源只走只读工具。

## 探表先于业务 SQL

对将写入或依赖结构的表，先 `search_objects` full，确认列名与唯一键后再写任何 SELECT/INSERT/UPDATE。

## 读写边界

- 只读源：禁止 INSERT/UPDATE/DELETE。
- 可写源：本轮决策变更（存量调权 + hints + 审计）尽量包在**单次** `START TRANSACTION; … ; COMMIT;` 中（细则见工作区 write-invariants 决策专段）。
- 本技能**禁止**写 `seo_topic_publish_plan`；禁止 INSERT 新 `seo_sub_topic`。

## 查询纪律

- 聚合优先；禁止 30 天原词 dump。
- 列名以探表结果为准，不用记忆中的列名。
- 抽样带 LIMIT；子 Agent 只回 digest，不回传全量词表。
- pack 进决策上下文约 40KB 预算；超限丢字段并记录，禁止盲截半条 JSON。

## 不在库内的数据

新闻、validator jsonl、submit 反馈若不在 manifest / `evidence/` 中，标不可用，不要编造。
