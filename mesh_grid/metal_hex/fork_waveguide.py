"""AB straight waveguide with shared-gap, slotted dual-stub fork feeds."""
from dataclasses import dataclass, field, asdict
import math
from .spec import MetalHexSpec
from .geometry import build_geometry
from .fork_probe import ForkProbeSpec, build_fork_probe


@dataclass(frozen=True)
class ForkWaveguideSpec:
    """Upper/lower boundary positions in row spacings sqrt(3)*a/2.

    The default boundaries pass through the fifth upper and second lower
    hexagon-centre rows, leaving half of each boundary row.
    """
    lattice_constant: float = .606
    x_periods: int = 10
    upper_rows: float = 5.
    lower_rows: float = 2.
    substrate_thickness: float = .1
    ring_inset: float = .04
    pad_ratio: float = .5
    substrate_margin: float = .303
    probe: ForkProbeSpec = field(default_factory=ForkProbeSpec)

    def __post_init__(self):
        for name in ('lattice_constant','upper_rows','lower_rows','substrate_thickness',
                     'ring_inset','pad_ratio','substrate_margin'):
            value=getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be finite and positive')
        if isinstance(self.x_periods,bool) or not isinstance(self.x_periods,int) or self.x_periods < 1:
            raise ValueError('x_periods must be a positive integer')
        if not isinstance(self.probe,ForkProbeSpec):
            raise TypeError('probe must be ForkProbeSpec')

    @property
    def row_spacing(self):
        return math.sqrt(3)*self.lattice_constant/2

    @property
    def y_bounds(self):
        return -self.lower_rows*self.row_spacing, self.upper_rows*self.row_spacing

    def base_spec(self):
        n=max(2,math.ceil(max(self.upper_rows,self.lower_rows)*math.sqrt(3)/2)+2)
        return MetalHexSpec(lattice_constant=self.lattice_constant, x_periods=self.x_periods,
                            y_half_periods=n, substrate_thickness=self.substrate_thickness,
                            ring_inset=self.ring_inset,pad_ratio=self.pad_ratio,
                            centered=True,probes_enabled=False,layout='AB')

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, values):
        values=dict(values)
        if 'probe' in values:
            values['probe']=ForkProbeSpec(**values['probe'])
        return cls(**values)


def build_fork_waveguide(spec=None):
    """Build actual copper polygons offline and verify both arm contacts."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    spec = ForkWaveguideSpec() if spec is None else spec
    if not isinstance(spec,ForkWaveguideSpec):
        raise TypeError('spec must be ForkWaveguideSpec')
    base=build_geometry(spec.base_spec())
    half=spec.x_periods*spec.lattice_constant/2
    ymin,ymax=spec.y_bounds
    clip=box(-half,ymin,half,ymax)
    feed=build_fork_probe(spec.probe,boundary_x=-half,
                          ring_width=spec.ring_inset*math.cos(math.pi/6))
    slots=unary_union([feed['slot_left'],feed['slot_right']])
    rings=base.rings.intersection(clip).difference(slots)
    phase_a=base.phase_a.intersection(clip)
    phase_b=base.phase_b.intersection(clip)
    if unary_union([phase_a,phase_b]).intersection(slots).area > 1e-12:
        raise ValueError('slot intersects a phase pad; adjust geometry')
    core=unary_union([rings,phase_a,phase_b])
    reach=-feed['left'].bounds[0]+spec.substrate_margin
    substrate=box(-reach,ymin,reach,ymax)
    for probe in (feed['left'],feed['right']):
        if probe.difference(substrate).area>1e-12:
            raise ValueError('probe is not supported by substrate')
        for lo,hi in ((-1e3,0),(0,1e3)):
            if probe.intersection(core).intersection(box(-1e3,lo,1e3,hi)).area<=1e-12:
                raise ValueError('both fork arms must overlap the crystal copper')
    return {'rings':rings,'phase_a':phase_a,'phase_b':phase_b,'core':core,
            'probe_left':feed['left'],'probe_right':feed['right'],
            'slot_left':feed['slot_left'],'slot_right':feed['slot_right'],
            'substrate':substrate,'metal':unary_union([core,feed['left'],feed['right']]),
            'spec':spec}
