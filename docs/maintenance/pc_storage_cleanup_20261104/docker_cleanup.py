#!/usr/bin/python3
"""Default read-only. --apply removes only two approved, unused image IDs, without force or ancestor pruning."""
import argparse
import json
import subprocess
import time

TARGETS = {
    'brainicism/bgutil-ytdlp-pot-provider:latest': 'sha256:1aaa43a0ca72dfca6a6d2129a0fb4a23465c25adb1b043f8aff829a20825646b',
    'nvidia/cuda:11.8.0-base-ubuntu22.04': 'sha256:f895871972c1c91eb6a896eee68468f40289395a1e58c492e1be7929d0f8703b',
}


def docker(*args):
    p = subprocess.run(['/usr/bin/docker', *args], capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()


def check(tag, expected_id):
    image = json.loads(docker('image', 'inspect', tag))[0]
    if image['Id'] != expected_id or image['RepoTags'] != [tag]:
        raise RuntimeError(f'Approved image ID or tags changed: {tag}')
    containers = docker('ps', '-a', '-q', '--no-trunc').splitlines()
    if containers:
        for cid in containers:
            if docker('container', 'inspect', cid, '--format', '{{.Image}}') == expected_id:
                raise RuntimeError(f'Container references approved image: {cid}')
    return {'tag': tag, 'id': expected_id, 'bytes': image['Size'], 'referencing_containers': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    evidence = [check(tag, iid) for tag, iid in TARGETS.items()]
    print(json.dumps({'apply': args.apply, 'time': time.time(), 'preflight': evidence}), flush=True)
    if args.apply:
        for tag, iid in TARGETS.items():
            check(tag, iid)
            output = docker('image', 'rm', '--no-prune', iid)
            print(json.dumps({'deleted_id': iid, 'output': output}), flush=True)
    print(docker('system', 'df', '--format', '{{json .}}'), flush=True)


if __name__ == '__main__':
    main()
