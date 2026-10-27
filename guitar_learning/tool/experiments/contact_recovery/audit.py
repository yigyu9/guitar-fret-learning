"""Recovery capture audit; explicit native/reward auditor copy with new schema.

Original transition/refinement auditors remain unchanged. Native, observation,
full music and refinement reward gates below retain their original criteria.
"""
import gzip
import json
from pathlib import Path


def _audit_native(folder):
    import numpy as np
    from guitar_learning.training.recording import digest
    from guitar_learning.imitation.imitation_io import BUNDLE
    from guitar_learning.imitation.imitation import dataset_manifest
    from guitar_learning.training.parallel import FIELDS
    from guitar_learning.core.observations import ObservationBuilder
    from guitar_learning.song.quality import SongLedger
    from guitar_learning.song.metrics import HISTORY_SCALES
    from guitar_learning.song.measurement import SongMeasurement
    from guitar_learning.core.safety import StabilityMonitor, SafetyConfig
    from guitar_learning.tool.experiments.transition.task import make_task
    from guitar_learning.tool.experiments.transition.metrics import TransitionLedger

    folder=Path(folder).resolve()
    read=lambda name:json.loads((folder/name).read_text())
    report=read('result.json');parent_path=Path(report['parent_result_path'])
    parent=json.loads(parent_path.read_text())
    if (report.get('schema')!='guitar_learning.contact_recovery_capture.v1'
            or parent.get('schema')!='guitar_learning.contact_recovery_probe.v1'
            or report.get('success') is not True or report.get('completed') is not True
            or report.get('source_unchanged') is not True or report.get('physical_flags_ok') is not True
            or report.get('forbidden_calls') or report.get('failure') or report.get('cleanup_error')
            or parent.get('completed') is not True or parent.get('source_unchanged') is not True
            or parent.get('failure') or parent.get('cleanup_error')
            or parent.get('case_manifests',{}).get(str(folder))!=digest(folder/'result.json')):
        raise ValueError('complete finalized successful native capture required')
    if (report.get('action_source') != 'solver' or report.get('teacher_intervention') is not True
            or report.get('mode') != 'collect'
            or report.get('missing_import_pins') or parent.get('missing_import_pins')
            or parent.get('physical_flags_ok') is not True or parent.get('forbidden_calls')):
        raise ValueError('teacher-assisted finalized native collection required for BC')
    files={'trace_sha256':'trace.jsonl.gz','demonstration_sha256':'demonstration.npz',
           'contract_sha256':'contract.json','settings_sha256':'settings.json',
           'inputs_before_sha256':'inputs_before.json','context_sha256':'context.json',
           'initial_sha256':'initial.json','recovery_sha256':'recovery.json','plan_sha256':'plan.json',
           'initial_state_sha256':'initial_state.json','case_spec_sha256':'case_spec.json'}
    if any(report.get(key)!=digest(folder/name) for key,name in files.items()):
        raise ValueError('capture artifact SHA mismatch')
    pins=read('inputs_before.json')
    if dataset_manifest(pins)!=pins:raise RuntimeError('capture consumed inputs changed')
    contract=read('contract.json');settings=read('settings.json');context=read('context.json');initial=read('initial.json')
    task=make_task(BUNDLE,settings['transition'])
    if contract['task']['transition']!=task.provenance['transition']:
        raise ValueError('capture task provenance changed')
    with np.load(folder/'demonstration.npz',allow_pickle=False) as archive:
        arrays={key:np.array(archive[key],copy=True) for key in (*FIELDS,'action','task_time_s')}
    ticks=round(task.duration_s*60)
    shapes=dict(state=(ticks,500),events=(ticks,64,24),mask=(ticks,64),
                priority_events=(ticks,2,24),priority_mask=(ticks,2),action=(ticks,39),task_time_s=(ticks,))
    if any(arrays[key].shape!=shape for key,shape in shapes.items()):raise ValueError('complete capture dimensions required')
    if any(not np.isfinite(arrays[k]).all() for k in ('state','events','priority_events','action','task_time_s')):
        raise ValueError('finite native capture required')
    if arrays['mask'].dtype!=np.bool_ or arrays['priority_mask'].dtype!=np.bool_ or np.any(np.abs(arrays['action'])>1):
        raise ValueError('boolean masks and bounded actions required')
    if settings['transition']['role']=='left' and np.any(arrays['action'][:,33:]!=0):
        raise ValueError('inactive right channels changed')
    if not np.allclose(arrays['task_time_s'],np.arange(ticks)/60.,rtol=0,atol=1e-10):
        raise ValueError('capture time must precede action')
    builder=ObservationBuilder(context['names'],context['human_names'],context['guitar_names'],
        context['human_com'],context['guitar_com'],context['reference105'],task)
    if builder.fields!=contract['observation']['fields'][:468]:raise ValueError('physical observation fields changed')
    builder.scales=np.asarray(contract['observation']['scales'][:468],dtype=float)
    def canonical(value):
        def encode(item):
            if isinstance(item,np.ndarray):return item.tolist()
            if isinstance(item,np.generic):return item.item()
            raise TypeError(type(item).__name__)
        return json.loads(json.dumps(value,default=encode,allow_nan=False))
    measurement=SongMeasurement(task,context['human_names'],context['guitar_names'])
    if canonical(measurement.reset(initial['sample']))!=initial['measured']:
        raise ValueError('initial native contact/geometry measurement changed')
    safety_config=SafetyConfig(**{key:contract['termination'][key] for key in SafetyConfig.__dataclass_fields__})
    stability=StabilityMonitor(context['human_names'],context['guitar_names'],safety_config)
    if canonical(stability.reset(initial['sample']))!=initial['safety']:
        raise ValueError('initial native stability measurement changed')
    song=SongLedger(task,initial['measured']);transition=TransitionLedger(task,initial['measured'],settings['transition'])
    def observe(sample,measured,safety,target,previous_action):
        safety=dict(safety,foot_delta_m=np.asarray(safety['foot_delta_m'],dtype=float))
        value=builder.build(sample,measured,safety,target,previous_action)
        value['state']=np.r_[value['state'],np.clip(np.asarray(song.history())/HISTORY_SCALES,-10,10)].astype(np.float32)
        return value
    expected=observe(initial['sample'],initial['measured'],initial['safety'],initial['target105'],np.zeros(39))
    count=0;physical_failure=False;episode=None
    with gzip.open(folder/'trace.jsonl.gz','rt') as stream:
        for count,line in enumerate(stream,1):
            if count>ticks:raise ValueError('excess native trace rows')
            row=json.loads(line);index=count-1
            if row['tick']!=index or not np.array_equal(row['action'],arrays['action'][index]):
                raise ValueError('capture action/native trace mismatch')
            for key in FIELDS:
                if not np.array_equal(np.asarray(row['before_observation'][key]),arrays[key][index]) or not np.array_equal(expected[key],arrays[key][index]):
                    raise ValueError('before-action observation/native trace mismatch: '+key)
            info=row['info'];measurements=info['physics_measurements'];samples=info['native_control']['physics_samples240']
            if len(measurements)!=4 or len(samples)!=4:raise ValueError('four actual native substeps required')
            for measured,sample in zip(measurements,samples):
                if measured['physics_step']!=sample['native']['physics_step']:raise ValueError('same native sample required')
                if canonical(measurement.update(sample))!=measured['music']:
                    raise ValueError('raw native contact/geometry measurement changed')
                actual_safety=stability.update(sample)
                if canonical(actual_safety)!=measured['stability']:
                    raise ValueError('raw native stability measurement changed')
                song.update(measured['music'],sample);transition.update(measured['music'])
                physical_failure|=bool(measured['stability']['failure_reasons'])
            physical_failure|=bool(info['failure_reasons'])
            if canonical(actual_safety)!=row['safety_after']:
                raise ValueError('last native stability measurement changed')
            expected=observe(samples[-1],measurements[-1]['music'],row['safety_after'],row['target105'],row['action'])
            if 'episode'in info:
                if count!=ticks:raise ValueError('early native episode is not complete capture')
                episode=info['episode']
    if count!=ticks or not episode or episode['valid'] is not True or episode['reason']!='timeline_complete' or physical_failure:
        raise ValueError('safe full native episode required')
    measured=transition.summary(completed=True);musical=song.summary(completed=True)
    if not measured['diagnostic_success'] or musical['left_success_count']!=len(task.targets):
        raise ValueError('native transition success did not reproduce')
    if settings['transition']['role']=='joint' and (musical['coupled_hit_count']!=len(task.targets)
            or musical['strict_music']['matched100']!=len(task.targets) or musical['wrong_crossings'] or musical['repeat_crossings']):
        raise ValueError('native joint musical success did not reproduce')
    for key,value in measured.items():
        if episode['transition'].get(key)!=value:raise ValueError('transition ledger summary mismatch: '+key)
    if episode['song']!=musical:raise ValueError('song ledger summary mismatch')
    source_pins=dict(pins)
    for path in (parent_path,folder/'result.json',*(folder/name for name in files.values())):
        source_pins[str(path.resolve())]=digest(path)
    return dict(contract=contract,settings=settings,arrays=arrays,source_pins=source_pins,report=report)


