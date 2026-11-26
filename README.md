# TPC 拓扑光子晶体工具箱

TPC 用于设计三角与六边晶格中的拓扑光子晶体器件。你可以在本机浏览器中点选域壁、划分 A/B 相区并导出版图，也可以用 Python 从器件参数生成几何和尺寸图。晶格设计可离线完成，创建 CST 工程时通过 `cst-automation` 调用本机 CST。

## 按任务开始

| 我想做什么 | 从哪里开始 |
| --- | --- |
| 在三角孔晶格上画域壁、接分支、导出毫米 DXF | [域壁路径编辑器](docs/PATH_EDITOR.md) |
| 用 Python 生成晶格、定义路径或裁剪相区 | [晶格与路径](skills/lattice-paths/SKILL.md) |
| 画石英基板上金属六边晶格的 AB、BA 或 A—空气直波导 | [金属六边晶格模型与参数](docs/METAL_HEX.md) |
| 选择波导、天线、透镜或功分器模板，准备 CST 建模 | [器件模板](skills/topological-templates/SKILL.md) · [建模与预检](skills/topological-modeling/SKILL.md) |
| 规划参数扫描、分析已有 S 参数或优化晶格 | [参数扫描](skills/topological-parameter-scan/SKILL.md) · [结果分析](skills/topological-analysis/SKILL.md) · [优化](skills/topological-optimization/SKILL.md) |

## 安装 Codex 插件

在仓库根目录运行以下命令即可注册本地市场并安装 `tpc`。安装后新开一个 Codex 聊天即可使用[九项技能](skills/README.md)。使用分发 ZIP 时，先解压并进入其中的 `tpc` 目录。[插件安装与分发说明](docs/PLUGIN.md)

```powershell
codex plugin marketplace add "$PWD"
codex plugin add tpc@tpc-local
```

插件随包提供 Python 源码；首次使用按[运行环境指引](skills/runtime.md)检查依赖。已有 Python 包安装方式继续适用。

## 能力与依赖

- `mesh_grid`: 三角/六边晶格、路径/相区、裁剪和绘图；几何导出使用 `geometry` extra。
- `topo_modeler`: 离线预检、配置、几何表达、扫描/结果解释，以及惰性加载的 CST 建模入口。
- `topo_templates`: 拓扑器件模板。
- `tpc_toolkit`: 拓扑优化与等效介质；通用曲线/S 参数通过兼容入口委托给 `cst-automation`。
- `topo_service`: 拓扑领域服务适配器。已有跨包测试使用 FakeBackend 验证注册与分派，实机状态见[支持矩阵](docs/API_AND_SUPPORT.md)。

### 安装 Python 包

直接使用 Python API 时，在仓库根目录用 Python 3.9 或更高版本安装基础包。

```powershell
python -m pip install .
```

从源码开发、运行测试与构建发行包见[贡献指南](CONTRIBUTING.md)。

运行下方金属晶格预览和域壁编辑器示例时，安装几何依赖。

```powershell
python -m pip install '.[geometry]'
```

科学计算、YAML 配置和开发测试可分别选装 `science`、`yaml` 和 `dev`。需要 CST 建模时，准备好本机 CST 提供的 Python API，再安装兼容版本的 `cst-automation` 和本包的 `cst` extra。若两个源码仓库位于同一父目录，可运行以下命令。

```powershell
python -m pip install ../cst-automation
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
print(path.xy)
```

完整的设备参数、构建入口和证据边界见 [API 与支持矩阵](docs/API_AND_SUPPORT.md)。纯离线 CI 不安装 `cst-automation`；跨包注册测试使用本地构建的实际 `cst-automation` wheel 和 fake backend。真实 CST rebuild、结果 readback 和 solver 需要在安装 CST 的机器上单独验证。

### 金属六边晶格直波导

安装 `tpc-topology[geometry]` 后，可离线生成居中金属晶格及可调叉形馈源：

```python
from pathlib import Path
from topo_templates.fork_waveguide import ForkWaveguide

device = ForkWaveguide()
files = device.preview(Path('outputs/fork_waveguide').resolve())
```

默认 10a AB 晶格与上下半行边界、共享槽口/叉口间隙及双枝节参数见[金属晶格模块说明](docs/METAL_HEX.md)。CST 几何接口只提交建模命令，真实 CST 读回与求解须单独验证。

### 点击域壁点绘制路径

安装 `geometry` extra 后，在本机浏览器中打开编辑器：

```powershell
python -B -m tpc_editor --workspace "<你的设计目录>"
```

选择并核对三角孔晶胞，点击域壁路径点；结束本段后从已有点接出分支。支持相区 A/B 分配、JSON 保存重开、SVG/PNG 尺寸图，以及通过几何检查后的毫米 DXF 版图导出。启动插件分发内的编辑器可使用 `scripts/open_path_editor.py`。详见[路径编辑器](docs/PATH_EDITOR.md)。

## 兼容入口

旧模块名 `mesh_grid`、`topo_modeler`、`topo_templates`、`templates` 和 `tpc_toolkit` 会保留。`templates` shim 仅转发拓扑模板，暂定保留一个次版本周期后移除；新代码应使用 `topo_templates`。`tpc_toolkit.curves` 与 `.s2p` 延迟导入 `cst_automation` 的唯一实现；使用它们时需安装提供离线数据子模块的通用包。

## 文档

从[任务技能目录](skills/README.md)选择工作流程。[文档索引](docs/README.md)汇总支持矩阵、验证记录、贡献指南及历史迁移资料。
