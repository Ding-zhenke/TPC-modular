"""Interpret the adapter's native parametric operations as independent XY shapes.

This proves the adapter's geometric command intent, not CST sheet-kernel success.
"""
import math
import json

import pytest
from shapely.geometry import Polygon, box
from shapely.affinity import rotate, translate
from shapely.ops import unary_union


class PlanarApp:
    """Caller-owned CST protocol double with actual planar state transitions."""
    def __init__(self, unit='mm'):
        self.unit, self.params, self.curves, self.shapes = unit, {}, {}, {}
        self.expressions, self.thicknesses, self.translations = [], [], []
        self.materials = []

    def value(self, value):
        if not isinstance(value, str):
            return value
        return eval(value, {'__builtins__': {}}, dict(
            self.params, sqr=math.sqrt, cosd=lambda x: math.cos(math.radians(x)),
            sind=lambda x: math.sin(math.radians(x)), int=int))

    def get_units(self, unit_type='length'):
        return self.unit

    def activate_global_wcs(self):
        pass

    def new_curve(self, name):
        pass

    def new_material(self, name):
        self.materials.append(name)

    def para(self, name, value, log_flag=0, expression=''):
        self.expressions.append((name, value))
        self.params[name] = self.value(value)

    def polyline(self, data, name='1', curve='curve1', log_flag=1):
        self.curves[f'{curve}:{name}'] = Polygon(
            [(self.value(x), self.value(y)) for x, y in data])

    def extrude(self, curve, name, thickness, component='component1', material='PEC', log_flag=1):
        self.thicknesses.append(self.value(thickness))
        self.shapes[name] = self.curves.pop(curve)

    def hexagon(self, a, h, center, theta, name, curve='curve1',
                component='component1', material='Silicon (lossy)'):
        r, angle = self.value(a), theta[2]
        self.thicknesses.append(self.value(h))
        g = Polygon([(r*math.cos(math.radians(angle+60*j)),
                      r*math.sin(math.radians(angle+60*j))) for j in range(6)])
        self.shapes[name] = translate(g, self.value(center[0]), self.value(center[1]))

    def square(self, xmin, xmax, ymin, ymax, zmin, zmax, name,
               component='component1', material='PEC'):
        self.shapes[name] = box(self.value(xmin), self.value(ymin),
                                self.value(xmax), self.value(ymax))
        self.substrate_z = self.value(zmin), self.value(zmax)

    def subtract(self, name1, name2, component1='component1', component2='component1'):
        self.shapes[name1] = self.shapes[name1].difference(self.shapes.pop(name2))

    def intersect(self, name1, name2, component1='component1', component2='component1'):
        self.shapes[name1] = self.shapes[name1].intersection(self.shapes.pop(name2))

    def rotation(self, name, angle, center=None, repetition=1, component='component1',
                 copy=False, unite=False, log_flag=1):
        centre = tuple(self.value(v) for v in (center or [0, 0, 0])[:2])
        source = self.shapes[name]
        copies = [rotate(source, angle[2]*j, origin=centre) for j in range(1, repetition+1)]
        self.shapes[name] = unary_union([source, *copies]) if copy else copies[-1]

    def translate(self, name, vector, component='component1', repetitions=1,
                  copy=False, unite=False, log_flag=1):
        n = int(self.value(repetitions))
        assert n > 0, 'CST disallows zero copy repetitions'
        self.translations.append(repetitions)
        source = self.shapes[name]
        dx, dy = self.value(vector[0]), self.value(vector[1])
        copies = [translate(source, j*dx, j*dy) for j in range(1, n+1)]
        self.shapes[name] = unary_union([source, *copies]) if copy else copies[-1]


