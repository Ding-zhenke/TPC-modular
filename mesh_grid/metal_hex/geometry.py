"""Exact planar transform/union/clip reconstruction of the supplied AB design."""
from dataclasses import dataclass
import math

from .spec import MetalHexSpec


def _shapely():
    try:
        from shapely import affinity
        from shapely.geometry import Polygon, box
        from shapely.ops import unary_union
    except ImportError as exc:
        raise ImportError('Metal hex geometry requires tpc-topology[geometry]') from exc
    return affinity, Polygon, box, unary_union


@dataclass(frozen=True)
class MetalHexGeometry:
    spec: MetalHexSpec
    unit_ring: object
    unit_a: object
    unit_b: object
    rings: object
    phase_a: object
    phase_b: object
    metal: object
    substrate: object
    metal_extent: object
    core_metal: object
    probe_left: object
    probe_right: object

    @property
    def bottom_blank(self):
        """Actual unfilled bottom strip, which depends on the source array."""
        return self.metal.bounds[1] - self.substrate.bounds[1]

    def summary(self):
        return dict(unit='mm', spec=self.spec.to_dict(),
                    metal_clip_bounds=self.spec.metal_bounds,
                    substrate_bounds=self.substrate.bounds,
                    actual_metal_bounds=self.metal.bounds,
                    metal_area_mm2=self.metal.area,
                    core_metal_area_mm2=self.core_metal.area,
                    probe_contact_areas_mm2=[p.intersection(self.core_metal).area
                                             for p in (self.probe_left,self.probe_right)],
                    right_blank=self.spec.right_blank, bottom_blank=self.bottom_blank,
                    single_ring_normal_width=self.spec.single_ring_width,
                    phase_sides=self.spec.phase_sides,
                    evidence='offline planar geometry; no CST rebuild/readback/solve')


def build_geometry(spec=None):
    """Generate all copper polygons from one validated spec, without CST.

    Shared ring walls are unioned, not drawn as overlapping translucent lines.
    Positive then negative Y copies act on the full previous result, exactly
    as in the source; do not replace with guessed row counts or symmetric fill.
    """
    spec = MetalHexSpec() if spec is None else spec
    if not isinstance(spec, MetalHexSpec):
        raise TypeError('spec must be MetalHexSpec')
    affinity, Polygon, box, union = _shapely()
    a, r, p = spec.lattice_constant, spec.ring_radius, spec.pad_length

    def hexagon(radius):
        return Polygon([(radius*math.cos(math.radians(90+60*j)),
                         radius*math.sin(math.radians(90+60*j))) for j in range(6)])

    ring = hexagon(r).difference(hexagon(r-spec.ring_inset))
    kite = Polygon([(p*math.cos(math.pi/6), p/2), (0, 0), (0, -p),
                    (p*math.cos(math.pi/6), -p/2)])
    kite = affinity.translate(kite, -a/2, r/2)
    b = union([affinity.rotate(kite, 120*j, origin=(0, 0)) for j in range(3)])
    motif_a = affinity.rotate(b, 180, origin=(0, 0))

    def array(g):
        g = union([affinity.rotate(g, 120*j, origin=(0, r)) for j in range(3)])
        g = union([affinity.translate(g, j*a, 0) for j in range(spec.x_periods+1)])
        g = union([affinity.translate(g, 0, j*3*r)
                   for j in range(spec.y_half_periods//2+1)])
        return union([affinity.translate(g, 0, -j*3*r)
                      for j in range((spec.y_half_periods+1)//2+1)])

    xl, yl, xr, yr = spec.source_metal_bounds
    extent = box(xl, yl, xr, yr)
    upper, lower = box(xl, 0, xr, yr), box(xl, yl, xr, 0)
    rings = array(ring).intersection(upper if spec.layout == 'A_air' else extent)
    phase_a = array(motif_a).intersection(lower if spec.layout == 'BA' else upper)
    phase_b = (Polygon() if spec.layout == 'A_air' else
               array(b).intersection(upper if spec.layout == 'BA' else lower))
    if spec.centered:
        rings, phase_a, phase_b, extent = [affinity.translate(g, spec.horizontal_shift, 0)
                                          for g in (rings, phase_a, phase_b, extent)]
    core = union([rings, phase_a, phase_b])
    substrate = box(*spec.substrate_bounds)
    left, right = Polygon(), Polygon()
    if spec.probes_enabled:
        left = Polygon(spec.probe_coordinates)
        right = affinity.scale(left, -1, 1, origin=(0, 0))
        tolerance = spec.lattice_constant**2*1e-12
        for probe in (left, right):
            if probe.intersection(core).area <= tolerance:
                raise ValueError('Probe does not overlap crystal copper; adjust insertion, width or probe_y')
            if probe.difference(substrate).area > tolerance:
                raise ValueError('Probe is not fully supported by quartz; adjust substrate width or probe_y')
    return MetalHexGeometry(spec, ring, motif_a, b, rings, phase_a, phase_b,
                           union([core, left, right]), substrate, extent, core, left, right)
