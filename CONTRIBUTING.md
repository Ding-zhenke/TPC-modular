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

TPC 的 `cst` extra 声明 `cst-automation>=0.1,<1`。本地联调使用相邻 checkout 构建的 wheel 或已有兼容 wheel。在隔离开发环境安装 TPC 与底层发行包后，显式选择跨包测试：

```powershell
python -m pytest -m integration tests/test_cst_automation_integration.py
```

默认配置排除 integration。核对汇总中该用例实际执行并通过；它覆盖 FakeBackend 的 handler 注册和服务分派。

## 变更要求

遵循[项目约定](AGENTS.md)中的接口兼容、发布和证据要求。新功能附离线测试。领域接口变更时同步更新[支持矩阵](docs/API_AND_SUPPORT.md)、[验证记录](docs/VALIDATION.md)和相关 skill。
