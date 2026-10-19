---
name: topological-modeling
description: Use when specifying, preflighting, preparing CST templates for, building, or reviewing a topological photonic crystal device with this TPC package.
---

# Topological modeling

Use TPC's `topo_modeler` configuration, preflight, builders, and `topo_templates` as the topology source of truth. Keep path and phase calculations offline; instantiate CST only for an explicit model build or solve. For CST operations, follow the `cst-automation` skill and public API.

Before constructing a new device geometry, present a parameter-backed sketch and wait for approval. For existing approved specifications, finish the agreed build and checks without re-asking routine steps.

## CST template preparation

1. Rebuild from a clean template. Retain only parameters needed by the current device and their dependencies; remove unused inherited variables. Check history and settings references before removing parameters. If cleanup or reuse fails, create a new blank project and recreate the required settings within the approved specification. Preserve the source template.
2. Define the simulation frequency bounds as CST parameters `fmin` and `fmax`, and make the solver frequency settings reference those parameters.
3. For the T (time-domain) solver, extend the simulation band beyond both ends of the frequency band of interest: `fmin < interest_min < interest_max < fmax`. Choose and record the margins for the device and excitation; no fixed margin is prescribed. Keep the band of interest separate from the simulation band.
4. After rebuilding, read back the parameter table, frequency settings, and rebuild messages. Confirm that unused inherited variables are absent, required references resolve, and the effective simulation band matches the chosen bounds. Use the [acceptance checklist](references/evidence.md#template-and-frequency-acceptance) before reporting the template ready.

Read [evidence and acceptance](references/evidence.md) when reporting geometry, readback, or solver outcomes. Read [service integration](references/service-integration.md) when registering domain jobs.
