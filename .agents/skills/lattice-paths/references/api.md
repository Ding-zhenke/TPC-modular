# Lattice and path API

Existing import names are stable: `mesh_grid.tri_grid` (including `TopoPath`, `TopoPathBuilder`, coordinate conversion, phase diagrams) and `mesh_grid.hex_grid` (hex grid generation, clipping and DXF helpers). Optional geometry dependencies are installed with `tpc-topology[geometry]`.

Check lattice constant, origin, orientation, integer bounds, phase assignment, and path turn convention together. For arrays clipped to a domain, verify the surviving node count and boundary extents. Tests establish algorithmic invariants only; they do not validate a CST solid or solver mesh.
