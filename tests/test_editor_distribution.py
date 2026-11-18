"""The installed plugin includes the interactive editor, not just Python code."""
from pathlib import Path
import runpy
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def test_editor_static_resources_and_portable_launcher_are_packaged(tmp_path):
    build = runpy.run_path(str(ROOT/'scripts/build_plugin.py'))['build_plugin']
    archive = build(ROOT, tmp_path)
    with zipfile.ZipFile(archive) as bundle:
        for name in ['tpc_editor/server.py', 'tpc_editor/static/index.html',
                     'tpc_editor/static/editor.css', 'tpc_editor/static/editor.js',
                     'scripts/open_path_editor.py']:
            assert 'tpc/'+name in bundle.namelist(), f'Installed editor missing {name}'
        bundle.extractall(tmp_path/'cache with spaces')
    plugin = tmp_path/'cache with spaces/tpc'
    result = subprocess.run([sys.executable, '-I', str(plugin/'scripts/open_path_editor.py'), '--help'],
                            cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert '--workspace' in result.stdout
    assert not list(plugin.rglob('__pycache__'))


def test_editor_package_import_has_no_geometry_or_cst_side_effects():
    code = "import sys; import tpc_editor; assert not any(n in sys.modules for n in ['numpy','matplotlib','cst_solver','shapely'])"
    result = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
