# 工作区契约

技能不内嵌任何品牌的配额、表名或审查规则。部署内容由工作区 manifest 提供。

## Manifest

- 默认路径：`knowledge/README.md`（相对会话 cwd / 工作区根）
- 用户可指定其它 manifest 路径；以用户或工作区 `AGENTS.md` 说明为准
- manifest 列出**必读**与**可选**文件及读取时机
- manifest **可按技能**分列必读/可选/禁止（例如共用必读 + `seo-topic-learning` / `seo-decision` 专段）；本技能只读「共用」与**本技能名**下列出的文件，其它技能专段视为禁止

## 纪律

1. 开始前读取 manifest。
2. manifest 对本技能标记为必读的每个文件必须可读；**任一缺失 → 停止**，不要用记忆或训练数据补全。
3. 技能不假设固定文件名；以 manifest 列出的路径为准。
4. 示例 JSON 中的 `pillar`、`publish_platform`、`reason`、`notes` 前缀等枚举，以工作区 `write-invariants` 与 `topic-boundaries` 为准。
5. `proposals/pending/` 不是现行规则；未人工 approve 前不得当必读。
6. **配额对账**：逐日满额、超配改期/精简、欠配补槽/向后延伸的**算法**在本技能；语种/平台日配额数字与平台枚举在工作区 `write-invariants`；技能**不设**排产天数上限。

## 典型 manifest 结构（示例）

| 类型 | 常见文件名 | 用途 |
|---|---|---|
| MCP 路由 | `mcp-and-tables.md` | 数据源、表、语种路由 |
| 采集 brief | `collector-briefs.md` | 各 lane 具体 SQL 任务 |
| 品牌边界 | `topic-boundaries.md` | 审查、清题 |
| 产品能力 | `product.md` | 补题、起标题 |
| 写库护栏 | `write-invariants.md` | 配额、账本、事务 |
| 主题评分 | `scoring-rubric.md` | 主题日批硬门闩与战略软评分 |
| 复盘规则/评分 | `decision-rules.md` / `scoring-decision.md` | 仅 `seo-decision` |
| 覆盖清单 | `coverage-taxonomy.md` | 可选，补题缺口 |

不同工作区可替换上述文件内容，manifest 路径也可不同；技能流程不变。
