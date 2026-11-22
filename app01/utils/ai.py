# -*- coding: utf-8 -*-
"""T1：统一大模型调用客户端 LLMClient（OpenAI 兼容接口）

- API_KEY / BASE_URL / MODEL 全部从环境变量读取（项目根 .env 或系统环境变量），
  代码里不写死密钥，.env 已被 .gitignore 忽略，不会提交到 Git。
- 对外只暴露 chat(prompt) -> str；调用失败返回友好提示，不让页面崩溃。
"""
import os
from pathlib import Path

import requests


def _load_env():
    """极简 .env 加载器：把项目根 .env 的键值写入 os.environ（不覆盖已有值）。
    不依赖 python-dotenv，避免额外安装。
    """
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


class LLMClient:
    """把大模型当成"一个会写字的接口"：给文字，返回文字。"""

    def __init__(self):
        _load_env()
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.base_url = os.environ.get(
            "LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = os.environ.get(
            "LLM_MODEL", "Qwen/Qwen3-VL-8B-Instruct")
        self.timeout = 30

    def chat(self, prompt, system=None, temperature=0.3, max_tokens=800):
        """调用对话接口，返回模型回答文本。任何异常都转成友好提示返回。"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = requests.post(
                self.base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + self.api_key,
                         "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages,
                      "temperature": temperature, "max_tokens": max_tokens},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # 网络/认证/限流等统一兜底
            return "抱歉，AI 服务暂时不可用，请稍后再试。（原因：%s）" % str(exc)[:120]


# 模块级单例，视图直接 get_client() 复用，避免重复初始化
_client = None


def get_client():
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
