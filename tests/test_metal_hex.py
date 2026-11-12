"""Approved notebook geometry, independent literal measurements and invariants."""
import json
import subprocess
import sys

import pytest


def test_import_parameters_without_geometry_plotting_or_cst():
    result = subprocess.run([sys.executable, '-B', '-c',
        "import sys; from mesh_grid.metal_hex import MetalHexSpec; "
        "s=MetalHexSpec(); "
        "assert not any(n.split('.')[0] in {'shapely','matplotlib','cst','cst_solver','cst_automation'} for n in sys.modules)"],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_approved_baseline_dimensions_and_geometry():
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    spec = MetalHexSpec.legacy_notebook()
    geom = build_geometry(spec)
    assert spec.ring_radius == pytest.approx(.349874263128913)
    assert spec.single_ring_width == pytest.approx(.03464101615137755)
    assert geom.substrate.bounds == pytest.approx((-.303, -3.636, 3.636, 3.636))
    assert geom.metal.bounds == pytest.approx((-.303, -3.4987426312891325, 3.333, 3.636))
    assert geom.metal.area == pytest.approx(9.319165634016292, abs=1e-9)
    assert geom.bottom_blank == pytest.approx(.13725736871086758)
    assert spec.right_blank == pytest.approx(.303)
    assert geom.metal.is_valid
    assert geom.metal.difference(geom.metal_extent).area < 1e-12


def test_ab_rotation_and_phase_side():
    from shapely.affinity import rotate
    from shapely.geometry import box
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    g = build_geometry(MetalHexSpec())
    assert g.unit_a.symmetric_difference(rotate(g.unit_b, 180, origin=(0, 0))).area < 1e-12
    assert g.phase_a.intersection(box(-10, -10, 10, 0)).area < 1e-12
    assert g.phase_b.intersection(box(-10, 0, 10, 10)).area < 1e-12


def test_geometry_scales_and_spec_roundtrips():
    from shapely.affinity import scale
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    base = MetalHexSpec.legacy_notebook()
    double = MetalHexSpec.legacy_notebook(lattice_constant=1.212, ring_inset=.08, substrate_thickness=.2)
    assert build_geometry(double).metal.symmetric_difference(
        scale(build_geometry(base).metal, 2, 2, origin=(0, 0))).area < 1e-10
    assert MetalHexSpec.from_dict(json.loads(json.dumps(double.to_dict()))) == double
    with pytest.raises(TypeError):
        MetalHexSpec.from_dict({'unused_old_parameter': 1})


@pytest.mark.parametrize('kwargs', [
    {'lattice_constant': 0}, {'substrate_thickness': float('nan')},
    {'ring_inset': -.01}, {'ring_inset': .4}, {'pad_ratio': 0},
    {'pad_ratio': 1.1}, {'metal_thickness': .001},
    {'x_periods': 0}, {'x_periods': 2.5}, {'x_periods': True},
    {'y_half_periods': -1}, {'lattice_constant': True},
])
def test_reject_invalid_dimensions(kwargs):
    from mesh_grid.metal_hex import MetalHexSpec
    with pytest.raises((ValueError, TypeError)):
        MetalHexSpec(**kwargs)


def test_small_and_odd_array_ranges_are_valid():
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    for n in [1, 3, 7]:
        g = build_geometry(MetalHexSpec.legacy_notebook(x_periods=1, y_half_periods=n))
        assert g.metal.is_valid and not g.metal.is_empty
        assert g.metal.difference(g.metal_extent).area < 1e-12


def test_ba_swaps_phase_regions_without_mirroring_array_or_substrate():
    from shapely.geometry import box
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    ab = build_geometry(MetalHexSpec())
    ba = build_geometry(MetalHexSpec(layout='BA'))
    assert ba.phase_a.bounds[3] <= 0
    assert ba.phase_b.bounds[1] >= 0
    assert ba.rings.symmetric_difference(ab.rings).area < 1e-12
    assert ba.substrate.equals(ab.substrate)
    assert ba.core_metal.difference(box(-1.818, -3.636, 1.818, 3.636)).area < 1e-12
    assert ba.summary()['phase_sides'] == {'B': 'y>0', 'A': 'y<0'}
    assert MetalHexSpec.from_dict(ba.spec.to_dict()).layout == 'BA'


def test_a_air_removes_lower_crystal_and_keeps_adjustable_substrate():
    from shapely.geometry import box
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    ab = build_geometry(MetalHexSpec())
    aa = build_geometry(MetalHexSpec(layout='A_air'))
    assert aa.phase_b.is_empty
    assert aa.core_metal.bounds[1] >= 0
    assert aa.core_metal.symmetric_difference(ab.core_metal.intersection(box(-10, 0, 10, 10))).area < 1e-10
    assert aa.substrate.bounds[1] == pytest.approx(-.606)
    assert aa.summary()['phase_sides'] == {'A': 'y>0', 'air': 'y<0 (no crystal; adjustable quartz support)'}


def test_invalid_layout_rejected():
    from mesh_grid.metal_hex import MetalHexSpec
    with pytest.raises(ValueError, match='layout'):
        MetalHexSpec(layout='wrong')
