---
name: metal-hex-topological-modeling
description: Use for metal hexagonal photonic-crystal waveguides on quartz (金属六边晶格), including AB/BA/A-air layouts, tapered or fork probes, parameter previews and CST geometry builds.
---

# 金属六边晶格直波导

按器件选入口，使用本库实现。运行插件内的几何代码时按[运行环境](../runtime.md)选择带 `geometry` 的解释器，预览输出到用户工作区的绝对路径。

- AB、BA 或 A—空气单片渐变探针用 `topo_templates.metal_hex.MetalHexStraight`。复现旧 notebook 用 `MetalHexSpec.legacy_notebook()`；读取旧字段 JSON 用 `from_dict()` 保留原布局。
- 开槽双枝节探针用 `topo_templates.fork_waveguide.ForkWaveguide`；叉口和晶格槽口由同一 gap 控制。两类器件的尺寸、调参示例和地参考假设见[模块说明](../../docs/METAL_HEX.md)。

用 `device.geometry()` 检查参数、探针与晶格铜面的正面积搭接及基板支撑。断开或悬空时调整规格再检查。用 `device.preview(output_dir)` 输出实际多边形的等比例参数图和可恢复 JSON。新几何实建前提交[参数草图](../topological-schematic/SKILL.md)并等待批准；参考设计的批准仅适用于对应规格。

写入 CST 前核对调用者提供的干净 mm 工程、地参考及[参数分支的重建条件](../../docs/METAL_HEX.md#cst-接口与证据)。`device.build(app)` 只提交参数化几何；P01/P02 标识晶格界面节点。准备仿真模板时执行[模板验收](../topological-modeling/references/evidence.md#template-and-frequency-acceptance)。报告区分离线几何、命令提交、实际铜面布尔与材料读回、求解及性能。
