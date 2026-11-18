# Evidence and acceptance

Report the project or artifact supporting each claim and any missing evidence.

- **Offline design** — target configuration, calculated coordinates, phase labels and geometry checks. Draw dimensions and phase order from the target device.
- **CST geometry and settings** — named project, completed build history, rebuild messages and entity or settings readback.
- **Existing results** — source project or dataset, run identity, units and port direction. Attribute results to the run that produced them.
- **Solver completion** — intended solver, completed run identity, results and convergence status.
- **Performance or topology** — evidence specific to the claim, such as a common band gap, Chern-number calculation, tracked interface modes or converged directional measurements.

A sketch, mock app, submitted build command, saved project or localized field alone cannot substantiate later stages.

## Template and frequency acceptance

1. Preserve the source template. Work in a clean project and retain only parameters used by the target device and their dependencies. Check history and settings references before removing inherited variables. If cleanup or reuse fails, start from a blank project and recreate the approved settings.
2. Define CST project parameters `fmin` and `fmax`. Make the solver frequency settings reference both parameters. Record the solver type, units, band of interest and simulation band.
3. For the time-domain (T) solver, require `fmin < interest_min < interest_max < fmax`. Record both margins and explain their choice for the device and excitation.
4. After rebuilding, record the source and output project, retained parameter table, removed variables and rebuild messages. Read back the solver references and their evaluated frequency limits. Confirm that references resolve, no unused variables remain and the effective range matches the specified band. Record errors or missing readback and leave the affected checks unverified.
