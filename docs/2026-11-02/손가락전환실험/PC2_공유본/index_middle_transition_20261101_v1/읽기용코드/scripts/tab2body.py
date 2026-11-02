#!/usr/bin/env python3
"""Run shared Tab2Body sources with a verified, PC-local Isaac Gym runtime."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import resource
import shutil
import stat
import sys
import sysconfig
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
SCHEMA = 'tab2body.local_isaacgym.v1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def tree_manifest(root, ignore_bytecode=True):
    """Hash authoritative files and internal links; never traverse an external link."""
    root = root.resolve(strict=True)
    entries = {}
    for current, dirs, files in os.walk(str(root), followlinks=False):
        dirs[:] = sorted(name for name in dirs if not ignore_bytecode or name != '__pycache__')
        for name in sorted(dirs + files):
            path = Path(current) / name
            if ignore_bytecode and name.endswith(('.pyc', '.pyo')):
                continue
            key = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                target = os.readlink(str(path))
                if os.path.isabs(target):
                    raise ValueError('Runtime has an absolute symlink: ' + key)
                resolved = path.resolve(strict=True)
                if root not in resolved.parents and resolved != root:
                    raise ValueError('Runtime symlink escapes package: ' + key)
                entries[key] = {'link': target}
            elif stat.S_ISREG(mode):
                entries[key] = {'sha256': file_sha(path), 'mode': stat.S_IMODE(mode)}
            elif not stat.S_ISDIR(mode):
                raise ValueError('Unsupported runtime file: ' + key)
    return entries


def mount_type(path):
    """Find the longest enclosing Linux mount, including bind-mounted SSHFS."""
    path = path.resolve()
    match = ('', 'unknown')
    for row in Path('/proc/self/mountinfo').read_text().splitlines():
        before, after = row.split(' - ', 1)
        mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), before.split()[4])
        point = Path(mount)
        if (path == point or point in path.parents) and len(mount) >= len(match[0]):
            match = (mount, after.split()[0])
    return match[1]


def require_local(path):
    kind = mount_type(path)
    if kind.startswith(('fuse', 'nfs', 'cifs', 'smb', '9p', 'ceph', 'afs', 'gluster', 'lustre')) or kind == 'unknown':
        raise ValueError('Cache/build directory must be on a local filesystem; {} is {}. '
                         'Use --cache-root /local/disk/tab2body'.format(path, kind))


def prepare_runtime(source, cache_root):
    source = source.resolve(strict=True)
    cache_root = cache_root.expanduser().resolve()
    # Check before creating anything on a remote mount, and after resolving links.
    require_local(cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)
    manifest = tree_manifest(source)
    setup = source.parent / 'setup.py'
    release = None
    if setup.is_file():
        version = re.search(r"\bversion\s*=\s*['\"]([^'\"]+)['\"]", setup.read_text())
        if version is None:
            raise ValueError('Cannot identify Isaac Gym release in ' + str(setup))
        release = {'version': version.group(1), 'setup_sha256': file_sha(setup)}
    payload = {'schema': SCHEMA, 'release': release, 'files': manifest}
    identity = hashlib.sha256(canonical(payload)).hexdigest()
    payload['sha256'] = identity
    target = cache_root / 'isaacgym' / identity
    target.parent.mkdir(exist_ok=True)
    require_local(target.parent)
    with (target.parent / (identity + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if target.is_symlink() or (target / 'isaacgym').is_symlink():
            raise ValueError('Local runtime cache must not redirect through symlinks: ' + str(target))
        if target.exists():
            stored = json.loads((target / 'manifest.json').read_text())
            if stored != payload or tree_manifest(target / 'isaacgym', ignore_bytecode=False) != manifest:
                raise ValueError('Local runtime cache failed SHA verification: {}. '
                                 'Remove this cache entry and prepare again.'.format(target))
        else:
            temporary = Path(tempfile.mkdtemp(prefix=identity + '.', dir=str(target.parent)))
            try:
                shutil.copytree(str(source), str(temporary / 'isaacgym'), symlinks=True,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
                if tree_manifest(temporary / 'isaacgym', ignore_bytecode=False) != manifest:
                    raise ValueError('Runtime changed during copy; prepare again after writes stop')
                (temporary / 'manifest.json').write_bytes(canonical(payload))
                temporary.rename(target)
            finally:
                if temporary.exists():
                    shutil.rmtree(str(temporary))
    return target, identity


def execution_environment(runtime, identity, cache_root):
    # Read distribution metadata without importing torch before isaacgym.
    versions = {}
    for package in ('torch', 'numpy', 'ninja'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    build_identity = hashlib.sha256(canonical({
        'runtime': identity, 'python': sys.version, 'prefix': sys.prefix,
        'soabi': sysconfig.get_config_var('SOABI'), 'machine': platform.machine(),
        'packages': versions, 'CXX': os.environ.get('CXX'),
        'CUDA_HOME': os.environ.get('CUDA_HOME'),
    })).hexdigest()
    extensions = cache_root.expanduser().resolve() / 'torch_extensions' / build_identity
    require_local(extensions)
    extensions.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', os.defpath)
    # Do not inherit a shared binary/build location from a different PC.
    env['PYTHONPATH'] = os.pathsep.join((str(runtime), str(PROJECT)))
    env['TORCH_EXTENSIONS_DIR'] = str(extensions)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    libs = [str(Path(sys.prefix) / 'lib')]
    libdir = sysconfig.get_config_var('LIBDIR')
    if libdir and libdir not in libs:
        libs.append(libdir)
    if env.get('LD_LIBRARY_PATH'):
        libs.append(env['LD_LIBRARY_PATH'])
    env['LD_LIBRARY_PATH'] = os.pathsep.join(libs)
    env['TAB2BODY_RUNTIME_SHA256'] = identity
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-root', type=Path, default=Path(os.environ.get(
        'TAB2BODY_CACHE_ROOT', str(Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'tab2body'))))
    parser.add_argument('command', choices=('prepare', 'run', 'probe'))
    args, command = parser.parse_known_args()
    if args.command != 'run' and command:
        parser.error('Unexpected arguments: ' + ' '.join(command))
    if command[:1] == ['--']:
        command = command[1:]
    if args.command == 'run' and not command:
        parser.error('run requires Python arguments, e.g. run -m guitar_learning.train --out runs/new')
    try:
        runtime, identity = prepare_runtime(PROJECT / 'isaacgym/python/isaacgym', args.cache_root)
        env = execution_environment(runtime, identity, args.cache_root)
    except (OSError, ValueError) as error:
        parser.exit(1, 'Tab2Body runtime preparation failed: {}\n'.format(error))
    summary = {'schema': SCHEMA, 'project': str(PROJECT), 'runtime': str(runtime),
               'runtime_sha256': identity, 'python': sys.executable,
               'torch_extensions': env['TORCH_EXTENSIONS_DIR'],
               'cache_filesystem': mount_type(runtime)}
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if args.command == 'prepare':
        return 0
    if args.command == 'probe':
        command = [str(PROJECT / 'scripts/probe_isaacgym.py')]
    # Native failures must not generate multi-GB dumps in shared sources.
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # Native MJCF loading can reset LC_CTYPE to C after Python starts. Keep
    # text/JSON I/O UTF-8 even then, without requiring a caller environment flag.
    os.execvpe(sys.executable, [sys.executable, '-X', 'utf8'] + command, env)


if __name__ == '__main__':
    sys.exit(main())
