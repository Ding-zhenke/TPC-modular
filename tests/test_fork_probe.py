import pytest
from shapely.affinity import scale
from shapely.geometry import box
from mesh_grid.metal_hex.fork_probe import ForkProbeSpec, build_fork_probe


def test_approved_shape_gap_and_mirror():
    spec = ForkProbeSpec()
    result = build_fork_probe(spec, boundary_x=-3.03)
    left, right = result['left'], result['right']
    assert left.is_valid and left.geom_type == 'Polygon'
    assert left.symmetric_difference(scale(right, -1, 1, origin=(0, 0))).area < 1e-12
    assert left.symmetric_difference(scale(left, 1, -1, origin=(0, 0))).area < 1e-12
    assert result['slot_left'].bounds[3] - result['slot_left'].bounds[1] == pytest.approx(spec.gap)
    assert left.intersection(box(-3.04, -.029, -3.02, .029)).area == pytest.approx(0)
    assert left.bounds == pytest.approx((-4.38, -.27, -3.018, .27))


def test_adjustable_gap_moves_both_arms_and_slot():
    result = build_fork_probe(ForkProbeSpec(gap=.08), boundary_x=-3.03)
    assert result['slot_left'].bounds[1:4:2] == pytest.approx((-.04, .04))
    assert result['left'].intersection(box(-3.04, -.039, -3.02, .039)).area == pytest.approx(0)


@pytest.mark.parametrize('values', [{'gap':0}, {'fork_length':1}, {'stub_distance':.01}, {'insertion':.5}])
def test_invalid_dimensions(values):
    with pytest.raises(ValueError):
        ForkProbeSpec(**values)
