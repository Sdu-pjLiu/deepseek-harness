---
name: seo-topic-learning
description: >
  用 MCP 做主题池自学习与排产：探表、并行只读采集、自主调权/补题/清题/排产，
  对照工作区 manifest 中的品牌、写库与评分配置审查后写入。不执行外部 Python 日批引擎。
  用户提到主题池、小主题、排产、seo_sub_topic、seo_topic_publish_plan、
  调权、补题、清题、topic_learning 时必须加载。
---

# 主题自学习与排产

你是运营决策者，不是 SQL 模板执行器。不执行工作区外的 Python 日批引擎。
表结构以 MCP 探到的为准；分析怎么查、权加多少、补哪条、排谁，由你根据证据决定。
部署配置（表路由、配额、品牌边界、评分标准）由工作区 manifest 提供（见 [references/workspace-contract.md](references/workspace-contract.md)）；必读缺失则停止。
通用 MCP 与采集纪律见 [mcp-discipline.md](references/mcp-discipline.md)、[collector-lanes.md](references/collector-lanes.md)。

## 运行模式（mode，由你根据用户意图判断）

| 用户倾向 | mode | 行为 |
|---|---|---|
| 执行日批 / 更新排产 / 写入 / apply | `write` | 评分 `pass=true` 且写前检验通过后 **COMMIT** |
| 看看 / 分析 / 预览 / 不要写库 | `dry_run` | 输出决策 + 评分 + 将执行 SQL，**不 COMMIT** |
| 意图模糊 | `dry_run` | 先输出决策与评分摘要，**询问是否写入**后再 COMMIT |

写前检验、品牌审查、配额对账、评分门禁、回读验证在任何模式下都适用。

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
→ 配额对账循环（SELECT ≥run_date → 调日期/精简/延伸 → 再 SELECT，最多 3 轮）
→ 评分门禁（manifest 评分文件）→ 写前 SELECT 检验
→ [pass 且 write → 单事务 COMMIT | 否则不写库] → 回读再对账 → 汇报
```

### 2.1 父 Agent 探写表结构

对将写入的表 `search_objects` full（表名以工作区 mcp-and-tables 为准，通常含 `seo_sub_topic`、`seo_topic_publish_plan`、`seo_sub_topic_change_log`）。
确认唯一键后再写任何 UPDATE/INSERT。

### 2.2 并行派发采集子 Agent（只读）

读工作区 `collector-briefs.md` 与 [collector-lanes.md](references/collector-lanes.md)。**同一回合**并行启动必派 lane：`pool_schedule`、`search_queries`、`site_trend`、`page_engagement`。

对可选 lane：**先 COUNT 再决定是否派**。`video_signal`：工作区 brief 有定义且对应语种主源 COUNT>0 才派；失败或空数据则 `available=false`，父 Agent 继续。视频信号只影响补题候选、weight/target（受工作区规则）、`schedule_intents.priority`；**不**把 `news_urgent` 扩到视频；**不**在 intents 里写死日期窗口；**不**因视频写 `extra.writing_hints`。视频相关 `notes_prefix` / `reason_codes` 以工作区 `collector-briefs.md` 该 lane 父 Agent 段为准。

**新闻**若不在 manifest 所列 MySQL 表中，无搜索/SerpAPI 则汇报「本轮无新闻信号」，不要编造热点。

### 2.3 综合决策

合并各 lane digest 后，按 manifest 读取品牌与写库文件（通常含 `topic-boundaries`、`product`；覆盖缺口时含 `coverage-taxonomy`）。
不要读 manifest 标记为禁止的文件（如写稿专用的 injection 规则）。

自主决定（均可「本轮不做」）：

1. **清题**：越界 → 按工作区 write-invariants 归档或硬删。
2. **调权**：按工作区 write-invariants 的单题日封顶与全池边界自定幅度；存量 target 只增不减。
3. **补题**：有证据且过品牌审查才 INSERT；`notes` 带工作区约定的证据前缀。
4. **排产**：优先输出 `schedule_intents`（key + platform + priority）；**具体撰写日由配额对账循环分配**，不要在 intents 里拍死固定短窗口。须过配额与 min_gap；remaining>0 才排。钉住行、官网禁删重建、done/dispatched 不可动等以 write-invariants 为准。

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
  ],
  "quota_ledger": {
    "horizon_days_used": 0,
    "days": [
      {
        "date": "YYYY-MM-DD",
        "quota_lang": 0,
        "quota_official": 0,
        "quota_third_party": 0,
        "occupied_lang": 0,
        "occupied_official": 0,
        "occupied_third_party": 0,
        "frozen": 0,
        "movable": 0,
        "delta": 0
      }
    ],
    "adjustments": [],
    "shortfall_reason": null
  }
}
```

`quota_ledger` 中的配额数字从工作区 write-invariants 读取填入（示例用 `0` 占位）；`delta = occupied - quota`。
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

### 2.5 配额对账

品牌审查之后、评分之前。读 write-invariants 的日配额与可动/冻结规则。

1. 只读 SELECT：`article_language=本轮` 且 `planned_write_date >= run_date`，状态 ∈ planned/dispatched/done；区分 frozen vs movable。
2. 按日、平台、pillar 汇总，写入 `quota_ledger`（`delta = occupied - quota`）。
3. 若存在非合法空日的 `delta ≠ 0`：调整（最多 3 轮）后再次 SELECT。
   - 超配：可动行改到最近欠配日；无欠配日则改到「当前最后一天 + 1」（向后延伸，**不设天数上限**）；仍超则取消多余 movable。
   - 欠配：有合格题则补槽；否则向后按日延伸；新的每一天仍须恰好满额。
   - 合法空日：无 remaining>0 且过 min_gap 的题 → `shortfall_reason=no_eligible_topic`，不硬凑补题。
