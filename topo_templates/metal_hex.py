"""Straight metal hex layouts; deliberately separate from silicon YAML types."""
from mesh_grid.metal_hex.spec import MetalHexSpec


class MetalHexStraight:
    """Offline-first convenience entry. No app/session is acquired implicitly."""
    def __init__(self, spec=None):
        self.spec = MetalHexSpec() if spec is None else spec
        if not isinstance(self.spec, MetalHexSpec):
            raise TypeError('spec must be MetalHexSpec')

    def geometry(self):
        from mesh_grid.metal_hex import build_geometry
        return build_geometry(self.spec)

    def preview(self, output_dir):
        from mesh_grid.metal_hex import export_preview
        return export_preview(self.spec, output_dir)

    def build(self, app, *, prefix='mh', component='metal_hex'):
        """Explicit write to caller-owned CST app; no save or solve."""
        from topo_modeler.builders.metal_hex import build_metal_hex
        return build_metal_hex(app, self.spec, prefix=prefix, component=component)
