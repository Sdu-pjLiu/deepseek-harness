---
name: seo-decision
description: >
  用 MCP 做昨日 SEO 复盘决策：探表、并行只读采集、拼 pack、存量调权与 writing_hints，
  独立审查后可写库；Prompt/评分进化只写工作区 pending 提案。不执行外部 Python 复盘引擎，
  不改排产、不新建题、不改 SKILL。用户提到 seo_decision、复盘、调权纠错、writing_hints、
  Prompt 优化提案、昨日决策时必须加载。
---

# SEO 复盘决策

你是**昨日复盘**决策者，不是主题日批排产器，也不是 SQL 模板执行器。
不执行工作区外的 Python 复盘引擎。表结构以 MCP 探到的为准。
部署配置由工作区 manifest 提供（见 [references/workspace-contract.md](references/workspace-contract.md)）；必读缺失则停止。
MCP 纪律见 [mcp-discipline.md](references/mcp-discipline.md)；轨说明见 [tracks.md](references/tracks.md)。

与并列技能 `seo-topic-learning` 分工：对方管**今日**扩池/排产（`source=topic_learning`）；本技能管**昨日**存量纠错（`source=seo_decision`）。

## 运行模式（mode）

| 用户倾向 | mode | 行为 |
|---|---|---|
| 写入 / apply / full / 落库 | `full` | 独立审查 `pass=true` 后 **COMMIT** 主题轨；Prompt 轨只写 `proposals/pending/` |
| 看看 / 分析 / 预览 / diagnose / 不要写库 | `diagnose` | 输出决策 + 审查 + 将执行 SQL，**不 COMMIT** |
| 意图模糊 | `diagnose` | 先输出摘要，**询问是否 full** 后再写库 |

写前检验、独立审查、门禁在任何模式下都适用。

## 为什么要分「你定」和「工作区锁」

写错 weight 可次日改；写错排产、新建越界题、改 `published_count`、或改自己的 SKILL 会污染生产与闸门。
策略放开，破坏性操作收紧；自进化只走 pending 提案，不本轮自批。

## 1. 开始前

1. 确认 MCP 有可写主题库与只读指标库的 `search_objects_*` 和 `execute_sql_*`。
2. 确定 `cutoff_date`（默认上海**昨天**）和 `article_language`（`zh` 或 `en`；一轮一种）。
3. 读工作区 manifest，再读**共用**与 **seo-decision** 专段全部必读文件（含 `decision-rules.md`、`scoring-decision.md`）。
4. Prompt 轨额外读 `prompt-surfaces.md`；可选 `writing-injection.md`。
5. 任一必读不可读 → 停止。不要读主题技能专属的 `scoring-rubric.md` 来做复盘写库判定。

## 2. 工作流

```text
读 manifest → 探表结构 → 并行采集 lane → 拼 pack_topic / pack_outcome
→ Gate → 主题决策 JSON → 独立审查子 Agent（scoring-decision）
→ [pass 且 full → 单事务 COMMIT | 否则不写库]
→ Prompt 轨策略（writing_hints_only 并入主题 hints；评分提案写 pending）
→ 回读汇报
```

### 2.1 探表

对将依赖的表 `search_objects` full（通常 `seo_sub_topic`、`seo_sub_topic_change_log`；可探 `seo_topic_publish_plan` 但**本技能不得写它**）。
确认唯一键后再写任何 SELECT/UPDATE。

### 2.2 并行采集（只读）

读工作区 `collector-briefs.md`。**同一回合**并行必派：`pool_schedule`、`search_queries`、`site_trend`、`page_engagement`。
可选：`geo`、`competitor`、`delivery`（复盘优先；autocomplete 非必须）。
**不派 `video_signal`**（视频证据仅主题日批消费；本技能不补题、不改排产）。

子 Agent 只回 digest；父 Agent 压缩为 `pack_topic`（约 40KB 预算，见 collector-briefs / decision-rules）。
按 `decision-rules.md` 打 `outcome_topics`（P1–P7）；禁止自造现象 ID。
禁止把今日排产占槽当作调权主证据。

### 2.3 Gate（程序门禁，零「凭感觉」）

主题轨 Gate 不通过则 `should_act=false`，可输出分析但不进入写库：

| 条件 | 处理 |
|---|---|
| `pool_summary.topic_count == 0` | skip |
| 词表/趋势/页面/GEO/竞争/outcome **全无**可用信号 | skip |
| `full` 且距上次同语种 `seo_decision` full &lt; 7 天 | skip 写库（diagnose 仍可分析） |

### 2.4 主题轨决策 JSON

规则与白名单以工作区 `decision-rules.md` 为准。最小集：

```json
{
  "cutoff_date": "YYYY-MM-DD",
  "article_language": "zh",
  "mode": "diagnose",
  "should_act": true,
  "confidence": 0.82,
  "adjustments": [
    {
      "sub_topic_key": "existing_key_only",
      "weight_delta": 5,
      "target_total_delta": 0,
      "reason_codes": ["zero_click_opportunity"],
      "evidence_refs": ["gsc.zero_click_top10[0]"]
    }
  ],
  "writing_hints": [
    {
      "sub_topic_key": "existing_key_only",
      "strategy_tags": ["competitor_layout_gap"],
      "competitor_gap_note": "...",
      "evidence_refs": ["competition_recommendations[0]"]
    }
  ],
  "skipped_mutex_keys": [],
  "no_change_reason": ""
}
```

禁止：新建 key、改 pillar/title、任何排产字段、无 evidence_refs 的调权。
未知 key → 记 skip，**不得** pillar 猜题后写库。

