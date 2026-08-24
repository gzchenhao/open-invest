# Open Invest Protocol API 文档

## 📖 概述

Open Invest Protocol 基于 JSON-RPC 2.0 标准，提供了一套实验性 API 接口框架，用于探索高科技项目方与政府招商局之间的互联方案。

## 🔗 基础信息

- **协议版本**: JSON-RPC 2.0
- **基础 URL**: `http://localhost:8000`
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 🔧 快速开始（实验性）

### 端点列表

| 端点 | 方法 | 描述 |
|------|------|------|
| `/rpc` | POST | JSON-RPC 统一端点 |
| `/health` | GET | 健康检查 |
| `/` | GET | 服务信息 |

## 📋 详细 API

### 1. JSON-RPC 统一端点

#### 端点
```
POST /rpc
```

#### 描述
统一的 JSON-RPC 2.0 端点，处理所有协议请求。

#### 请求格式

```json
{
  "jsonrpc": "2.0",
  "method": "get_tech_readiness",
  "params": {
    "project_id": "ai-auto-pilot-2024"
  },
  "id": "req-001"
}
```

#### 参数说明

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| jsonrpc | string | 是 | JSON-RPC 版本，固定为 "2.0" |
| method | string | 是 | API 方法名 |
| params | object | 是 | 方法参数 |
| id | string | 是 | 请求唯一标识符 |

#### 响应格式

```json
{
  "jsonrpc": "2.0",
  "result": {
    "project_id": "ai-auto-pilot-2024",
    "level": "prototype",
    "description": "基于深度学习的自动驾驶系统",
    "timeline": {
      "2024-Q1": "完成算法优化",
      "2024-Q2": "实车测试"
    },
    "milestones": [
      "算法模型训练完成",
      "封闭场地测试通过"
    ],
    "risks": [
      "算法安全性验证",
      "法规合规性"
    ]
  },
  "id": "req-001"
}
```

#### 错误响应

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {
      "details": "Missing required parameter: project_id"
    }
  },
  "id": "req-001"
}
```

#### 错误代码

| 代码 | 消息 | 描述 |
|------|------|------|
| -32600 | Invalid Request | 无效请求 |
| -32601 | Method not found | 方法未找到 |
| -32602 | Invalid params | 无效参数 |
| -32603 | Internal error | 内部错误 |
| -32604 | Parse error | 解析错误 |

### 2. 健康检查

#### 端点
```
GET /health
```

#### 描述
检查服务运行状态。

#### 响应格式

```json
{
  "status": "healthy",
  "service": "open-invest-protocol-server"
}
```

### 3. 服务信息

#### 端点
```
GET /
```

#### 描述
获取服务基本信息。

#### 响应格式

```json
{
  "service": "Open Invest Protocol Server",
  "version": "1.0.0",
  "description": "高科技项目方服务端实验 - 探索与政府招商局的互联方案",
  "endpoints": {
    "rpc": "/rpc - JSON-RPC 2.0 endpoint",
    "health": "/health - Health check"
  }
}
```

## 🔧 核心方法

### 1. get_tech_readiness

#### 描述
获取项目技术成熟度信息。

#### 方法签名
```json
{
  "method": "get_tech_readiness",
  "params": {
    "project_id": "string"
  }
}
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| project_id | string | 是 | 项目唯一标识符 |

#### 响应

```json
{
  "project_id": "ai-auto-pilot-2024",
  "level": "prototype",
  "description": "基于深度学习的自动驾驶系统，已实现L3级别自动驾驶功能",
  "timeline": {
    "2024-Q1": "完成算法优化",
    "2024-Q2": "实车测试",
    "2024-Q3": "小批量生产",
    "2024-Q4": "商业化部署"
  },
  "milestones": [
    "算法模型训练完成",
    "封闭场地测试通过",
    "开放道路测试启动",
    "获得相关认证"
  ],
  "risks": [
    "算法安全性验证",
    "法规合规性",
    "硬件可靠性",
    "用户体验优化"
  ]
}
```

#### 技术成熟度等级

| 等级 | 描述 |
|------|------|
| concept | 概念阶段 |
| proof_of_concept | 概念验证 |
| prototype | 原型阶段 |
| pilot | 试点阶段 |
| production | 生产阶段 |

### 2. get_landing_requirements

#### 描述
获取项目落地要求信息。

#### 方法签名
```json
{
  "method": "get_landing_requirements",
  "params": {
    "location": "string",
    "industry": "string",
    "project_scale": "string"
  }
}
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| location | string | 是 | 目标地区 |
| industry | string | 是 | 行业类型 |
| project_scale | string | 否 | 项目规模 (small/medium/large) |

#### 响应

```json
{
  "location": "上海",
  "industry": "autonomous_driving",
  "requirements": [
    {
      "type": "资质要求",
      "description": "需要高新技术企业认证",
      "mandatory": true
    },
    {
      "type": "场地要求",
      "description": "研发场地面积不少于1000平方米",
      "mandatory": true
    }
  ],
  "incentives": [
    {
      "type": "税收优惠",
      "description": "企业所得税减免15%",
      "value": "15%"
    },
    {
      "type": "资金支持",
      "description": "最高500万研发补贴",
      "value": "最高500万"
    }
  ],
  "infrastructure": [
    "5G网络覆盖",
    "云计算平台",
    "测试验证中心",
    "产业园区配套"
  ],
  "timeline": {
    "审批": "1-2个月",
    "场地准备": "2-3个月",
    "测试验证": "3-6个月"
  }
}
```

#### 行业类型

| 类型 | 描述 |
|------|------|
| autonomous_driving | 自动驾驶 |
| embodied_ai | 具身智能 |
| robotics | 机器人技术 |
| ai_hardware | AI硬件 |
| quantum_computing | 量子计算 |

#### 项目规模

| 规模 | 描述 |
|------|------|
| small | 小型项目 |
| medium | 中型项目 |
| large | 大型项目 |

### 3. get_economic_and_compliance

#### 描述
获取项目经济合规信息。

#### 方法签名
```json
{
  "method": "get_economic_and_compliance",
  "params": {
    "project_id": "string",
    "region": "string",
    "compliance_level": "string"
  }
}
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| project_id | string | 是 | 项目唯一标识符 |
| region | string | 是 | 目标地区 |
| compliance_level | string | 否 | 合规级别 (basic/standard/enhanced) |

