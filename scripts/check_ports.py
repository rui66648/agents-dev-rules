#!/usr/bin/env python3
"""
端口冲突检测脚本

用于在启动多个本地开发服务前检查端口是否已被占用。
支持检查 .env.template 中定义的所有标准端口。

用法:
    python scripts/check-ports.py                  # 检查所有端口
    python scripts/check-ports.py --ports 8000 3000  # 检查指定端口
    python scripts/check-ports.py --json           # 输出 JSON 格式
"""

import argparse
import json
import socket
import sys
from pathlib import Path
from typing import Optional

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# 从 .env.template 定义的标准端口配置
STANDARD_PORTS: dict[str, dict] = {
    "postgres": {"port": 5432, "service": "PostgreSQL", "protocol": "TCP"},
    "redis": {"port": 6379, "service": "Redis", "protocol": "TCP"},
    "qdrant": {"port": 6333, "service": "Qdrant", "protocol": "TCP"},
    "qdrant-grpc": {"port": 6334, "service": "Qdrant gRPC", "protocol": "TCP"},
    "adlc-backend": {"port": 8000, "service": "ADLC Backend", "protocol": "HTTP"},
    "adlc-frontend": {"port": 3000, "service": "ADLC Frontend", "protocol": "HTTP"},
    "free-llm-api": {"port": 3001, "service": "FreeLLMAPI", "protocol": "HTTP"},
    "trae-gateway": {"port": 4000, "service": "Trae LLM Gateway", "protocol": "HTTP"},
    "omniroute-dashboard": {"port": 20128, "service": "OmniRoute Dashboard", "protocol": "HTTP"},
    "omniroute-api": {"port": 20129, "service": "OmniRoute API", "protocol": "HTTP"},
    "omniroute-ws": {"port": 20132, "service": "OmniRoute WebSocket", "protocol": "WS"},
    "bifrost": {"port": 8080, "service": "Bifrost LLM Router", "protocol": "HTTP"},
    "cliproxyapi": {"port": 8317, "service": "CLIProxyAPI", "protocol": "HTTP"},
}


def check_port(port: int, host: str = "127.0.0.1") -> bool:
    """
    检查指定端口是否可用（未被占用）

    Args:
        port: 要检查的端口号
        host: 主机地址，默认为 127.0.0.1

    Returns:
        True 表示端口可用，False 表示端口已被占用
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            return False  # 端口已被占用
        except (ConnectionRefusedError, OSError):
            return True  # 端口可用


def check_ports(ports: list[int]) -> dict[int, bool]:
    """
    批量检查多个端口的可用性

    Args:
        ports: 端口号列表

    Returns:
        {port: is_available} 字典
    """
    results: dict[int, bool] = {}
    for port in ports:
        results[port] = check_port(port)
    return results


def parse_env_file(env_path: Path) -> dict[str, int]:
    """
    解析 .env 文件并提取端口配置

    Args:
        env_path: .env 文件路径

    Returns:
        {variable_name: port} 字典
    """
    port_vars: dict[str, int] = {}
    if not env_path.exists():
        return port_vars

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # 匹配可能的端口变量名
            port_keywords = [
                "PORT", "BACKEND_PORT", "FRONTEND_PORT", "REDIS_PORT",
                "POSTGRES_PORT", "QDRANT_PORT", "LIVE_WS_PORT"
            ]
            for keyword in port_keywords:
                if keyword in key.upper():
                    try:
                        port_vars[key] = int(value)
                    except ValueError:
                        pass
                    break

    return port_vars


def main():
    parser = argparse.ArgumentParser(
        description="检查开发环境端口冲突",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python check-ports.py                          # 检查所有标准端口
    python check-ports.py --ports 8000 3000        # 检查指定端口
    python check-ports.py --json                   # 输出 JSON 格式
    python check-ports.py --env src/.env          # 检查 .env 中定义的端口
        """,
    )
    parser.add_argument(
        "--ports",
        nargs="+",
        type=int,
        help="指定要检查的端口号",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果",
    )
    parser.add_argument(
        "--env",
        type=Path,
        help="指定 .env 文件路径，从中提取端口配置",
    )
    args = parser.parse_args()

    # 确定要检查的端口
    ports_to_check: set[int] = set()

    if args.ports:
        ports_to_check.update(args.ports)
    else:
        # 默认检查所有标准端口
        ports_to_check.update(v["port"] for v in STANDARD_PORTS.values())

    if args.env:
        env_ports = parse_env_file(args.env)
        ports_to_check.update(env_ports.values())

    # 检查端口
    results = check_ports(sorted(ports_to_check))

    # 输出结果
    if args.json:
        output = {
            "checked_at": "now",  # Python 中没有简单的 ISO 时间
            "ports": {
                str(port): {"available": available, "service": STANDARD_PORTS.get(
                    next(k for k, v in STANDARD_PORTS.items() if v["port"] == port),
                    {"service": f"Port {port}"}
                )["service"]}
                for port, available in results.items()
            }
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("\n=== 开发环境端口状态检查 ===\n")
        print(f"{'服务':<25} {'端口':>6} {'协议':<4} {'状态':<10}")
        print("-" * 55)

        for port, available in sorted(results.items()):
            info = STANDARD_PORTS.get(
                next((k for k, v in STANDARD_PORTS.items() if v["port"] == port), ""),
                {"service": f"自定义服务", "protocol": "TCP"}
            )
            status = "✓ 可用" if available else "✗ 占用"
            print(f"{info['service']:<25} {port:>6} {info['protocol']:<4} {status:<10}")

        print("\n" + "=" * 55)
        free_count = sum(1 for v in results.values() if v)
        used_count = len(results) - free_count
        print(f"可用端口: {free_count}/{len(results)}")

        if used_count > 0:
            print(f"\n⚠ 警告: {used_count} 个端口已被占用，可能导致启动失败！")
            print("请停止占用端口的进程，或修改 .env.template 中的端口配置")
        else:
            print("\n✓ 所有端口均可用，可以安全启动服务")

        sys.exit(0 if free_count == len(results) else 1)


if __name__ == "__main__":
    main()
