# SEO 运营 Cordis 补丁

当 DSH 工作区选 **外部知识包**（如 `DeepBI/`）时，project root 停在该包的 `.git` 目录，不会自动扫描 Harness 的 `.agents/skills`。本补丁通过 `customSkillDirs` 注册 Harness 技能根目录。

## 用法

在 `deepseek-harness` 目录执行：

```bash
dsh web --patch apps/cli/config/examples/seo-ops/cordis.yml
```

CLI 同理：

```bash
dsh --patch apps/cli/config/examples/seo-ops/cordis.yml
```

## 工作区

DSH Web 侧边栏添加工作区，选择 DeepBI 仓库根目录，例如：

```text
/path/to/SEO/DeepBI
```

## 验证技能已加载

启动后在新会话中检查技能目录是否含 `seo-topic-learning`，或发起主题任务口令：

```text
缺 Listing 转化漏斗则补题；评估 Shopify 多平台；先预览
```

Agent 应加载 Harness 技能并读取 DeepBI `knowledge/README.md` manifest。

可选：用 `--dump-config` 确认 `skill-filesystem` 的 `customSkillDirs` 已指向 Harness `.agents/skills`：

```bash
dsh web --patch apps/cli/config/examples/seo-ops/cordis.yml --dump-config 2>/dev/null | rg customSkillDirs -A2
```

## 持久化（可选）

若每次启动都要带 patch，可将等效配置写入用户级 `$DSH_HOME/cordis.patch.yml`：

```yaml
- id: skill-filesystem
  config:
    customSkillDirs:
      - /absolute/path/to/deepseek-harness/.agents/skills
```

将路径替换为本机 Harness 仓库绝对路径。

## 分工

| 位置 | 内容 |
|---|---|
| `DeepBI/knowledge/` | 配额、品牌、表路由、采集 brief（部署真源） |
| `deepseek-harness/.agents/skills/seo-topic-learning/` | 通用工作流、mode、决策/审查 JSON |
