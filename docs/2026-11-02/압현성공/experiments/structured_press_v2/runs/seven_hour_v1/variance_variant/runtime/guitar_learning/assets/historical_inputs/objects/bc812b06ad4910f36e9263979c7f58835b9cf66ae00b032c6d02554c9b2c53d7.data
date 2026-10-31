"""One-checkpoint, evaluation-use provenance relocation after source internalization.

This writes a separate normal PPO payload. Evaluation-only is a usage boundary,
not a technical prohibition against resuming training with a normal PPO loader.
No prior musical success is inherited by the newly evaluated source contract.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import sys


SUPPORTED_SHA256 = 'ed4408f945b47732988927428a2228281abe777ac13a2b0ad797e0e64e6ffde7'
ROOT = Path(__file__).resolve().parents[4]
_DATA = (
    ('manifest.json', 'fa3834acdaa379b09e1de962fe476518f3d1861c36f167173c6e5cf7933b042a', 2674),
    ('mapping/fingering.json', '1deacbb5255d1241433a471ba32a7f412c1e4f5d19fea9b001150791b0726b75', 23171),
    ('source/annotation.jams', '5abf98549f95013c0c8735dc93089bd1b53c63bfd0ebf7323f055494546f05f8', 563246),
    ('source/audio.wav', '322c58673a25a8cfd9a3362502d0b274509b9e6013b94f2b3f06205881198220', 2584868),
    ('training/fret_training.json', '7cb149e32400945416fb00acc2fbd46b03783c756fc682c8b866ae77d9f7c8ca', 625511),
    ('training/strike_plan.json', '69f39ea8586a7433b7c1e130ef6030ac591c2189b664dff70bb870ddd7d0b81c', 39094),
    ('training/strike_training.json', '17d66fa7f1e40c7c3328972408d8c214129cb99507333775ad6617f0e25a02d3', 5870))
_CODE = (
    ('guitar_learning/music_task.py', 'guitar_learning/music_task.py', 'f2e7f3d7cbf05fe58d179269c66fc26274a71e33012580b478cca972259dd960', '39ea7926406c22c0f619146e7c1c828a063706e83d57552f36c246c3207595f6', 14245, 14232),
    ('guitar_learning/song/task.py', 'guitar_learning/song/task.py', '3901d8efe41ec88d312bc30cac83b69fc780dc1ccad48f235e34f4153cb9395b', '068470a000fa5ed726fe57b1492a1928ba0a2970fb7c51403197a82430025a76', 7913, 7900),
    ('stability_adapter_2/fresh_music_v1/events.py', 'guitar_learning/score/events.py', '0b81ce572ac56d5301f379dc31e87bf04a1a7ab58c83ea9d975a15a695aaec62', '8129fa576a320d950e46d8363af357c9f01e9f233d0522eaf57f917d6a0eed2d', 10034, 9425),
    ('tab2body/env/strike_goal_compiler.py', 'guitar_learning/score/strike_goal_compiler.py', 'ecc644771879eb095c9af5db14b20218401f718d682da45ab58430b02c876017', '8ff4e7f96e205f3bd67bfa1f7d4e6e366e89c1547c7ae1c49707170cc247e2c4', 53068, 31861),
    ('tab2body/full/events.py', 'guitar_learning/score/canonical.py', 'c586d262c99560d95eef7da1425c693725e8d2520481e24a0a94161b048ac03d', '8df2f0be90b0d4b5530e2ac895ce51e1180b5841e0222f4552c5d5fe75829609', 51530, 51518))


def expected_provenance(current=False):
    rows = [dict(path=str(ROOT/'data/song_bundles/05_BN2-131-B_solo'/name), sha256=sha, bytes=size)
            for name, sha, size in _DATA]
    rows += [dict(path=str(ROOT/(new if current else old)), sha256=new_sha if current else old_sha,
                  bytes=new_size if current else old_size)
             for old, new, old_sha, new_sha, old_size, new_size in _CODE]
    return sorted(rows, key=lambda row: row['path'])


def relocated_contract(original, target):
    """Only the exact historical/current provenance rows may differ."""
    before, after = copy.deepcopy(original), copy.deepcopy(target)
    old = before['task']['provenance'].pop('provenance')
    new = after['task']['provenance'].pop('provenance')
    if old != expected_provenance() or new != expected_provenance(current=True):
        raise ValueError('only the fixed supported source relocation is permitted')
    if before != after:
        raise ValueError('observation/action/target/reward/physical contract changed outside source provenance')
    result = copy.deepcopy(original)
    result['task']['provenance']['provenance'] = copy.deepcopy(new)
    return result


def verify_provenance_bytes(old, new):
    from guitar_learning.historical_inputs import fingerprint_paths, evidence_input_pins
    from guitar_learning.training.recording import digest
    expected = {row['path']: row['sha256'] for row in old}
    if fingerprint_paths(expected) != expected:
        raise RuntimeError('historical source provenance SHA mismatch')
    for row in old:
        physical = evidence_input_pins({row['path']: row['sha256']})
        paths = [Path(path) for path, sha in physical.items() if sha == row['sha256']]
        if len(paths) != 1 or paths[0].stat().st_size != row['bytes']:
            raise ValueError('historical provenance byte count mismatch')
    for row in new:
        path = Path(row['path'])
        if path.resolve() != path or path.stat().st_size != row['bytes'] or digest(path) != row['sha256']:
            raise ValueError('current live provenance SHA/bytes mismatch')


def exact_payload_equal(a, b):
    """Exact nested tensor/array equality used after checkpoint serialization."""
    import numpy as np
    import torch
    if type(a) is not type(b):
        return False
    if isinstance(a, torch.Tensor):
        return a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return a.dtype == b.dtype and np.array_equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact_payload_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(exact_payload_equal(x, y) for x, y in zip(a, b))
    return a == b


def migrate(checkpoint, capture, out):
    import torch
    from guitar_learning.training.recording import digest, write
    from guitar_learning.imitation.imitation import dataset_manifest
    checkpoint, capture, out = Path(checkpoint).resolve(), Path(capture).resolve(), Path(out).resolve()
    if out.exists():
        raise FileExistsError('new migration output directory required')
    if digest(checkpoint) != SUPPORTED_SHA256:
        raise ValueError('only the fixed reference B32 checkpoint is supported')
    from guitar_learning.tool.experiments.contact_recovery.audit_v2 import audit_capture
    migration_source_sha = digest(__file__)
    proof = audit_capture(capture)
    if proof['report'].get('perturbation') is not None:
        raise ValueError('successful nominal capture required')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    contract = payload['identity']['architecture']['contract']
    replacement = relocated_contract(contract, proof['contract'])
    old = contract['task']['provenance']['provenance']
    new = replacement['task']['provenance']['provenance']
    verify_provenance_bytes(old, new)
    migrated = dict(payload, identity=copy.deepcopy(payload['identity']))
    migrated['identity']['architecture']['contract'] = replacement
    out.mkdir(parents=True, exist_ok=False)
    path = out/'checkpoint_evaluation_only.pt'
    with path.open('xb') as stream:
        torch.save(migrated, stream)
    readback = torch.load(path, map_location='cpu', weights_only=False)
    if not exact_payload_equal(migrated, readback):
        raise RuntimeError('serialized migrated checkpoint did not preserve full payload')
    restored = dict(readback, identity=copy.deepcopy(readback['identity']))
    restored['identity']['architecture']['contract']['task']['provenance']['provenance'] = copy.deepcopy(old)
    if not exact_payload_equal(payload, restored):
        raise RuntimeError('checkpoint changed outside the permitted provenance list')
    if (digest(checkpoint) != SUPPORTED_SHA256 or digest(__file__) != migration_source_sha
            or dataset_manifest(proof['source_pins']) != proof['source_pins']):
        raise RuntimeError('original checkpoint/capture evidence changed during migration')
    verify_provenance_bytes(old, new)
    manifest = dict(schema='guitar_learning.contact_recovery.checkpoint_provenance.v1',
        completed=True, evaluation_only=True, evaluation_only_enforced_by_loader=False,
        usage_boundary='Evaluation-use artifact; ordinary PPO payload remains technically resumable. No training resume is authorized by this migration.',
        prior_success_inherited=False, optimizer_updates_unchanged=payload['updates'],
        changed_field='identity.architecture.contract.task.provenance.provenance',
        original_checkpoint=str(checkpoint), original_sha256=SUPPORTED_SHA256,
        migrated_checkpoint=str(path), migrated_sha256=digest(path), capture=str(capture),
        capture_result_sha256=digest(capture/'result.json'), capture_contract_sha256=digest(capture/'contract.json'),
        capture_source_pins=proof['source_pins'], migration_source=str(Path(__file__).resolve()),
        migration_source_sha256=migration_source_sha, old_provenance=old, new_provenance=new,
        payload_roundtrip_exact=True, other_payload_fields_exact=True,
        scope='Explicit source provenance relocation only; CPU deserialization preserves tensor values, optimizer, RNG and all other identity fields; new native performance must be evaluated')
    write(out/'manifest.json', manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    if args.out.exists():
        raise FileExistsError('new migration output directory required')
    audit_path = args.out.parent/(args.out.name+'_runtime_json_audit.json')
    if audit_path.exists():
        raise FileExistsError('new runtime audit path required')
    import isaacgym
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.activation import activated
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.observer import Observer
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.audit import publish
    observer = Observer()
    completed = False
    try:
        with activated(observer):
            manifest = migrate(args.checkpoint, args.capture, args.out)
            completed = manifest['completed'] is True
    finally:
        publish(observer, audit_path, completed=completed, mode='checkpoint_provenance',
                out=args.out, primary=sys.exc_info()[1])


if __name__ == '__main__':
    main()
