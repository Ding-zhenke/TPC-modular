---
name: topological-analysis
description: Use when extracting metrics from existing TPC S parameters, comparing completed runs, or generating topology-device result reports and audits.
---

# TPC 已有结果分析

记录曲线来源、对应的参数组合和运行 ID，核对频率单位、端口方向和指标定义。按[运行环境](../runtime.md)选择 Python；读取已有曲线并导出指标时使用 `ResultReader`，接入内存数据见[曲线读取示例](references/analysis.md)。

用 `report` 和 `audit` 汇总结果，按[证据与验收](../topological-modeling/references/evidence.md)标注数据来自合成示例、已有工程读回或实际求解。规划参数组合或执行批处理见[参数扫描](../topological-parameter-scan/SKILL.md)；注册领域任务见[服务适配](../topological-modeling/references/service-integration.md)。
