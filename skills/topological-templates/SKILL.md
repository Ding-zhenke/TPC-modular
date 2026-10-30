---
name: topological-templates
description: Use when selecting or configuring existing TPC straight-waveguide, antenna, GRIN-lens, multiport, MZI-switch or power-divider device templates.
---

# TPC 器件模板

先读[插件运行环境](../runtime.md)。以 `topo_modeler.config` 的注册表、字段定义与 `topo_templates` 源码为依据选择已有模板；参数预检保持离线。

读[模板入口与离线示例](references/templates.md)，确认器件类型、参数单位、默认值及输出路径。模板示例参数用于演示，不能替代目标器件的权威参数。

新几何实建前，使用 [topological-schematic](../topological-schematic/SKILL.md) 输出真实参数草图并等待用户审批。已有批准规格按约定继续执行。实际调用 `build_all()` 前遵循 [topological-modeling](../topological-modeling/SKILL.md) 的干净模板、`fmin/fmax`、时域频段裕量和读回验收规则。

构造或导入模板不代表实体已经创建；访问模板的 `app`、调用 `build_all()` 属于显式 CST 操作。模板支持情况以当前实现为准，不把旧文档中的参考模型等同于本库生成几何。
