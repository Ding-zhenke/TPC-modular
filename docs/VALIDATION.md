# 验证记录

状态：TPC 离线迁移、包构建、安装和 `cst-automation` handler 跨包分派已完成本地验证。所有 CST 实机 readback、几何 rebuild 和实际电磁求解仍未运行。

## 源状态与迁移说明

- 迁移源 HEAD：`51e4a63d302f0deea58d2a2df349892087dbfe7`。
- `work/source-snapshot/` 仅保存 tracked/staged diff、status 和未跟踪路径清单，未跟踪源码/文档的文件内容没有复制进快照；源仓库原文件保持原处。
- 源只读约束是在源状态读取后补充。此前普通 `git status --short` 未使用 `--no-optional-locks`，Git 可能刷新源 `.git/index` 统计缓存；没有在源仓库运行 import/test/build/install，也没有主动改写源文件，无法确认是否触及 index，未做恢复/清理。
- 此前一次全局 Python 测试经 editable hook 导入过源仓库 `cst_solver`，Python 可能在源目录生成 `__pycache__`；后续没有访问或清理旧源目录，之后的验证已过滤该 editable hook。
- TPC builder 的参数前置检查已从私有 `cst_solver._guards` 移除，改为调用公开 `setup.get_parameter()`。实际 `cst-automation` wheel 的 `setup` 类型包含该方法；没有在真实 CST session 调用该方法。

## 已完成验证

| 检查 | 命令/方法 | 结果 |
|---|---|---|
| TPC 离线与兼容测试 | `python work/run_clean_pytest.py`；`python -m pytest -q -m 'not integration' --basetemp=work/pytest-ci` | 两种运行均通过，覆盖 `mesh_grid/tri_grid/tests`、`topo_modeler/tests`、`topo_templates/tests`、`tests`；integration 标记由基础测试排除。出现一条外部 fontTools deprecation warning。 |
| 参数缺失前置检查 | `python -m pytest topo_modeler/tests/test_multiport_feed.py topo_modeler/tests/test_probe_hole_array.py topo_modeler/tests/test_grin_lens_insitu.py -q` | 58 项通过。测试使用 `get_parameter()` fake，不依赖 `_guards` 私有模块。 |
| handler 跨包注册与分派 | 隔离 venv 安装两个本地 wheel 后，在 `work/isolated-run` 运行 `..\\venv-cross\\Scripts\\python.exe -I run_cross.py` | 通过，1 项。运行时 `cst_solver`、`tpc_service` 和 `mesh_grid` 均从 `work/venv-cross/Lib/site-packages` 加载。使用 `FakeBackend` 验证服务注册和 solve handler 分派；不代表 CST solve/readback。 |
| `get_parameter` API 符号 | 在同一隔离 venv 检查 `from cst_solver import setup; hasattr(setup, 'get_parameter')` | 为 `True`。未打开 CST，也未查询 CST 工程参数。 |
| wheel/sdist 构建 | `python -m build --no-isolation --sdist --wheel --outdir work/dist` | 成功生成 `tpc_topology-0.1.0.tar.gz` 与 `tpc_topology-0.1.0-py3-none-any.whl`。本机 setuptools 发现可选 `bdist_conda` entry point 缺其 conda 模块并输出非致命警告。 |
| 发行清单边界 | `work/check_artifacts.py` 检查最终 wheel/sdist | wheel 53 项、sdist 98 项；未发现 `cst_solver`、`tpc_service`、`cst_mcp`、`em_enclosure`、`__pycache__` 或 `.pyc`；sdist 包含 `docs/README.md` 和 skills，wheel 不包含文档/skills。 |
| README 离线示例 | `TopoPath` 构造、`TopoModeler()` 构造与 `close()` | 通过；不触发 CST 初始化。不要调用未配置模型的 `validate()` 并期待返回通过。 |
| 隔离构建模式 | `python -m build --sdist --wheel --outdir work/dist` | 未通过：本机隔离环境初始化时 `ensurepip` 遇 Unicode decode error。改用已安装 build/setuptools 的 `--no-isolation` 成功。 |

## 未验证边界

| 能力 | 状态 |
|---|---|
| CST 参数查询、建模器对真实工程执行 rebuild、结果文件 readback | 未运行；只确认 API 符号存在，fake tests 只验证分支行为。 |
| 真实 CST 求解与收敛 | 未运行。 |
| 拓扑带隙、Chern 数、单向传输、器件隔离性能 | 没有由本次代码迁移或离线测试证明。 |
| handler 的 `build`/`study` 在真实 CST 下执行 | 未运行；跨包测试只验证注册以及 `solve` 经 `FakeBackend` 的服务分派。 |

离线测试、wheel 安装和 fake backend 只支持其覆盖范围内的 Python/API 结论，不能升级为 CST 几何或电磁性能证据。
