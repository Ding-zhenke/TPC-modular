"""Planar forked feed geometry for the slotted metal-hexagonal interface.

Dimensions are millimetres. The slot gap and fork gap share one parameter.
The wide-end default is a quasi-static estimate for the documented substrate,
not an electromagnetic impedance or matching verification.
"""
from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class ForkProbeSpec:
    wide_width: float = .213938021932
    neck_length: float = .270
    taper_length: float = .780
    fork_length: float = .320
    arm_length: float = .312
    arm_width: float = .050
    gap: float = .060
    stub_length: float = .190
    stub_width: float = .080
    stub_distance: float = .192
    insertion: float = .012

    def __post_init__(self):
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f'{name} must be a real number')
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be finite and positive')
        if self.insertion >= self.arm_length:
            raise ValueError('insertion must be smaller than arm_length')
        if self.fork_length >= self.taper_length:
            raise ValueError('fork_length must be smaller than taper_length')
        if self.stub_distance - self.stub_width / 2 <= 0 or self.stub_distance + self.stub_width / 2 >= self.arm_length:
            raise ValueError('stub must lie entirely within the straight arms')

    def coordinates(self):
        """Return closed left-facing outline relative to the crystal boundary."""
        tip = self.insertion
        arm = tip - self.arm_length
        taper = arm - self.taper_length
        end = taper - self.neck_length
        fork = arm - self.fork_length
        outer = self.gap / 2 + self.arm_width
        return ((end, -self.wide_width/2), (taper, -self.wide_width/2),
                (arm, -outer), (tip, -outer), (tip, -self.gap/2),
                (arm, -self.gap/2), (fork, 0), (arm, self.gap/2),
                (tip, self.gap/2), (tip, outer), (arm, outer),
                (taper, self.wide_width/2), (end, self.wide_width/2),
                (end, -self.wide_width/2))


def build_fork_probe(spec=None, *, boundary_x=0.0, ring_width=.0346410161514):
    """Return left probe, mirrored right probe and cutouts at +/- boundary.

    ``boundary_x`` is the negative x coordinate of the left crystal edge.
    ``ring_width`` is the full perpendicular width of the edge being cut.
    A small fixed overlap joins each stub to its arm before union.
    """
    from shapely.affinity import scale, translate
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    spec = spec or ForkProbeSpec()
    if not isinstance(spec, ForkProbeSpec):
        raise TypeError('spec must be ForkProbeSpec')
    if boundary_x > 0 or not math.isfinite(boundary_x):
        raise ValueError('boundary_x must be finite and non-positive')
    if not math.isfinite(ring_width) or ring_width <= 0:
        raise ValueError('ring_width must be finite and positive')
    outer = spec.gap/2 + spec.arm_width
    center = spec.insertion - spec.stub_distance
    x0, x1 = center-spec.stub_width/2, center+spec.stub_width/2
    # Touching rectangles share finite-length edges with each arm.
    upper = box(x0, outer, x1, outer+spec.stub_length)
    lower = box(x0, -outer-spec.stub_length, x1, -outer)
    local = unary_union([Polygon(spec.coordinates()), upper, lower])
    left = translate(local, xoff=boundary_x)
    right = scale(left, -1, 1, origin=(0, 0))
    # Cover the whole boundary strip with finite tolerance on either side.
    slot = box(boundary_x-ring_width, -spec.gap/2,
               boundary_x+ring_width+spec.insertion, spec.gap/2)
    return {'left': left, 'right': right, 'slot_left': slot,
            'slot_right': scale(slot, -1, 1, origin=(0, 0)),
            'gap': spec.gap}
