# Open Invest Protocol

<div align="center">

![Open Invest Protocol](https://img.shields.io/badge/Open-Invest-Protocol-blue?style=for-the-badge&logo=github)
![Version](https://img.shields.io/badge/version-3.1.0-gold?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-orange?style=for-the-badge)
![Build](https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge)
![Contributors](https://img.shields.io/badge/contributors-wanted-red?style=for-the-badge)

**The Open Standard for Borderless High-Tech Investment & Cross-Border Compliance**  
*The USB-C for DeepTech • Zero Data Leakage • Agent-to-Agent (A2A) Planned*

[📖 Docs](docs/API.md) • [🚀 Quick Start](#-quick-start) • [🧪 Tests](#-testing) • [📡 API](docs/API.md) • [🤝 Contribute](CONTRIBUTING.md) • [🌍 Join Us](#-join-the-revolution)

</div>

---

## 🚀 The Open Protocol for Borderless DeepTech Investment

**Open Invest Protocol** is the open-source protocol for borderless DeepTech investment and alignment, connecting High-Tech Innovators (Server) with Global Capital & Government Ecosystems (Client).

Like USB-C unified device connectivity and TCP/IP unified network communication, **Open Invest Protocol unifies the data exchange standards between DeepTech projects and global governments**, making cross-border investment promotion transparent, efficient, and secure.

### 🎯 Core Value Proposition

- **🔌 The USB-C for DeepTech**: Universal standard connecting AI, robotics, quantum computing, and biotech projects with global governments
- **🔒 Zero Data Leakage** *(PROTOTYPE)*: Built-in data anonymization utilities (`client/hooks/ai_agent_direct_apply.py::SecurityGateway`) — functional demo, not audited for production
- **🤖 Agent-to-Agent (A2A)** *(PLANNED)*: Multi-agent protocols (MCP/A2A) are a roadmap item; no MCP/A2A implementation exists in this repository yet
- **🌐 Borderless Compliance** *(PROTOTYPE)*: Structured policy intelligence — current seed coverage: 12 policy records across 10 regions (China-focused); global expansion is a target, not a verified fact
- **⚡ FastAPI-Powered** *(UNVERIFIED)*: Built on FastAPI. Performance targets (10,000+ concurrent queries, sub-100ms response) are benchmark goals; no load-test evidence exists yet
- **🎯 Data-Led Growth**: Global policy intelligence engine serving as bait pool to attract global DeepTech projects

> **Reality Status Legend** (used throughout this README):  
> **IMPLEMENTED** = code exists with runnable tests/verification • **PARTIALLY IMPLEMENTED** = code exists with notable gaps • **SCAFFOLDED** = structure/interfaces only • **PROTOTYPE** = runnable demo, not production-grade • **PLANNED** = design/roadmap only • **UNVERIFIED** = code may exist but correctness/performance lacks evidence

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip or conda
- Docker (optional for production)

### 1. Clone & Install

```bash
git clone https://github.com/gzchenhao/open-invest.git
cd open-invest
pip install -r requirements.txt
```

### 2. Start Server

```bash
cd server
python main.py
```

Server starts at `http://localhost:8000` with comprehensive API documentation.

### 3. Run Client

```bash
cd client
python main.py
```

Client connects to server and generates global investment matching reports.

### 4. Test Everything

```bash
# Run all tests (regression gate — minimum verification command)
python -m pytest tests/ -q

# Run specific test suites
python -m pytest tests/server/test_server.py -q
python -m pytest tests/client/test_client.py -q
python -m pytest tests/integration/test_integration.py -q
```

---

## 🛠️ Core Protocol Features

### 🔧 JSON-RPC 2.0 Interface

Standardized protocol defining three core tools:

#### 1. get_tech_readiness
Retrieve project technology readiness level

```json
{
  "jsonrpc": "2.0",
  "method": "get_tech_readiness",
  "params": {
    "project_id": "ai-auto-pilot-2024",
    "industry": "autonomous_driving",
    "trl_level": "prototype"
  },
  "id": "req-001"
}
```

#### 2. get_landing_requirements
Get global landing requirements and incentives

```json
{
  "jsonrpc": "2.0",
  "method": "get_landing_requirements",
  "params": {
    "location": "Shanghai",
    "industry": "quantum_computing",
    "project_scale": "large",
    "incentive_types": ["tax_break", "subsidy", "land_grant"]
  },
  "id": "req-002"
}
```

#### 3. get_economic_and_compliance
Access economic compliance and risk assessment

```json
{
  "jsonrpc": "2.0",
  "method": "get_economic_and_compliance",
  "params": {
    "project_id": "ai-auto-pilot-2024",
    "region": "Shanghai",
    "compliance_level": "enhanced",
    "export_controls": true
  },
  "id": "req-003"
}
```

### 🔒 Multi-Tier Data Protection *(PARTIALLY IMPLEMENTED)*

Tiered CORS access control is implemented in `server/main.py` (public/gov/partner/internal tiers). Full authentication and authorization enforcement is **not yet implemented**:

- **public_client**: Public policy data only
- **gov_client**: Internal government data access
- **partner_client**: Confidential project data access
- **internal_client**: Full system access

### 🌍 Global Policy Intelligence

Structured policy intelligence — current seed coverage: **12 policy records across 10 regions** (China high-tech zones; global expansion is PLANNED):

- **Tax Incentives**: R&D tax credits, corporate tax breaks
- **Subsidies**: Computing power subsidies, factory rent reductions
- **Landing Requirements**: R&D staff ratios, patent requirements
- **Compliance Standards**: Export controls, data localization laws

---

## 🏗️ Architecture Overview

```
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│   DeepTech Innovators  │    │   Open Invest Protocol   │    │   Global Capital &     │
│       (Server)         │◄──►│     (Protocol Layer)    │◄──►│   Government Ecosystems │
│                       │    │                       │    │       (Client)          │
│ • AI/ML Startups       │    │                       │    │                       │
│ • Robotics Companies   │    │ • Protocol Specification│    │ • Investment Agencies  │
│ • Quantum Computing    │    │ • Data Protection      │    │ • Government Bodies    │
│ • Biotech Firms       │    │ • Policy Intelligence  │    │ • Special Economic     │
└─────────────────────────┘    │ • A2A Agent Interface   │    │   Zones               │
                                │        (PLANNED)        │    └─────────────────────────┘
                                └─────────────────────────┘
                                       ▲       ▲       ▲
                                       │       │       │
                               ┌───────┴───────┴───────┴───────┐
                               │   Policy Crawler Engine        │
                               │   (Data-Led Growth Bait Pool)  │
                               └─────────────────────────────────┘
```

---

## 📁 Project Structure

```
open-invest/
├── schema/                       # Protocol Specification Layer
│   ├── api-spec.json             # OpenAPI 3.0 Specification
│   └── types.py                  # Pydantic Protocol Types (JSON-RPC models)
├── server/                       # Server Implementation (IMPLEMENTED, 25 endpoint tests)
│   ├── main.py                   # FastAPI entry, JSON-RPC 2.0 `/rpc` endpoint, tiered CORS
│   ├── config/
│   │   └── config.py
│   └── services/                 # Business Logic
│       ├── tech_readiness_service.py
│       ├── landing_requirements_service.py
│       ├── economic_compliance_service.py
│       ├── data_protection.py
│       └── data_storage.py
├── client/                       # Client Implementation (IMPLEMENTED, 17 tests)
│   ├── main.py                   # CLI client: investment matching report
│   ├── api/
│   │   └── protocol_client.py
│   ├── utils/
│   │   └── project_evaluator.py
│   └── hooks/
│       └── ai_agent_direct_apply.py  # SecurityGateway anonymization prototype
├── policy_crawler/               # Original Policy Crawler Engine (PROTOTYPE)
│   ├── crawlers/                 # china / eu / silicon_valley / singapore
│   ├── processors/               # policy_cleaner / data_structurer / intelligence_aggregator
│   ├── schemas/                  # policy_schema.json + domain schemas
│   └── data/                     # raw_policies/ + structured_policies/ (mock/sample data)
├── global_policy_aggregator/     # China Policy Intelligence Engine (PROTOTYPE)
│   ├── crawlers/                 # 5 China-focused crawlers + crawler engine
│   ├── processors/
│   │   └── policy_cleaner.py
│   ├── schemas/                  # incl. deeptech_policy_schema.json
│   ├── web/
│   │   └── interactive_ai_server.py  # FastAPI Web Portal + PDF generation
│   ├── data/                     # raw_policies/ + seed_data/ + structured_policies/
│   ├── services/  agents/  scripts/  cleaned_data/
│   └── test_api.ps1              # PowerShell API test script
├── tests/                        # Test Suite (68 tests, regression gate)
│   ├── server/                   # Server endpoint tests
│   ├── client/                   # Client logic tests
│   └── integration/              # End-to-end server+client tests
├── docs/                         # Documentation
│   ├── API.md                    # API Documentation
│   └── examples/                 # Example scripts (basic_usage, ai_agent_direct_apply, ...)
├── marketing/                    # Marketing & Launch Kit
├── requirements.txt              # Python Dependencies
├── pytest.ini                    # Test Configuration (regression gate)
├── Qoder_Technical_Handover_20260824.md  # AI Handover Constitution (read this first)
└── README.md                     # Project Documentation
```

**Planned (not yet in repository)**: `a2a_protocol_handler.py` (MCP/A2A), `policy_intelligence_service.py`, `policy_matcher.py`, `tests/policy/`, `tests/performance/`, `docker-compose.yml` — see the Roadmap in the Handover Constitution.

---

## 🧪 Testing

Regression gate for every change (minimum verification command):

```bash
# Regression gate — must pass before any further development
python -m pytest tests/ -q

# Collection check only
python -m pytest tests/ --collect-only -q

# Coverage report (requires pytest-cov)
python -m pytest tests/ --cov=. --cov-report=term -q
```

### Current Test Reality (verified 2026-08-24)

- ✅ Server API endpoints — 25 tests
- ✅ Client functionality — 17 tests
- ✅ End-to-end integration (real server + client) — 26 tests
- ✅ Data anonymization (`SecurityGateway`) — covered by client tests
- ⬜ A2A protocol interfaces — PLANNED (no implementation, no tests)
- ⬜ Performance benchmarks — PLANNED (no load tests)
- ⬜ Security penetration tests — PLANNED (no security test suite)

**Current result**: 68 passed, 0 failed • **Coverage**: 67% TOTAL (2114 statements)

---

## 🌍 Global Policy Intelligence Engine

### Policy Data Schema Design

```json
{
  "policy_schema": {
    "incentives": {
      "tax_breaks": {
        "description": "Corporate tax incentives for R&D",
        "schema": {
          "rate_reduction": "float",
          "duration_years": "int",
          "eligibility_criteria": "string[]"
        }
      },
      "subsidies": {
        "description": "Direct financial subsidies",
        "schema": {
          "amount_usd": "float",
          "purpose": "string",
          "application_deadline": "date"
        }
      }
    },
    "requirements": {
      "staffing": {
        "min_researchers": "int",
        "phd_percentage": "float",
        "experience_years": "int"
      },
      "intellectual_property": {
        "patent_count": "int",
        "trademarks": "int",
        "copyrights": "int"
      }
    },
    "compliance": {
      "data_localization": "boolean",
      "export_controls": "boolean",
      "security_clearance": "string"
    }
  }
}
```

### Mock Policy Database & Cleaning Service

```python
# global_policy_aggregator/processors/policy_cleaner.py
class PolicyCleaner:
    """Clean and structure global policy data"""
    
    def clean_policy_text(self, raw_policy_text: str) -> StructuredPolicy:
        """Convert raw policy text to structured format"""
        # 1. Extract key information using NLP
        incentives = self._extract_incentives(raw_policy_text)
        requirements = self._extract_requirements(raw_policy_text)
        compliance = self._extract_compliance(raw_policy_text)
        
        # 2. Validate against schema
        validated_policy = self._validate_policy_schema({
            "incentives": incentives,
            "requirements": requirements,
            "compliance": compliance
        })
        
        # 3. Enrich with metadata
        enriched_policy = self._enrich_policy_metadata(validated_policy)
        
        return enriched_policy
```

---

## 🤖 AI Agent Direct Apply Integration

### Integration Hook Example

```python
# client/hooks/ai_agent_direct_apply.py
class AIAgentDirectApply:
    """AI Agent Direct Apply integration hook"""
    
    def __init__(self, protocol_client: ProtocolClient):
        self.client = protocol_client
        self.security_gateway = SecurityGateway()
    
    async def direct_apply(self, project_id: str, policy_id: str) -> ApplyResult:
        """
        Trigger direct application through secure gateway
        """
        # 1. Retrieve project data (anonymized)
        project_data = await self.client.get_tech_readiness(project_id)
        
        # 2. Retrieve target policy
        policy_data = await self.client.get_landing_requirements(
            location=policy_id,
            industry=project_data["industry"]
        )
        
        # 3. Apply data anonymization
        anonymized_data = self.security_gateway.anonymize(project_data)
        
        # 4. Secure transmission to target client
        apply_result = await self.security_gateway.transmit(
            source_data=anonymized_data,
            target_policy=policy_data,
            encryption_level="enhanced"
        )
        
        return apply_result
```

### Usage Example

```python
# docs/examples/ai_agent_direct_apply.py
from client.api.protocol_client import ProtocolClient
from client.hooks.ai_agent_direct_apply import AIAgentDirectApply

# Initialize client
client = ProtocolClient("https://api.open-invest.org")
direct_apply = AIAgentDirectApply(client)

# Browse policies and trigger direct apply
policy_id = "shanghai-quantum-hub-2024"
project_id = "quantum-encryption-startup-2024"

result = await direct_apply.direct_apply(project_id, policy_id)

print(f"Application Status: {result.status}")
print(f"Match Score: {result.match_score}")
print(f"Next Steps: {result.next_steps}")
```

---

## 🌐 Web Interface & Policy Intelligence Portal

### Interactive Policy Query System

Access the web-based policy intelligence portal at `http://localhost:8017` (after starting the server):

```bash
cd global_policy_aggregator/web
python interactive_ai_server.py
```

**Features**:
- 🔍 **Smart Search**: Full-text search across policy titles, regions, industries, and descriptions
- 🏷️ **Region Filter**: Filter policies by high-tech zones (Beijing Zhongguancun, Shanghai Zhangjiang, Shenzhen High-Tech Park, etc.)
- 📄 **PDF Download**: Download structured policy documents with official contact information
- 📞 **Official Contacts**: Every policy card displays government contact details (department, phone, email, address)
- 🎯 **Policy Claim System**: Government bodies can claim and maintain their policy listings
- 📊 **12 Pre-loaded Policy Records**: Seed data from 10 major Chinese high-tech zones (mock/seed data, marked in code)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Get system statistics (total policies, regions, industries) |
| `/api/search` | POST | Search policies with JSON body `{"keywords": "AI", "limit": 10}` |
| `/api/policy/{id}/pdf` | GET | Download policy document as PDF |

### Testing the API

```powershell
# Run the test suite
cd global_policy_aggregator
powershell -ExecutionPolicy Bypass -File test_api.ps1

# Or test manually
Invoke-RestMethod -Uri 'http://localhost:8017/api/stats' -Method GET
```

---

## 🚀 Join the Revolution

🚀 **Join the Open Invest Protocol Revolution!** 🚀

**Version 3.1.0 with Web Portal & PDF Generation** (built on Python/FastAPI with a tiered-CORS gateway prototype + Global Policy Intelligence Engine + Interactive Web Interface) - **We're calling all hackers, AI pioneers, and policy tech wizards!** 

This project has completed its 3.1 **prototype** implementation (built on Python/FastAPI with a tiered-CORS gateway prototype, interactive web portal, and PDF policy document generation; full security/auth layer and MCP/A2A are PLANNED). We warmly invite developers interested in embodied AI, government-facing large models, and multi-agent protocols (MCP/A2A) to join us in co-building and defining the open standard for high-tech industrial investment and alignment!

**Let's build the future of intelligent cross-border collaboration, one protocol at a time.** 🤖🌐🚀

---

## 📡 API Documentation

- [OpenAPI 3.0 Specification](schema/api-spec.json)
- [Protocol Types](schema/types.py)
- [Policy Intelligence Schema](global_policy_aggregator/schemas/deeptech_policy_schema.json)

## 🤝 Contributing

We welcome all forms of contribution! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the project
2. Create feature branch (`git checkout -b feature/global-compliance`)
3. Commit changes (`git commit -m 'feat: add EU compliance standards'`)
4. Push to branch (`git push origin feature/global-compliance`)
5. Create Pull Request

### Code Standards

- Follow PEP 8 guidelines
- Write comprehensive tests
- Update documentation
- Ensure all tests pass
- Run security checks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Thank you to all contributors and organizations supporting the Open Invest Protocol initiative.

## 👥 Contributors

Thanks to all the amazing people who have contributed to this project:

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/gzchenhao">
        <img src="https://github.com/gzchenhao.png?size=100" width="100px;" alt="gzchenhao"/>
        <br />
        <sub><b>gzchenhao</b></sub>
      </a>
      <br />
      <sub>Project Lead & Core Developer</sub>
    </td>
  </tr>
</table>

*Want to contribute? Check out our [contributing guidelines](CONTRIBUTING.md) and join the revolution!*

## 📞 Contact Us

- Project Homepage: https://github.com/gzchenhao/open-invest
- Issues: https://github.com/gzchenhao/open-invest/issues
- Email: contact@open-invest.org
- Discord: [Join our community](https://discord.gg/open-invest)

---

<div align="center">

**Making Borderless DeepTech Investment Possible**  
*The USB-C for High-Tech Innovation Across Borders*

⭐ If this project advances borderless DeepTech innovation, give us a star!

</div>