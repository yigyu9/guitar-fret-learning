"""Audit the current J training inputs without creating a simulator.

Historical path labels in JSON are evidence identifiers. Only files actually
resolved for the current runtime must be inside the copied project directory.
"""
import argparse
import hashlib
import json
from pathlib import Path


def audit(song='05_BN2-131-B_solo'):
    from guitar_learning.native.paths import ROOT, PROVENANCE, resolve_input_path, verify_provenance
    from guitar_learning.runtime.prepared_reset_v1 import (
        load_prepared_reset_contract, prepared_input_paths)
    from guitar_learning.song.task import make_task, load_anchor_track

    if not song or Path(song).name != song or song in ('.', '..'):
        raise ValueError('one registered song identifier required')
    provenance = verify_provenance()
    contract = load_prepared_reset_contract()
    bundle = ROOT / 'data/song_bundles' / song
    task = make_task(bundle)
    load_anchor_track(bundle)
    manifest = json.loads(PROVENANCE.read_text())
    required = set(prepared_input_paths()) | {PROVENANCE}
    for row in manifest['files'] + manifest.get('generated_files', []):
        required.add(resolve_input_path(row['internal']))
    required.update(path for path in bundle.rglob('*') if path.is_file() or path.is_symlink())
    compound = ROOT / 'guitar_learning/assets/gpu_rigid_guitar_v1'
    required.update(path for path in compound.rglob('*') if path.is_file() or path.is_symlink())
    compound_manifest = json.loads((compound / 'manifest.json').read_text())
    required.update(resolve_input_path(ROOT / name) for name in compound_manifest['source_sha256'])
    from guitar_learning.gpu.scene import _MANIFEST_SHA256
    if hashlib.sha256((compound / 'manifest.json').read_bytes()).hexdigest() != _MANIFEST_SHA256:
        raise ValueError('compound guitar manifest SHA mismatch')
    if hashlib.sha256((compound / 'guitar_compound.xml').read_bytes()).hexdigest() != compound_manifest['asset_sha256']:
        raise ValueError('compound guitar asset SHA mismatch')
    for name, expected in compound_manifest['visual_mesh_sha256'].items():
        if hashlib.sha256((compound / name).read_bytes()).hexdigest() != expected:
            raise ValueError('compound visual mesh SHA mismatch: ' + name)
    for name, expected in compound_manifest['source_sha256'].items():
        if hashlib.sha256(resolve_input_path(ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('compound source SHA mismatch: ' + name)
    files, errors = [], []
    for lexical in sorted(required):
        path = lexical.resolve()
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError:
            errors.append('external runtime input: ' + str(lexical))
            continue
        if not path.is_file():
            errors.append('missing runtime input: ' + str(lexical))
            continue
        files.append(dict(path=relative, bytes=path.stat().st_size,
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return dict(schema='tab2body.portable_input_audit.v1', completed=not errors,
                project_root=str(ROOT), song=song, target_count=len(task.targets),
                prepared_target_count=len(contract['target105']),
                provenance=provenance, required_file_count=len(files),
                required_bytes=sum(row['bytes'] for row in files),
                external_or_missing_inputs=errors, files=files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--song', default='05_BN2-131-B_solo')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit(args.song)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x') as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'files'},
                     ensure_ascii=False, indent=2))
    return 0 if result['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