#### 响应

```json
{
  "project_id": "ai-auto-pilot-2024",
  "region": "上海",
  "compliance_status": "严格监管",
  "requirements": [
    {
      "category": "税务合规",
      "items": [
        "增值税一般纳税人资格",
        "企业所得税申报",
        "税务登记备案"
      ]
    },
    {
      "category": "工商合规",
      "items": [
        "营业执照年检",
        "企业年报公示",
        "经营范围变更"
      ]
    }
  ],
  "timeline": {
    "setup": "1-2周",
    "monthly": "每月",
    "quarterly": "每季度",
    "yearly": "每年"
  },
  "estimated_costs": {
    "setup": 50000,
    "monthly": 10000,
    "quarterly": 30000,
    "yearly": 100000
  },
  "risks": [
    "税务申报延误",
    "工商信息变更不及时",
    "劳动用工纠纷"
  ]
}
```

#### 合规级别

| 级别 | 描述 |
|------|------|
| basic | 基础合规 |
| standard | 标准合规 |
| enhanced | 增强合规 |

## 🔒 数据保护

### 访问控制

系统支持多级数据访问控制：

| 客户端类型 | 可访问数据级别 | 可访问字段 |
|-----------|---------------|-----------|
| public_client | 公开数据 | description, requirements, incentives, infrastructure |
| gov_client | 内部数据 | description, timeline, milestones, risks, requirements, incentives, infrastructure, compliance_status |
| partner_client | 机密数据 | 所有字段，除 technical_secrets 和 strategy_info |
| internal_client | 限制数据 | 所有字段 |

### 数据脱敏

敏感数据会被自动脱敏：

- 手机号: `138****1234`
- 邮箱: `user***@example.com`
- 身份证: `110101********1234`
- 银行账号: `6222****1234`
- 地址: `北京市**区**街道`

## 🧪 测试 API

### 使用 curl 测试

```bash
# 健康检查
curl http://localhost:8000/health

# 获取技术成熟度
curl -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_tech_readiness",
    "params": {"project_id": "ai-auto-pilot-2024"},
    "id": "test-001"
  }'

# 获取落地要求
curl -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_landing_requirements",
    "params": {
      "location": "上海",
      "industry": "autonomous_driving",
      "project_scale": "large"
    },
    "id": "test-002"
  }'

# 获取经济合规
curl -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_economic_and_compliance",
    "params": {
      "project_id": "ai-auto-pilot-2024",
      "region": "上海",
      "compliance_level": "standard"
    },
    "id": "test-003"
  }'
```

### 使用 Python 测试

```python
import requests
import json

# 健康检查
response = requests.get("http://localhost:8000/health")
print(response.json())

# 技术成熟度查询
data = {
    "jsonrpc": "2.0",
    "method": "get_tech_readiness",
    "params": {"project_id": "ai-auto-pilot-2024"},
    "id": "test-001"
}
response = requests.post("http://localhost:8000/rpc", json=data)
print(response.json())
```

## 📊 性能指标

- **响应时间**: < 100ms (95% of requests)
- **并发处理**: 1000+ requests/second
- **数据传输**: < 1MB per request
- **可用性**: 99.9%

## 🔧 错误处理

### 常见错误

1. **连接错误**
   ```json
   {
     "jsonrpc": "2.0",
     "error": {
       "code": -32603,
       "message": "Request failed: Connection error"
     },
     "id": "req-001"
   }
   ```

2. **参数错误**
   ```json
   {
     "jsonrpc": "2.0",
     "error": {
       "code": -32600,
       "message": "Missing required parameter: project_id"
     },
     "id": "req-001"
   }
   ```

3. **方法未找到**
   ```json
   {
     "jsonrpc": "2.0",
     "error": {
       "code": -32601,
       "message": "Method 'invalid_method' not found"
     },
     "id": "req-001"
   }
   ```

### 错误处理建议

1. 检查网络连接
2. 验证请求参数
3. 检查方法名称拼写
4. 查看服务器日志
5. 联系技术支持

## 📝 更新日志

### v1.0.0 (2024-01-01)

- 初始版本发布
- 支持 JSON-RPC 2.0 协议
- 实现三个核心方法
- 完整的数据保护机制
- 全面的测试覆盖

---

如有问题或建议，请通过 [GitHub Issues](https://github.com/your-org/open-invest-protocol/issues) 联系我们。