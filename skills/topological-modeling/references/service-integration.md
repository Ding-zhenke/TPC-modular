# Topology service integration

The generic `RunService`, queue, job state, and MCP tools belong to `cst-automation`. TPC owns only topology handlers and their input/output semantics.

Use `topo_service.register_topology_handlers(service)` with a `cst-automation` release that implements the `DomainHandler` protocol in its `docs/PUBLIC_API.md`. If that API is missing, stop at the offline adapter and report the exact missing method. Do not copy `tpc_service` into TPC or mock an installed package to claim cross-package success.

Handler call shape: `handler(*, project, params, job, backend) -> mapping`. Paths and artifacts must remain inside the service work directory. A solve handler must preserve the generic backend's save/run identity and report topology postprocessing failures separately.
