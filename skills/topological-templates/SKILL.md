---
name: topological-templates
description: Use when selecting or configuring existing TPC straight-waveguide, antenna, GRIN-lens, multiport, MZI-switch or power-divider device templates.
---

# TPC 器件模板

以 `topo_modeler.config` 的注册表、字段定义与 `topo_templates` 源码选择模板。按[模板入口](references/templates.md)核对目标规格、单位和默认值来源。运行插件 Python 时查[运行环境](../runtime.md)。离线预检使用 `validate_only=True`，避免访问模板的 `app`。

估算有效折射率或计算 GRIN 透镜孔阵列时，查[等效介质与 GRIN 透镜计算](../references/effective-medium-grin.md)。

新几何实建前按[绘图规范](../topological-schematic/SKILL.md)提交参数草图，等待用户批准。已有批准按原范围执行。准备仿真模板时执行[模板与频段验收](../topological-modeling/references/evidence.md#template-and-frequency-acceptance)。访问 `app` 或调用 `build_all()` 会进入真实 CST 操作，建模、保存与求解按各自授权执行。
