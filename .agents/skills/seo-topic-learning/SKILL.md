---
name: seo-topic-learning
description: >
  用 DBHub MCP 做主题池自学习：父 Agent 探表后并行派发只读子 Agent 按域采集（池/排产/词表/趋势/页面），
  综合决策调权、补题、越界清题与排产，经 DeepBI 审查后事务写入 seo_ai。
  用户提到主题池、小主题、排产、seo_sub_topic、seo_topic_publish_plan、调权、补题、清题、
  topic_learning，或要用 DeepSeek Harness 替代 topic_learning_scheduled.sh 时必须加载。
---

# 主题自学习与排产

你是运营决策者，不是 SQL 模板执行器。Python 引擎不参与本轮。
表结构以 MCP 探到的为准；分析怎么查、权加多少、补哪条、排谁，由你根据证据决定。
边界数字与 DeepBI 规则在 `references/`，需要时再读。

## 运行模式（mode，由你根据用户意图判断）

| 用户倾向 | mode | 行为 |
|---|---|---|
| 执行日批 / 更新排产 / 写入 / apply | `write` | 检验通过后 **COMMIT** |
| 看看 / 分析 / 预览 / 不要写库 | `dry_run` | 输出决策 + 将执行 SQL，**不 COMMIT** |
| 意图模糊 | `dry_run` | 先输出决策摘要，**询问是否写入**后再 COMMIT |

写前检验、DeepBI 门禁、回读验证在任何模式下都适用。

## 为什么要分「你定」和「references 锁」

写错 weight 可次日改；写错 `published_count`、动 `dispatched` 行、插入 Shopify 题会污染生产。
策略放开，破坏性操作收紧。

## 1. 开始前

1. 确认 MCP 有 **可写** `seo_ai` 与 **只读** `geo_collect_db` 的 `search_objects_*` 和 `execute_sql_*`（以当前工具列表为准）。
2. 确定 `run_date`（默认上海当天）和 `article_language`（`zh` 或 `en`；一轮一种；用户未指定可先 zh 再问 en）。
3. 读 [references/mcp-and-tables.md](references/mcp-and-tables.md) 对齐必读表与语种路由。

## 2. 工作流

```text
探写表结构 → 并行派发采集 lane → 汇 digest → 决策 JSON → DeepBI 审查
→ 写前 SELECT 检验 → [dry_run 停 | 单事务写入] → 回读汇报
```

### 2.1 父 Agent 探写表结构

对将写入的表 `search_objects` full：`seo_sub_topic`、`seo_topic_publish_plan`、`seo_sub_topic_change_log`。
确认唯一键后再写任何 UPDATE/INSERT。

### 2.2 并行派发采集子 Agent（只读）

读 [references/collector-briefs.md](references/collector-briefs.md)。**同一回合**并行启动必派 lane：

| Lane | 域 |
|---|---|
| `pool_schedule` | 主题池 + 排产占槽 + min_gap |
| `search_queries` | 词表（zh 百度 / en GSC） |
| `site_trend` | 站点趋势 |
| `page_engagement` | 页面级信号 |

可选 lane（可先 COUNT 再决定是否派）：`geo`、`autocomplete`、`competitor`、`delivery`。

**子 Agent 纪律**：

- 只读 MCP；禁止写 `seo_ai`。
- prompt 自包含：`run_date`、`article_language`、工具名、lane brief、digest JSON schema。
- 只回结构化 digest，禁止回传 30 天原词表。
- 失败或空数据：`available=false`，父 Agent 继续。

无 `subagent` 工具时：父 Agent 按相同 lane 顺序自己做。

**新闻**不在 MySQL。无搜索/SerpAPI 则汇报「本轮无新闻信号」，不要编造热点。

### 2.3 综合决策

合并各 lane digest 后：

1. 读 [references/deepbi-and-pillars.md](references/deepbi-and-pillars.md)。
2. 补题或判覆盖缺口时读 [references/coverage-taxonomy.md](references/coverage-taxonomy.md)。

自主决定（均可「本轮不做」）：

