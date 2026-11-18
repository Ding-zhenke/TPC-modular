# API 与支持矩阵

| 能力 | 模块 | 无 CST | 额外依赖 | 当前状态 |
|---|---|---:|---|---|
| 三角晶格、坐标、相区、域壁、路径 | `mesh_grid.tri_grid` | 是 | numpy、matplotlib、tqdm | 已纳入[离线回归](VALIDATION.md#已完成验证) |
| 六边晶格、裁剪、DXF | `mesh_grid.hex_grid` | 是 | `geometry` extra | 已回读核对 DXF 的毫米单位、合并内孔和分离区域 |
| 域壁编辑器毫米 DXF | `tpc_editor.export.render_dxf` | 是 | `geometry` extra | 已回读核对完整孔轮廓及域壁坐标，见[编辑器说明](PATH_EDITOR.md) |
| 配置、预检、离线报告/扫描 | `topo_modeler.config`, `preflight`, `scanner`, `report` | 是 | YAML 配置读写需 `yaml` extra | 支持必需指标校验与扫描重跑，见[离线数据与扫描](../skills/topological-analysis/references/analysis.md) |
| CST 拓扑实体建模与模板 | `topo_modeler`, `topo_templates` | 否（显式操作时） | `cst` extra + 本机 CST | 延迟依赖与安装提示已实现；参数前置检查调用 `setup.get_parameter()`；CST 实机验证未做 |
| 拓扑 GA、等效介质 | `tpc_toolkit.ga_optimizer`, `.effective_medium` | 是 | science/绘图 | 顶层模块惰性导入 |
| 曲线/S 参数共享规则 | `tpc_toolkit.curves`, `.s2p` → `cst_automation.*` | 是，但需通用发行包 | `cst` extra | 兼容入口惰性转发，已有[导入及缺依赖测试](../tests/test_compatibility.py)；解析数值的跨包验证需单独记录 |
| 拓扑任务 handler | `topo_service` | 取决于 handler 类型 | `cst` extra | 通过 `RunService.register_handler()` 注册；[FakeBackend 注册与分派已验证](VALIDATION.md#已完成验证)，真实 CST 执行见[未验证边界](VALIDATION.md#未验证边界) |

`templates` 是有期限兼容名，不推荐给新代码。所有离线测试仅证明所覆盖的 Python/算法性质。几何预览不等于 CST rebuild；CST rebuild 不等于 solver 成功；solver 成功也不自动证明拓扑/隔离性能。

金属六边晶格、参数化叉形探针、离线预览和 CST 几何接口见 [金属晶格说明](METAL_HEX.md)。实际 CST 构建、读回和求解未验证。