@pytest.mark.parametrize('dimensions', [{}, {'x_periods': 1, 'y_half_periods': 1},
                                         {'x_periods': 3, 'y_half_periods': 3},
                                         {'layout': 'BA'}, {'layout': 'A_air'},
                                         {'layout':'A_air','taper_length':1.5,'neck_length':.3,
                                          'port_width':.18,'tip_width':.12,'probe_y':.06,
                                          'probe_insertion':.015,'substrate_margin':.2,'air_substrate_width':.35},
                                         {'centered':False,'probes_enabled':False,'layout':'AB'},
                                         {'lattice_constant': .8, 'ring_inset': .05, 'pad_ratio': .4}])
def test_native_commands_match_offline_geometry(dimensions):
    from mesh_grid.metal_hex import MetalHexSpec, build_geometry
    from topo_modeler.builders.metal_hex import build_metal_hex
    spec, app = MetalHexSpec(**dimensions), PlanarApp()
    result = build_metal_hex(app, spec)
    expected = build_geometry(spec)
    names = result['shapes']
    for role, geometry in [('rings', expected.rings), ('phase_a', expected.phase_a),
                           ('phase_b', expected.phase_b), ('substrate', expected.substrate),
                           ('probe_left',expected.probe_left), ('probe_right',expected.probe_right)]:
        if geometry.is_empty:
            assert role not in names
        else:
            assert app.shapes[names[role]].symmetric_difference(geometry).area < 1e-10
    assert app.substrate_z == pytest.approx((-spec.substrate_thickness, 0))
    assert all(v == 0 for v in app.thicknesses)
    assert set(app.shapes) == set(names.values())  # no leftover clipping solids
    assert result['evidence'] == 'native geometry commands submitted; CST readback unverified'
    assert ('r1', 'a/sqr(3)') in app.expressions
    assert 'int(nx)' in app.translations
    if spec.y_half_periods > 1:
        assert 'int(nu/2)' in app.translations
    if spec.probes_enabled:
        assert ('xt','-nx*a/2+li') in app.expressions
        assert ('bx','-xe+mg') in app.expressions


def test_detached_probe_fails_before_any_cst_mutation():
    from mesh_grid.metal_hex import MetalHexSpec
    from topo_modeler.builders.metal_hex import build_metal_hex
    app = PlanarApp()
    with pytest.raises(ValueError, match='Probe'):
        build_metal_hex(app,MetalHexSpec(probe_y=9))
    assert not app.params and not app.materials and not app.shapes


def test_wrong_units_and_invalid_names_fail_before_mutation():
    from topo_modeler.builders.metal_hex import build_metal_hex
    app = PlanarApp(unit='um')
    with pytest.raises(ValueError, match='mm'):
        build_metal_hex(app)
    assert not app.params and not app.materials
    app.unit = 'mm'
    with pytest.raises(ValueError):
        build_metal_hex(app, prefix='bad"name')
    assert not app.params and not app.materials


@pytest.mark.parametrize('layout,stem', [('AB', 'metal_hex_ab'), ('BA', 'metal_hex_ba'), ('A_air', 'metal_hex_a_air')])
def test_template_exports_same_geometry_and_reusable_json(tmp_path, layout, stem):
    from topo_templates.metal_hex import MetalHexStraight
    from mesh_grid.metal_hex import MetalHexSpec
    device = MetalHexStraight(MetalHexSpec(layout=layout))
    assert device.spec == MetalHexSpec(layout=layout)
    output = device.preview(tmp_path)
    assert output['png'].read_bytes().startswith(b'\x89PNG')
    assert output['png'].stem == stem
    assert '<svg' in output['svg'].read_text(encoding='utf-8')
    doc = json.loads(output['json'].read_text(encoding='utf-8'))
    assert MetalHexSpec.from_dict(doc['spec']) == device.spec
    assert doc['metal_area_mm2'] == pytest.approx(device.geometry().metal.area)
    result = device.build(PlanarApp())
    expected = {'rings', 'phase_a', 'substrate', 'probe_left', 'probe_right'}
    if layout != 'A_air': expected.add('phase_b')
    assert set(result['shapes']) == expected
