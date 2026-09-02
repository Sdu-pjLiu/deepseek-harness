# 工作区契约

技能不内嵌任何品牌的配额、表名或审查规则。部署内容由工作区 manifest 提供。

## Manifest

- 默认路径：`knowledge/README.md`（相对会话 cwd / 工作区根）
- 用户可指定其它 manifest 路径；以用户或工作区 `AGENTS.md` 说明为准
- manifest 列出**必读**与**可选**文件及读取时机

## 纪律

1. 开始前读取 manifest。
2. manifest 标记为必读的每个文件必须可读；**任一缺失 → 停止**，不要用记忆或训练数据补全。
3. 技能不假设固定文件名；以 manifest 列出的路径为准。
4. 示例 JSON 中的 `pillar`、`publish_platform`、`reason`、`notes` 前缀等枚举，以工作区 `write-invariants` 与 `topic-boundaries` 为准。

## 典型 manifest 结构（示例）

| 类型 | 常见文件名 | 用途 |
|---|---|---|
| MCP 路由 | `mcp-and-tables.md` | 数据源、表、语种路由 |
| 采集 brief | `collector-briefs.md` | 各 lane 具体 SQL 任务 |
| 品牌边界 | `topic-boundaries.md` | 审查、清题 |
| 产品能力 | `product.md` | 补题、起标题 |
| 写库护栏 | `write-invariants.md` | 配额、账本、事务 |
| 覆盖清单 | `coverage-taxonomy.md` | 可选，补题缺口 |

不同工作区可替换上述文件内容，manifest 路径也可不同；技能流程不变。
