# 验证记录

状态：TPC 离线迁移、包构建、安装和 `cst-automation` handler 跨包分派已完成本地验证。所有 CST 实机 readback、几何 rebuild 和实际电磁求解仍未运行。

## TPC 六技能插件（2026-10-30）

新增 `tpc` 插件入口，根清单与 Codex 兼容清单共用 `skills/`，本地市场标识 `tpc-local`。插件构建白名单包含现有 Python 源码与许可证；没有加入通用 CST 驱动或 MCP。

| 检查 | 实际结果 |
|---|---|
| 六项技能 frontmatter | `skill-creator/scripts/quick_validate.py` 全部通过；Windows 使用 `-X utf8` 读取中文 |
| 插件打包/可移植测试 | 7 项通过；包含解压后导入、技能本地引用、无私有目录/大工程（含嵌套缓存目录）、只读运行环境检查、错误 extra 前置拒绝、损坏导入/过低版本识别及离线冒烟 |
| 完整离线回归 | 最终 `python -m pytest --basetemp=work/pytest-plugin-final --tb=short`：545 passed、1 deselected；1 条外部 fontTools deprecation warning |
| 解压后的插件冒烟 | 六个技能入口，三角路径 PNG、六边 DXF、功分器配置预检、合成 S21 指标、两点扫描 HTML/CSV、连续优化及等效介质计算通过；代码确实来自解压目录，未导入 CST |
| 独立参考技能使用 | 新上下文使用模板、分析、优化三个技能，在插件之外创建任务脚本并执行通过；53 个本地文档链接无断链；发现并修正运行环境输出中工作目录指引不一致 |
| 全新 Python 环境 | `plugin_runtime.py --prepare` 创建独立 venv，基础依赖与 geometry/science/yaml 安装成功；在新环境运行解压包冒烟全部通过 |
| Python wheel/sdist | 独立构建环境成功构建；sdist 包含两个插件清单、本地市场配置、三个脚本与全部六个技能；wheel 保持原 Python 模块发行边界 |
| 旧独立技能冲突检查 | 用户技能目录中的三个同名技能与仓库原版完全一致，无用户自定义差异；安装成功后备份停用以避免重复加载 |
| 本机实际安装 | 原生 `codex plugin marketplace add` / `plugin add` 成功；`plugin list --marketplace tpc-local --json` 返回 `tpc@tpc-local`、版本 0.1.0、installed=true、enabled=true；缓存内六项技能完整 |
| 仓库外技能发现 | 实际调用本机 Codex `skills/list`，工作目录位于仓库之外；返回六项 `tpc:<skill-name>`，全部 enabled=true；没有创建聊天或调用模型 |
| 安装缓存运行 | 在全新独立 Python 环境执行真实安装缓存里的 `verify_plugin.py`，全部离线例子通过，模块来源确实是用户插件缓存而非开发目录 |

当前合成分析数值：110 GHz 的 `S2,1` 为 −6.0205999133 dB（幅度 0.5）；两个扫描点共用该合成曲线。优化数学例子的 seed=7，4 次评估得到 length=16、目标值 4，不是器件优化性能。

本次早期 Python 包构建尝试使用本机旧 setuptools 65.5.0，不能解析现有 `license="MIT"` 格式；随后使用独立构建环境安装新版构建工具。该环境问题与插件 ZIP 无关，不修改用户全局 Python。

独立代码审阅发现并修正两项问题：白名单目录内嵌套 `work/build/dist/venv` 文件可能进入发布包；`find_spec()` 可能把损坏模块误报为可用。对应回归先复现失败，再验证通过。

原三个独立技能已移到用户技能目录之外的 `~/.codex/skill-backups/tpc-plugin-20261030/`，可恢复，未删除。已运行的聊天可能保留旧技能上下文，安装后开新聊天使用插件；若插件界面未刷新再重启应用。

真实 CST 参数表读回、几何 rebuild、电磁求解与器件性能验证没有因插件打包而新增。

## 源状态与迁移说明

- 迁移源 HEAD：`51e4a63d302f0deea58d2a2df349892087dbfe7`。
- `work/source-snapshot/` 仅保存 tracked/staged diff、status 和未跟踪路径清单，未跟踪源码/文档的文件内容没有复制进快照；源仓库原文件保持原处。
- 源只读约束是在源状态读取后补充。此前普通 `git status --short` 未使用 `--no-optional-locks`，Git 可能刷新源 `.git/index` 统计缓存；没有在源仓库运行 import/test/build/install，也没有主动改写源文件，无法确认是否触及 index，未做恢复/清理。
- 此前一次全局 Python 测试经 editable hook 导入过源仓库 `cst_solver`，Python 可能在源目录生成 `__pycache__`；后续没有访问或清理旧源目录，之后的验证已过滤该 editable hook。
- TPC builder 的参数前置检查已从私有 `cst_solver._guards` 移除，改为调用公开 `setup.get_parameter()`。实际 `cst-automation` wheel 的 `setup` 类型包含该方法；没有在真实 CST session 调用该方法。