def _audit_refinement(folder, evidence):
    from guitar_learning.tool.experiments.transition.task import make_task
    from guitar_learning.imitation.imitation_io import BUNDLE
    from guitar_learning.tool.experiments.transition_refinement.reward import RewardLedger, metadata
    contract, settings = evidence['contract'], evidence['settings']
    task = make_task(BUNDLE, settings['transition'])
    if contract['reward'].get('refinement') != metadata(task, settings['transition']):
        raise ValueError('new refinement reward contract required; old native gates cannot be reused')
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


def _teacher_environment(contract, context, initial):
    import numpy as np
    from types import SimpleNamespace
    from guitar_learning.core.control import JointTargetContract
    metadata = contract['action']['target_contract']
    codec = JointTargetContract(metadata['native_order'], metadata['q_ref_rad'],
        metadata['native_lower_rad'], metadata['native_upper_rad'], metadata['rates_rad_s'],
        half_range_rad=metadata['half_range_rad'], control_hz=metadata['control_hz'],
        smoothing_alpha=metadata['smoothing_alpha'])
    if codec.metadata != metadata:
        raise ValueError('original target codec metadata must reconstruct exactly')
    indices = [context['names'].index(name) for name in codec.names]
    scene = SimpleNamespace(names=context['names'], human_bodies=context['human_names'],
        guitar_bodies=context['guitar_names'])
    control = SimpleNamespace(contract=codec, codec_previous=np.asarray(initial['target105'])[indices],
        session=SimpleNamespace(scene=scene))
    env = SimpleNamespace(control=control, last_sample=initial['sample'],
        last_measured=initial['measured'], last_safety=initial['safety'])
    return env, indices


