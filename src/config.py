"""配置模块：从环境变量读取模型、API Key、token 预算等。

用法：
  export OPENAI_API_KEY=sk-xxx        # 真实调用时必填
  export VIBE_MODEL=deepseek-chat      # 可选，默认见下方
未配置 API Key 时，LLM 客户端会走 Mock 模式，便于离线演示与测试。
"""
import os
from pathlib import Path

# dotenv 为可选依赖：未安装时跳过 .env 加载，改用系统环境变量（Mock 模式仍可运行）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

# 仓库根目录（用于定位 references/ 角色卡等资源）
REPO_ROOT = Path(__file__).resolve().parents[1]

# ---- 模型配置 ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
API_BASE_URL = os.getenv("VIBE_API_BASE", "https://api.deepseek.com/v1")
MODEL = os.getenv("VIBE_MODEL", "deepseek-chat")

# ---- 专家证人 - 固定 5 位，与 references/agents/*.md 对应 ----
EXPERT_NAMES = ["product-manager", "code-engineer", "filing-agent", "competitor-analyst", "growth-hacker"]

# ---- 消费群体候选库（7 选 2-3，动态匹配） ----
JURY_POOL = ["baoma", "student", "sme-founder", "senior", "office-worker", "freelancer", "creator"]
JURY_PICK = int(os.getenv("VIBE_JURY_PICK", "2"))  # 实际匹配个数，默认 2

# ---- 裁决权重：消费群体 60% / 专家 40% ----
JURY_WEIGHT = 0.6
EXPERT_WEIGHT = 0.4

# ---- token 预算与降级 ----
TOTAL_TOKEN_BUDGET = int(os.getenv("VIBE_TOKEN_BUDGET", "8000"))

# ---- 是否走 Mock（无 API Key 时自动开启） ----
def is_mock():
    return not OPENAI_API_KEY
