"""Audit original native evidence and independently replay the new reward."""
import gzip
import json
from pathlib import Path


def audit_capture(folder):
    from ..transition.capture import audit_capture as original
    from ..transition.task import make_task
    from ..imitation_io import BUNDLE
    from .reward import RewardLedger, metadata
    folder = Path(folder).resolve()
    contract = json.loads((folder/'contract.json').read_text())
    settings = json.loads((folder/'settings.json').read_text())
    task = make_task(BUNDLE, settings['transition'])
    if contract['reward'].get('refinement') != metadata(task, settings['transition']):
        raise ValueError('new refinement reward contract required; old native gates cannot be reused')
    evidence = original(folder)
    initial = json.loads((folder/'initial.json').read_text())
    ledger = RewardLedger(task, initial['measured'], settings['transition'])
    total = 0.
    with gzip.open(folder/'trace.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            info = row['info']
            computed = []
            for sample in info['physics_measurements']:
                terms = ledger.update(sample['music'])
                if info['failure_reasons']:
                    terms = {key:min(0., value) for key,value in terms.items()}
                if sample.get('refinement_reward_terms') != terms:
                    raise ValueError('refinement physics reward did not reproduce')
                computed.append(terms)
            if info['failure_reasons']:
                ledger.invalidate(info['failure_reasons'])
            legacy = info['legacy_reward_terms']
            expected = {key:legacy[key] for key in ('action_change', 'terminal_failure')}
            for terms in computed:
                for key,value in terms.items():
                    expected[key] = expected.get(key, 0.)+value
            if expected != info['reward_terms'] or sum(expected.values()) != row['reward']:
                raise ValueError('new reward composition or legacy reward removal mismatch')
            total += row['reward']
            completed = 'episode' in info
            summary = ledger.summary(completed)
            summary.update(successful=info['transition']['successful'],
                stage_success=info['transition']['successful'], role='left')
            if info.get('refinement') != summary:
                raise ValueError('refinement reward/readiness summary did not reproduce')
            if completed and (info['episode'].get('refinement') != summary
                    or abs(info['episode']['reward']-total) > 1e-10):
                raise ValueError('refinement episode accounting did not reproduce')
    evidence['refinement_reward_replayed'] = True
    return evidence
