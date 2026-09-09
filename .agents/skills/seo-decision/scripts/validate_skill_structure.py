#!/usr/bin/env python3
"""
静态校验 seo-decision 技能目录结构与工作流要点。

Author: pjliu
Date: 2026-09-07
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_REFERENCES = (
    "workspace-contract.md",
    "mcp-discipline.md",
    "tracks.md",
)
FORBIDDEN_REFERENCES = (
    "write-invariants.md",
    "mcp-and-tables.md",
    "collector-briefs.md",
    "decision-rules.md",
    "scoring-decision.md",
    "brand-pack.md",
    "deepbi-and-pillars.md",
)
FORBIDDEN_PATTERNS = (
    r"AI-SEO-Agent",
    r"/home/deepinsight",
    r"seo_decision\.sh",
    r"config\.yml",
    r"brand-pack",
    r"topic_learning_scheduled",
    r"SHOW CREATE TABLE",
    r"##\s*4\.\s*SQL",
)
REQUIRED_SKILL_HINTS = (
    "workspace-contract",
    "manifest",
    "search_objects",
    "cutoff_date",
    "diagnose",
    "full",
    "gates_pass",
    "skipped_mutex_keys",
    "scoring-decision",
    "proposals/pending",
    "独立审查",
    "seo-topic-learning",
)


def validate_skill_root(root: Path) -> list[str]:
    """校验技能目录，返回错误列表。"""
    errors: list[str] = []

    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"缺少 SKILL.md: {skill_md}")
        return errors

    body = skill_md.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, body, re.IGNORECASE):
            errors.append(f"SKILL.md 含禁止模式: {pattern}")

    for hint in REQUIRED_SKILL_HINTS:
        if hint not in body:
            errors.append(f"SKILL.md 缺少关键片段: {hint}")

    if re.search(r"\.agents/skills.*作为可写|改写.*SKILL\.md.*自进化", body):
        pass
    if "禁止" not in body or "SKILL.md" not in body:
        errors.append("SKILL.md 应明确禁止修改 SKILL.md")

    ref_dir = root / "references"
    if not ref_dir.is_dir():
        errors.append(f"缺少 references 目录: {ref_dir}")
    else:
        for name in REQUIRED_REFERENCES:
            path = ref_dir / name
            if not path.is_file():
                errors.append(f"缺少 reference: {path}")
        for name in FORBIDDEN_REFERENCES:
            path = ref_dir / name
            if path.is_file():
                errors.append(f"不应存在的部署 reference: {path}")

    evals_path = root / "evals" / "evals.json"
    if not evals_path.is_file():
        errors.append(f"缺少 evals/evals.json: {evals_path}")
    else:
        try:
            data = json.loads(evals_path.read_text(encoding="utf-8"))
            evals = data.get("evals", [])
            if len(evals) < 4:
                errors.append("evals.json 应至少包含 4 条用例")
        except json.JSONDecodeError as exc:
            errors.append(f"evals.json 解析失败: {exc}")

    return errors


def main() -> int:
    """入口：校验技能并打印结果。"""
    errors = validate_skill_root(SKILL_ROOT)
    if errors:
        print("SMOKE FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("SMOKE PASS")
    print(f"skill_root={SKILL_ROOT}")
    print(f"references={len(REQUIRED_REFERENCES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
