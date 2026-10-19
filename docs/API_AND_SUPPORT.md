# API 与支持矩阵

| 能力 | 模块 | 无 CST | 额外依赖 | 当前状态 |
|---|---|---:|---|---|
| 三角晶格、坐标、相区、域壁、路径 | `mesh_grid.tri_grid` | 是 | numpy、matplotlib、tqdm | 源实现迁入；副本测试待执行 |
| 六边晶格、裁剪、DXF | `mesh_grid.hex_grid` | 是 | `geometry` extra | 源实现迁入；DXF/布尔规则待实测 |
| 配置、预检、离线报告/扫描 | `topo_modeler.config`, `preflight`, `scanner`, `report` | 是 | YAML 配置读写需 `yaml` extra | 改为不默认诊断 CST |
| CST 拓扑实体建模与模板 | `topo_modeler`, `topo_templates` | 否（显式操作时） | `cst` extra + 本机 CST | 延迟依赖与安装提示已实现；参数前置检查调用 `setup.get_parameter()`；CST 实机验证未做 |
| 拓扑 GA、等效介质 | `tpc_toolkit.ga_optimizer`, `.effective_medium` | 是 | science/绘图 | 顶层模块惰性导入 |
| 曲线/S 参数共享规则 | `tpc_toolkit.curves`, `.s2p` → `cst_automation.*` | 是，但需通用发行包 | `cst` extra | 委托入口已建；真实发行包联调待服务发布 |
| 拓扑任务 handler | `topo_service` | 取决于 handler 类型 | `cst` extra | 通过 `RunService.register_handler()` 注册；fake backend 服务闭环由跨包集成测试验证；真实 CST 未验证 |

`templates` 是有期限兼容名，不推荐给新代码。所有离线测试仅证明所覆盖的 Python/算法性质。几何预览不等于 CST rebuild；CST rebuild 不等于 solver 成功；solver 成功也不自动证明拓扑/隔离性能。
