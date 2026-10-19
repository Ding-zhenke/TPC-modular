import warnings
import sys


def test_legacy_templates_shim_reexports_topology_template():
    sys.modules.pop('templates', None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        from templates import StraightWaveguide
    from topo_templates import StraightWaveguide as Current

    assert StraightWaveguide is Current
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)


def test_shared_curve_proxy_reports_missing_optional_distribution():
    import tpc_toolkit.curves as curves

    try:
        curves.find_resonances
    except ImportError as exc:
        assert 'cst-automation' in str(exc)
    else:
        # A development environment may already have the real shared module.
        assert curves.find_resonances.__module__ == 'cst_automation.curves'
