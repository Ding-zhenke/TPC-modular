---
name: metal-hex-topological-modeling
description: Use for metal hexagonal photonic-crystal waveguides on quartz (金属六边晶格), including AB/BA/A-air layouts, tapered or fork probes, parameter previews and CST geometry builds.
---

# 金属六边晶格直波导

按探针选模板：

- AB、BA 或 A—空气直波导，使用单片渐变探针时选 `topo_templates.metal_hex.MetalHexStraight`。
- AB 直波导，使用开槽双枝节叉形探针时选 `topo_templates.fork_waveguide.ForkWaveguide`。

**几何预检。** 按[运行环境](../runtime.md)选择带 `geometry` 的 Python，用 `device.geometry()` 检查规格、探针与晶格铜面的正面积搭接及基板支撑。断开或悬空时调整规格并复查。用 `device.preview(output_dir)` 将实际多边形的等比例参数图和规格 JSON 输出到用户工作区的绝对路径。

**建模前审批。** 提交[参数草图](../topological-schematic/SKILL.md)，取得对应规格的批准后，在已核对单位和地参考的干净 mm 工程中调用 `device.build(app)`。准备仿真模板时按[模板验收](../topological-modeling/references/evidence.md#template-and-frequency-acceptance)回读设置。

复现历史设计、调整叉形探针或判断改参后如何重建时，查[金属六边晶格模块说明](../../docs/METAL_HEX.md)。
