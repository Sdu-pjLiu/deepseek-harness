#!/usr/bin/env python3
"""
静态校验 seo-topic-learning 技能目录结构与工作流要点。

Author: pjliu
Date: 2026-09-01
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_REFERENCES = (
    "mcp-and-tables.md",
    "deepbi-and-pillars.md",
    "coverage-taxonomy.md",
    "write-invariants.md",
    "collector-briefs.md",
)
FORBIDDEN_PATTERNS = (
    r"##\s*4\.\s*SQL",
    r"§4\s*SQL",
    r"SHOW CREATE TABLE",
    r"ORDER BY\s+weight\s+DESC",
)
REQUIRED_SKILL_HINTS = (
    "search_objects",
    "pool_schedule",
    "search_queries",
    "mode",
    "dry_run",
    "write",
    "collector-briefs",
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

    ref_dir = root / "references"
    if not ref_dir.is_dir():
        errors.append(f"缺少 references 目录: {ref_dir}")
    else:
        for name in REQUIRED_REFERENCES:
            path = ref_dir / name
            if not path.is_file():
                errors.append(f"缺少 reference: {path}")

    evals_path = root / "evals" / "evals.json"
    if not evals_path.is_file():
        errors.append(f"缺少 evals/evals.json: {evals_path}")
    else:
        try:
            data = json.loads(evals_path.read_text(encoding="utf-8"))
            if len(data.get("evals", [])) < 3:
                errors.append("evals.json 应至少包含 3 条用例")
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