4. 全部 `delta=0`（或仅合法空日）才能进入评分。未产出 `quota_ledger` → 评分 `gates_pass=false`（见评分文件 `QUOTA` / `QUOTA_UNDERFILL`）。

zh 官网可动行只 UPDATE 日期，禁止 DELETE 重建。不动 dispatched/done/钉住行。

### 2.6 评分门禁

读 manifest 列出的**评分**文件（标准、权重、及格线、门闩列表均以该文件为准；技能不硬编码分数）。

顺序：

1. **硬门闩**（对照评分文件 + write-invariants + 品牌审查 + `quota_ledger`）→ `gates_pass`
2. 仅当 `gates_pass=true` 时做**战略软评分** → `score` 与 `dimensions`
3. 整体 `pass` = 评分文件规定的通过条件（通常含 `gates_pass` 与分数门槛）

评分 JSON 最小集：

```json
{
  "gates_pass": true,
  "score": 0.0,
  "pass": true,
  "dimensions": [
    {"id": "goal_align", "score": 0.0, "notes": "..."}
  ],
  "issues": [
    {"code": "PRIORITY_MISORDER", "severity": "warning", "message": "..."}
  ],
  "gate_codes": [],
  "revision_hints": "",
  "blockers": []
}
```

- `gates_pass=false` 或 `pass=false` → **禁止 COMMIT**（dry_run 可输出决策，须标明 blocked）
- `pass=false` 时 `revision_hints` 必须非空
- 不得用记忆补全评分标准；评分文件缺失 → 停止

### 2.7 写前检验

读工作区 write-invariants。对每条拟写变更用只读 SELECT 核对配额、min_gap、账本余量、唯一键、钉住与终态行。
失败则跳过并记 `skip_reason`。

### 2.8 写入与回读

仅当评分 `pass=true`，且 `mode=write`、用户意图允许：按工作区 write-invariants 的单事务约定 COMMIT。
`mode=dry_run` 或评分未过：输出将执行 SQL，不 COMMIT。
写完 SELECT 回读 weight/target/status/extra、`planned_write_date >= run_date` 的 planned、最新 change_log。
**回读后再对账一次**：非合法空日仍 `delta≠0` → 报告失败，禁止假装成功（write 已 COMMIT 则说明不一致项并建议下一轮纠正）。

**审计强制**：`seo_sub_topic_change_log.source` 必须为 `topic_learning`；
`source_ref` 必须为 `topic_learning:<run_date>:<lang>`。禁止写成 `seo_decision`（复盘由并列技能 `seo-decision` 负责）。

## 3. 不变量（违反就停）

- 只写 manifest 指定的可写库；只读库只读。
- 不改 `published_count`（除非工作区 write-invariants 明确允许，默认禁止）。
- 不删、不改期 `dispatched` / `done` / `abandoned`。
- 不破坏 write-invariants 中列出的钉住行前缀与官网禁删规则。
- 禁止 DDL / 无 WHERE DELETE。
- 评分未通过不得 COMMIT。
- **未完成配额对账**（无 `quota_ledger`）或回读后非合法空日仍 `delta≠0` → 禁止 COMMIT / 不得报成功。
- **本任务不执行 `seo-decision`**（昨日复盘 / Prompt 提案）；同日不要对同一 key 与复盘技能同时 `write`。

配额、账本、清题护栏、审计字段详见工作区 write-invariants。


## 4. 失败处理

- 事务失败 → ROLLBACK，报告语句与原因。
- 唯一键冲突 → 改下一空 seq 或跳过，不覆盖。
- 同日已有 `dispatched` → 不改 planned，其余可继续。

## 5. 汇报格式

```text
run_date=YYYY-MM-DD lang=zh mode=write|dry_run
采集: pool/search/trend/page=[available|skip]; geo/autocomplete/video=...
分析: 活跃题 N；remaining 合计；新闻=无|有
决策: 归档 A / 硬删 D / 新建 X / 调权 +up/-down / target +C / 拟排 M
品牌审查: 通过 P / 拒绝 [keys...]
对账: span=N日 满额|短欠|调整条数；horizon_days_used=N；shortfall=...
评分: pass=.. score=.. gates_pass=.. gate_codes=[..] issues=[..]
检验: 通过/跳过 [skip_reason...]
执行: COMMIT 成功 | 未写库（含评分未过）
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
- 未做评分门禁、或 `pass=false` / `gates_pass=false` 仍 COMMIT。
- 执行工作区禁止的外部 Python 主题日批。
- 删除 split/faq 钉住行，或 DELETE 重建官网在途 planned。
- change_log 写成 `source=seo_decision`，或在本任务中执行复盘技能流程。
- 只防超配额、不防欠配额；或只读近 2 天占用就停而不对账整段 `>= run_date`。
- 把超配堆在同一天，或未做 `quota_ledger` 就评分/COMMIT。

## 7. References 索引


| 何时读 | 文件 |
|---|---|
| 开始前 | 工作区 manifest + 其列出的必读文件 |
| 技能内（流程） | [workspace-contract.md](references/workspace-contract.md)、[mcp-discipline.md](references/mcp-discipline.md)、[collector-lanes.md](references/collector-lanes.md) |
