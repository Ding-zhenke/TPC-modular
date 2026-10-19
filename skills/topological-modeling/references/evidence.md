# Evidence and acceptance

Keep these claims separate:

1. **Offline design:** normalized parameters, path coordinates, phase labels, and geometry-rule checks.
2. **CST geometry:** session opened, build history completed, rebuild/messages and entity checks read back from the named project.
3. **Solver:** the intended solver run completed and its run identity/results were read from that run.
4. **Device performance/topology:** full required evidence such as a common band gap, Chern-number calculation, tracked interface modes, convergence, and driven directional measurements.

A schematic, mock app, successful Python build call, field localization, or saved project does not establish later evidence levels. Report missing stages and exact artifacts.

Use the selected device's configuration and source geometry as the authority. Never transfer dimensions, phase order, or node coordinates from a concept drawing to another device without recalculating them.

## Template and frequency acceptance

For each CST template rebuild, record:

- The source template and output project, including whether a clean template or a new blank project was used.
- The retained parameter table and dependency check; identify removed inherited variables and any unresolved history or settings references.
- The frequency unit, solver type, band of interest, `fmin`/`fmax` values, and readback showing the solver settings reference these parameters and evaluate to the intended bounds.
- For the T solver, both margins (`interest_min - fmin` and `fmax - interest_max`) must be positive. Record the reason for the chosen margins; a wider total bandwidth alone does not establish coverage at both ends.
- Rebuild messages and any remaining errors. Missing readback leaves template acceptance unverified; a clean rebuild and correct frequency range establish settings/geometry evidence only, not a completed solver run or device performance.
