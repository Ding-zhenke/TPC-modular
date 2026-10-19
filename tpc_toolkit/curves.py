"""Compatibility proxy for the single curve implementation in cst-automation.

The proxy is importable offline. Resolving a function requires the data-only
submodule supplied by the optional ``cst-automation`` dependency.
"""

from importlib import import_module

__all__ = ['contiguous_bands', 'find_resonances', 'match_resonances',
           'resonance_criterion']


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    try:
        module = import_module('cst_automation.curves')
    except ImportError as exc:
        raise ImportError(
            'tpc_toolkit.curves is a compatibility proxy. Install the '
            'cst-automation data-analysis extra to use curve rules.'
        ) from exc
    return getattr(module, name)


def __dir__():
    return sorted(set(globals()) | set(__all__))
