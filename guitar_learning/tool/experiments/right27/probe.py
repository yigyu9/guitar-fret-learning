"""강제 상태 변경 없이 정책 행동을 넣어 오른손21축의 native 물리 응답을 기록한다."""
from pathlib import Path
import sys


def probe(settings, out):
    import torch
    from guitar_learning.training.training_log_io import (
        active_source_paths, digest, project_source_paths, write)
    from .pool import Right27Pool
    from .policy import Right27Policy
    from guitar_learning.core.control import RIGHT_GRIP_NAMES
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.paths import pin
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[4]
    sources = active_source_paths(root/'guitar_learning') | prepared_input_paths()
    sources.update((root/'guitar_learning/assets').rglob('*.json'))
    sources.update((root/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*.xml'))
    sources.update(p for p in Path(settings['song_training']['bundle']).rglob('*') if p.is_file())
    pins = pin(BASELINE_CONFIG, extra=sources)
    write(out/'settings.json', settings)
    write(out/'inputs_before.json', pins)
    pool = None
    report = dict(completed=False, failure=None)
    try:
        pool = Right27Pool(settings, out)
        write(out/'training_contract.json', pool.contract)
        policy = Right27Policy(pool.observation['state'].shape[-1], size=settings['size'],
                               contract=pool.contract).to(settings['device'])
        sample = pool.scene.snapshot()
        indices = pool.controller.finger_indices
        start_q = sample['q'][:, indices].clone()
        q_min, q_max = start_q.clone(), start_q.clone()
        target_min = pool.controller.target[:, indices].clone()
        target_max = target_min.clone()
        max_tick_delta = 0.
        with torch.no_grad():
            observation = pool.observation
            policy_output = policy.act(**{key: observation[key] for key in
                ('state', 'events', 'mask', 'priority_events', 'priority_mask')})
        if (policy_output['action'][:, :12] != 0).any():
            raise AssertionError('비활성12축 출력이 0이 아닙니다')
        for tick in range(60):
            action = torch.zeros(settings['num_envs'], 39, device=settings['device'])
            action[:, 12:33] = .25 if tick < 30 else -.25
            previous = pool.controller.target[:, indices].clone()
            pool.step(action)
            current = pool.controller.target[:, indices]
            max_tick_delta = max(max_tick_delta, float((current-previous).abs().max()))
            target_min = torch.minimum(target_min, current)
            target_max = torch.maximum(target_max, current)
            q = pool.scene.snapshot()['q'][:, indices]
            q_min, q_max = torch.minimum(q_min, q), torch.maximum(q_max, q)
        moved = (q_max-q_min).amax(0)
        requested = (target_max-target_min).amax(0)
        if not (requested > 1e-5).all() or not (moved > 1e-5).all():
            raise AssertionError('일부 오른손 관절에서 명령 또는 실제 응답이 없습니다')
        # 중간 reset이 없는 짧은 검사에서 tick당 속도 제한도 함께 확인한다.
        if max_tick_delta > 4./60.+1e-5:
            raise AssertionError('오른손 목표각 속도 제한 초과')
        report.update(completed=True, controlled_dofs=27, finger_dofs=21,
            action_container=39, ticks=60, control_hz=60,
            max_target_delta_rad_per_tick=max_tick_delta,
            joints=[dict(name=name, target_range_rad=float(requested[i]),
                         actual_range_rad=float(moved[i]))
                    for i, name in enumerate(RIGHT_GRIP_NAMES)],
            scope='native 관절 명령과 물리 응답 검사; 타현 학습 성공을 의미하지 않음')
    except BaseException as exc:
        report['failure'] = repr(exc)
        raise
    finally:
        if pool is not None:
            pool.close()
        changed = [name for name, sha in pins.items() if digest(name) != sha]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        report.update(changed_inputs=changed, missing_import_pins=missing)
        report['completed'] = report['completed'] and not changed and not missing
        write(out/'report.json', report)
    if not report['completed']:
        raise RuntimeError('검사 중 실행 소스가 바뀌었습니다')
    return report
