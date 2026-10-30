# TPC 插件 skills

一次安装 `tpc` 插件，自动发现以下六项技能。此目录是仓库与插件共用的唯一技能源。

| Skill | 任务 | 主要代码 |
|---|---|---|
| [lattice-paths](lattice-paths/SKILL.md) | 三角/六边晶格、坐标、路径、相区、域壁、裁剪、DXF | `mesh_grid` |
| [topological-schematic](topological-schematic/SKILL.md) | 权威参数驱动的结构、路径、尺寸与相区示意图 | `mesh_grid.plotting`、绘图 API |
| [topological-modeling](topological-modeling/SKILL.md) | 器件配置、几何预检、拓扑实体与 CST 模板验收 | `topo_modeler`、builders |
| [topological-templates](topological-templates/SKILL.md) | 波导、天线、GRIN 透镜、多端口、MZI、功分器模板 | `topo_templates`、config |
| [topological-analysis](topological-analysis/SKILL.md) | 扫描、批处理、已有结果指标、报告、审计与领域服务适配 | scanner、batch、result_reader、report、audit、`topo_service` |
| [topological-optimization](topological-optimization/SKILL.md) | 连续参数/二值晶格优化、等效介质与透镜设计计算 | optimizer、`tpc_toolkit` |

代码定位与依赖准备见[运行环境](runtime.md)；插件安装、分发和更新见[插件说明](../docs/PLUGIN.md)。`mesh_grid` 表示离线晶格几何，不是 CST 电磁求解网格。

通用 CST 会话、API、求解和诊断继续使用独立的 `cst-automation`。TPC 不复制通用 CST 手册、驱动或 MCP；`tpc_toolkit.curves/s2p` 保持兼容转发。
