# 写库不变量

与 AI-SEO-Agent `config.yml` 的 `topic_learning` 及 `TOPIC_LEARNING_FIXED` 对齐。
改配置后改本页，不要改 SKILL 策略段。

## 排产配额

- 窗口：`[run_date, run_date + 2 - 1]`（horizon_days=2）
- 语种日配额（planned+dispatched+done）：zh **3** / en **1**
- 平台日配额：zh 官网 **1** + 第三方平台 **2**；en 官网 **1** + 第三方平台 **0**
- 同 pillar 日上限：zh **3** / en **1**
- 同题 min_gap：**7** 天；`news_urgent` 时 **3** 天；含窗口外 planned/dispatched/done
- 窗口内同题最多 **2** 条；同日 `daily_sequence` ∈ {1,2} 且未占用
- 平台枚举字面量：`官网`、`第三方平台`
- remaining = target_total - published_count **> 0** 才插入 planned

重建窗口时：可删普通 `planned`（含 `auto:topic_learning:`）。不可动 dispatched/done/abandoned，也不可动 `split:` / `auto:faq_expand:` 前缀行。

同一 `run_date` 已出现 `dispatched` 行时：不要再改 planned（日批已抢占）；调权/补题/归档仍可做。

## 权重与目标篇数（每题每天，不是全池）

账本在该题 `extra.topic_learning_idempotency.daily["YYYY-MM-DD"]`：

```json
{
  "weight_increase": 0,
  "weight_decrease": 0,
  "target_total_increase": 0
}
```

上限：上调 **20**、下调 **10**、target 上调 **5**（单题单次建议再加最多 **2**）。已记账则只做差额。
合并写入时保留 extra 里其它键（如 `writing_hints`）。

全池绝对边界：约 `[max(同语种 active 的 p10, 45), 200]`。
存量 `target_total` 只增不减。不要改 `published_count`。

## JSON_SET 坑

MySQL `JSON_SET` 不会自动创建中间对象。`extra` 为空或没有 `topic_learning_idempotency.daily` 时，先 `JSON_OBJECT` / `JSON_MERGE_PATCH` 建好路径再改数字，或在应用层拼完整 JSON 写回。

## 审计

每次改主题池插 `seo_sub_topic_change_log`：

- `change_type` ∈ `weight` | `target_total` | `topic_create` | `status`
- `source` = `topic_learning`
- `source_ref` = `topic_learning:<run_date>:<lang>`
- `old_value` / `new_value` / `delta` 与实际 UPDATE 一致

## 清题护栏

| 条件 | 动作 |
|---|---|
| 越界且 published_count=0，且无 dispatched/done 排产 | 可硬删：先删该题 planned，再删主题 |
| 已有发布或在途/历史 dispatched·done | 只把 `status` 改为 `archived`（或 `paused`），不删行 |
| 不确定 | 归档，不要删 |

日链路不要 UPDATE 存量 `pillar`。

## 事务

同一 MCP 调用：`START TRANSACTION;` 本轮所有 INSERT/UPDATE/DELETE（主题 + 账本 + 审计 + planned）`; COMMIT;`
失败 `ROLLBACK`。不要把调权和插 planned 拆成两次提交。

## planned 行

- status=`planned`
- notes 以 `auto:topic_learning:<run_date>:<lang>` 开头

## 禁止语句

`DROP` / `TRUNCATE` / `ALTER` / 无 WHERE 的 DELETE。
