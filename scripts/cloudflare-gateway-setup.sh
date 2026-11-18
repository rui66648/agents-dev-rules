#!/bin/bash
# ============================================================
# Cloudflare AI Gateway 路由配置脚本
# 参考: trae-llm-gateway 项目架构
# ============================================================

# 使用说明:
# 1. 修改下方配置变量
# 2. 运行: bash setup-cloudflare-gateway.sh
# 3. 访问 Cloudflare Dashboard 验证配置

# ===================== 配置区域 =====================

# Cloudflare 认证
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN}"  # 从环境变量或 Dashboard 获取
ACCOUNT_ID=""  # 你的 Cloudflare Account ID

# Gateway 配置
GATEWAY_ID="ai-proxy"  # 你的 Gateway ID

# Custom Provider 配置 (自定义厂商)
CUSTOM_PROVIDER_NAME="My Custom LLM Provider"
CUSTOM_PROVIDER_SLUG="my-custom-llm"
CUSTOM_PROVIDER_BASE_URL="https://api.your-provider.com"  # 替换为你的 API 地址

# Cloudflare Workers AI 模型
WORKERS_AI_MODEL="@cf/meta/llama-3.3-70b-instruct"

# OpenAI 模型
OPENAI_MODEL="gpt-4o"

# Fallback 配置
FALLBACK_ENABLED=true

# ===================== 执行区域 =====================

echo "=========================================="
echo "Cloudflare AI Gateway 路由配置"
echo "=========================================="
echo ""
echo "Account ID: ${ACCOUNT_ID:-未设置}"
echo "Gateway ID: ${GATEWAY_ID}"
echo ""

# 检查必要变量
if [ -z "${ACCOUNT_ID}" ]; then
    echo "[ERROR] 请先设置 ACCOUNT_ID 变量"
    exit 1
fi

if [ -z "${CLOUDFLARE_API_TOKEN}" ]; then
    echo "[ERROR] 请先设置 CLOUDFLARE_API_TOKEN 环境变量"
    echo "  export CLOUDFLARE_API_TOKEN='your-token-here'"
    exit 1
fi

# 1. 创建 Custom Provider
echo "[1/3] 创建 Custom Provider..."
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/ai-gateway/custom-providers" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "'${CUSTOM_PROVIDER_NAME}'",
    "slug": "'${CUSTOM_PROVIDER_SLUG}'",
    "base_url": "'${CUSTOM_PROVIDER_BASE_URL}'",
    "enable": true
  }' | jq .

echo ""

# 2. 创建 Dynamic Route
echo "[2/3] 创建 Dynamic Route..."
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/ai-gateway/gateways/${GATEWAY_ID}/dynamic-routes" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "auto",
    "routes": [
      {
        "match": "model == \"'${OPENAI_MODEL}'\"",
        "handler": {
          "type": "model",
          "model": "'${OPENAI_MODEL}'",
          "provider": "openai"
        }
      }
    ],
    "fallback_routes": [
      {
        "handler": {
          "type": "model",
          "model": "'${WORKERS_AI_MODEL}'",
          "provider": "workers-ai"
        }
      }
    ]
  }' | jq .

echo ""

# 3. 验证配置
echo "[3/3] 验证 Gateway 配置..."
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/ai-gateway/gateways/${GATEWAY_ID}" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" | jq '.result | {id, name, created_at, modified_at}'

echo ""
echo "=========================================="
echo "配置完成!"
echo "=========================================="
echo ""
echo "访问 Dashboard 验证:"
echo "  https://dash.cloudflare.com/${ACCOUNT_ID}/ai/ai-gateway/${GATEWAY_ID}/dynamic-routes"
echo ""
echo "测试 API:"
echo "  curl https://gateway.ai.cloudflare.com/v1/${ACCOUNT_ID}/${GATEWAY_ID}/openai/v1/chat/completions \\"
echo "    -H 'cf-aig-authorization: Bearer ${CLOUDFLARE_API_TOKEN}' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\": \"${OPENAI_MODEL}\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}'"
echo ""
