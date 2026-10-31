"""Explicit held-out seeds and finite target perturbations for native trials."""
import copy

from guitar_learning.tool.experiments.contact_recovery.evaluation import evaluation_case


SCHEMA = 'guitar_learning.contact_recovery.protocol.v1'


def protocol_document(raw, mode):
    if (mode not in ('evaluate', 'collect') or not isinstance(raw, dict)
            or set(raw) != {'schema', 'process_mode', 'evaluation_mode', 'cases'}
            or raw['schema'] != SCHEMA or not isinstance(raw['cases'], list)
            or not 1 <= len(raw['cases']) <= 20):
        raise ValueError('explicit contact recovery protocol and1..20 cases required')
    value = copy.deepcopy(raw)
    for case in value['cases']:
        if not isinstance(case, dict) or set(case) != {'seed', 'perturbation'}:
            raise ValueError('each case requires its explicit seed and perturbation')
        evaluation_case(case['seed'], case_index=0, evaluation_mode=value['evaluation_mode'],
                        process_mode=value['process_mode'])
        if case['perturbation'] is not None and not isinstance(case['perturbation'], dict):
            raise ValueError('perturbation must be an explicit mapping or null')
        if mode == 'evaluate' and case['perturbation'] is not None:
            raise ValueError('unassisted evaluation cannot inject teacher perturbation commands')
    if mode == 'collect' and value['evaluation_mode'] != 'deterministic':
        raise ValueError('teacher-assisted collection has no stochastic policy')
    return value
