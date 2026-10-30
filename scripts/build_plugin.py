"""Build a portable plugin ZIP from reviewed source files, never a checkout copy."""
import argparse
import json
from pathlib import Path
import zipfile


ROOT_FILES = ('plugin.json', '.codex-plugin/plugin.json', 'pyproject.toml',
              'README.md', 'LICENSE', 'MANIFEST.in', 'AGENTS.md', 'CONTRIBUTING.md',
              '.agents/plugins/marketplace.json')
TREES = {
    'mesh_grid': {'.py', '.md'}, 'topo_modeler': {'.py'},
    'topo_templates': {'.py'}, 'templates': {'.py'},
    'tpc_toolkit': {'.py'}, 'topo_service': {'.py'},
    'skills': {'.md', '.yaml'}, 'docs': {'.md'}, 'tests': {'.py'},
}
SCRIPTS = ('build_plugin.py', 'plugin_runtime.py', 'verify_plugin.py')
EXCLUDED_DIRS = {'work', 'build', 'dist', 'venv', 'node_modules', '__pycache__'}


def build_plugin(source: Path, output: Path) -> Path:
    """Return a self-contained ZIP with a single `tpc/` top-level directory."""
    source, output = Path(source).resolve(), Path(output).resolve()
    manifest = json.loads((source / 'plugin.json').read_text(encoding='utf-8'))
    if manifest['name'] != 'tpc':
        raise ValueError('Expected the tpc plugin manifest')
    files = [source / name for name in ROOT_FILES]
    for tree, suffixes in TREES.items():
        files.extend(p for p in (source / tree).rglob('*')
                     if p.is_file() and p.suffix in suffixes
                     and not any(part.startswith('.') or part.lower() in EXCLUDED_DIRS
                                 or part.endswith('.egg-info')
                                 for part in p.relative_to(source).parts))
    files.extend(source / 'scripts' / name for name in SCRIPTS
                 if (source / 'scripts' / name).is_file())
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError(f'Plugin files must stay inside the source: {path}')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"tpc-{manifest['version']}.zip"
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(set(files)):
            # Stable metadata makes rebuilds comparable across machines.
            info = zipfile.ZipInfo('tpc/' + path.relative_to(source).as_posix(),
                                   date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, default=Path('dist'))
    args = parser.parse_args()
    print(build_plugin(args.source, args.output))


if __name__ == '__main__':
    main()
