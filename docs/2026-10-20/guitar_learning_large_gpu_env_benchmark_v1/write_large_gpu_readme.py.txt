"""Write the GPU benchmark README from verified summaries; never run training."""
import json
from pathlib import Path

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_large_gpu_env_benchmark_v1')


def write_readme(base=BASE):
    comparison = json.loads((base/'comparison.json').read_text()) if (base/'comparison.json').exists() else {}
    repeat = json.loads((base/'repeat_verification.json').read_text()) if (base/'repeat_verification.json').exists() else {}
    probe = json.loads((base/'cuda_probe.json').read_text()) if (base/'cuda_probe.json').exists() else {}
    source = json.loads((base/'source_manifest.json').read_text()) if (base/'source_manifest.json').exists() else {}
    rows = sorted(comparison.get('runs', []), key=lambda row: row['num_envs'])
    fresh_ok = (len(rows) == 3 and {row['num_envs'] for row in rows} == {2, 4, 8}
                and all(row.get('all_checks_passed') is True and row.get('updates') == 1 for row in rows)
                and comparison.get('source_unchanged') is True and len(source) == 410)
    cuda_ok = (probe.get('available') is True and probe.get('device_count') == 1
               and probe.get('tensor_device') == 'cuda:0' and probe.get('tensor_value') == 512.
               and 'RTX 4070 Ti' in probe.get('name', ''))
    repeat_ok = (repeat.get('completed') is True and repeat.get('num_envs') == 8
                 and repeat.get('horizon') == 256 and repeat.get('new_updates') == 2
                 and repeat.get('total_optimizer_updates') == 3
                 and repeat.get('checks', {}).get('restored_payload_exact_except_metadata') is True)
    done = fresh_ok and cuda_ok and repeat_ok
    eligible = [row for row in rows if row.get('all_checks_passed') is True]
    best = max(eligible, key=lambda row: row['runner_transitions_per_s']) if eligible else None
    lead = ('현재 기본 왼손의 **large·CUDA 정책/CPU 물리**에서 2/4/8환경 전곡 시험과 8환경 strict resume 반복 검증을 완료했다. '
            '시험한 후보 중 runner 처리율은 **%d환경**이 가장 높았다.' % best['num_envs']) if done else (
            '**집계·검증 진행 중인 문서다.** 2/4/8환경의 모든 검사와8환경 재개 검증이 완료되기 전에는 최종 권장값을 확정하지 않는다.')
    lines = ['# large 모델의 GPU 학습·병렬 환경 수 실측', '', '2026-10-20. '+lead,
        '**16환경은 측정하지 않았으며 시험한 8환경을 절대 최대치로 해석하지 않는다.**', '', '## 조건', '',
        ('- [실제 CUDA 확인](cuda_probe.json): %s 1개에서 `cuda:0` 텐서 계산값 512를 확인했다. '
         'sandbox에서 `/dev` 장치가 보이지 않았던 사실과 실제 GPU 실행 가능 여부를 구분한다.' % probe['name']) if cuda_ok else
        '- 실제 CUDA 텐서 계산·장치 확인은 아직 검증 대기다. [CUDA 확인 자료](cuda_probe.json).',
        '- 세 후보 모두 `--device cuda:0`을 명시했다. 부모의 정책 추론·PPO는 GPU, 독립 worker의 Isaac Gym PhysX 물리는 기존 CPU 방식이다. CPU로 자동 대체한 측정이 아니다.',
        '- 현재 기본 왼손 512상태/39행동·유연한 LH21 제어·성능 기반 보상, `05_BN2-131-B_solo`의 67음 전체다. 초기 035/v14·native 대기 0·정책 준비 3초·240Hz 물리/60Hz 정책·headless를 유지했다.',
        '- `large` 결합층 1024→1024→512·seed 7. N2/N4/N8은 각각 새 정책으로 **H1969·PPO 1회** 수행한다. 환경 수 외 설정 일치를 검사하며, 고정 Python 소스 410개와 실행 입력 SHA를 확인한다.',
        '- 후보는 동시에 겹치지 않게 실행한다. 서로 다른 N은 배치·난수·수집 자료가 달라지므로 처리율을 연주 성능의 우열로 읽지 않는다.', '',
        '## 전곡 부하와 처리율', '',
        '| 환경 수 | 전이 | 수집 시간 | PPO 시간 | runner 시간 | runner 처리율 | 검사 |',
        '| ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for row in rows:
        lines.append('| %d | %s | %.1f분 | %.1f초 | %.1f분 | %.2f전이/초 | %s |' % (
            row['num_envs'], format(row['transitions'], ','), row['collection_s']/60,
            row['update_s'], row['wall_s']/60, row['runner_transitions_per_s'],
            '통과' if row.get('all_checks_passed') is True else '미통과/검증 중'))
    if not rows:
        lines.append('| — | — | — | — | — | — | 집계 대기 |')
    lines += ['', '처리율은 `report.transitions / report.wall_s`이며 runner 시작~보고 구간 기준이다. CLI 바깥 초기 import와 최종 전곡 요약까지 포함한 전체 프로세스 처리율은 아니다. N8은 N2보다 수집 전이가 4배이므로 업데이트 1회의 실행 시간도 함께 비교한다.', '',
        '## RAM·GPU 메모리', '',
        '| 환경 수 | 가용 RAM 관측 최소 | GPU 전체 사용 관측 최대 | GPU 전체 여유 관측 최소 | Torch allocated 최고 | Torch reserved 최고 |',
        '| ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in rows:
        lines.append('| %d | %.2fGiB | %.1fMiB | %.1fMiB | %.1fMiB | %.1fMiB |' % (
            row['num_envs'], row['minimum_available_gib'], row['global_gpu_sample_peak_used_mib'],
            row['global_gpu_sample_min_free_mib'], row['torch_gpu_allocated_peak_mib'], row['torch_gpu_reserved_peak_mib']))
    if not rows:
        lines.append('| — | — | — | — | — | — |')
    lines += ['', '- GPU 전체 사용/여유는 약 2초 간격 `nvidia-smi` 표본이다. 다른 프로세스의 사용량도 포함하며 순간 최고/최저를 보장하지 않는다.',
        '- Torch 수치는 해당 부모 학습 프로세스의 실제 CUDA allocator 최고치다. `allocated`는 텐서 등에 할당한 양이고 `reserved`는 allocator가 확보한 영역이므로 같은 값이나 전체 GPU 사용량으로 취급하지 않는다.',
        '- 가용 RAM은 다른 프로그램도 포함한 host `MemAvailable` 관측 최소다. runner 값은 제어 tick 표본도 포함한다. 단계별 RSS/PSS는 약 5초/단계 전환 표본이며 worker별 누적 HWM 합은 동시에 사용한 RAM의 최고치가 아니다.',
        '- 외부 supervisor는 GPU 여유 1GiB·host 가용 6GiB를 보호 기준으로 사용한다. 프로세스 그룹의 종료·잔존 여부도 기록한다. 이 기준이나 기존 물리 안전을 완화하지 않았다.', '']
    if fresh_ok:
        lines += ['세 후보는 기대 전이·PPO 1회·유한 모델/optimizer·CUDA 난수/메모리 사용·입력 SHA·persistent/worker/guard 감사를 통과했다. '
                  '집계상 안전 전곡은 %d회, 물리 실패는 %d회, **손별 전곡 음악 성공은 %d회**다. 자원·실행 안정성과 압현 학습 성공을 구분한다.' % (
                      sum(row['full_safe_episodes'] for row in rows), sum(row['physical_failure_episodes'] for row in rows),
                      sum(row['whole_song_successful_episodes'] for row in rows)), '']
    lines += ['원자료: [N2](n2/report.json) · [N4](n4/report.json) · [N8](n8/report.json) · [집계와 검사](comparison.json). 각 실행의 설정·계약·checkpoint·전이·에피소드·자원 기록을 보존한다.', '',
        '## 저장 모델 재개·반복 확인', '']
    if repeat_ok:
        lines += ['N8의 `final.pt`를 같은 8환경·large·CUDA 계약으로 strict resume하고 **H256·PPO 2회**를 추가 수행했다. 추가 %s전이이며 누적 업데이트는 1→3회다.' % format(repeat['transitions'], ','),
            '재개 직후 모델·optimizer·부모 난수·curriculum을 포함한 payload는 이전 저장본과 metadata를 제외하고 정확히 같았다. 수집 길이와 이번 업데이트 수 외 설정도 일치한다.',
            '가용 RAM 관측 최소 %.2fGiB·실행시간 %.1f분이다. 이 짧은 재개 시험의 메모리를 H1969 전곡 부하의 최고치로 대신하지 않는다. [재개 검사](repeat_verification.json) · [실행 보고](n8_repeat/report.json).' % (repeat['minimum_available_gib'], repeat['wall_s']/60), '']
    else:
        lines += ['8환경·H256/PPO2회 strict resume 검증은 아직 완료하지 않았다. [재개 검사](repeat_verification.json)가 완료되기 전에는 payload 일치나 반복 안정성을 확정하지 않는다.', '']
    n = best['num_envs'] if done else 2
    lines += ['## 실행 예', '', '프로젝트 [실행 환경 설정](/home/ajou/yigyu/3/guitar_learning/README.md)을 적용한 뒤, 아직 없는 새 출력 경로에 실행한다. 아래는 전곡 1업데이트 명령이며 100업데이트를 측정했다는 뜻이 아니다.', '',
        '```bash', 'cd /home/ajou/yigyu/3', 'python -m guitar_learning.train \\', '  --hand left \\',
        '  --song 05_BN2-131-B_solo \\', '  --size large \\', '  --num-envs %d \\' % n,
        '  --device cuda:0 \\', '  --horizon 1969 \\', '  --updates 1 \\',
        '  --out /home/ajou/yigyu/3/runs/left_large_gpu_n%d_01' % n, '```', '',
        '같은 크기·손·곡·제어·PPO 계약끼리만 strict resume한다. `medium`을 `large`로 바꿔 재개하거나 이전 제어 계약을 암묵적으로 이전하지 않는다.', '',
        '## 범위와 보존', '',
        '- 한 seed의 전곡 1업데이트와 별도 H256 재개 시험이다. 16환경·100업데이트 장기 안정성·메모리 누수 부재·보상 진급·압현 수렴을 입증하지 않는다.',
        '- [이전 CPU 측정](../guitar_learning_large_env_benchmark_v1/README.md)은 당시 CPU 명시 경로의 별도 결과이며 원문을 보존한다. 이번 GPU 처리율로 과거 CPU 결과를 다시 분류하지 않는다.', '',
        '[고정 소스 SHA](source_manifest.json) · [CUDA 확인](cuda_probe.json) · [집계](comparison.json) · [재개 검사](repeat_verification.json) · [계획](PLAN.md) · [실행 감시 버전](controller_versions.json) · [독립 검수](review.json)', '']
    (base/'README.md').write_text('\n'.join(lines))
    print(json.dumps(dict(readme=str(base/'README.md'), completed=done, fresh_verified=fresh_ok,
                         cuda_verified=cuda_ok, repeat_verified=repeat_ok), ensure_ascii=False))


if __name__ == '__main__':
    write_readme()
