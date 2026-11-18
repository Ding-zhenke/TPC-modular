---
name: lattice-paths
description: Use when generating triangular or hexagonal photonic-crystal lattices, phase maps, domain walls, or TPC paths.
---

# Lattice and paths

Read the [plugin runtime guide](../runtime.md) before importing the bundled Python code from an installed plugin.

Use `mesh_grid.tri_grid` for triangular photonic-crystal coordinates, phase patterns, and paths; use `mesh_grid.hex_grid` for hexagonal layouts, clipping, and DXF. These modules describe offline lattice geometry, not the electromagnetic solver mesh. Read [API and invariants](references/api.md) for public entry points and checks.

## Interactive domain-wall editor

When the user wants to click triangular-lattice domain-wall points or draw branches, launch the local browser editor using the [editor guide](../../docs/PATH_EDITOR.md). Keep the reported URL and stop instructions. Verify session identity before reusing a port or stopping a session. Confirm the example cell parameters in the editor and retain unresolved phase conflicts as drafts.
