# 工作区契约

技能不内嵌任何品牌的配额、表名或审查规则。部署内容由工作区 manifest 提供。

## Manifest

- 默认路径：`knowledge/README.md`（相对会话 cwd / 工作区根）
- 用户可指定其它 manifest 路径；以用户或工作区 `AGENTS.md` 说明为准
- manifest 列出**必读**与**可选**文件及读取时机
- manifest **可按技能**分列必读/可选/禁止；本技能（`seo-decision`）只读「共用」与 **seo-decision** 专段；主题技能专段（如仅给排产用的评分门闩用法）不要拿来做复盘写库判定

## 纪律

1. 开始前读取 manifest。
2. manifest 对本技能标记为必读的每个文件必须可读；**任一缺失 → 停止**，不要用记忆或训练数据补全。
3. 技能不假设固定文件名；以 manifest 列出的路径为准。
4. 调权 cap、互斥、间隔以工作区 `write-invariants` 决策专段为准；当则规则以 `decision-rules` 为准；审查以 `scoring-decision` 为准。
5. `proposals/pending/` 不是现行规则；未人工 approve 前不得当必读。
6. 禁止本轮修改任何技能目录下的 `SKILL.md`。

## 典型文件（示例名，以 manifest 为准）

| 类型 | 常见文件名 | 用途 |
|---|---|---|
| MCP 路由 | `mcp-and-tables.md` | 数据源、表、语种路由 |
| 采集 brief | `collector-briefs.md` | lane SQL + 决策 pack 字段 |
| 品牌/产品 | `topic-boundaries.md` / `product.md` | 边界背景（本轨不新建题） |
| 写库护栏 | `write-invariants.md` | 决策专段 + 互斥 |
| 复盘规则 | `decision-rules.md` | 当则、白名单、P1–P7 |
| 复盘评分 | `scoring-decision.md` | 独立审查过线 0.90 |
| Prompt 映射 | `prompt-surfaces.md` | Prompt 轨 |