### 2.5 独立审查（必须另起）

派**一个**审查子 Agent（或独立回合），读 `scoring-decision.md`。
输入：决策 JSON + 每条 candidate 的 `evidence_slice`（合计 ≤8192 字符）。
禁止决策者自评后直接 COMMIT。

过线：`gates_pass=true` **且** `score >= 0.90` 且无 error 级 issue（见评分文件）。
`pass=false` 时 `revision_hints` 必填；最多按 revision 修正决策 **3** 轮，仍不过则 skip 写库。

审查 JSON 最小集：

```json
{
  "gates_pass": true,
  "score": 0.92,
  "pass": true,
  "dimensions": [
    {"id": "GAP_JUSTIFICATION", "score": 0.32, "notes": "..."}
  ],
  "issues": [],
  "gate_codes": [],
  "revision_hints": "",
  "blockers": []
}
```

### 2.6 写前检验（full）

读 `write-invariants.md` 决策专段。对每条拟写 key：

1. SELECT 确认 key 存在于本语种池。
2. SELECT 近 24h `change_log`：`source=topic_learning` 且 weight/target → 加入 `skipped_mutex_keys`，不写该 key。
3. delta 在 cap 内；不改 pillar / published_count。
4. `full` 间隔 7 天已通过 Gate。

### 2.7 写入与回读（仅 full 且 pass）

单次事务：`START TRANSACTION;` 存量 UPDATE weight/target + 合并 `extra.writing_hints`（保留 `topic_learning_idempotency`）+ INSERT `change_log`（`source=seo_decision`，`source_ref=seo_decision:<cutoff>:<lang>`）`; COMMIT;`

失败 `ROLLBACK`。diagnose 或未过审：只输出将执行 SQL，不 COMMIT。
写完 SELECT 回读 weight/target/extra/最新 change_log。确认排产表与 `published_count` 无本轮变更。

### 2.8 Prompt 轨（策略 + 知识进化）

在主题决策之后执行（可与写库同轮，但提案落盘独立于业务事务）。读 `prompt-surfaces.md`。

输出策略 JSON（`bundle_plans`，`max_plans≤2`）。`change_intent`：

| intent | 行为 |
|---|---|
| `writing_hints_only` | 并入主题轨 `writing_hints`，不单开提案文件 |
| `adjust_scoring_rubric` | 写入 `proposals/pending/{cutoff}_{lang}_scoring.json`；**不改**现行评分文件 |
| `patch_prompt` | **仅当**工作区存在失败样本或 `evidence/` 摘要；否则 Gate 掉（`NO_PROMPT_EVIDENCE`） |
| `no_change` | 记录 blockers |

同 bundle / 同 knowledge 目标 7 天内已有 pending → skip。
提案不得指向 `.agents/skills/**` 或任何 `SKILL.md`。
本轮评分/审查仍读**冻结**的 `scoring-decision.md`。

有 `evidence/` 或可读失败摘要且审查通过时，`patch_prompt` 提案可含「改哪几段、禁止删 `{{runtime.*}}`/`{{shared.*}}`」；**空 diff 不得通过**；落地由人贴回写稿仓，本技能不调用外部 `create_proposal`。

## 3. 不变量（违反就停）

- 只写 manifest 指定的可写库；只读库只读。
- 不改 `published_count`；不写 `seo_topic_publish_plan`；不 INSERT 新主题。
- 不删、不改期 `dispatched` / `done` / `abandoned`。
- 禁止 DDL / 无 WHERE DELETE。
- 审查未通过不得 COMMIT。
- **禁止**本轮修改任何 `SKILL.md`、`.agents/skills/`、或正在使用的评分/规则文件。
- 不执行外部复盘日批脚本 / `python -m` 复盘模块入口。
- 不执行 `seo-topic-learning` 的排产/补题流程。

## 4. 失败处理

- 事务失败 → ROLLBACK，报告语句与原因。
- 互斥命中 → skip 该 key，其余可继续。
- 审查耗尽 → 不写库，落盘决策与审查 JSON 摘要到汇报。

## 5. 汇报格式

```text
cutoff=YYYY-MM-DD lang=zh mode=diagnose|full
采集: pool/search/trend/page=[available|skip]; geo/competitor=...
Gate: passed|skip_reason
决策: should_act=.. adj=N hints=M mutex_skip=K
审查: pass=.. score=.. gates_pass=.. gate_codes=[..]
执行: COMMIT 成功 | 未写库
Prompt轨: plans=.. pending_files=[..] patch_prompt=blocked|wrote
验证: 回读一致 | 不一致项；planned/published_count 未改
```

## 6. 反例

- 用今天的 `run_date` 当 cutoff，或读取今日抢占排产当复盘主证据。
- 新建题、改排产、改 pillar、改 published_count。
- 决策者自评 0.70 过线后直接 COMMIT（必须独立审查且 ≥0.90）。
- 无 evidence 仍输出 `patch_prompt`。
- 把 pending 提案当现行规则，或本轮改写 `scoring-decision.md`。
- 修改本技能或主题技能的 `SKILL.md` 并称为「自进化」。
- 执行外部 Python 复盘日批，或与 `seo-topic-learning` 同轮对同一 key 双写。
- 记忆列名不探表；原词表 dump 进决策上下文。

## 7. References 索引

| 何时读 | 文件 |
|---|---|
| 开始前 | 工作区 manifest + seo-decision 必读 |
| 技能内 | [workspace-contract.md](references/workspace-contract.md)、[mcp-discipline.md](references/mcp-discipline.md)、[tracks.md](references/tracks.md) |
