"""CPU strict input check and source seal; never starts native evaluation."""
import json
from pathlib import Path

from protocol import HERE, BASELINE, REFERENCE, CONDITIONS, protocol
from probe import sha, write


def main():
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import SCHEMA, read_teacher, read_reference
    from guitar_learning.gpu.thumb_support import load_thumb_support
    from guitar_learning.gpu.episode_diagnostics import DIAGNOSTIC_CONTRACT
    assert not torch.cuda.is_initialized()
    metadata = torch.load(BASELINE/'train/initial.pt', map_location='cpu', weights_only=False)['metadata']
    runner._validate_pins(metadata)  # Original current-source strict checker, no bypass.
    settings = metadata['settings']; spec = settings['song']['short_learning']
    assert metadata['schema'] == SCHEMA and settings['num_envs'] == 128
    assert spec['mode'] == 'incremental' and spec['finger'] == 2 and spec['view']['duration_ticks'] == 218
    assert 'ablation' not in spec and settings['ppo']['gamma'] == .99
    assert read_teacher(spec['teacher']['input_path']) == spec['teacher']
    reference = read_reference(REFERENCE, spec)
    patch = load_thumb_support()
    assert patch['contract']['schema'] == 'guitar_learning.gpu_thumb_rear_support.v3'
    assert DIAGNOSTIC_CONTRACT['schema'] == 'guitar_learning.gpu_left_episode_diagnostics.v6'
    facts = []
    for name, filename, control, update in CONDITIONS:
        path = BASELINE/'train'/filename
        if not path.is_file():
            facts.append(dict(condition=name, available=False, status='not yet captured; original strict evaluation required later'))
            continue
        payload = torch.load(path, map_location='cpu', weights_only=False)
        runner._validate_pins(payload['metadata'])
        assert payload['metadata']['settings'] == settings and payload['updates'] == update
        facts.append(dict(condition=name, available=True, checkpoint_sha256=sha(path), updates=update,
            strict_input_pins_valid=True,
            strict_native_trainer_load='CPU does not restore CUDA RNG; unchanged original trainer.load will validate full identity and CUDA topology at runtime'))
        del payload
    paths = {Path(p) for p in metadata['input_pins']} | {REFERENCE, *map(Path, reference['source_evidence'])}
    paths |= {HERE/name for name in ('probe.py', 'protocol.py', 'self_test.py', 'prepare.py', 'README.md')}
    pins = {str(p.resolve()): sha(p) for p in sorted(paths)}
    write(HERE/'precommit.json', dict(protocol=protocol(), input_pins=pins,
        active_python_count=len([p for p in pins if '/guitar_learning/' in p and p.endswith('.py') and '/archive/' not in p]),
        current_helper_contract=patch['contract'], diagnostic_contract=DIAGNOSTIC_CONTRACT,
        status='CPU preparation only; root GPU handoff required, no additional user approval'))
    write(HERE/'checkpoint_cpu_check.json', dict(completed=True, GPU_used=False, checkpoints=facts,
        own_current_source_inputs_valid=True, teacher_and_reference_evidence_valid=True,
        checkpoint_copy_saved=False, full_CUDA_trainer_load_deferred=True))
    print(json.dumps(dict(completed=True, GPU_used=False, source_input_pins=len(pins), checkpoint_conditions=facts), indent=2))


if __name__ == '__main__':
    main()
