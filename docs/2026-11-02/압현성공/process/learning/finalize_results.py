"""실험 종료를 기다려 실제 평가·영상 결과를 읽기 쉬운 표로 기록한다."""
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent


def read(path):
    return json.loads(path.read_text())


def main():
    while True:
        status = read(HERE / 'status.json')
        if status['phase'] in ('complete', 'failed'):
            break
        time.sleep(20)
    out = BASE / 'analysis/learning'
    out.mkdir(parents=True, exist_ok=True)
    summary_path = out / 'summary.json'
    rows = read(summary_path)['goals'] if summary_path.exists() else []
    text = ['# 실제 학습 환경의 가상 단음 압현 결과', '',
            f"실행 상태: {status['phase']}. 평가 완료 목표: {len(rows)}/16.", '',
            'large·64환경·H32·100회·seed 7, 목표마다 새 정책으로 학습했다. '
            '목표는 3.0~5.5초이며 기존 기준인 연속 clean 1.0초를 달성해야 한다. '
            '기존 J33 보상·제어·조기 종료를 유지했다. 각 모델은 16환경에서 평가했다.', '',
            '성공 횟수는 음 달성과 물리·손목 실패가 없는 평가 에피소드 수이다. '
            '이는 1개 seed의 짧은 학습이며 실패가 곧 물리적 도달 불가능을 뜻하지 않는다.', '',
            '| 목표 | 초기→최종 성공 /16 | 최종 최장 clean (초) | 평균 보상 초기→최종 |',
            '|---|---:|---:|---:|']
    for row in rows:
        text.append(f"| {row['label']} | {row['initial_success_count']} → {row['final_success_count']} | "
                    f"{row['final_max_best_clean_streak_s']:.3f} | "
                    f"{row['initial_mean_reward']:.3f} → {row['final_mean_reward']:.3f} |")
    if status['phase'] == 'failed':
        text.extend(['', '중단 사유: ' + status.get('failure', '상태 파일 확인 필요')])
    media = HERE / 'media_manifest.json'
    if media.exists():
        text.extend(['', '## 실제 정책 영상', '',
                     '영상은 별도 재평가의 환경 0을 촬영했다. 평가에서 성공한 목표라도 '
                     '이 촬영 에피소드의 성공 여부는 아래에 따로 표시한다.'])
        for item in read(media)['videos']:
            report = read(Path(item['native_render_report']))
            episode = report['episode']
            term = episode['termination']
            success = (episode['song']['left_success_count'] > 0
                       and not term['physical_failure'] and not term['wrist_failure'])
            text.extend(['', f"- {item['label']}: 촬영 에피소드 {'성공' if success else '미달성'}"])
            for view, path in item['videos'].items():
                subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', path, '-f', 'null', '-'], check=True)
                text.append(f'  - [{view}]({path})')
    text.extend(['', '과거 기하 후보 재생 결과는 상위 디렉토리에 별도로 보존했다. '
                 '본 표와 video/learning만 실제 PPO 학습 결과이다.', ''])
    (out / 'RESULTS.md').write_text('\n'.join(text))
    (out / 'finalization.json').write_text(json.dumps(
        {'completed': True, 'runner_phase': status['phase'], 'evaluated_goals': len(rows),
         'all_listed_videos_decoded': media.exists()}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