1. **清题**：越界 → [write-invariants.md](references/write-invariants.md) 归档或硬删。
2. **调权**：在单题日封顶与全池 45–200 内自定幅度；存量 target 只增不减。
3. **补题**：有证据且过 DeepBI 才 INSERT；`notes` 带证据前缀。
4. **排产**：自定优先级与平台；须过配额与 min_gap；remaining>0 才排。

决策 JSON 最小集：

```json
{
  "run_date": "YYYY-MM-DD",
  "article_language": "zh",
  "mode": "write",
  "removals": [
    {"sub_topic_key": "...", "action": "archive|delete", "reason": "deepbi_violation"}
  ],
  "sub_topics": [
    {
      "sub_topic_key": "acos_zh_xxx",
      "pillar": "amazon_ads",
      "sub_topic_title": "...",
      "weight_delta": 6,
      "target_total_delta": 1,
      "news_urgent": false,
      "status": "active",
      "reason_codes": ["zero_click"],
      "notes_prefix": "gsc:"
    }
  ],
  "schedule_intents": [
    {"sub_topic_key": "acos_zh_xxx", "publish_platform": "官网", "priority": "normal"}
  ]
}
```

新建 key：`^[a-z][a-z0-9_]+$`。不要改存量 `pillar`。

### 2.4 DeepBI 审查

对每个新建题与拟继续 active 的越界嫌疑存量题做 pass/fail（见 deepbi-and-pillars）。
可选：派**一个**审查子 Agent，只审 key/title/pillar/notes，回 `rejected_keys`。
未 pass 不得 INSERT 或维持 active。

### 2.5 写前检验

读 [references/write-invariants.md](references/write-invariants.md)。对每条拟写变更用只读 SELECT 核对配额、min_gap、账本余量、唯一键。
失败则跳过并记 `skip_reason`。

### 2.6 写入与回读

`mode=write` 且用户意图允许：`START TRANSACTION;` 本轮所有主题变更 + extra 账本 + change_log + planned `; COMMIT;`（单次 MCP）。
`mode=dry_run`：输出将执行 SQL，不 COMMIT。
写完 SELECT 回读 weight/target/status/extra、窗口 planned、最新 change_log。

## 3. 不变量（违反就停）

- 只写 `seo_ai`；`geo_collect_db` 只读。
- 不改 `published_count`。
- 不删、不改期 `dispatched` / `done` / `abandoned`。
- `split:` / `auto:faq_expand:`  planned 钉住。
- 禁止 DDL / 无 WHERE DELETE。
- planned.notes 前缀：`auto:topic_learning:<run_date>:<lang>`。

配额、账本、清题护栏详见 write-invariants。

## 4. 失败处理

- 事务失败 → ROLLBACK，报告语句与原因。
- 唯一键冲突 → 改下一空 seq 或跳过，不覆盖。
- 同日已有 `dispatched` → 不改 planned，其余可继续。

## 5. 汇报格式

```text
run_date=YYYY-MM-DD lang=zh mode=write|dry_run
采集: pool/search/trend/page=[available|skip]; geo/autocomplete=...
分析: 活跃题 N；remaining 合计；新闻=无|有
决策: 归档 A / 硬删 D / 新建 X / 调权 +up/-down / target +C / 拟排 M
DeepBI: 通过 P / 拒绝 [keys...]
检验: 通过/跳过 [skip_reason...]
执行: COMMIT 成功 | 未写库
验证: 回读一致 | 不一致项
```

## 6. 反例

- 先查业务数据、后探表。
- 把记忆里的列名直接写 SQL。
- 无证据批量补题。
- 把「每题每日 weight +20」当成全池共享额度。
- 子 Agent 写库或回传全量词表。

## 7. References 索引

| 何时读 | 文件 |
|---|---|
| 开始前、派子 Agent | [mcp-and-tables.md](references/mcp-and-tables.md)、[collector-briefs.md](references/collector-briefs.md) |
| 决策、DeepBI、清题 | [deepbi-and-pillars.md](references/deepbi-and-pillars.md) |
| 补题覆盖缺口 | [coverage-taxonomy.md](references/coverage-taxonomy.md) |
| 写前检验、事务、清题护栏 | [write-invariants.md](references/write-invariants.md) |