## 已完成验证

| 检查 | 命令/方法 | 结果 |
|---|---|---|
| TPC 离线与兼容测试 | `python -m pytest -q -m 'not integration' --basetemp=work/pytest-ci-final` | 538 项通过，1 项 integration 测试按 CI 设计排除；覆盖 `mesh_grid/tri_grid/tests`、`topo_modeler/tests`、`topo_templates/tests`、`tests`。出现一条外部 fontTools deprecation warning。 |
| ResultReader 离线错误顺序 | 阻止 `cst_solver` 导入，再测试缺失和存在的 `.cst` 路径 | 专项 27 项通过；缺失路径先报文件不存在且未尝试导入，存在路径仍给安装依赖提示。 |
| ResultReader 最终 wheel 回归 | 隔离 venv 从 `site-packages` 导入最终 wheel，并在脚本内阻止 `cst_solver` | 通过；缺失路径不触发 CST 导入且报告文件不存在，存在路径报告依赖安装提示。 |
| 参数缺失前置检查 | `python -m pytest topo_modeler/tests/test_multiport_feed.py topo_modeler/tests/test_probe_hole_array.py topo_modeler/tests/test_grin_lens_insitu.py -q` | 58 项通过。测试使用 `get_parameter()` fake，不依赖 `_guards` 私有模块。 |
| handler 跨包注册与分派 | 隔离 venv 安装两个本地 wheel 后，在 `work/isolated-run` 运行 `..\\venv-cross\\Scripts\\python.exe -I run_cross.py` | 通过，1 项。运行时 `cst_solver`、`tpc_service` 和 `mesh_grid` 均从 `work/venv-cross/Lib/site-packages` 加载。使用 `FakeBackend` 验证服务注册和 solve handler 分派；不代表 CST solve/readback。 |
| `get_parameter` API 符号 | 在同一隔离 venv 检查 `from cst_solver import setup; hasattr(setup, 'get_parameter')` | 为 `True`。未打开 CST，也未查询 CST 工程参数。 |
| wheel/sdist 构建 | `python -m build --no-isolation --sdist --wheel --outdir work/dist` | 成功生成 `tpc_topology-0.1.0.tar.gz` 与 `tpc_topology-0.1.0-py3-none-any.whl`。本机 setuptools 发现可选 `bdist_conda` entry point 缺其 conda 模块并输出非致命警告。 |
| 发行清单边界 | `work/check_artifacts.py` 检查最终 wheel/sdist | wheel 53 项、sdist 98 项；未发现 `cst_solver`、`tpc_service`、`cst_mcp`、`em_enclosure`、`__pycache__` 或 `.pyc`；sdist 包含 `docs/README.md` 和 skills，wheel 不包含文档/skills。 |
| README 离线示例 | `TopoPath` 构造、`TopoModeler()` 构造与 `close()` | 通过；不触发 CST 初始化。不要调用未配置模型的 `validate()` 并期待返回通过。 |
| CI actions | `.github/workflows/ci.yml` | 使用 `actions/checkout@v7.0.1` 和 `actions/setup-python@v7.0.0`；纯离线测试/build job 不安装 `cst-automation`。 |
| 隔离构建模式 | `python -m build --sdist --wheel --outdir work/dist` | 未通过：本机隔离环境初始化时 `ensurepip` 遇 Unicode decode error。改用已安装 build/setuptools 的 `--no-isolation` 成功。 |

## 未验证边界

| 能力 | 状态 |
|---|---|
| CST 参数查询、建模器对真实工程执行 rebuild、结果文件 readback | 未运行；只确认 API 符号存在，fake tests 只验证分支行为。 |
| 真实 CST 求解与收敛 | 未运行。 |
| 拓扑带隙、Chern 数、单向传输、器件隔离性能 | 没有由本次代码迁移或离线测试证明。 |
| handler 的 `build`/`study` 在真实 CST 下执行 | 未运行；跨包测试只验证注册以及 `solve` 经 `FakeBackend` 的服务分派。 |

离线测试、wheel 安装和 fake backend 只支持其覆盖范围内的 Python/API 结论，不能升级为 CST 几何或电磁性能证据。
