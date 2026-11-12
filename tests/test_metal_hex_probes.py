"""Approved centred probe sketches, frozen numeric expectations from review."""
import pytest
from shapely.affinity import scale


@pytest.mark.parametrize('mode,ymin,area', [
    ('AB', -3.636, 9.996715627415632),
    ('BA', -3.636, 9.856592691630423), ('A_air', -.606, 5.287166855054615),
])
def test_approved_centered_geometry(mode, ymin, area):
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    spec = MetalHexSpec(layout=mode)
    g = build_geometry(spec)
    assert spec.centered and spec.probes_enabled
    assert spec.metal_bounds[0] == pytest.approx(-1.818)
    assert spec.metal_bounds[2] == pytest.approx(1.818)
    assert g.substrate.bounds == pytest.approx((-3.513, ymin, 3.513, 3.636))
    assert g.probe_left.bounds[0] == pytest.approx(-3.210)
    assert g.probe_right.bounds[2] == pytest.approx(3.210)
    assert g.probe_left.symmetric_difference(scale(g.probe_right,-1,1,origin=(0,0))).area < 1e-12
    assert g.metal.symmetric_difference(scale(g.metal,-1,1,origin=(0,0))).area < 1e-10
    for probe in (g.probe_left,g.probe_right):
        assert probe.intersection(g.core_metal).area > 1e-5
        assert probe.difference(g.substrate).area < 1e-12
    if area is not None:
        assert g.metal.area == pytest.approx(area, abs=1e-9)
    if mode=='A_air':
        assert g.phase_b.is_empty
        assert g.rings.bounds[1] == pytest.approx(0)
        assert g.probe_left.intersection(g.core_metal).bounds[1] >= -1e-12


def test_taper_parameters_and_air_substrate_remain_adjustable():
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    s = MetalHexSpec(layout='A_air', taper_length=1.5, neck_length=.3,
                    port_width=.18, tip_width=.12, probe_y=.06,
                    probe_insertion=.015, substrate_margin=.2, air_substrate_width=.35)
    g = build_geometry(s)
    assert g.substrate.bounds == pytest.approx((-3.803,-.35,3.803,3.636))
    assert g.probe_left.bounds == pytest.approx((-3.603,-.03,-1.803,.15))
    assert s == MetalHexSpec.from_dict(s.to_dict())


def test_legacy_json_restores_original_geometry_and_current_json_is_centered():
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    old = {'lattice_constant':.606,'substrate_thickness':.1,'ring_inset':.04,
           'pad_ratio':.5,'x_periods':6,'y_half_periods':6,'metal_thickness':0,'layout':'A_air'}
    legacy = MetalHexSpec.from_dict(old)
    assert not legacy.centered and not legacy.probes_enabled
    assert legacy == MetalHexSpec.legacy_notebook(layout='A_air')
    assert build_geometry(legacy).substrate.bounds == pytest.approx((-.303,-3.636,3.636,3.636))
    assert MetalHexSpec.from_dict(MetalHexSpec().to_dict()) == MetalHexSpec()


def test_centered_without_probes_still_has_equal_margins():
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    g=build_geometry(MetalHexSpec(probes_enabled=False))
    assert g.probe_left.is_empty and g.probe_right.is_empty
    assert g.substrate.bounds == pytest.approx((-2.121,-3.636,2.121,3.636))


@pytest.mark.parametrize('changes', [
    {'taper_length':0}, {'probe_insertion':2}, {'port_width':float('nan')},
    {'air_substrate_width':0}, {'centered':'yes'}, {'probes_enabled':1},
    {'centered':False}, {'probe_y':9}, {'air_substrate_width':.001,'layout':'A_air'},
])
def test_invalid_or_unconnected_probes_rejected(changes):
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    with pytest.raises((ValueError,TypeError)):
        build_geometry(MetalHexSpec(**changes))
