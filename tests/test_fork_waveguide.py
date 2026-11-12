"""Offline geometry and native adapter checks for approved 10a fork design."""
import importlib.util
from pathlib import Path
import pytest
from shapely.affinity import scale
from shapely.geometry import box
from shapely.ops import unary_union
from mesh_grid.metal_hex.fork_waveguide import ForkWaveguideSpec, build_fork_waveguide
from topo_modeler.builders.fork_waveguide import build_fork_waveguide_cst

_p=Path(__file__).with_name('test_metal_hex_builder.py')
_s=importlib.util.spec_from_file_location('metal_fake',_p)
_m=importlib.util.module_from_spec(_s);_s.loader.exec_module(_m)


class App(_m.PlanarApp):
    def add(self,name1,name2,component1='component1',component2='component1'):
        self.shapes[name1]=unary_union([self.shapes[name1],self.shapes.pop(name2)])
    def delete_solid(self,name,component='component1'):
        self.shapes.pop(name)


@pytest.mark.parametrize('upper,lower',[(5,2),(5.5,2.5),(4,1)])
def test_row_boundaries_and_native_geometry_agree(upper,lower):
    spec=ForkWaveguideSpec(upper_rows=upper,lower_rows=lower)
    geom=build_fork_waveguide(spec)
    assert geom['substrate'].bounds[1] == pytest.approx(-lower*spec.row_spacing)
    assert geom['substrate'].bounds[3] == pytest.approx(upper*spec.row_spacing)
    app=App();result=build_fork_waveguide_cst(app,spec)
    for role in ('rings','phase_a','phase_b','probe_left','probe_right','substrate'):
        assert app.shapes[result['shapes'][role]].symmetric_difference(geom[role]).area < 1e-9
    assert app.params['g'] == spec.probe.gap
    assert app.params['yu'] == pytest.approx(upper*spec.row_spacing)
    assert app.params['yd'] == pytest.approx(lower*spec.row_spacing)


def test_changed_shared_gap_and_stub_dimensions_match_native():
    from mesh_grid.metal_hex.fork_probe import ForkProbeSpec
    spec=ForkWaveguideSpec(probe=ForkProbeSpec(gap=.08,stub_length=.15,stub_width=.06,stub_distance=.18))
    geom=build_fork_waveguide(spec);app=App();result=build_fork_waveguide_cst(app,spec)
    assert app.params['g']==pytest.approx(.08)
    for role in ('rings','probe_left','probe_right'):
        assert app.shapes[result['shapes'][role]].symmetric_difference(geom[role]).area<1e-9
    assert geom['core'].intersection(geom['slot_left']).area<1e-12


def test_half_row_default_shared_cut_and_contacts():
    spec=ForkWaveguideSpec();g=build_fork_waveguide(spec)
    from mesh_grid.metal_hex import build_geometry
    original=build_geometry(spec.base_spec())
    assert spec.y_bounds == pytest.approx((-1.0496227893867396,2.624056973466849))
    assert g['core'].intersection(g['slot_left']).area < 1e-12
    assert g['core'].intersection(g['slot_right']).area < 1e-12
    assert original.rings.intersection(g['slot_left']).area > 1e-6
    assert original.rings.intersection(g['slot_right']).area > 1e-6
    assert g['probe_left'].symmetric_difference(scale(g['probe_right'],-1,1,origin=(0,0))).area < 1e-12
    assert g['probe_left'].symmetric_difference(scale(g['probe_left'],1,-1,origin=(0,0))).area < 1e-12
    for feed in (g['probe_left'],g['probe_right']):
        for y0,y1 in [(-1,0),(0,1)]:
            assert feed.intersection(g['core']).intersection(box(-10,y0,10,y1)).area > 1e-8
        assert feed.difference(g['substrate']).area < 1e-12


def test_template_preview_and_json_roundtrip(tmp_path):
    import json
    from topo_templates.fork_waveguide import ForkWaveguide
    device=ForkWaveguide()
    files=device.preview(tmp_path)
    data=json.loads(files['json'].read_text(encoding='utf-8'))
    assert ForkWaveguideSpec.from_dict(data['spec']) == device.spec
    assert files['png'].read_bytes().startswith(b'\x89PNG')
    assert '<svg' in files['svg'].read_text(encoding='utf-8')
