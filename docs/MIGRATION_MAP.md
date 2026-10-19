# TPC 逐文件迁移归属表

源仓库：用户指定的旧 TPC 只读迁移仓库
源 HEAD：`51e4a63d302f0deea58d2a2df349892087dbfe7`
源工作树：实施开始时包含 14 个已修改 tracked 路径、6 个未跟踪源码/文档路径以及大量 `.pytest_tmp/` 运行产物。完整状态、tracked patch 与 staged patch 位于本仓库忽略目录 `work/source-snapshot/`；源仓库不改写。

本表覆盖提交时实际迁移结果；实现变更在合并前更新。

| 源路径 | 本仓库归属/处理 | 说明 |
|---|---|---|
| `mesh_grid/__init__.py`, `plotting.py`, `hex_grid/**`, `tri_grid/**` | 迁入同名路径，跳过 `__pycache__` | 晶格和拓扑路径绘图/几何算法；不是电磁求解网格。相关 tests 一并迁入。 |
| `topo_modeler/__init__.py`, `name_manager.py`, `config.py`, `preflight.py`, `audit.py`, `report.py`, `scanner.py`, `batch.py`, `optimizer.py`, `result_reader.py`, `lens_build*.py`, `modeler.py`, `builders/**` | 迁入同名路径；修改 CST 初始化边界、延迟依赖和默认路径 | 保留配置、拓扑几何构造器、透镜、扫描/解释逻辑；CST adapter 必须显式调用。 |
| `topo_modeler/tests/**` | 迁入同名测试并按离线/adapter 分层 | mock 构造验证标为 offline/mock；源测试中引用 cst_solver 私有保护器的部分改为不依赖私有实现的行为检查。 |
| `topo_templates/*.py`, `topo_templates/__init__.py`, `topo_templates/tests/**` | 迁入同名路径 | 拓扑器件模板；保留既有导入名。 |
| `templates/__init__.py` | 保留受限兼容 shim | 转发 `topo_templates`，记录弃用；不增加 `templates.*` 发行子模块。 |
| `tpc_toolkit/effective_medium.py`, `ga_optimizer.py` | 迁入 | 拓扑有效介质和晶格遗传优化。GA 相关科学/绘图库按 extras 延迟使用。 |
| `tpc_toolkit/curves.py`, `s2p.py` | 以延迟转发模块替代实现 | 唯一通用解析逻辑归 `cst_automation.curves`/`.s2p`。 |
| `tpc_toolkit/__init__.py` | 重写惰性入口 | 避免 import 时载入 GA、matplotlib 或 CST；保留常见属性访问。 |
| `tpc_service/backends/cst_backend.py` | 只提取拓扑领域分支至 `topo_service`，不复制通用实现 | 原服务状态、队列、CST 会话归 `cst-automation`。公共接口未发布前适配器边界标记待联调。 |
| `tpc_service/**`（其余） | 排除 | 通用任务服务、注册/调度/状态由 cst-automation 独家发行。 |
| `cst_solver/**`, `integrations/cst-mcp/**` | 排除 | 通用 CST 驱动/MCP 属 cst-automation。 |
| `tests/test_curve_rules.py`, `tests/test_compat_shims.py` | 提取适用断言至新 `tests/` | 曲线唯一实现委托断言、历史导入兼容断言迁入。 |
| `tests/test_chinese_plotting.py`, API consistency、model parameter、template registration tests | 迁入对应新测试目录/调整路径 | 仅保留拓扑模块检查；去除通用 CST 包要求。 |
| 其余顶层通用 CST/service/MCP tests | 排除 | 不在 TPC 发布包维护。 |
| `skills/user/hex-grid.md`, `tri-grid.md`, `topo-modeler.md`, `topo-quickstart.md`, `topological-schematic.md` | 精简后分别落入 `skills/lattice-paths/`、`skills/topological-modeling/`、`skills/topological-schematic/` 的 `SKILL.md`/references | 保留参数来源、相区/节点/尺寸、等比例和证据要求；删除通用 CST 手册部分。 |
| `.github/skills/*` | 不直接复制发布 | 新建仓库本地 `skills/` 权威入口，避免依赖源仓库插件布局。 |
| 源 `pyproject.toml`, README, SUPPORT_MATRIX / ARCHITECTURE | 不复制整份；从中提取拓扑职责、许可、支持边界，生成独立元数据与文档 | 原发行包同时含 CST/MCP/service，不适合沿用。 |
| `docs/validation/**`, CST 实验和真实工程证据 | 不迁移原始产物 | 在新的能力矩阵中只引用公开可读且与拓扑包相关的证据等级；不把旧机器状态作为当前验证。 |
| `skills/user/references/ba-sigma-approval.png` 与其它原始模型/SAT/大数据 | 不迁入发行包 | 与库级接口无关，且二进制来源/再分发资格或项目专属性未能确认。 |
| 源未提交 generic dialog 文件、MCP/CST/service diff | 仅留私有 `work/source-snapshot/` 供源仓库主人恢复 | 属于 CST 通用服务；不在拓扑仓库提交。 |
| 源 `.pytest_tmp/**`, `.venv`, `__pycache__` | 不迁移；状态与路径清单留快照 | 临时执行文件/缓存，不作为源码。 |

## 迁移后接口方向

```text
mesh_grid -> 仅离线科学/绘图库
topo_templates -> topo_modeler -> mesh_grid
topo_modeler CST adapter -> cst_automation public API
topo_service handler -> cst_automation handler protocol
tpc_toolkit.curves / s2p -> cst_automation.curves / s2p (lazy delegation)
```

TPC 不导入 `em_enclosure`，通用 CST 包不导入 TPC 模块。实现后的精确文件/符号变化和排除细项随提交更新本表。
