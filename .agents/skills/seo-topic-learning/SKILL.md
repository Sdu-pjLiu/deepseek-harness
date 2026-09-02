---
name: seo-topic-learning
description: >
  用 MCP 做主题池自学习与排产：探表、并行只读采集、自主调权/补题/清题/排产，
  对照工作区 manifest 中的品牌与写库配置审查后写入。不执行外部 Python 日批引擎。
  用户提到主题池、小主题、排产、seo_sub_topic、seo_topic_publish_plan、
  调权、补题、清题、topic_learning 时必须加载。
---

# 主题自学习与排产

你是运营决策者，不是 SQL 模板执行器。不执行工作区外的 Python 日批引擎。
表结构以 MCP 探到的为准；分析怎么查、权加多少、补哪条、排谁，由你根据证据决定。
部署配置（表路由、配额、品牌边界）由工作区 manifest 提供（见 [references/workspace-contract.md](references/workspace-contract.md)）；必读缺失则停止。
通用 MCP 与采集纪律见 [mcp-discipline.md](references/mcp-discipline.md)、[collector-lanes.md](references/collector-lanes.md)。

## 运行模式（mode，由你根据用户意图判断）

| 用户倾向 | mode | 行为 |
|---|---|---|
| 执行日批 / 更新排产 / 写入 / apply | `write` | 检验通过后 **COMMIT** |
| 看看 / 分析 / 预览 / 不要写库 | `dry_run` | 输出决策 + 将执行 SQL，**不 COMMIT** |
| 意图模糊 | `dry_run` | 先输出决策摘要，**询问是否写入**后再 COMMIT |

写前检验、品牌审查、回读验证在任何模式下都适用。

## 为什么要分「你定」和「工作区锁」

写错 weight 可次日改；写错 `published_count`、动 `dispatched` 行、插入越界题会污染生产。
策略放开，破坏性操作收紧。

## 1. 开始前

1. 确认 MCP 有可写主题库与只读指标库的 `search_objects_*` 和 `execute_sql_*`（以当前工具列表为准）。
2. 确定 `run_date`（默认上海当天）和 `article_language`（`zh` 或 `en`；一轮一种；用户未指定可先 zh 再问 en）。
3. 读工作区 manifest（默认 `knowledge/README.md`），再读 manifest 列出的全部**必读**文件。
4. 任一必读不可读 → 停止并提示用户配置工作区 manifest，不要用记忆补全。

## 2. 工作流

```text
读 manifest → 探写表结构 → 并行派发采集 lane → 汇 digest → 决策 JSON → 品牌审查
→ 写前 SELECT 检验 → [dry_run 停 | 单事务写入] → 回读汇报
```

### 2.1 父 Agent 探写表结构

对将写入的表 `search_objects` full（表名以工作区 mcp-and-tables 为准，通常含 `seo_sub_topic`、`seo_topic_publish_plan`、`seo_sub_topic_change_log`）。
确认唯一键后再写任何 UPDATE/INSERT。

### 2.2 并行派发采集子 Agent（只读）

读工作区 `collector-briefs.md` 与 [collector-lanes.md](references/collector-lanes.md)。**同一回合**并行启动必派 lane：`pool_schedule`、`search_queries`、`site_trend`、`page_engagement`。

**新闻**若不在 manifest 所列 MySQL 表中，无搜索/SerpAPI 则汇报「本轮无新闻信号」，不要编造热点。

### 2.3 综合决策

合并各 lane digest 后，按 manifest 读取品牌与写库文件（通常含 `topic-boundaries`、`product`；覆盖缺口时含 `coverage-taxonomy`）。
不要读 manifest 标记为禁止的文件（如写稿专用的 injection 规则）。

自主决定（均可「本轮不做」）：

1. **清题**：越界 → 按工作区 write-invariants 归档或硬删。
2. **调权**：按工作区 write-invariants 的单题日封顶与全池边界自定幅度；存量 target 只增不减。
3. **补题**：有证据且过品牌审查才 INSERT；`notes` 带工作区约定的证据前缀。
4. **排产**：自定优先级与平台；须过工作区配额与 min_gap；remaining>0 才排。

决策 JSON 最小集：

```json
{
  "run_date": "YYYY-MM-DD",
  "article_language": "zh",
  "mode": "write",
  "removals": [
    {"sub_topic_key": "...", "action": "archive|delete", "reason": "brand_violation"}
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

`publish_platform` 等枚举以工作区 write-invariants 为准。新建 key：`^[a-z][a-z0-9_]+$`。不要改存量 `pillar`。

### 2.4 品牌审查

对每个新建题与拟继续 active 的越界嫌疑存量题做 pass/fail。规则来自工作区 `topic-boundaries` 与 `product`（路径以 manifest 为准）。

可选：派**一个**审查子 Agent；须自行读取工作区边界文件或在 prompt 中内嵌要点。

审查 JSON 最小集：

```json
{
  "reviews": [
    {
      "sub_topic_key": "example",
      "pass": false,
      "profile": "standard",
      "violations": ["multi_platform"],
      "rationale": "标题含 Shopify"
    }
  ],
  "rejected_keys": ["example"]
}
```

未 pass 不得 INSERT 或维持 active。

### 2.5 写前检验

读工作区 write-invariants。对每条拟写变更用只读 SELECT 核对配额、min_gap、账本余量、唯一键。
失败则跳过并记 `skip_reason`。

### 2.6 写入与回读

`mode=write` 且用户意图允许：按工作区 write-invariants 的单事务约定 COMMIT。
`mode=dry_run`：输出将执行 SQL，不 COMMIT。
写完 SELECT 回读 weight/target/status/extra、窗口 planned、最新 change_log。

## 3. 不变量（违反就停）

- 只写 manifest 指定的可写库；只读库只读。
- 不改 `published_count`（除非工作区 write-invariants 明确允许，默认禁止）。
- 不删、不改期 `dispatched` / `done` / `abandoned`。
- 不破坏 write-invariants 中列出的钉住行前缀。
- 禁止 DDL / 无 WHERE DELETE。

配额、账本、清题护栏、审计字段详见工作区 write-invariants。

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
品牌审查: 通过 P / 拒绝 [keys...]
检验: 通过/跳过 [skip_reason...]
执行: COMMIT 成功 | 未写库
验证: 回读一致 | 不一致项
```

## 6. 反例

- 先查业务数据、后探表。
- 把记忆里的列名直接写 SQL。
- 无证据批量补题。
- 把单题日 weight 上限当成全池共享额度。
- 子 Agent 写库或回传全量词表。
- manifest 必读文件缺失仍用记忆继续写库。
- 去读工作区外的代码仓或配置文件来决定策略。
- 用写稿 injection 规则决定主题是否进池。

## 7. References 索引

| 何时读 | 文件 |
|---|---|
| 开始前 | 工作区 manifest + 其列出的必读文件 |
| 技能内（流程） | [workspace-contract.md](references/workspace-contract.md)、[mcp-discipline.md](references/mcp-discipline.md)、[collector-lanes.md](references/collector-lanes.md) |
