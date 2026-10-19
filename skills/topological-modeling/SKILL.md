---
name: topological-modeling
description: Use when specifying, preflighting, building, or reviewing a topological photonic crystal device with this TPC package.
---

# Topological modeling

Use TPC's `topo_modeler` configuration, preflight, builders, and `topo_templates` as the topology source of truth. Keep path and phase calculations offline; instantiate CST only for an explicit model build or solve. For CST operations, follow the `cst-automation` skill and public API.

Before constructing a new device geometry, present a parameter-backed sketch and wait for approval. For existing approved specifications, finish the agreed build and checks without re-asking routine steps.

Read [evidence and acceptance](references/evidence.md) when reporting geometry, readback, or solver outcomes. Read [service integration](references/service-integration.md) when registering domain jobs.
