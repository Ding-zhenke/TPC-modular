---
name: metal-hex-topological-modeling
description: Model and preview straight AB, BA or A-air metal hexagonal topological photonic crystals on quartz with centred mirror symmetry, planar tapered probes, adjustable substrate support and CST geometry adapters. Use for 金属六边晶格、微带金属拓扑光子晶体; silicon triangular-hole devices use the existing topological modeling skills.
---

# 金属六边晶格直波导

先按[运行环境](../runtime.md)检查 geometry extra。使用 TPC 自带代码，不执行原 notebook 的 CST 调用或导入旧本机路径。完整参数、例子和兼容规则见[模块说明](../../docs/METAL_HEX.md)。

```python
from mesh_grid.metal_hex import MetalHexSpec
from topo_templates.metal_hex import MetalHexStraight

spec = MetalHexSpec(layout='AB')
device = MetalHexStraight(spec)
geometry = device.geometry()
files = device.preview(output_dir)
```

output_dir 使用当前用户工作区绝对路径，不能写入插件缓存。geometry/preview 均离线；参数入口不加载 Shapely、matplotlib 或 CST。输出实际多边形的等比例 PNG/SVG 和可恢复 JSON。

## 当前默认：已批准的居中双端馈源

- centered=True，晶格、两端探针及石英基板沿 x=0 镜像；不改变原晶格单元内部几何。
- layout='AB' 为 A 上 B 下；BA 为 B 上 A 下，仅换相区、不镜像阵列；A_air 删除下半晶格，石英空气侧保留宽度 air_substrate_width 可调，默认 a=0.606 mm。
- 铜面 t=0，石英 -h≤z≤0。两端馈源是沿基板平面的金属渐变探针，不使用垂直针，也不把硅介质探针直接更换材料。
- 默认 Lt=1.212、Ln=.2、Wp=.2、Li=.02、外边距=.303 mm；Wt 为 AB .303、BA/A_air .1；yf 为 A_air .05、其它 0。全部可调，均为用户确认的起点，不能宣称已匹配或收敛。
- 在 geometry() 及任何 CST 写入前，检查双端探针与晶格铜面的正面积搭接、基板支撑及参数有效性。断开或悬空时调整 spec，不绕过检查。
- A_air 无下半晶格，但探针直颈在晶格外侧可跨过 y=0；接触尖端默认从 A 侧接入。不要误删馈源来强制下半平面完全无铜。
- ring_inset 是六边形半径差，单环法向宽为其乘 cos(30°)；x_periods/y_half_periods 分别是长度/a、原半区高度/a，不是单元数。

## 开槽双枝节叉形直波导

使用 `from topo_templates.fork_waveguide import ForkWaveguide`。默认 AB 晶格长度 10a，沿 y 的上下裁剪边界分别为 5dy、−2dy，dy=√3a/2；最外侧两行各保留半行。`device.geometry()`、`device.preview(output_dir)` 离线运行，`device.build(app)` 仅向调用者提供的 CST 工程提交几何。`ForkWaveguideSpec(upper_rows=..., lower_rows=...)` 可调裁剪，嵌套 `ForkProbeSpec` 可调探针尺寸。单一 gap 同时控制叉口和晶格槽口，双枝节位于等宽支臂且上下镜像；此接口独立于 A_air 和既有单片渐变探针。

默认宽端 0.213938021932 mm 来自 h=0.1 mm、εr=3.78、t=0 和连续底面地的准静态假设；不代表 CST 已读回地或介电常数，也不代表高频匹配已验证。完整参数和证据见[模块说明](../../docs/METAL_HEX.md)。

## 历史设计

旧 notebook 复现使用 MetalHexSpec.legacy_notebook()：原坐标、无探针、完整基板。from_dict 对只有旧字段的 JSON 也恢复该旧模式；新配置 to_dict 包含全部参数，能够往返恢复。新任务通过构造器指定参数，不能把旧 JSON 的兼容行为误当作新的默认布局。

## 审批、CST 与报告

新目标器件按[结构图规范](../topological-schematic/SKILL.md)先输出真实参数草图并确认。默认值是参考设计初值，不代表新任务已经获得审批。既有任务的授权以当前会话及可核验设计记录为准，在已批准范围内继续执行。更改参数后保留几何与证据一致。

真实操作用独立 cst-automation。调用者提供审阅过的干净 mm 工程与地参考后，显式 device.build(app)；仅写参数化几何，不创建会话、端口、地板，不配置求解器或启动求解。是否求解依当前任务授权决定。P01/P02 是晶格界面节点，不是端口。

CST 参数是全局短名，形状前缀不隔离参数。改变 layout/centered/probes_enabled，或跨越 ny=1 分支时，须在干净工程按新 spec 重新生成。使用当前 material=、subtract() 等公共接口，不沿用旧拼写。仿真模板按[拓扑建模要求](../topological-modeling/SKILL.md)落实 fmin/fmax、时域裕量及回读；旧模板的电壁和频段不视为自动生效。

报告分别区分离线几何、命令提交、CST 实体/材料读回及求解。零厚度布尔、铜面接触/合并需真实 CST 验收；build() 的 evidence 不表示 readback 已验证。面积、草图和 fake adapter 不证明带隙、拓扑不变量或性能。
