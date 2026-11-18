"""User-visible connectivity, independent of drawing order."""
import copy
import importlib.util
import json

import pytest


def api():
    assert importlib.util.find_spec('tpc_editor'), 'The approved path editor is missing'
    from tpc_editor.document import new_document, validate_document
    from tpc_editor.graph import apply_command
    return new_document, validate_document, apply_command


def draw(doc, points, **kw):
    apply = api()[2]
    for r, c in points:
        doc = apply(doc, {'type': 'point', 'r': r, 'c': c, **kw})
    return apply(doc, {'type': 'end'})


def pairs(doc):
    return {frozenset((tuple(doc['nodes'][e['u']][k] for k in ('r', 'c')),
                       tuple(doc['nodes'][e['v']][k] for k in ('r', 'c'))))
            for e in doc['edges'].values()}


def test_separate_strokes_do_not_invent_endpoint_connection():
    doc = draw(api()[0](), [(0, -4), (0, 0), (2, 0)])
    doc = draw(doc, [(0, 0), (-2, 0)])
    assert len(doc['edges']) == 3
    assert frozenset(((2, 0), (-2, 0))) not in pairs(doc)
    assert len(doc['strokes']) == 2


def test_branch_at_middle_splits_existing_edge():
    doc = draw(api()[0](), [(0, -4), (0, 4)])
    doc = draw(doc, [(0, 0), (3, 0)])
    assert len(doc['edges']) == 3
    assert frozenset(((0, -4), (0, 4))) not in pairs(doc)
    assert len(doc['strokes'][0]['nodes']) == 3


def test_illegal_direction_rolls_back_without_mutating_document():
    doc = api()[2](api()[0](), {'type': 'point', 'r': 0, 'c': 0})
    before = copy.deepcopy(doc)
    with pytest.raises(ValueError, match='方向'):
        api()[2](doc, {'type': 'point', 'r': 1, 'c': 2})
    assert doc == before


def test_overlap_is_split_and_deduplicated():
    doc = draw(api()[0](), [(0, -4), (0, 2)])
    doc = draw(doc, [(0, -2), (0, 4)])
    assert len(doc['edges']) == 3
    assert len(pairs(doc)) == 3


def crossing_setup():
    doc = draw(api()[0](), [(0, -3), (0, 3)])
    return api()[2](doc, {'type': 'point', 'r': -2, 'c': 0})


def test_crossing_requires_explicit_decision_then_connects():
    doc = crossing_setup()
    with pytest.raises(ValueError, match='交叉'):
        api()[2](doc, {'type': 'point', 'r': 2, 'c': 0})
    doc = api()[2](doc, {'type': 'point', 'r': 2, 'c': 0, 'crossing': 'connect'})
    assert len(doc['edges']) == 4
    assert len(doc['nodes']) == 5


def test_separate_crossing_survives_roundtrip():
    doc = api()[2](crossing_setup(), {'type': 'point', 'r': 2, 'c': 0,
                                     'crossing': 'separate'})
    assert len(doc['edges']) == 2
    assert doc['crossings'][0]['mode'] == 'separate'
    loaded = api()[1](json.loads(json.dumps(doc)))
    assert loaded == doc


def test_move_rejects_illegal_incident_edge_and_preserves_input():
    doc = draw(api()[0](), [(0, -3), (0, 3)])
    before = copy.deepcopy(doc)
    with pytest.raises(ValueError):
        api()[2](doc, {'type': 'move', 'id': 'P02', 'r': 1, 'c': 3})
    assert doc == before


def test_closed_loop_reuses_start_and_document_rejects_missing_node():
    doc = draw(api()[0](), [(0, 0), (0, 2), (2, 0), (0, 0)])
    assert len(doc['nodes']) == 3
    assert len(doc['edges']) == 3
    broken = copy.deepcopy(doc)
    broken['edges']['E01']['v'] = 'missing'
    with pytest.raises(ValueError):
        api()[1](broken)


def test_integer_coordinates_are_not_silently_truncated():
    with pytest.raises(ValueError):
        api()[2](api()[0](), {'type': 'point', 'r': 0.5, 'c': 1})