def _audit_recovery(folder, evidence):
    import numpy as np
    from guitar_learning.tool.experiments.transition.task import make_task
    from guitar_learning.imitation.imitation_io import BUNDLE
    from guitar_learning.tool.experiments.contact_recovery.controller import Controller
    from guitar_learning.tool.experiments.contact_recovery.capture import select_bc_rows
    read = lambda name: json.loads((folder/name).read_text())
    initial, context, plan = read('initial.json'), read('context.json'), read('plan.json')
    task = make_task(BUNDLE, evidence['settings']['transition'])
    report = evidence['report']
    controller = Controller(plan, task, report.get('perturbation'), evidence['settings']['transition'])
    env, upper_indices = _teacher_environment(evidence['contract'], context, initial)
    labels = []
    last_override = None
    with gzip.open(folder/'trace.jsonl.gz', 'rt') as stream:
        for index, line in enumerate(stream):
            row = json.loads(line)
            diagnostic = row['teacher_diagnostic']
            action = np.asarray(controller.action(row['task_time_before_s'], row['before_observation'], env), dtype=np.float32)
            if not np.array_equal(action, np.asarray(row['action'])):
                raise ValueError('measured-state teacher/probe action did not replay exactly')
            if diagnostic != controller.diagnostic:
                raise ValueError('measured-state teacher/probe diagnostic did not replay exactly')
            if (type(diagnostic.get('teacher_corrective')) is not bool
                    or diagnostic['teacher_corrective'] != diagnostic['teacher']['contact_feedback_applied']):
                raise ValueError('actual teacher corrective label required')
            if type(diagnostic.get('override_active')) is not bool:
                raise ValueError('explicit actual probe override label required')
            teacher = np.asarray(diagnostic['teacher_action39'], dtype=np.float32).tolist()
            actual = np.asarray(row['action'], dtype=np.float32).tolist()
            if row.get('teacher_action39_float32') != teacher:
                raise ValueError('canonical float32 teacher label must match replayed teacher command')
            if not diagnostic['override_active'] and actual != teacher:
                raise ValueError('nonoverride expert label must equal actual canonical float32 action')
            if diagnostic['override_active']: last_override = index
            measurements = row['info']['physics_measurements']
            for sample in measurements:
                controller.observe_physics(sample['music'], sample['stability'])
            labels.append(dict(task_time_s=float(row['task_time_before_s']), action39=actual,
                teacher_action39=teacher, override_active=diagnostic['override_active'],
                teacher_corrective=diagnostic['teacher_corrective'],
                native_safe=not row['info']['failure_reasons'] and all(
                    not sample['stability']['failure_reasons'] for sample in measurements)))
            env.last_sample = row['info']['native_control']['physics_samples240'][-1]
            env.last_measured, env.last_safety = measurements[-1]['music'], measurements[-1]['stability']
            env.control.codec_previous = np.asarray(row['target105'], dtype=float)[upper_indices]
    summary = controller.ledger.summary(completed=True,
        musical_success=report['episode']['transition']['successful'])
    if read('recovery.json') != summary:
        raise ValueError('240Hz recovery ledger did not replay exactly')
    selected = select_bc_rows(labels, summary, completed=True,
        input_pins_verified=True, native_audit_verified=True)
    # Nominal controls and states before the probe are baseline evidence only.
    # A command override without actual measured loss/recovery is not recovery data.
    if last_override is None or summary['recovery_success'] is not True:
        selected = []
    else:
        selected = [index for index in selected if index > last_override]
    evidence.update(recovery=summary, selected_indices=selected,
        teacher_replayed=True, recovery_replayed=True)


def audit_capture(folder):
    """Audit a completed collect capture without weakening old import guards."""
    from guitar_learning.imitation.imitation import dataset_manifest
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.evidence import validate_report
    folder = Path(folder).resolve()
    report = json.loads((folder/'result.json').read_text())
    parent_out = Path(report['parent_result_path']).resolve().parent
    runtime = parent_out.parent/(parent_out.name+'_runtime_json_audit.json')
    runtime_pins = dataset_manifest([runtime])
    validate_report(runtime, parent_out, 'collect')
    evidence = _audit_native(folder)
    _audit_refinement(folder, evidence)
    _audit_recovery(folder, evidence)
    evidence['source_pins'].update(runtime_pins)
    if dataset_manifest(evidence['source_pins']) != evidence['source_pins']:
        raise RuntimeError('capture inputs changed during full recovery audit')
    return evidence
