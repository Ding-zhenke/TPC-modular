---
name: topological-modeling
description: Use when specifying, preflighting, preparing CST templates for, building, or reviewing a topological photonic crystal device with this TPC package.
---

# Topological modeling

Use the target configuration, `topo_modeler` builders and `topo_templates` as the geometry source. Keep path and phase calculations offline. Consult the [runtime guide](../runtime.md) when running bundled Python, and use the public `cst-automation` API for authorized CST operations.

Before constructing new device geometry, present a parameter-backed sketch and wait for approval. Continue within an existing approved specification without repeating the approval.

- To select an existing device, use [device templates](../topological-templates/SKILL.md).
- To prepare or rebuild a CST template, follow [template and frequency acceptance](references/evidence.md#template-and-frequency-acceptance) through readback.
- To report geometry or solver claims, use the [evidence requirements](references/evidence.md). For scans or existing results, use [analysis](../topological-analysis/SKILL.md).
- To register domain jobs, use [service integration](references/service-integration.md).
