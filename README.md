# Open Invest Protocol

<div align="center">

![Open Invest Protocol](https://img.shields.io/badge/Open-Invest-Protocol-blue?style=for-the-badge&logo=github)
![Version](https://img.shields.io/badge/version-1.0.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-orange?style=for-the-badge)

**硬科技时代的"USB-C"：高科技项目方与政府招商局之间的安全合规互联协议**

[📖 文档](docs/README.md) • [🔧 快速开始](#快速开始) • [🧪 测试](#测试) • [📋 API](docs/API.md) • [🤝 贡献](CONTRIBUTING.md) • [🚀 加入我们](#加入我们)

</div>

---

## 🚀 加入我们

🚀 **Join the Open Invest Protocol Revolution!** 🚀

**Version 1.0 scaffold complete** (built with Python/FastAPI + secure multi-tier gateway) - **We're calling all hackers, AI pioneers, and policy tech wizards!** 

If you're passionate about **Embodied AI**, **Government LLMs**, or **Multi-Agent Protocols (MCP/A2A)**, this is your chance to co-define the open standard for hard-tech investment promotion!

**Let's build the future of intelligent cross-border collaboration, one protocol at a time.** 🤖🌐�️

---

## 🚀 项目简介

Open Invest Protocol 是一个开源的轻量级协议脚手架，旨在实现高科技项目方（Server）与政府招商局（Client）之间的安全、合规、标准化的 Agent 互联。

就像 USB-C 接口统一了设备连接一样，Open Invest Protocol 统一了高科技项目与地方政府之间的数据交互标准，让招商引资变得更加透明、高效、安全。

### 🎯 核心特性

- **🔒 安全合规**: 内置数据脱敏和访问控制，确保核心机密数据不出域
- **📋 标准化**: 基于 JSON-RPC 2.0 的标准化协议
- **🚀 高性能**: FastAPI 构建，支持高并发请求
- **🧪 可测试**: 完整的单元测试和集成测试覆盖
- **📊 智能评估**: 自动化项目评估和匹配算法
- **🌐 跨平台**: 支持多种客户端类型和访问权限

### 🏗️ 架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   高科技项目方   │    │   Open Invest   │    │   地方政府       │
│     (Server)     │◄──►│    Protocol     │◄──►│   招商局 (Client) │
│                 │    │     (Protocol)  │    │                 │
│ • AI自动驾驶     │    │                 │    │ • 项目评估       │
│ • 机器人技术     │    │ • 协议规范层    │    │ • 政策匹配       │
│ • 量子计算       │    │ • 数据保护层    │    │ • 合规审查       │
│ • 生物科技       │    │ • 服务实现层    │    │ • 投资决策       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 快速开始

### 环境要求

- Python 3.8+
- pip 或 conda

### 1. 克隆项目

```bash
git clone https://github.com/your-org/open-invest-protocol.git
cd open-invest-protocol
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务端

```bash
cd server
python main.py
```

服务端将在 `http://localhost:8000` 启动。

### 4. 运行客户端

```bash
cd client
python main.py
```

客户端将连接到服务端并生成招商引资评估报告。

### 5. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/server/test_server.py
pytest tests/client/test_client.py
pytest tests/integration/test_integration.py
```

## 🛠️ 核心功能

### 🔧 协议规范

基于 JSON-RPC 2.0 标准，定义了三个核心工具：

#### 1. get_tech_readiness
获取项目技术成熟度信息

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

#### 2. get_landing_requirements
获取项目落地要求信息

```json
{
  "jsonrpc": "2.0",
  "method": "get_landing_requirements",
  "params": {
    "location": "上海",
    "industry": "autonomous_driving",
    "project_scale": "large"
  },
  "id": "req-002"
}
```

#### 3. get_economic_and_compliance
获取项目经济合规信息

```json
{
  "jsonrpc": "2.0",
  "method": "get_economic_and_compliance",
  "params": {
    "project_id": "ai-auto-pilot-2024",
    "region": "上海",
    "compliance_level": "standard"
  },
  "id": "req-003"
}
```

### 🔒 数据保护

支持多级数据访问控制：

- **public_client**: 只能访问公开数据
- **gov_client**: 可以访问内部数据
- **partner_client**: 可以访问机密数据
- **internal_client**: 可以访问所有数据

### 📊 智能评估

自动化的项目评估系统，包括：

- 技术成熟度评分
- 落地要求匹配度
- 经济合规风险评估
- 综合评分和排名

## 📁 项目结构

```
open-invest-protocol/
├── schema/                    # 协议规范层
│   ├── api-spec.json          # OpenAPI 规范
│   └── types.py               # 数据类型定义
├── server/                    # 服务端实现
│   ├── main.py                # 主服务程序
│   ├── config/                # 配置管理
│   │   └── config.py
│   └── services/              # 业务逻辑
│       ├── tech_readiness_service.py
│       ├── landing_requirements_service.py
│       ├── economic_compliance_service.py
│       ├── data_protection.py
│       └── data_storage.py
├── client/                    # 客户端实现
│   ├── main.py                # 主客户端程序
│   ├── api/                   # API 客户端
│   │   └── protocol_client.py
│   └── utils/                 # 工具模块
│       └── project_evaluator.py
├── tests/                     # 测试套件
│   ├── server/                # 服务端测试
│   ├── client/                # 客户端测试
│   └── integration/           # 集成测试
├── docs/                      # 文档
│   ├── README.md              # 文档首页
│   ├── API.md                 # API 文档
│   └── examples/              # 示例代码
├── requirements.txt           # Python 依赖
├── pytest.ini                # 测试配置
└── README.md                  # 项目说明
```

## 🧪 测试

项目包含完整的测试套件：

```bash
# 运行所有测试
pytest

# 运行特定测试类别
pytest -m unit          # 单元测试
pytest -m integration   # 集成测试
pytest -m slow         # 慢速测试

# 生成测试覆盖率报告
pytest --cov=server --cov=client --cov-report=html
```

### 测试覆盖

- ✅ 服务端 API 测试
- ✅ 客户端功能测试
- ✅ 数据保护测试
- ✅ 并发性能测试
- ✅ 错误处理测试
- ✅ 端到端工作流测试

## 📖 使用示例

### 服务端示例

```python
from server.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 获取技术成熟度
response = client.post("/rpc", json={
    "jsonrpc": "2.0",
    "method": "get_tech_readiness",
    "params": {"project_id": "ai-auto-pilot-2024"},
    "id": "test-001"
})

print(response.json())
```

### 客户端示例

```python
from client.api.protocol_client import ProtocolClient
from client.utils.project_evaluator import ProjectEvaluator

# 创建客户端
client = ProtocolClient("http://localhost:8000")
evaluator = ProjectEvaluator(client)

# 评估项目
result = await evaluator.evaluate_project(
    "ai-auto-pilot-2024", 
    "上海", 
    "standard"
)

print(f"项目评分: {result.overall_score}")
print(f"匹配等级: {result.match_level}")
```

## 🔧 配置

### 环境变量

```bash
# 服务端配置
export OIP_HOST=localhost
export OIP_PORT=8000
export OIP_DEBUG=true
export OIP_DATA_DIR=./data

# 客户端配置
export OIP_CLIENT_TYPE=gov_client
```

### 配置文件

服务端配置文件位于 `server/config/config.py`：

```python
class ServerConfig:
    host: str = "localhost"
    port: int = 8000
    debug: bool = True
    data_dir: str = "./data"
    max_request_size: int = 10 * 1024 * 1024  # 10MB
```

## 🤝 贡献

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 规范
- 编写测试用例
- 更新文档
- 确保所有测试通过

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和组织。

## 📞 联系我们

- 项目主页: https://github.com/your-org/open-invest-protocol
- 问题反馈: https://github.com/your-org/open-invest-protocol/issues
- 邮箱: contact@open-invest-protocol.org

---

<div align="center">

**让高科技项目与政府的连接更加简单、安全、高效**

⭐ 如果这个项目对你有帮助，请给我们一个 Star！

</div>