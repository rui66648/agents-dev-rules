#!/usr/bin/env python3
"""
RULE-041 模型网关强制接入 Linter
扫描代码中直接调用模型 API 的 import / 调用，阻断直连，强制走统一网关 (LiteLLM/OpenRouter)。

用法:
    python model_gateway_lint.py [--path .] [--ci] [--format text|json]

退出码:
    0 = 通过 (无直连)
    1 = 存在直连模型 API (阻断)
    2 = 参数错误 / 运行异常
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 直连模型 API 的 SDK import 特征（黑名单）
DIRECT_IMPORTS = {
    "openai": "OpenAI SDK 直连",
    "anthropic": "Anthropic SDK 直连",
    "cohere": "Cohere SDK 直连",
    "google.generativeai": "Google Gemini SDK 直连",
    "mistralai": "Mistral SDK 直连",
    "together": "Together SDK 直连",
    "replicate": "Replicate SDK 直连",
    "groq": "Groq SDK 直连",
    "bedrock": "AWS Bedrock 直连",
    "vertexai": "Google Vertex AI 直连",
}

# 允许的网关 SDK（白名单）
GATEWAY_IMPORTS = {
    "litellm": "LiteLLM 网关",
    "openrouter": "OpenRouter 网关",
    "langchain": "LangChain 网关层",
    "langchain_openai": "LangChain OpenAI 适配器",
    "langchain_anthropic": "LangChain Anthropic 适配器",
}

# 直连 HTTP 调用的特征（绕过 SDK 直接请求模型 endpoint）
DIRECT_HTTP_MARKERS = [
    "api.openai.com",
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "api.cohere.ai",
    "api.mistral.ai",
    "api.together.xyz",
    "api.replicate.com",
    "api.groq.com",
    "bedrock-runtime",
    "api.deepseek.com",
    "api.moonshot.cn",
    "dashscope.aliyuncs.com",
]

SKIP_DIRS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "archive",
    "docs",
    "rules",
    "skills",
    "agents",
    "hooks",
}


def scan_file(path: Path) -> list[dict]:
    """扫描单个文件，返回直连模型 API 的发现列表。"""
    findings: list[dict] = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip().lower()
        # 跳过注释行
        if stripped.startswith(("#", "//", "*", "/*")):
            continue
        # 检查 import 直连
        for imp, desc in DIRECT_IMPORTS.items():
            if imp in stripped and ("import" in stripped or "from" in stripped):
                findings.append(
                    {
                        "file": str(path),
                        "line": idx,
                        "category": "direct_import",
                        "target": imp,
                        "message": f"直连模型 SDK ({desc})，应通过统一网关",
                    }
                )
        # 检查 HTTP endpoint 直连
        for marker in DIRECT_HTTP_MARKERS:
            if marker in stripped:
                findings.append(
                    {
                        "file": str(path),
                        "line": idx,
                        "category": "direct_http",
                        "target": marker,
                        "message": f"直连模型 endpoint ({marker})，应通过统一网关",
                    }
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="RULE-041 模型网关强制接入 Linter")
    parser.add_argument("--path", default=".", help="扫描根目录")
    parser.add_argument("--ci", action="store_true", help="CI 模式，失败时以非零退出码阻断")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"错误: 路径不存在 {root}", file=sys.stderr)
        return 2

    all_findings: list[dict] = []
    scanned_files = 0
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".js", ".ts", ".tsx", ".jsx"}:
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            scanned_files += 1
            all_findings.extend(scan_file(path))

    # 去重（同一文件同一行同一 target 只报一次）
    unique: list[dict] = []
    seen: set[tuple] = set()
    for f in all_findings:
        key = (f["file"], f["line"], f["target"])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rule": "RULE-041",
                    "scanned_files": scanned_files,
                    "findings": unique,
                    "verdict": "pass" if not unique else "block",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if not unique:
            print(f"✅ RULE-041 通过: 扫描 {scanned_files} 个文件，无直连模型 API")
        else:
            print(f"❌ RULE-041 未通过: 发现 {len(unique)} 处直连模型 API")
            for f in unique:
                print(f"  - {f['file']}:{f['line']} [{f['category']}] {f['message']}")

    if unique:
        if args.ci:
            print("阻断: 存在直连模型 API，违反 RULE-041", file=sys.stderr)
            return 1
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
