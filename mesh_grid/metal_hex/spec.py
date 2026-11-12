"""Physical dimensions in mm; defaults use the approved centred probe sketch."""
from dataclasses import asdict, dataclass
import math
from numbers import Integral, Real
from typing import Optional


@dataclass(frozen=True)
class MetalHexSpec:
    """Straight layout with centred quartz and mirror-paired copper tapers.

    layout='AB': A above, B below; 'BA': B above, A below;
    'A_air': A above, no lower crystal, with adjustable air-side quartz width.

    x_periods is metal clipping length/a, NOT number of cell centres.
    y_half_periods is region half-height/a; source array repetition rules
    are derived from it. ring_inset is radial, not normal trace width.
    Only zero-thickness metal sheets are supported in this first version.
    """
    lattice_constant: float = .606
    substrate_thickness: float = .1
    ring_inset: float = .04
    pad_ratio: float = .5
    x_periods: int = 6
    y_half_periods: int = 6
    metal_thickness: float = 0.
    layout: str = 'AB'
    centered: bool = True
    probes_enabled: bool = True
    taper_length: Optional[float] = None
    neck_length: float = .2
    port_width: float = .2
    tip_width: Optional[float] = None
    probe_insertion: float = .02
    probe_y: Optional[float] = None
    substrate_margin: Optional[float] = None
    air_substrate_width: Optional[float] = None

    def __post_init__(self):
        if self.layout not in ('AB', 'BA', 'A_air'):
            raise ValueError("layout must be 'AB', 'BA' or 'A_air'")
        for name in ('centered', 'probes_enabled'):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f'{name} must be bool')
        if self.probes_enabled and not self.centered:
            raise ValueError('Paired probes require centered=True')
        for name in ('lattice_constant', 'substrate_thickness', 'ring_inset', 'pad_ratio'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f'{name} must be a real number')
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be finite and positive')
            object.__setattr__(self, name, float(value))
        for name in ('x_periods', 'y_half_periods'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise TypeError(f'{name} must be a positive integer')
            if value < 1:
                raise ValueError(f'{name} must be a positive integer')
            object.__setattr__(self, name, int(value))
        if (isinstance(self.metal_thickness, bool)
                or not isinstance(self.metal_thickness, Real)):
            raise TypeError('metal_thickness must be numeric zero')
        if self.metal_thickness != 0:
            raise ValueError('Only metal_thickness=0 sheets are supported')
        object.__setattr__(self, 'metal_thickness', 0.)
        if self.ring_inset >= self.ring_radius:
            raise ValueError('ring_inset must be smaller than the outer ring radius')
        if self.pad_ratio > 1:
            raise ValueError('pad_ratio must be in (0, 1]')
        defaults = dict(taper_length=2*self.lattice_constant,
                        tip_width=self.lattice_constant/2 if self.layout=='AB' else .1,
                        probe_y=.05 if self.layout=='A_air' else 0.,
                        substrate_margin=self.lattice_constant/2,
                        air_substrate_width=self.lattice_constant if self.layout=='A_air'
                        else self.lattice_constant*self.y_half_periods)
        for name, default in defaults.items():
            if getattr(self, name) is None:
                object.__setattr__(self, name, default)
        for name in ('taper_length', 'neck_length', 'port_width', 'tip_width',
                     'probe_insertion', 'substrate_margin', 'air_substrate_width', 'probe_y'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f'{name} must be a real number')
            if not math.isfinite(value):
                raise ValueError(f'{name} must be finite')
            if name != 'probe_y' and (value < 0 or (name != 'substrate_margin' and value == 0)):
                raise ValueError(f'{name} must be positive (margin may be zero)')
            object.__setattr__(self, name, float(value))
        if self.probes_enabled and self.probe_insertion >= min(
                self.taper_length, self.x_periods*self.lattice_constant/2):
            raise ValueError('probe_insertion must be shorter than taper and half core length')

    @property
    def ring_radius(self):
        return self.lattice_constant / math.sqrt(3)

    @property
    def pad_length(self):
        return self.pad_ratio * self.ring_radius

    @property
    def single_ring_width(self):
        return self.ring_inset * math.cos(math.pi / 6)

    @property
    def right_blank(self):
        return self.substrate_bounds[2] - self.metal_bounds[2]

    @property
    def metal_bounds(self):
        """Crystal clipping envelope; probes are separate geometry."""
        xl, yl, xr, yr = self.source_metal_bounds
        return xl+self.horizontal_shift, yl, xr+self.horizontal_shift, yr

    @property
    def source_metal_bounds(self):
        a = self.lattice_constant
        return (-a/2, -a*self.y_half_periods,
                -a/2+a*self.x_periods, a*self.y_half_periods)

    @property
    def horizontal_shift(self):
        return -(self.x_periods-1)*self.lattice_constant/2 if self.centered else 0.

    @property
    def substrate_bounds(self):
        xl, yl, xr, yr = self.metal_bounds
        if self.layout == 'A_air':
            yl = -self.air_substrate_width
        if self.centered:
            half = (-self.probe_coordinates[0][0] if self.probes_enabled else xr) + self.substrate_margin
            return -half, yl, half, yr
        return xl, yl, xr+self.lattice_constant/2, yr

    @property
    def probe_coordinates(self):
        """Left copper polygon, six vertices; right is its exact x reflection."""
        tip = -self.x_periods*self.lattice_constant/2+self.probe_insertion
        base = tip-self.taper_length
        end = base-self.neck_length
        y, wp, wt = self.probe_y, self.port_width, self.tip_width
        return ((end,y-wp/2),(base,y-wp/2),(tip,y-wt/2),
                (tip,y+wt/2),(base,y+wp/2),(end,y+wp/2))

    @property
    def domain_wall(self):
        xl, _, xr, _ = self.metal_bounds
        return ((xl, 0.), (xr, 0.))

    @property
    def phase_sides(self):
        if self.layout == 'A_air':
            return {'A': 'y>0', 'air': 'y<0 (no crystal; adjustable quartz support)'}
        upper, lower = self.layout
        return {upper: 'y>0', lower: 'y<0'}

    def to_dict(self):
        """JSON-ready constructor fields only (lengths in mm)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, fields):
        """Round-trip current specs; pre-probe JSON restores notebook geometry."""
        old_fields = {'lattice_constant', 'substrate_thickness', 'ring_inset', 'pad_ratio',
                      'x_periods', 'y_half_periods', 'metal_thickness', 'layout'}
        if set(fields) <= old_fields:
            return cls.legacy_notebook(**fields)
        return cls(**fields)

    @classmethod
    def legacy_notebook(cls, **fields):
        """Explicit old placement, no probes, full quartz; source remains read-only."""
        width = fields.get('lattice_constant', .606)*fields.get('y_half_periods', 6)
        return cls(centered=False, probes_enabled=False, air_substrate_width=width, **fields)

    def cst_parameters(self):
        """Dependency-ordered parameters, all referenced by native geometry.

        Short CST names avoid carrying unused historical notebook variables.
        This mapping is the adapter's sole parameter source.
        """
        parameters = dict(a=self.lattice_constant, h=self.substrate_thickness,
                    t=self.metal_thickness, d1=self.ring_inset, k1=self.pad_ratio,
                    nx=self.x_periods, ny=self.y_half_periods,
                    r1='a/sqr(3)', p1='k1*r1', xl='-a/2', xr='xl+nx*a',
                    ym='ny*a', dy='3*r1', nu='ny', nd='ny+1')
        if self.y_half_periods == 1:
            del parameters['nu']  # positive-Y zero-copy operation is omitted
        if self.centered:
            parameters['sx'] = '-(nx-1)*a/2'
            parameters['mg'] = self.substrate_margin
        if self.probes_enabled:
            parameters.update(lt=self.taper_length, ln=self.neck_length,
                              wp=self.port_width, wt=self.tip_width,
                              li=self.probe_insertion, yf=self.probe_y,
                              xt='-nx*a/2+li', xb='xt-lt', xe='xb-ln')
        if self.centered:
            parameters['bx'] = '-xe+mg' if self.probes_enabled else 'nx*a/2+mg'
        if self.layout == 'A_air':
            parameters['wa'] = self.air_substrate_width
        return parameters
