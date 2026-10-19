# 贡献指南

## 开发环境

使用 Python 3.9 或更新版本。在仓库根目录安装离线开发依赖：

```powershell
python -m pip install -e '.[all,dev]'
```

运行纯离线检查并构建发行包：

```powershell
python -m pytest
python -m build --sdist --wheel
```

基础 CI 不安装 CST、不打开 CST 工程，也不运行电磁求解。测试需要几何、科学或 YAML 可选项时，应把依赖列在对应 extra 中。

## 跨包联调

TPC 的 `cst` extra 声明 `cst-automation>=0.1,<1`。本地跨包联调应使用与 TPC 同目录的 `cst-automation` checkout 或其本地构建 wheel；不要假设该私有包已发布到 PyPI。将底层发行 wheel 安装进隔离环境后，运行 `tests/test_cst_automation_integration.py`。这项测试使用 `FakeBackend`，只验证 handler 注册和服务分派，不验证 CST。

## 变更要求

- 保持既有 Python 导入名，除非先更新接口约定和迁移文档。
- 离线算法、几何构建、结果读取、CST readback 和实际 solver 证据分别记录。
- CST 会话只在用户显式调用真实 CST 操作时创建；拓扑包不复制通用 service、MCP 或曲线/S 参数实现。
- 新功能附离线测试；修改领域接口时同步更新 `docs/API_AND_SUPPORT.md`、`docs/VALIDATION.md` 和相关 skills。
- 不加入来源或再分发许可不清楚的工程、SAT、模型或实验产物。
