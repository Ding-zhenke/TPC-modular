"""Exercise all installed skills offline, writing examples only to --output."""
import argparse
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def verify(output: Path):
    output = output.expanduser().resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Choose an output directory outside the plugin cache')
    output.mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mesh_grid.tri_grid import TopoPath
    from mesh_grid.hex_grid import HexLib, create_hex_polygon, save_to_dxf
    from topo_modeler.config import example_config, template_from_config
    from topo_modeler.preflight import validate_model_spec
    from topo_modeler.result_reader import ResultReader
    from topo_modeler.scanner import ParameterScan, value_metric
    from topo_modeler.optimizer import GeneticOptimizer, continuous_variables
    from tpc_toolkit.effective_medium import effective_permittivity
    from topo_templates.metal_hex import MetalHexStraight
    from mesh_grid.metal_hex import MetalHexSpec
    from topo_templates.fork_waveguide import ForkWaveguide

    skills = sorted(p.parent.name for p in (ROOT / 'skills').glob('*/SKILL.md'))
    expected = {'lattice-paths', 'topological-modeling', 'topological-schematic',
                'topological-templates', 'topological-analysis', 'topological-optimization',
                'metal-hex-topological-modeling'}
    assert set(skills) == expected, skills
    path = TopoPath.builder(a=0.25).start(0, 0).move(2, 'c').build()
    points = path.xy
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot([p[0] for p in points], [p[1] for p in points], 'o-')
    ax.set_aspect('equal', adjustable='datalim')
    ax.set_title('Offline API example: a = 0.25 (synthetic)')
    fig.savefig(output / 'lattice.png', dpi=120)
    plt.close(fig)
    hexlib = HexLib(hex_size=0.25, orientation='pointy')
    grid = hexlib.create_staggered_grid((0, 2), (0, 2))
    polygons = [create_hex_polygon(hexlib.hex_to_pixel(h), 0.25, 0) for h in grid]
    save_to_dxf(polygons, str(output / 'hex.dxf'))

    cfg = example_config('power_divider')
    preflight = validate_model_spec(cfg, check_paths=False, diagnose_cst=False)
    assert preflight['ok'], preflight['errors']
    kwargs = template_from_config(cfg, validate_only=True)

    class CurveSource:
        def read_all_s_parameters(self, run_id=0):
            return {'S2,1': [(110.0, complex(0.5)), (120.0, complex(0.25))]}

        def read_s_parameter(self, name, run_id=0):
            return self.read_all_s_parameters(run_id)[name]

    reader = ResultReader(CurveSource())
    s21 = reader.value_at('S2,1', 110.0)
    assert math.isclose(s21, -6.020599913279624)
    scan = ParameterScan(
        example_config('straight_waveguide'), {'length': [8, 10]},
        runner=lambda point: reader, workdir=str(output),
        metric_specs={'S21@110': value_metric('S2,1', 110.0)})
    scan.plan()
    scan.run()
    assert len(scan.succeeded) == 2 and not scan.failed
    scan.export_csv(str(output / 'scan.csv'))
    scan.report(str(output / 'scan.html'))
    opt = GeneticOptimizer(
        continuous_variables({'length': (10, 30, 'int')}),
        evaluate=lambda genes: (genes[0] - 18) ** 2, maximize=False,
        population_size=4, generations=3, seed=7)
    result = opt.run()
    assert result.improved and result.evaluations <= 12
    opt.report(result, path=str(output / 'optimization.html'))
    assert math.isclose(effective_permittivity(12, 1, 1, 1), 6.5)
    metal = MetalHexStraight()
    metal.preview(output / 'metal_hex')
    metal_area = metal.geometry().metal.area
    assert math.isclose(metal_area, 9.996715627415611, abs_tol=1e-9)
    assert math.isclose(metal.geometry().core_metal.area, 9.319165634016292, abs_tol=1e-9)
    fork=ForkWaveguide()
    fork.preview(output / 'fork_waveguide')
    assert math.isclose(fork.spec.y_bounds[1],2.624056973466849,abs_tol=1e-9)
    for layout in ('BA', 'A_air'):
        device = MetalHexStraight(MetalHexSpec(layout=layout))
        device.preview(output / 'metal_hex')
        geometry = device.geometry()
        if layout == 'A_air':
            assert geometry.phase_b.is_empty and geometry.core_metal.bounds[1] >= 0
            assert math.isclose(geometry.substrate.bounds[1], -.606)
        else:
            assert geometry.phase_a.bounds[3] <= 0 and geometry.phase_b.bounds[1] >= 0
    cst_loaded = any(n.split('.')[0] in {'cst', 'cst_solver', 'cst_automation'}
                     for n in sys.modules)
    assert not cst_loaded, 'Offline checks must not import a CST backend'
    import mesh_grid
    assert Path(mesh_grid.__file__).resolve().parent.parent == ROOT
    return {
        'plugin_root': str(ROOT), 'module_root': str(Path(mesh_grid.__file__).parent.parent),
        'skills': skills, 'output': str(output),
        'checks': {'template_class': kwargs['_class'], 'scan_points': len(scan.succeeded),
                   's21_db': s21, 'optimization_evaluations': result.evaluations,
                   'cst_loaded': cst_loaded, 'metal_hex_area_mm2': metal_area,
                   'metal_hex_core_area_mm2': metal.geometry().core_metal.area},
        'evidence': 'Synthetic offline API examples only; no CST build, readback or solve.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Library helpers may print status; keep stdout machine-readable JSON.
    import contextlib
    with contextlib.redirect_stdout(sys.stderr):
        status = verify(args.output)
    print(json.dumps(status, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
