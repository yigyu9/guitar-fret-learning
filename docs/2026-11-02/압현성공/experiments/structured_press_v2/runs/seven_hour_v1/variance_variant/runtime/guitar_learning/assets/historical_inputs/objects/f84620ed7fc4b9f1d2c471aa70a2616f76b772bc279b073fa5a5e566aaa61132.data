"""Audited BC Actor migration and four new unassisted native gates."""
import copy
from pathlib import Path

from guitar_learning.tool.experiments.transition.train import initialization_evidence as ORIGINAL_EVIDENCE
from guitar_learning.tool.experiments.transition.policy import SpecialistPolicy as OriginalPolicy, INITIALIZATION


def source_paths():
    return sorted(Path(__file__).parent.glob('*.py'))


def target_contract(source, settings):
    from guitar_learning.imitation.imitation_io import BUNDLE
    from guitar_learning.tool.experiments.transition.task import make_task
    from guitar_learning.tool.experiments.transition_refinement.reward import metadata
    value = copy.deepcopy(source)
    if 'refinement' in value['reward']:
        raise ValueError('original audited transition BC contract required')
    value['reward']['refinement'] = metadata(make_task(BUNDLE, settings['transition']), settings['transition'])
    return value


def initialization_evidence(settings, *, require_gate=False):
    import json
    from guitar_learning.imitation.imitation import dataset_manifest
    from guitar_learning.tool.experiments.transition_refinement.capture import audit_capture
    evidence = ORIGINAL_EVIDENCE(settings, require_gate=False)
    expected = target_contract(evidence['payload']['architecture']['contract'], settings)
    pins = dict(evidence['source_pins'])
    if require_gate:
        gates = settings['initialization']['gate_evaluations']
        if len(gates) != 4 or len(set(gates)) != 4:
            raise ValueError('four distinct new successful native refinement cases required')
        checkpoint = str(Path(settings['initialization']['checkpoint']).resolve())
        source_sha = dataset_manifest([checkpoint])[checkpoint]
        sources = dataset_manifest(source_paths())
        demonstrations = []
        for folder in gates:
            if not isinstance(folder, str) or not Path(folder).is_absolute():
                raise ValueError('absolute new native gate case paths required')
            audit = audit_capture(folder)
            report, actual = audit['report'], audit['settings']
            if (audit['contract'] != expected or report['action_source'] != 'policy'
                    or report['teacher_intervention'] is not False
                    or report['initialization_checkpoint_sha256'] != source_sha
                    or actual.get('refinement', {}).get('schema') != settings['refinement']['schema']
                    or actual['refinement'].get('evaluation_mode') != 'deterministic'
                    or actual['refinement'].get('exploration') != settings['refinement']['exploration']
                    or actual['size'] != settings['size']):
                raise ValueError('exact migrated BC, reward and deterministic exploration gates required')
            consumed = json.loads((Path(folder)/'inputs_before.json').read_text())
            if any(consumed.get(path) != sha for path,sha in sources.items()):
                raise ValueError('new native gates must pin the actual refinement implementation')
            for path,sha in audit['source_pins'].items():
                if path in pins and pins[path] != sha:
                    raise ValueError('conflicting refinement gate evidence')
                pins[path] = sha
            demonstrations.append(audit['arrays'])
    for path,sha in dataset_manifest(source_paths()).items():
        if path in pins and pins[path] != sha:
            raise RuntimeError('refinement implementation changed')
        pins[path] = sha
    if dataset_manifest(pins) != pins:
        raise RuntimeError('refinement initialization evidence changed')
    result = dict(evidence, source_pins=pins, target_contract=expected)
    if require_gate:
        import numpy as np
        from guitar_learning.tool.experiments.transition.learning import SHAPES
        result['rehearsal_data'] = {key:np.concatenate([d[key] for d in demonstrations]) for key in SHAPES}
    return result


def initialize_actor(model, settings):
    import torch
    from guitar_learning.imitation.imitation import dataset_manifest
    from guitar_learning.tool.experiments.transition.transfer import _model_state
    from guitar_learning.tool.experiments.transition_refinement.policy import SpecialistPolicy
    if not isinstance(model, SpecialistPolicy):
        raise ValueError('explicit refinement policy required')
    evidence = initialization_evidence(settings)
    source = evidence['payload']
    expected = copy.deepcopy(model.architecture)
    expected['schema'] = OriginalPolicy.schema
    expected['initialization'] = INITIALIZATION
    expected.pop('exploration'); expected.pop('mean_constraint')
    if expected['contract'] != evidence['target_contract']:
        raise ValueError('only the declared reward contract migration is permitted')
    expected['contract'] = source['architecture']['contract']
    if expected != source['architecture']:
        raise ValueError('exact500-state physical/action architecture required for Actor migration')
    _model_state(model, source['model'])
    values = model.state_dict()
    with torch.no_grad():
        for key in values:
            if key.startswith(('actor_encoders.left.', 'actor_heads.left.')):
                values[key].copy_(source['model'][key])
    model.reset_exploration()
    if dataset_manifest(evidence['source_pins']) != evidence['source_pins']:
        raise RuntimeError('BC evidence changed during selected Actor migration')
    return dict(schema='guitar_learning.transition_refinement_migration.v1',
        source_checkpoint=str(Path(settings['initialization']['checkpoint']).resolve()),
        source_pins=evidence['source_pins'], copied='selected left Actor only',
        exploration=settings['refinement']['exploration'], critic='fresh', optimizer='fresh',
        ppo_updates=0, success='not inherited; four new native gates required')
