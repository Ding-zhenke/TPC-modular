"""Compatibility proxy for S-parameter text utilities in cst-automation."""

from importlib import import_module

__all__ = ['read_s2p_groups', 'filter_by_frequency',
           'filter_parameters_by_condition', 'find_param_indices']


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    try:
        module = import_module('cst_automation.s2p')
    except ImportError as exc:
        raise ImportError(
            'tpc_toolkit.s2p is a compatibility proxy. Install cst-automation '
            'to use the shared S-parameter utilities.'
        ) from exc
    return getattr(module, name)


def __dir__():
    return sorted(set(globals()) | set(__all__))
