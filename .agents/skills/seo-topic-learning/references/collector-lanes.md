# 采集 lane（通用）

各 lane 的具体表、SQL 任务与 summary 字段见工作区 manifest 中的 `collector-briefs.md`（或等价文件）。

## 必派 lane（同一回合并行）

| Lane | 域 |
|---|---|
| `pool_schedule` | 主题池 + 排产占槽 + min_gap |
| `search_queries` | 词表（语种由工作区路由） |
| `site_trend` | 站点趋势 |
| `page_engagement` | 页面级信号 |

## 可选 lane（可先 COUNT 再决定是否派）

`geo`、`autocomplete`、`competitor`、`delivery`、`video_signal`

工作区 `collector-briefs.md` 若标明某可选 lane 仅某一技能使用，另一技能跳过。

## 统一 digest 外壳

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

- `available=false` 时 `reason` 必填，`signals` 可为空。
- `signals` 每条建议 ≤ 30 条（page_engagement 等工作区 brief 可更严）。

## 子 Agent 纪律

- 只读 MCP；禁止写可写库。
- prompt 自包含：`run_date`、`article_language`、工具名、该 lane 的工作区 brief 全文、digest schema。
- 只回结构化 digest；失败或空数据：`available=false`，父 Agent 继续。
- 不要塞整份产品能力长文；品牌审查由父 Agent 负责。

无 `subagent` 工具时：父 Agent 按相同 lane 顺序自己做。
