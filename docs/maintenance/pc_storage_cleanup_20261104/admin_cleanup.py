#!/usr/bin/python3
"""Reviewed, fixed-scope cleanup. Default: read-only checks. Root writes need --apply."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

APT = Path('/var/cache/apt/archives/chatgpt_26.1027.51404_amd64.deb')
APT_SHA = '46f1e22d028698fe9edaefd5847aece07c4509a30d3709e104220719d8c12822'
APT_EXPECTED = (66306, 275581, 535323606, 1793490291000000000)
LOCKS = ['/var/lib/dpkg/lock-frontend', '/var/lib/dpkg/lock', '/var/cache/apt/archives/lock']
XRDP = Path('/var/log/xrdp.log')
XRDP_ID = (66306, 269016)
TAIL = Path('/var/log/xrdp-cleanup-20261104-tail.log')
TAIL_BYTES = 16 * 1024 * 1024
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'}


def run(*args):
    p = subprocess.run(args, text=True, capture_output=True, env=ENV, timeout=60)
    if p.returncode:
        raise RuntimeError(f'{args[0]} failed: {p.stderr.strip() or p.stdout.strip()}')
    return p.stdout.strip()


def metadata(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise RuntimeError(f'Not a regular file: {path}')
    return {'device': s.st_dev, 'inode': s.st_ino, 'bytes': s.st_size,
            'allocated': s.st_blocks * 512, 'mtime_ns': s.st_mtime_ns,
            'uid': s.st_uid, 'gid': s.st_gid, 'mode': stat.S_IMODE(s.st_mode),
            'links': s.st_nlink}


def apt_activity():
    busy = []
    packagekit = False
    names = {'apt', 'apt-get', 'aptd', 'aptitude', 'dpkg', 'dpkg-deb',
             'synaptic', 'unattended-upgr', 'unattended-upgrade'}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():
            continue
        try:
            name = (p / 'comm').read_text().strip()
            if name == 'packagekitd':
                packagekit = True
            if name not in names:
                continue
            args = (p / 'cmdline').read_bytes().split(b'\0')
            watcher = (b'/usr/share/unattended-upgrades/unattended-upgrade-shutdown' in args
                       and b'--wait-for-signal' in args)
            if not watcher:
                busy.append({'pid': int(p.name), 'name': name})
        except FileNotFoundError:
            continue
    if packagekit:
        tx = run('/usr/bin/busctl', 'call', 'org.freedesktop.PackageKit',
                 '/org/freedesktop/PackageKit', 'org.freedesktop.PackageKit', 'GetTransactionList')
        if tx != 'ao 0':
            raise RuntimeError('PackageKit has active transactions')
    if busy:
        raise RuntimeError(f'Package installation process active: {busy}')
    active = Path('/proc/locks').read_text().splitlines()
    for name in LOCKS:
        s = os.stat(name)
        key = f'{os.major(s.st_dev):02x}:{os.minor(s.st_dev):02x}:{s.st_ino}'
        if any(key in line.split() for line in active):
            raise RuntimeError(f'Package lock is held: {name}')
    return {'installer_processes': [], 'packagekit_transactions': 0,
            'apt_dpkg_locks_held': False}


def apt_check():
    m = metadata(APT)
    if (m['device'], m['inode'], m['bytes'], m['mtime_ns']) != APT_EXPECTED or m['links'] != 1:
        raise RuntimeError('The approved APT installer metadata changed')
    installed = run('/usr/bin/dpkg-query', '-W', '-f=${db:Status-Abbrev}\t${Version}\t${Architecture}', 'chatgpt')
    if installed != 'ii \t26.1027.51404\tamd64':
        raise RuntimeError('The exact installer version is not installed')
    fields = run('/usr/bin/dpkg-deb', '--field', str(APT), 'Package', 'Version', 'Architecture')
    if fields != 'Package: chatgpt\nVersion: 26.1027.51404\nArchitecture: amd64':
        raise RuntimeError('Installer package metadata changed')
    h = hashlib.sha256()
    fd = os.open(APT, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    if h.hexdigest() != APT_SHA or metadata(APT) != m:
        raise RuntimeError('Installer checksum or metadata changed while reading')
    return {'path': str(APT), 'metadata': m, 'sha256': h.hexdigest()}


def remove_apt():
    apt_activity()
    with contextlib.ExitStack() as stack:
        for path in LOCKS:
            fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
            stream = stack.enter_context(os.fdopen(fd, 'r+b', buffering=0))
            fcntl.lockf(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # The exclusive package locks prevent a package operation starting during verification.
        evidence = apt_check()
        os.unlink(APT)
        if APT.exists():
            raise RuntimeError('Installer still exists after deletion')
    return {'status': 'deleted', **evidence}


def xrdp_writers():
    if os.geteuid() != 0:
        raise RuntimeError('Root is required to verify all XRDP writer file descriptors')
    writers = []
    denied = []
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            for fd in (p / 'fd').iterdir():
                try:
                    s = fd.stat()
                    if (s.st_dev, s.st_ino) != XRDP_ID:
                        continue
                    info = dict(line.split(':', 1) for line in (p / 'fdinfo' / fd.name).read_text().splitlines())
                    flags = int(info['flags'].strip(), 8)
                    if flags & os.O_ACCMODE not in (os.O_WRONLY, os.O_RDWR):
                        continue
                    name = (p / 'comm').read_text().strip()
                    if name not in {'xrdp', 'xrdp-sesman'} or not flags & os.O_APPEND:
                        raise RuntimeError(f'XRDP writer is unexpected or lacks O_APPEND: pid={p.name}')
                    writers.append({'pid': int(p.name), 'fd': int(fd.name), 'name': name, 'append': True})
                except FileNotFoundError:
                    continue
        except FileNotFoundError:
            continue
        except PermissionError:
            denied.append(int(p.name))
    if denied or not writers:
        raise RuntimeError(f'Cannot prove all XRDP writers use O_APPEND; denied={denied}, writers={len(writers)}')
    return writers


def xrdp_check():
    m = metadata(XRDP)
    if (m['device'], m['inode']) != XRDP_ID or (m['uid'], m['gid'], m['mode'], m['links']) != (131, 4, 0o640, 1):
        raise RuntimeError('XRDP log identity, permissions, or link count changed')
    if m['bytes'] <= TAIL_BYTES:
        raise RuntimeError('XRDP log already small; no truncation needed')
    if TAIL.exists() or TAIL.is_symlink():
        raise RuntimeError('Tail preservation file already exists; will not overwrite it')
    services = run('/usr/bin/systemctl', 'is-active', 'xrdp', 'xrdp-sesman')
    if services != 'active\nactive':
        raise RuntimeError('XRDP service state differs from the approved active state')
    return {'metadata': m, 'writers': xrdp_writers(), 'services': services.splitlines()}


def shrink_xrdp():
    before = xrdp_check()
    fd = os.open(XRDP, os.O_RDWR | os.O_NOFOLLOW)
    try:
        s = os.fstat(fd)
        if (s.st_dev, s.st_ino) != XRDP_ID:
            raise RuntimeError('XRDP log was replaced before opening')
        data = os.pread(fd, TAIL_BYTES, s.st_size - TAIL_BYTES)
        if len(data) != TAIL_BYTES:
            raise RuntimeError('XRDP log shrank during tail capture')
        backup_fd = os.open(TAIL, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(backup_fd, 'wb') as backup:
            backup.write(data)
            backup.flush()
            os.fchown(backup.fileno(), 0, 0)
            os.fchmod(backup.fileno(), 0o600)
            os.fsync(backup.fileno())
        backup_meta = metadata(TAIL)
        if backup_meta['bytes'] != TAIL_BYTES or (backup_meta['uid'], backup_meta['mode']) != (0, 0o600):
            raise RuntimeError('XRDP tail preservation could not be verified')
        if hashlib.sha256(TAIL.read_bytes()).digest() != hashlib.sha256(data).digest():
            raise RuntimeError('XRDP preserved tail checksum differs')
        xrdp_writers()
        current = metadata(XRDP)
        if (current['device'], current['inode']) != XRDP_ID or current['bytes'] < s.st_size:
            raise RuntimeError('XRDP log changed identity or shrank before truncation')
        # Standard copytruncate race: bytes appended after capture can be lost.
        # O_APPEND on every writer prevents stale descriptor offsets creating sparse holes.
        os.ftruncate(fd, 0)
        os.fsync(fd)
        after = metadata(XRDP)
        if (after['device'], after['inode'], after['uid'], after['gid'], after['mode']) != (*XRDP_ID, 131, 4, 0o640):
            raise RuntimeError('XRDP inode or permissions changed unexpectedly')
        services = run('/usr/bin/systemctl', 'is-active', 'xrdp', 'xrdp-sesman')
        return {'status': 'truncated', 'before': before, 'after': after,
                'tail_path': str(TAIL), 'tail_sha256': hashlib.sha256(data).hexdigest(),
                'tail_metadata': backup_meta, 'services_after': services.splitlines(),
                'copytruncate_race': 'A small concurrent-write window can lose newly appended log bytes.'}
    finally:
        os.close(fd)


def vacuum_journal():
    before = run('/usr/bin/journalctl', '--disk-usage')
    p = subprocess.run(['/usr/bin/journalctl', '--vacuum-size=1G'], text=True,
                       capture_output=True, env=ENV, timeout=60)
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    return {'status': 'vacuumed', 'before': before, 'result': p.stderr.strip() or p.stdout.strip(),
            'after': run('/usr/bin/journalctl', '--disk-usage'),
            'scope': 'Archived journals only, 1GiB archive budget. No forced rotation or configuration changes.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.apply and os.geteuid() != 0:
        raise SystemExit('Root is required; no cleanup performed.')
    result = {'apply': args.apply, 'uid': os.geteuid(), 'time': time.time(), 'steps': {}}
    checks = [('apt', lambda: {'candidate': apt_check(), 'activity': apt_activity()}),
              ('journal', lambda: {'disk_usage': run('/usr/bin/journalctl', '--disk-usage')}),
              ('xrdp', xrdp_check)]
    actions = [('apt', remove_apt), ('journal', vacuum_journal), ('xrdp', shrink_xrdp)]
    for name, action in (actions if args.apply else checks):
        try:
            result['steps'][name] = action()
        except Exception as error:
            result['steps'][name] = {'status': 'blocked', 'reason': str(error)}
        print(json.dumps({'step': name, 'result': result['steps'][name]}, ensure_ascii=False), flush=True)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if args.apply and any(v.get('status') == 'blocked' for v in result['steps'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
