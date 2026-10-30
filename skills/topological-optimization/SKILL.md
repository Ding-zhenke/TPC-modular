---
name: topological-optimization
description: Use when optimizing TPC continuous geometry parameters or binary lattice patterns, calculating effective-medium properties, or checking optimization histories and reproducibility.
---

# TPC 优化与等效介质

先读[插件运行环境](../runtime.md)和[优化接口与示例](references/optimization.md)。复用 `topo_modeler.optimizer` 的统一入口；二值模式复用 `tpc_toolkit.ga_optimizer`，等效介质计算使用 `tpc_toolkit.effective_medium`。

运行前确定变量、取值域、单位、目标函数、最大化/最小化方向、随机种子和评估预算。目标函数由调用方注入；离线数学函数和真实 CST 评估分别记录。先用极小离线例子确认数据流，只有用户范围包含实际求解时才接入 CST runner。

保留 `best_params`、`best_fitness`、`history`、`evaluations`、`seed` 和停止原因。`improved` 表示历史最优不劣于初代，不保证严格变好，更不证明全局最优。等效介质估计不替代离散器件的几何、频散和全波验证。

如果优化结果要变成新的 CST 几何，按 [topological-modeling](../topological-modeling/SKILL.md) 先提交真实参数草图并等待用户审批。
