---
name: lattice-paths
description: Use when generating triangular or hexagonal photonic-crystal lattices, phase maps, domain walls, or TPC paths.
---

# Lattice and paths

Read the [plugin runtime guide](../runtime.md) before importing the bundled Python code from an installed plugin.

Use `mesh_grid.tri_grid` for triangular photonic-crystal coordinates, phase patterns, and paths; use `mesh_grid.hex_grid` for hexagonal layouts, clipping, and DXF. These modules describe offline lattice geometry, not the electromagnetic solver mesh. Read [API and invariants](references/api.md) for public entry points and checks.
