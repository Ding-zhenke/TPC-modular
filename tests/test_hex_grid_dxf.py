import ezdxf
import pytest
from shapely.geometry import Polygon, box

from mesh_grid.hex_grid import save_multi_dxf, save_to_dxf


@pytest.mark.parametrize('grouped', [False, True])
def test_dxf_preserves_holes_and_disjoint_parts_in_mm(tmp_path, grouped):
    path = tmp_path / 'rings.dxf'
    frame = box(0, 0, 4, 4).difference(box(1, 1, 3, 3))
    shapes = [frame, box(6, 0, 7, 1)]
    if grouped:
        save_multi_dxf([[], shapes], path, layer_name='grid')
    else:
        save_to_dxf(shapes, path, layer_name='grid')
    drawing = ezdxf.readfile(path)
    assert drawing.units == ezdxf.units.MM
    rings = list(drawing.modelspace())
    assert all(r.closed and r.dxf.layer == ('grid1' if grouped else 'grid') for r in rings)
    areas = sorted(Polygon(r.get_points('xy')).area for r in rings)
    assert areas == pytest.approx([1, 4, 16])
