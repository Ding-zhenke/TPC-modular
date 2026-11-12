"""Metal hexagonal AB lattices; parameter imports need no geometry or CST backend."""
from .spec import MetalHexSpec

__all__ = ['MetalHexSpec', 'build_geometry', 'export_preview', 'ForkWaveguideSpec', 'build_fork_waveguide']


def __getattr__(name):
    if name in ('ForkWaveguideSpec', 'build_fork_waveguide'):
        from . import fork_waveguide
        return getattr(fork_waveguide, name)
    if name == 'build_geometry':
        from .geometry import build_geometry
        return build_geometry
    if name == 'export_preview':
        from .plotting import export_preview
        return export_preview
    raise AttributeError(f'{__name__!r} has no attribute {name!r}')
