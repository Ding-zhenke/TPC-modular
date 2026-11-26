---
name: topological-parameter-scan
description: Use when planning TPC parameter sweeps, enumerating device configurations, or running a per-point batch with a supplied runner and metrics.
---

# TPC 参数扫描

按[运行环境](../runtime.md)选择 Python。以目标器件配置、扫描变量、单位和取值建立 `ParameterScan`。用 `plan()` 交付组合表，列出点名、参数和值，核对总点数。

需要执行时，用 `run()` 对每个点调用 runner，并将点名、配置和运行身份对应到各自的结果。接入真实求解前核对授权范围。设置 `required_metrics` 后按成功点、失败点和错误详情汇总，按需导出 CSV 或 HTML。runner 返回协议、重跑行为和离线示例见[扫描参考](references/scan.md)。已有曲线的指标提取和跨轮比较见[结果分析](../topological-analysis/SKILL.md)。
