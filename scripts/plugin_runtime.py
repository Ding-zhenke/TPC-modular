"""Check dependencies or explicitly prepare a venv outside the installed plugin."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parents[1]
BASE = {'numpy': 'numpy>=1.21', 'matplotlib': 'matplotlib>=3.5', 'tqdm': 'tqdm>=4.60'}
EXTRAS = {
    'geometry': {'shapely': 'shapely>=2.0', 'ezdxf': 'ezdxf>=1.0'},
    'science': {'scipy': 'scipy>=1.7'},
    'yaml': {'yaml': 'PyYAML>=6.0'},
}


def dependencies(extras):
    requirements = dict(BASE)
    for extra in extras:
        if extra not in EXTRAS:
            raise ValueError(f'Unsupported extra {extra!r}; choose geometry,science,yaml')
        requirements.update(EXTRAS[extra])
    return requirements


def check(extras):
    # Import in a child so compiled-library errors and package side effects do not
    # contaminate the calling agent. Preserve this interpreter's search paths.
    probe = r'''
import contextlib, importlib, importlib.metadata, json, re, sys
sys.dont_write_bytecode = True
requirements = json.loads(sys.argv[1])
sys.path = json.loads(sys.argv[2])
available, errors, versions = {}, {}, {}
def release(value):
    match = re.match(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?', value)
    if not match:
        raise ValueError('Unrecognized dependency version: ' + value)
    return tuple(int(p or 0) for p in match.groups())
for module, requirement in requirements.items():
    try:
        with contextlib.redirect_stdout(sys.stderr):
            importlib.import_module(module)
        distribution, minimum = requirement.split('>=')
        current = importlib.metadata.version(distribution)
        versions[module] = current
        if release(current) < release(minimum) or (
                release(current) == release(minimum) and re.search(r'(a|b|rc|dev)\d', current)):
            raise ValueError(requirement + ' required; found ' + current)
        available[module] = True
    except Exception as exc:
        available[module] = False
        errors[module] = type(exc).__name__ + ': ' + str(exc)
print(json.dumps({'dependencies': available, 'errors': errors, 'versions': versions,
                  'ready': all(available.values())}))
'''
    result = subprocess.run([sys.executable, '-B', '-c', probe,
                             json.dumps(dependencies(extras)), json.dumps(sys.path)],
                            capture_output=True, text=True)
    if result.returncode:
        raise ValueError('Dependency probe failed: ' + result.stderr)
    status = json.loads(result.stdout)
    status.update({
        'plugin_root': str(ROOT),
        'python': sys.executable,
        'usage': 'Use this Python with plugin_root added to sys.path in your task script; '
                 'keep the working directory and outputs in your workspace, outside the plugin cache.',
    })
    return status


def prepare(target: Path, extras):
    requirements = dependencies(extras)  # validate before creating anything
    target = target.expanduser().resolve()
    if target.is_relative_to(ROOT) or ROOT.is_relative_to(target):
        raise ValueError('The virtual environment must be outside the plugin directory')
    executable = target / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not (target / 'pyvenv.cfg').is_file():
        if target.exists() and any(target.iterdir()):
            raise ValueError('Choose an empty directory or an existing virtual environment')
        venv.EnvBuilder(with_pip=True).create(target)
    # Do not install the project itself: source imports from ROOT avoid copying or
    # writing build metadata into the plugin cache. Only public dependencies use pip.
    subprocess.run([str(executable), '-m', 'pip', 'install', *requirements.values()],
                   check=True, stdout=sys.stderr)
    result = subprocess.run([str(executable), '-I', str(Path(__file__).resolve()),
                             '--check', '--extras', ','.join(extras)],
                            capture_output=True, text=True)
    if result.returncode:
        raise ValueError('Prepared environment failed dependency checks: ' +
                         (result.stdout or result.stderr))
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--check', action='store_true')
    actions.add_argument('--prepare', action='store_true')
    parser.add_argument('--venv', type=Path)
    parser.add_argument('--extras', default='')
    args = parser.parse_args()
    extras = [part.strip() for part in args.extras.split(',') if part.strip()]
    if sys.version_info < (3, 9):
        parser.error('Python 3.9 or newer is required')
    if args.prepare and not args.venv:
        parser.error('--prepare requires --venv PATH')
    try:
        status = prepare(args.venv, extras) if args.prepare else check(extras)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'{exc}\n')
    print(json.dumps(status, ensure_ascii=True, indent=2))
    if not status['ready']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
