# TPC

拓扑光子晶体离线晶格、路径、相区、示意图、DXF、器件模板与拓扑专用 CST 建模适配。目标是让纯设计与拓扑几何分析在没有 CST 的环境中运行；只有实际创建/求解 CST 工程时才需要通用 `cst-automation`。

## 能力与依赖

- `mesh_grid`: 三角/六边晶格、路径/相区、裁剪和绘图；几何导出使用 `geometry` extra。
- `topo_modeler`: 离线预检、配置、几何表达、扫描/结果解释，以及惰性加载的 CST 建模入口。
- `topo_templates`: 拓扑器件模板。
- `tpc_toolkit`: 拓扑优化与等效介质；通用曲线/S 参数通过兼容入口委托给 `cst-automation`。
- `topo_service`: 拓扑领域服务适配器；对接协议发布前不可声称已完成端到端服务注册。

安装基础离线能力：

```powershell
python -m pip install .
```

从源码开发并运行完整离线测试：

```powershell
python -m pip install -e '.[all,dev]'
python -m pytest
python -m build --sdist --wheel
```

包含 DXF/几何、科学和开发依赖：

```powershell
python -m pip install '.[geometry,science,dev]'
```

需要 CST 建模时，先从相邻 checkout 或其本地 wheel 安装兼容版本的 `cst-automation`，再安装本包的 `cst` extra 和本机 CST 提供的 Python API。例如：

```powershell
python -m pip install /path/to/cst_automation-0.1.0-py3-none-any.whl
python -m pip install '.[cst]'
```

`cst-automation>=0.1,<1` 是声明的兼容范围；在通用包未发布到所用索引前，不要假定 PyPI 能解析该依赖。TPC 不安装通用 CST MCP，也不依赖 `em-enclosure`。

## 快速示例

```python
from mesh_grid.tri_grid import TopoPath
from topo_modeler import TopoModeler

path = TopoPath.builder(a=0.25).start(0, 0).move(2, 'c').build()
modeler = TopoModeler()  # 离线构造，不会连接 CST
modeler.close()
print(path.points)
```

完整的设备参数、构建入口和证据边界见 [API 与支持矩阵](docs/API_AND_SUPPORT.md)。纯离线 CI 不安装 `cst-automation`；跨包注册测试使用本地构建的实际 `cst-automation` wheel 和 fake backend。真实 CST rebuild、结果 readback 和 solver 需要在安装 CST 的机器上单独验证。

## 兼容入口

旧模块名 `mesh_grid`、`topo_modeler`、`topo_templates`、`templates` 和 `tpc_toolkit` 会保留。`templates` shim 仅转发拓扑模板，暂定保留一个次版本周期后移除；新代码应使用 `topo_templates`。`tpc_toolkit.curves` 与 `.s2p` 延迟导入 `cst_automation` 的唯一实现；使用它们时需安装提供离线数据子模块的通用包。

## 文档

- [拆分与实施计划](docs/SPLIT_PLAN.md)
- [逐文件迁移归属](docs/MIGRATION_MAP.md)
- [验证记录与未验证边界](docs/VALIDATION.md)
- [迁移指南](docs/MIGRATION.md)
- [API 与支持矩阵](docs/API_AND_SUPPORT.md)
- [TPC 技能目录](skills/README.md)
- [贡献与验证指南](CONTRIBUTING.md)

几何预览、预检或 mock 结果不代表 CST 实际读回或求解成功，也不能单独证明拓扑带隙、Chern 数或单向传输。
