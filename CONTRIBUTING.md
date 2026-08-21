# 贡献指南

我们非常欢迎您为 Open Invest Protocol 项目做出贡献！🎉

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [测试要求](#测试要求)
- [提交规范](#提交规范)
- [问题报告](#问题报告)
- [功能请求](#功能请求)

## 🤝 行为准则

本项目采用贡献者契约行为准则。参与本项目即表示您同意遵守其条款。

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

- 友善和包容
- 尊重不同观点和经验
- 耐心接受建设性批评
- 关注社区最大利益

### 不当行为

不当行为包括：

- 使用性暗示语言或图像
- 网络暴力、人身攻击/贬低
- 公开或私人骚扰
- 未经明确许可发布他人信息
- 其他不适当的专业行为

### 执行

项目维护者有权删除、编辑或拒绝违反上述准则的贡献。项目维护者有权对违反准则的行为采取他们认为适当的任何行动。

## 🚀 如何贡献

### 报告 Bug

如果您发现了 bug，请通过 [GitHub Issues](https://github.com/your-org/open-invest-protocol/issues) 报告。

**报告模板：**
```markdown
## Bug 描述
简要描述 bug 的表现

## 复现步骤
1. 执行操作 A
2. 执行操作 B
3. 执行操作 C
4. 观察 bug 现象

## 期望行为
描述期望的正确行为

## 实际行为
描述实际发生的错误行为

## 环境信息
- 操作系统: [例如 Windows 10]
- Python 版本: [例如 3.8.5]
- 项目版本: [例如 1.0.0]
- 浏览器 (如果适用): [例如 Chrome 91]
```

### 提出新功能

如果您有新功能想法，请通过 [GitHub Issues](https://github.com/your-org/open-invest-protocol/issues) 提出。

**功能请求模板：**
```markdown
## 功能描述
详细描述您想要的功能

## 使用场景
描述这个功能将如何解决特定问题或满足特定需求

## 建议实现
提供您认为可能的实现方式或建议

## 替代方案
考虑过哪些替代方案？为什么选择当前方案？

## 额外信息
任何其他有助于理解功能的信息
```

### 贡献代码

#### 1. Fork 项目

```bash
# Fork 项目到您的 GitHub 账户
git clone https://github.com/your-username/open-invest-protocol.git
cd open-invest-protocol
```

#### 2. 创建功能分支

```bash
# 创建并切换到新分支
git checkout -b feature/amazing-feature
```

#### 3. 开发

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# 运行测试
pytest

# 格式化代码
black .

# 检查代码风格
flake8 .
```

#### 4. 提交更改

```bash
# 添加更改
git add .

# 提交更改
git commit -m "feat: add amazing feature"

# 推送到您的 fork
git push origin feature/amazing-feature
```

#### 5. 创建 Pull Request

1. 访问您的 GitHub fork 页面
2. 点击 "New Pull Request"
3. 选择源分支和目标分支
4. 填写 PR 描述
5. 点击 "Create Pull Request"

## 🛠️ 开发环境设置

### 系统要求

- Python 3.8+
- pip 或 conda
- Git

### 环境设置

```bash
# 克隆项目
git clone https://github.com/your-username/open-invest-protocol.git
cd open-invest-protocol

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov black flake8 mypy

# 运行测试确保一切正常
pytest
```

### IDE 配置

#### VS Code

创建 `.vscode/settings.json`：

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false
}
```

#### PyCharm

1. 打开项目
2. 设置 Python 解释器为虚拟环境
3. 配置代码风格为 Black
4. 配置测试运行器为 pytest

## 📝 代码规范

### Python 代码规范

我们遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范，并使用以下工具：

#### Black (代码格式化)

```bash
# 格式化所有 Python 文件
black .

# 格式化特定文件
black server/main.py

# 检查格式化
black --check .
```

#### Flake8 (代码检查)

```bash
# 检查代码风格
flake8 .

# 检查特定文件
flake8 server/main.py

# 忽略特定规则
flake8 --ignore=E203,W503
```

#### MyPy (类型检查)

```bash
# 类型检查
mypy .

# 类型检查特定文件
mypy server/main.py
```

### 命名规范

- **函数名**: 使用小写字母和下划线分隔
  ```python
  def get_tech_readiness():
      pass
  ```

- **变量名**: 使用小写字母和下划线分隔
  ```python
  project_id = "ai-auto-pilot-2024"
  ```

- **类名**: 使用 PascalCase
  ```python
  class TechReadinessService:
      pass
  ```

- **常量名**: 使用大写字母和下划线分隔
  ```python
  MAX_REQUEST_SIZE = 10 * 1024 * 1024
  ```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def calculate_tech_readiness_score(tech_info):
    """
    计算技术成熟度评分。
    
    Args:
        tech_info (Dict[str, Any]): 技术成熟度信息
        
    Returns:
        float: 技术成熟度评分 (0-100)
        
    Raises:
        ValueError: 当技术信息无效时
    """
    pass
```

### 注释

- 使用清晰的注释解释复杂的逻辑
- 注释应该解释 "为什么" 而不是 "是什么"
- 保持注释的更新

```python
# 使用快速排序算法对项目进行排序
# 时间复杂度: O(n log n)
def sort_projects_by_score(projects):
    pass
```

## 🧪 测试要求

### 测试覆盖率

- 新功能必须包含测试
- 测试覆盖率至少达到 80%
- 集成测试必须通过

### 测试类型

#### 单元测试

测试单个函数或方法：

```python
def test_get_tech_readiness_success():
    """测试成功获取技术成熟度"""
    service = TechReadinessService()
    result = asyncio.run(service.get_tech_readiness({"project_id": "test-project"}))
    
    assert result.project_id == "test-project"
    assert result.level == "prototype"
```

#### 集成测试

测试多个组件的交互：

```python
def test_server_client_integration():
    """测试服务端和客户端集成"""
    client = TestClient(app)
    
    # 测试技术成熟度查询
    response = client.post("/rpc", json={
        "jsonrpc": "2.0",
        "method": "get_tech_readiness",
        "params": {"project_id": "test-project"},
        "id": "test-001"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
```

#### 端到端测试

测试完整的工作流程：

```python
async def test_complete_workflow():
    """测试完整的工作流程"""
    # 1. 连接到服务器
    # 2. 获取技术成熟度
    # 3. 获取落地要求
    # 4. 获取经济合规
    # 5. 评估项目
    # 6. 生成报告
    pass
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/server/test_server.py

# 运行特定测试函数
pytest tests/server/test_server.py::TestServer::test_health_endpoint

# 生成覆盖率报告
pytest --cov=server --cov=client --cov-report=html

# 运行性能测试
pytest -m performance
```

## 📝 提交规范

### 提交消息格式

使用 [Conventional Commits](https://conventionalcommits.org/) 规范：

```bash
# 新功能
git commit -m "feat: add project evaluation functionality"

# 修复 bug
git commit -m "fix: resolve tech readiness calculation error"

# 文档更新
git commit -m "docs: update API documentation"

# 测试
git commit -m "test: add unit tests for landing requirements"

# 重构
git commit -m "refactor: improve data protection service"

# 样式
git commit -m "style: format code with black"

# 构建
git commit -m "build: update dependencies"

# 其他
git commit -m "chore: update README"
```

### 提交消息结构

```
<类型>(<范围>): <描述>

[可选的详细描述]

[可选的脚注]
```

#### 类型

- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 文档更新
- **style**: 代码格式化
- **refactor**: 重构
- **test**: 测试
- **build**: 构建系统或依赖变更
- **ci**: CI 配置变更
- **chore**: 其他不修改 src 或 test 文件的变更

#### 范围

- **server**: 服务端相关
- **client**: 客户端相关
- **schema**: 协议规范相关
- **docs**: 文档相关
- **test**: 测试相关
- ****: 全局变更

#### 描述

- 使用祈使句，现在时态
- 首字母小写
- 结尾不加句号

#### 详细描述

- 描述变更的动机
- 解释变更的影响
- 提供相关背景信息

#### 脚注

- **Closes #123**: 关闭 issue #123
- **Related to #456**: 相关 issue #456
- **Breaking Change**: 破坏性变更

### 分支管理

#### 主分支

- `main`: 稳定的发布版本
- `develop`: 开发版本

#### 功能分支

```bash
# 功能分支命名
feature/amazing-feature
feature/project-evaluation

# 修复分支命名
fix/bug-description
fix/server-error

# 文档分支命名
docs/api-documentation
docs/readme-update
```

### Pull Request 流程

#### 1. 创建 PR 前检查

- 所有测试必须通过
- 代码必须格式化
- 代码风格必须符合规范
- 文档必须更新

#### 2. PR 描述模板

```markdown
## 变更描述
简要描述这个 PR 的变更内容

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 重构
- [ ] 性能优化
- [ ] 其他

## 测试清单
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 端到端测试通过
- [ ] 手动测试完成

## 变更影响
- [ ] 破坏性变更
- [ ] 向后兼容
- [ ] 性能影响

## 相关 Issue
Closes #123

## 截图 (如果适用)
![截图描述](screenshot-url)
```

#### 3. PR 审查

- 等待至少一名维护者审查
- 及时响应审查意见
- 根据反馈进行修改
- 获得批准后合并

## 🐛 问题报告

### 创建 Issue 前检查

- 搜索现有 issues，避免重复
- 确认问题确实存在
- 提供足够的信息

### Issue 模板

```markdown
## 问题描述
简要描述问题

## 复现步骤
1. 执行操作 A
2. 执行操作 B
3. 执行操作 C
4. 观察问题

## 期望行为
描述期望的正确行为

## 实际行为
描述实际发生的错误行为

## 环境信息
- 操作系统: [例如 Windows 10]
- Python 版本: [例如 3.8.5]
- 项目版本: [例如 1.0.0]
- 浏览器 (如果适用): [例如 Chrome 91]

## 错误信息
```
错误信息
```

## 其他信息
任何其他有助于理解问题的信息
```

## 💡 功能请求

### 功能请求模板

```markdown
## 功能描述
详细描述您想要的功能

## 使用场景
描述这个功能将如何解决特定问题或满足特定需求

## 建议实现
提供您认为可能的实现方式或建议

## 替代方案
考虑过哪些替代方案？为什么选择当前方案？

## 额外信息
任何其他有助于理解功能的信息
```

## 📞 联系方式

如果您有任何问题，可以通过以下方式联系我们：

- GitHub Issues: [https://github.com/your-org/open-invest-protocol/issues](https://github.com/your-org/open-invest-protocol/issues)
- 邮箱: [contact@open-invest-protocol.org](mailto:contact@open-invest-protocol.org)

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT 许可证](LICENSE) 下发布。

---

感谢您对 Open Invest Protocol 项目的贡献！🎉