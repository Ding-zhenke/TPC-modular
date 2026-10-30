---
name: topological-analysis
description: Use when planning TPC parameter scans, extracting metrics from existing S parameters, comparing runs, or generating topology-device result reports and audits.
---

# TPC 扫描与分析

先读[插件运行环境](../runtime.md)，再读[数据接入与扫描示例](references/analysis.md)。复用 `topo_modeler.scanner`、`result_reader`、`report` 和 `audit`；拓扑领域任务注册见[服务适配](../topological-modeling/references/service-integration.md)。

记录数据来源、参数组合、运行 ID、频率单位、端口方向和指标定义。只规划组合用 `ParameterScan.plan()`；`run()` 会调用提供的 runner，是否求解由 runner 决定。读取已有数据不自动授权启动新的扫描求解。

原始 S 参数字典需要适配读取协议后交给 `ResultReader`。扫描 runner 直接返回字典表示最终指标，不能把曲线字典放进去期待 `metric_specs` 再处理。

报告使用[证据与验收](../topological-modeling/references/evidence.md)区分离线算法、已有结果读取、实体读回和真实求解。合成数据例子只证明分析流程可用，不能证明器件性能或拓扑性质。
