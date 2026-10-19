"""Topology job handlers implementing cst-automation's DomainHandler contract.

Importing this module is offline-safe. CST and the shared service are imported
only when a registered handler is invoked.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping


class TopologyServiceCompatibilityError(RuntimeError):
    """The installed cst-automation service does not expose the documented API."""


def _results():
    try:
        from tpc_service.backends.base import artifact, fail_result, ok_result
    except ImportError as exc:
        raise RuntimeError(
            "Topology service handlers require cst-automation>=0.1,<1. "
            "Install this package with its [cst] extra."
        ) from exc
    return artifact, fail_result, ok_result


def build_handler(*, project: Mapping[str, Any], params: Mapping[str, Any],
                  job: Mapping[str, Any], backend: Any) -> Dict[str, Any]:
    """Build a topology template from ``params['spec']`` and save it."""
    artifact, fail_result, ok_result = _results()
    from topo_modeler.config import template_from_config
    from topo_modeler.preflight import validate_model_spec

    spec = params.get('spec')
    if not isinstance(spec, dict):
        return fail_result('config_invalid', 'build requires params["spec"] as a mapping')
    project_path = os.path.abspath(str(project.get('path') or ''))
    workdir = os.path.dirname(project_path) or os.getcwd()
    report = validate_model_spec(spec, base_dir=workdir, diagnose_cst=False)
    if not report['ok']:
        error = (report.get('errors') or [{}])[0]
        return fail_result(error.get('code', 'config_invalid'),
                           error.get('message', 'Topology preflight failed'),
                           preflight=report)
    output = params.get('output') or os.path.join(
        workdir, f"{report['model_type']}_topology.cst")
    output = os.path.abspath(os.path.join(workdir, output) if not os.path.isabs(output)
                             else output)
    if os.path.commonpath([workdir, output]) != workdir:
        return fail_result('artifact_path_invalid',
                           'Topology output must remain inside the project work directory',
                           path=output)
    template = None
    logs = [f"Topology preflight passed for {report['model_type']}"]
    try:
        template = template_from_config(spec, template_cst=project_path)
        template.build_all()
        saved_path = template.save(output)
        validation = template.validate()
        logs.append(f"CST model validation status={validation.get('status', 'unknown')}")
        return ok_result(
            log=logs,
            artifacts=[artifact(str(saved_path), kind='project', note='topology build')],
            result_summary={'model_type': report['model_type'],
                            'validation': validation.get('status', 'unknown'),
                            'preflight_warnings': report.get('warnings', [])},
            saved=True)
    except Exception as exc:
        return fail_result('backend_failed',
                           f'Topology build failed: {type(exc).__name__}: {exc}',
                           retryable=True, log=logs)
    finally:
        if template is not None:
            try:
                template.close()
            except Exception:
                pass


def solve_handler(*, project: Mapping[str, Any], params: Mapping[str, Any],
                  job: Mapping[str, Any], backend: Any) -> Dict[str, Any]:
    """Delegate the generic solve to cst-automation, then add topology readback."""
    _, fail_result, _ = _results()
    solve = getattr(backend, 'solve', None)
    if not callable(solve):
        return fail_result('backend_failed', 'The configured backend has no solve() method')
    result = solve(project=dict(project), params=dict(params), job=dict(job))
    if not result.get('ok'):
        return result
    path = str(project.get('path') or '')
    try:
        from topo_modeler.result_reader import ResultReader
        reader = ResultReader(path, run_id=int(params.get('run_id', 0)))
        summary = dict(result.get('result_summary') or {})
        summary['topology_s_parameters'] = reader.read_s_parameters_db()
        result['result_summary'] = summary
    except Exception as exc:
        # Preserve the generic solve/save result and report the separate
        # topology postprocessing failure explicitly.
        summary = dict(result.get('result_summary') or {})
        summary['topology_readback_error'] = f'{type(exc).__name__}: {exc}'
        result['result_summary'] = summary
        result.setdefault('log', []).append(
            f'Topology postprocessing failed after generic solve: {exc!r}')
    return result


def study_handler(*, project: Mapping[str, Any], params: Mapping[str, Any],
                  job: Mapping[str, Any], backend: Any) -> Dict[str, Any]:
    """Run topology parameter scans through the shared backend's build/solve."""
    artifact, fail_result, ok_result = _results()
    from topo_modeler.scanner import ParameterScan

    study = params.get('study') or {}
    if study.get('kind', 'scan') != 'scan':
        return fail_result('study_kind_unsupported',
                           'TPC adapter currently supports study.kind="scan"')
    base_config = study.get('base_config')
    if not isinstance(base_config, dict):
        return fail_result('config_invalid', 'study.base_config must be a mapping')
    path = str(project.get('path') or '')
    outdir = os.path.join(os.path.dirname(os.path.abspath(path)),
                          f"topology_scan_{job.get('job_id', 'job')}")

    def runner(point):
        config = getattr(point, 'config', None)
        cst_path = getattr(point, 'cst_path', None) or os.path.join(outdir,
                                                                  f'{point.name}.cst')
        built = build_handler(project={'path': path},
                              params={'spec': config, 'output': cst_path},
                              job=job, backend=backend)
        if not built.get('ok'):
            raise RuntimeError(f"Topology build failed: {built.get('error')}")
        solved = solve_handler(project={'path': cst_path},
                               params={'run_id': study.get('run_id', 0)},
                               job=job, backend=backend)
        if not solved.get('ok'):
            raise RuntimeError(f"Topology solve failed: {solved.get('error')}")
        return (solved.get('result_summary') or {}).get('metrics', {})

    try:
        scan = ParameterScan(base_config=base_config, params=study['params'],
                             runner=runner, workdir=outdir,
                             apply_to=study.get('apply_to', 'geometry'),
                             name=study.get('name'))
        scan.run(continue_on_error=True)
        return ok_result(
            log=[f'Topology parameter scan finished: {len(scan.points)} points'],
            artifacts=[artifact(outdir, kind='dir', note='topology scan output')],
            result_summary={'n_points': len(scan.points),
                            'errors': dict(scan.last_errors),
                            'points': [{'name': p.name, 'status': p.status,
                                        'metrics': p.metrics} for p in scan.points]},
            saved=True)
    except Exception as exc:
        return fail_result('backend_failed',
                           f'Topology scan failed: {type(exc).__name__}: {exc}',
                           retryable=True)


def register_topology_handlers(service: Any, *, replace: bool = False) -> None:
    """Register build/solve/study handlers on a compatible RunService instance."""
    register = getattr(service, 'register_handler', None)
    if not callable(register):
        raise TopologyServiceCompatibilityError(
            'Installed cst-automation RunService does not implement the '
            'documented register_handler(kind, handler, *, replace=False) API. '
            'TPC adapter registration has not been performed.')
    for kind, handler in (('build', build_handler), ('solve', solve_handler),
                          ('study', study_handler)):
        register(kind, handler, replace=replace)
