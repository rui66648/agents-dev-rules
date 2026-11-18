#!/usr/bin/env python3
"""
Cloudflare AI Gateway 路由配置工具
参考: trae-llm-gateway 项目架构
功能:
  1. 创建 Custom Provider
  2. 配置 Dynamic Routes
  3. 设置 Fallback 路由
  4. 验证配置状态
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# 尝试导入 requests，如果不存在则使用 urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


class CloudflareGatewayConfig:
    """Cloudflare AI Gateway 配置管理器"""
    
    def __init__(
        self,
        account_id: str,
        gateway_id: str,
        api_token: str,
        base_url: str = "https://api.cloudflare.com/client/v4"
    ):
        self.account_id = account_id
        self.gateway_id = gateway_id
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送 HTTP 请求"""
        url = f"{self.base_url}/{endpoint}"
        
        if HAS_REQUESTS:
            resp = requests.request(method, url, headers=self.headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()
        else:
            req = urllib.request.Request(url, method=method)
            for k, v in self.headers.items():
                req.add_header(k, v)
            if data:
                req.data = json.dumps(data).encode('utf-8')
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else '{}'
                print(f"[ERROR] HTTP {e.code}: {error_body}")
                sys.exit(1)
    
    def create_custom_provider(
        self,
        name: str,
        slug: str,
        base_url: str,
        description: Optional[str] = None,
        enable: bool = True
    ) -> Dict:
        """创建 Custom Provider"""
        data = {
            "name": name,
            "slug": slug,
            "base_url": base_url,
            "enable": enable
        }
        if description:
            data["description"] = description
        
        print(f"[1/3] 创建 Custom Provider: {name} ({slug})")
        print(f"  Base URL: {base_url}")
        
        result = self._request("POST", f"accounts/{self.account_id}/ai-gateway/custom-providers", data)
        
        if result.get("success"):
            provider = result.get("result", {})
            print(f"  ✓ 创建成功: ID={provider.get('id')}")
            return provider
        else:
            print(f"  ✗ 创建失败: {result.get('errors')}")
            return {}
    
    def create_dynamic_route(
        self,
        route_name: str,
        primary_model: str,
        primary_provider: str,
        fallback_models: Optional[List[Dict]] = None,
        enable_fallback: bool = True
    ) -> Dict:
        """创建 Dynamic Route"""
        routes = [
            {
                "match": f"model == \"{primary_model}\"",
                "handler": {
                    "type": "model",
                    "model": primary_model,
                    "provider": primary_provider
                }
            }
        ]
        
        fallback_routes = []
        if enable_fallback and fallback_models:
            for fb in fallback_models:
                fallback_routes.append({
                    "handler": {
                        "type": "model",
                        "model": fb["model"],
                        "provider": fb.get("provider", "workers-ai")
                    }
                })
        
        data = {
            "name": route_name,
            "routes": routes
        }
        if fallback_routes:
            data["fallback_routes"] = fallback_routes
        
        print(f"\n[2/3] 创建 Dynamic Route: {route_name}")
        print(f"  Primary: {primary_model} ({primary_provider})")
        if fallback_routes:
            print(f"  Fallback: {[fb['handler']['model'] for fb in fallback_routes]}")
        
        result = self._request(
            "POST",
            f"accounts/{self.account_id}/ai-gateway/gateways/{self.gateway_id}/dynamic-routes",
            data
        )
        
        if result.get("success"):
            route = result.get("result", {})
            print(f"  ✓ 创建成功: ID={route.get('id')}")
            return route
        else:
            print(f"  ✗ 创建失败: {result.get('errors')}")
            return {}
    
    def get_gateway_info(self) -> Dict:
        """获取 Gateway 信息"""
        print(f"\n[3/3] 验证 Gateway 配置...")
        result = self._request("GET", f"accounts/{self.account_id}/ai-gateway/gateways/{self.gateway_id}")
        
        if result.get("success"):
            gateway = result.get("result", {})
            print(f"  Gateway: {gateway.get('name')}")
            print(f"  ID: {gateway.get('id')}")
            print(f"  Created: {gateway.get('created_at')}")
            print(f"  Modified: {gateway.get('modified_at')}")
            return gateway
        else:
            print(f"  ✗ 获取失败: {result.get('errors')}")
            return {}
    
    def list_custom_providers(self) -> List[Dict]:
        """列出所有 Custom Providers"""
        result = self._request("GET", f"accounts/{self.account_id}/ai-gateway/custom-providers")
        return result.get("result", [])
    
    def list_dynamic_routes(self) -> List[Dict]:
        """列出所有 Dynamic Routes"""
        result = self._request("GET", f"accounts/{self.account_id}/ai-gateway/gateways/{self.gateway_id}/dynamic-routes")
        return result.get("result", [])


def main():
    """主函数"""
    # 配置参数 (请根据实际情况修改)
    config = {
        "account_id": os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
        "gateway_id": os.environ.get("CLOUDFLARE_GATEWAY_ID", "ai-proxy"),
        "api_token": os.environ.get("CLOUDFLARE_API_TOKEN", ""),
        
        # Custom Provider 配置
        "custom_provider": {
            "name": "My Custom LLM Provider",
            "slug": "my-custom-llm",
            "base_url": os.environ.get("CUSTOM_PROVIDER_BASE_URL", "https://api.your-provider.com"),
            "description": "Custom LLM provider for tra-llm-gateway",
            "enable": True
        },
        
        # Dynamic Route 配置
        "route": {
            "name": "auto",
            "primary_model": os.environ.get("PRIMARY_MODEL", "gpt-4o"),
            "primary_provider": os.environ.get("PRIMARY_PROVIDER", "openai"),
            "fallback_models": [
                {"model": "@cf/meta/llama-3.3-70b-instruct", "provider": "workers-ai"},
                {"model": "gpt-4o-mini", "provider": "openai"}
            ],
            "enable_fallback": True
        }
    }
    
    # 检查必要的环境变量
    if not config["account_id"]:
        print("[ERROR] 请设置 CLOUDFLARE_ACCOUNT_ID 环境变量")
        print("  获取方式: https://dash.cloudflare.com -> Account Home")
        sys.exit(1)
    
    if not config["api_token"]:
        print("[ERROR] 请设置 CLOUDFLARE_API_TOKEN 环境变量")
        print("  获取方式: https://dash.cloudflare.com -> My Profile -> API Tokens")
        sys.exit(1)
    
    # 创建配置管理器
    gateway = CloudflareGatewayConfig(
        account_id=config["account_id"],
        gateway_id=config["gateway_id"],
        api_token=config["api_token"]
    )
    
    # 执行配置
    print("=" * 50)
    print("Cloudflare AI Gateway 路由配置")
    print("=" * 50)
    print(f"\nAccount ID: {config['account_id']}")
    print(f"Gateway ID: {config['gateway_id']}")
    print()
    
    # 1. 创建 Custom Provider
    provider = gateway.create_custom_provider(
        name=config["custom_provider"]["name"],
        slug=config["custom_provider"]["slug"],
        base_url=config["custom_provider"]["base_url"],
        description=config["custom_provider"].get("description"),
        enable=config["custom_provider"].get("enable", True)
    )
    
    # 2. 创建 Dynamic Route
    route = gateway.create_dynamic_route(
        route_name=config["route"]["name"],
        primary_model=config["route"]["primary_model"],
        primary_provider=config["route"]["primary_provider"],
        fallback_models=config["route"].get("fallback_models"),
        enable_fallback=config["route"].get("enable_fallback", True)
    )
    
    # 3. 验证配置
    gateway_info = gateway.get_gateway_info()
    
    # 打印测试命令
    print("\n" + "=" * 50)
    print("测试命令")
    print("=" * 50)
    print(f"""
# 测试 OpenAI 兼容端点
curl -X POST "https://gateway.ai.cloudflare.com/v1/{config['account_id']}/{config['gateway_id']}/openai/v1/chat/completions" \\
  -H "cf-aig-authorization: Bearer {config['api_token']}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "model": "{config['route']['primary_model']}",
    "messages": [{{"role": "user", "content": "Hello!"}}]
  }}'"
    """)
    
    print("\nDashboard 链接:")
    print(f"  https://dash.cloudflare.com/{config['account_id']}/ai/ai-gateway/{config['gateway_id']}/dynamic-routes")


if __name__ == "__main__":
    main()
