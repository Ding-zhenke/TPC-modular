"""Scene geometry and exported evidence use one source of truth."""
import importlib.util
import math

import pytest
from shapely.geometry import Polygon, Point

from tpc_editor.document import new_document, xy
from tpc_editor.graph import apply_command


def geometry():
    assert importlib.util.find_spec('tpc_editor.geometry'), 'Region/scene implementation missing'
    from tpc_editor.geometry import build_scene
    return build_scene


def straight():
    doc = new_document()
    doc['parameters']['confirmed'] = True
    for r, c in [(0, -8), (0, 8)]:
        doc = apply_command(doc, {'type': 'point', 'r': r, 'c': c})
    return apply_command(doc, {'type': 'end'})


def assign(doc):
    for face in geometry()(doc)['faces']:
        phase = 'A' if face['center'][1] < 0 else 'B'
        doc = apply_command(doc, {'type': 'phase', 'region': face['id'], 'phase': phase})
    return doc


def test_boundary_to_boundary_path_creates_two_assignable_faces():
    scene = geometry()(straight())
    assert len(scene['faces']) == 2
    doc = assign(straight())
    scene = geometry()(doc)
    assert {f['phase'] for f in scene['faces']} == {'A', 'B'}
    assert not any(c['code'] in ('same_phase', 'unassigned', 'dangling') for c in scene['checks'])


def test_scene_points_use_domain_wall_coordinates_and_holes_match_library():
    from mesh_grid.tri_grid import TopoPath, generate_crystal_holes
    doc = assign(straight())
    scene = geometry()(doc)
    assert scene['nodes']['P01']['xy'] == pytest.approx(xy({'r': 0, 'c': -8}, doc['parameters']))
    assert any(p['r'] == 0 and p['c'] == 0 and p['xy'] == [0.0, 0.0] for p in scene['snap_points'])
    a = doc['parameters']['a']
    expected = generate_crystal_holes(TopoPath([(0, 0), (0, 4)], a), xup=4, yup=4, ydn=4)
    for hole in scene['holes']:
        if 0 < hole['center'][0] < 3*a:
            assert min(math.dist(hole['center'], x) for x in expected['centers']) < a*1e-7
        assert min(abs(hole['size']-v*a) for v in [0.35, 0.65]) < 1e-12


def test_external_partial_holes_are_omitted_but_do_not_block_export():
    doc = assign(straight())
    scene = geometry()(doc)
    assert scene['omitted_holes']
    domain = Polygon(doc['boundary']).buffer(1e-9)
    assert all(domain.covers(Polygon(h['vertices'])) for h in scene['holes'])
    assert not any(c['code'] == 'boundary_hole' and c['level'] == 'error' for c in scene['checks'])


def test_dxf_matches_editor_geometry_in_world_coordinates(tmp_path):
    import ezdxf
    from tpc_editor.export import render_dxf

    doc = assign(straight())
    scene = geometry()(doc)
    file = tmp_path / 'layout.dxf'
    file.write_bytes(render_dxf(doc))
    drawing = ezdxf.readfile(file)
    assert drawing.units == ezdxf.units.MM
    model = drawing.modelspace()
    for layer, rings in [('BOUNDARY', [doc['boundary']])] + [
        ('HOLES_' + phase, [h['vertices'] for h in scene['holes'] if h['phase'] == phase])
        for phase in ('A', 'B')
    ]:
        entities = list(model.query(f'LWPOLYLINE[layer=="{layer}"]'))
        assert len(entities) == len(rings) > 0
        for entity, ring in zip(entities, rings):
            assert entity.closed and list(entity.get_points('xy')) == list(map(tuple, ring))
    wall, = model.query('LINE[layer=="DOMAIN_WALL"]')
    edge, = scene['edges'].values()
    assert [list(wall.dxf.start)[:2], list(wall.dxf.end)[:2]] == edge['xy']


def test_internal_dangling_path_and_separate_crossing_are_problems():
    doc = new_document()
    for r, c in [(0, 0), (0, 3)]:
        doc = apply_command(doc, {'type': 'point', 'r': r, 'c': c})
    assert any(c['code'] == 'dangling' for c in geometry()(doc)['checks'])
    doc['crossings'] = [{'r': 0, 'c': 1, 'mode': 'separate'}]
    # Stale separation markers cannot create a fake crossing in the scene.
    assert not any(c['code'] == 'separate_crossing' for c in geometry()(doc)['checks'])


def test_merge_of_distinct_regions_does_not_retain_a_stale_label():
    doc = assign(straight())
    doc = apply_command(doc, {'type': 'delete', 'id': next(iter(doc['edges']))})
    scene = geometry()(doc)
    assert len(scene['faces']) == 1
    assert scene['faces'][0]['phase'] is None


def test_svg_and_png_include_dimensions_and_unconfirmed_status():
    geometry()
    from tpc_editor.export import render_svg, render_png
    doc = new_document()
    svg = render_svg(doc)
    assert 'mm' in svg and 'a=' in svg and '草稿' in svg
    assert 'viewBox=' in svg
    assert render_png(doc).startswith(b'\x89PNG\r\n\x1a\n')


def test_oblique_faces_survive_wkt_roundoff_and_can_be_assigned():
    doc = new_document()
    doc['parameters']['a'] = 0.1
    doc['boundary'] = [xy({'r': r, 'c': c}, doc['parameters'])
                       for r, c in [(-4, -4), (-4, 4), (4, 4), (4, -4)]]
    for r, c in [(-4, 0), (4, 0)]:
        doc = apply_command(doc, {'type': 'point', 'r': r, 'c': c})
    faces = geometry()(doc)['faces']
    assert len(faces) == 2
    for phase, f in zip(['A', 'B'], faces):
        doc = apply_command(doc, {'type': 'phase', 'region': f['id'], 'phase': phase})
    assert {f['phase'] for f in geometry()(doc)['faces']} == {'A', 'B'}


def test_merged_labels_cannot_resurrect_when_wall_is_redrawn():
    doc = assign(straight())
    doc = apply_command(doc, {'type': 'delete', 'id': next(iter(doc['edges']))})
    doc = apply_command(doc, {'type': 'point', 'r': 0, 'c': -8})
    doc = apply_command(doc, {'type': 'point', 'r': 0, 'c': 8})
    assert all(f['phase'] is None for f in geometry()(doc)['faces'])


def test_portrait_svg_retains_readable_parameter_and_coordinate_space():
    import re
    from tpc_editor.export import render_svg
    doc = new_document()
    a = doc['parameters']['a']
    doc['boundary'] = [[-a, -4*a], [a, -4*a], [a, 4*a], [-a, 4*a]]
    svg = render_svg(doc)
    box = re.search(r'viewBox="([^"]+)"', svg)[1].split()
    assert float(box[2]) >= 1000


def test_imported_crossing_is_detected_without_a_decision_marker():
    doc = new_document()
    for r, c in [(0, -3), (0, 3)]:
        doc = apply_command(doc, {'type': 'point', 'r': r, 'c': c})
    doc = apply_command(doc, {'type': 'end'})
    doc = apply_command(doc, {'type': 'point', 'r': -2, 'c': 0})
    doc = apply_command(doc, {'type': 'point', 'r': 2, 'c': 0, 'crossing': 'separate'})
    doc['crossings'] = []
    assert any(c['code'] == 'unresolved_crossing' for c in geometry()(doc)['checks'])
