"""Offline dependency boundary checks for a clean Python subprocess."""

import subprocess
import sys
from pathlib import Path


def test_design_imports_and_modeler_construction_do_not_load_cst():
    root = Path(__file__).resolve().parents[1]
    code = r'''
import builtins, sys
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'cst_solver', 'cst_automation', 'tpc_service'}:
        raise AssertionError('offline import attempted: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from mesh_grid.tri_grid import TopoPath
from topo_modeler import TopoModeler
from topo_modeler.config import example_config, validate_config
from topo_modeler.preflight import validate_model_spec
path = TopoPath.builder(a=0.25).start(0, 0).move(4, 'c').build()
assert path is not None
assert validate_config(example_config('straight_waveguide'))
assert validate_model_spec(example_config('straight_waveguide'), check_paths=False,
                           diagnose_cst=False)['ok']
modeler = TopoModeler()
modeler.close()
assert 'tpc_toolkit.ga_optimizer' not in sys.modules
'''
    result = subprocess.run([sys.executable, '-I', '-c', code, str(root)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_toolkit_top_level_and_proxy_module_are_lazy():
    root = Path(__file__).resolve().parents[1]
    code = r'''
import builtins, sys
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'cst_solver', 'cst_automation', 'matplotlib'}:
        raise ImportError('blocked optional dependency: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import tpc_toolkit
assert 'tpc_toolkit.ga_optimizer' not in sys.modules
import tpc_toolkit.curves as curves
assert 'cst_automation.curves' not in sys.modules
try:
    curves.find_resonances
except ImportError as exc:
    assert 'cst-automation' in str(exc)
else:
    raise AssertionError('proxy resolved without the shared package')
'''
    result = subprocess.run([sys.executable, '-I', '-c', code, str(root)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_topology_service_adapter_import_is_offline_safe():
    root = Path(__file__).resolve().parents[1]
    code = r'''
import builtins, sys
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'cst_solver', 'cst_automation', 'tpc_service'}:
        raise AssertionError('adapter import attempted: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import topo_service
assert callable(topo_service.register_topology_handlers)
'''
    result = subprocess.run([sys.executable, '-I', '-c', code, str(root)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
