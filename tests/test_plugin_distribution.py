"""The plugin must run after extraction without the development checkout."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    path = ROOT / 'scripts' / 'build_plugin.py'
    assert path.is_file(), 'The plugin needs a reproducible distribution builder'
    spec = importlib.util.spec_from_file_location('build_plugin', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_archive_contains_portable_skills_and_code_without_private_files(tmp_path):
    archive = load_builder().build_plugin(ROOT, tmp_path)
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        assert 'tpc/plugin.json' in names
        assert 'tpc/.codex-plugin/plugin.json' in names
        assert 'tpc/mesh_grid/tri_grid/core.py' in names
        assert 'tpc/scripts/plugin_runtime.py' in names
        assert 'tpc/LICENSE' in names
        skills = {Path(n).parts[2] for n in names if n.endswith('/SKILL.md')}
        assert skills == {
            'lattice-paths', 'topological-modeling', 'topological-schematic',
            'topological-templates', 'topological-analysis', 'topological-optimization',
        }
        forbidden = {'.git', 'work', 'build', 'dist', '__pycache__', '.env',
                     '.pytest_cache', 'cst_solver', 'tpc_service', 'cst_mcp'}
        assert not any(set(Path(n).parts) & forbidden for n in names)
        assert not any(n.endswith(('.pyc', '.cst', '.sat', '.dxf')) for n in names)
        # All six skill references must resolve inside the extracted package.
        bundle.extractall(tmp_path / 'cache with spaces')
    plugin = tmp_path / 'cache with spaces' / 'tpc'
    import re
    for doc in (plugin / 'skills').rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                linked = (doc.parent / target.split('#')[0]).resolve()
                assert linked.is_relative_to(plugin), (doc, target)
                assert linked.exists(), (doc, target)


def test_packager_excludes_unknown_files_and_nested_runtime_directories(tmp_path):
    import shutil
    source = tmp_path / 'source'
    shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(
        '.git', 'work', 'build', '*.egg-info', '__pycache__', 'dist', '.pytest_cache'))
    (source / 'skills' / 'lattice-paths' / 'credentials.json').write_text('private')
    (source / 'mesh_grid' / 'local.env').write_text('private')
    for name in ['docs/work/private.md', 'mesh_grid/build/cache.py',
                 'mesh_grid/venv/local.py', 'skills/lattice-paths/dist/cache.md']:
        private = source / name
        private.parent.mkdir(parents=True, exist_ok=True)
        private.write_text('private')
    archive = load_builder().build_plugin(source, tmp_path / 'out')
    with zipfile.ZipFile(archive) as bundle:
        assert not any('credentials.json' in n or 'local.env' in n for n in bundle.namelist())
        assert not any({'work', 'build', 'dist', 'venv'} & set(Path(n).parts)
                       for n in bundle.namelist())


def test_runtime_check_works_from_extracted_plugin_and_is_read_only(tmp_path):
    archive = load_builder().build_plugin(ROOT, tmp_path)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(tmp_path / 'extracted')
    plugin = tmp_path / 'extracted' / 'tpc'
    before = set(plugin.rglob('*'))
    result = subprocess.run(
        [sys.executable, '-I', str(plugin / 'scripts' / 'plugin_runtime.py'), '--check'],
        cwd=tmp_path, text=True, capture_output=True, check=True,
    )
    status = json.loads(result.stdout)
    assert Path(status['plugin_root']) == plugin
    assert status['python'] == sys.executable
    assert 'numpy' in status['dependencies']
    assert set(plugin.rglob('*')) == before


def test_runtime_reports_broken_import_and_version_floor(tmp_path):
    import os
    script = ROOT / 'scripts' / 'plugin_runtime.py'
    (tmp_path / 'numpy.py').write_text("raise ImportError('broken NumPy binary dependency')")
    # A real package metadata fixture tests the minimum requirement independently
    # of whether this test interpreter has a modern installed PyYAML.
    (tmp_path / 'yaml.py').write_text('__version__ = "5.0"')
    metadata = tmp_path / 'PyYAML-5.0.dist-info'
    metadata.mkdir()
    (metadata / 'METADATA').write_text('Metadata-Version: 2.1\nName: PyYAML\nVersion: 5.0\n')
    env = dict(os.environ, PYTHONPATH=str(tmp_path))
    result = subprocess.run([sys.executable, '-B', str(script), '--check', '--extras', 'yaml'],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    status = json.loads(result.stdout)
    assert status['dependencies']['numpy'] is False
    assert 'broken NumPy' in status['errors']['numpy']
    assert status['dependencies']['yaml'] is False
    assert '6.0' in status['errors']['yaml']
    assert status['ready'] is False
    assert result.returncode != 0


def test_prepare_requires_external_environment_directory(tmp_path):
    script = ROOT / 'scripts' / 'plugin_runtime.py'
    assert script.exists(), 'The plugin needs a portable runtime entry point'
    result = subprocess.run(
        [sys.executable, '-I', str(script), '--prepare', '--venv', str(ROOT / '.venv')],
        text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert 'outside' in result.stderr.lower()


def test_invalid_extras_fail_before_environment_creation(tmp_path):
    script = ROOT / 'scripts' / 'plugin_runtime.py'
    assert script.exists(), 'The plugin needs a portable runtime entry point'
    target = tmp_path / 'runtime'
    result = subprocess.run(
        [sys.executable, '-I', str(script), '--prepare', '--venv', str(target),
         '--extras', 'cst'], text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert not target.exists()


def test_offline_smoke_uses_extracted_code_and_outputs_only_to_workspace(tmp_path):
    archive = load_builder().build_plugin(ROOT, tmp_path)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(tmp_path / 'cache')
    plugin = tmp_path / 'cache' / 'tpc'
    script = plugin / 'scripts' / 'verify_plugin.py'
    assert script.exists(), 'Users need an offline check for the installed plugin'
    output = tmp_path / 'results'
    result = subprocess.run([sys.executable, '-I', str(script), '--output', str(output)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    status = json.loads(result.stdout)
    assert len(status['skills']) == 6
    assert status['checks']['template_class'] == 'PowerDivider'
    assert status['checks']['scan_points'] == 2
    assert abs(status['checks']['s21_db'] + 6.020599913279624) < 1e-9
    assert status['checks']['cst_loaded'] is False
    assert Path(status['module_root']) == plugin
    assert (output / 'scan.html').is_file()
    assert (output / 'lattice.png').is_file()
    assert (output / 'hex.dxf').is_file()
    assert not list(plugin.rglob('__pycache__'))
