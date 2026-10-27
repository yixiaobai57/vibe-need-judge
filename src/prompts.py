"""提示词加载：从 references/ 目录读取角色卡、评分规则与报告模板。

这样骨架代码与仓库已有的 prompt 资产（references/*.md）解耦：
改角色卡无需改代码，只需更新 md 文件。
"""
from pathlib import Path
from typing import Optional
from . import config

REFS = config.REPO_ROOT / "references"


def load_md(path: Path) -> str:
    """读取 md 文件文本，不存在时返回空串。"""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def agent_card(agent_key: str) -> str:
    """读取单个专家角色卡。agent_key 如 'product-manager'。"""
    return load_md(REFS / "agents" / f"{agent_key}.md")


def consumer_card(group_key: str) -> str:
    """读取消费群体画像卡（references/agents/consumer-groups/ 下）。"""
    return load_md(REFS / "agents" / "consumer-groups" / f"{group_key}.md")


def case_library(group_key: str) -> str:
    """按需读取案例库（省 token，降级时可关闭）。"""
    return load_md(REFS / "case-library" / f"{group_key}-cases.md")


def scoring_rubric() -> str:
    return load_md(REFS / "scoring-rubric.md")


def verdict_template() -> str:
    return load_md(config.REPO_ROOT / "templates" / "verdict-report.md")
