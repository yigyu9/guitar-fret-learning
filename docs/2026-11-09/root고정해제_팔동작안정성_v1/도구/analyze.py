"""6조건 기록을 비교하고 고정/해제 영상의 한 화면 비교본을 만든다."""
import json
from pathlib import Path
import subprocess
import sys


def analyze(base):
    records, video = base/'기록', base/'video'
    results = []
    for mode in ('hold', 'right', 'left'):
        for state in ('fixed', 'free'):
            tag = state+'_'+mode
            report = json.loads((records/(tag+'.json')).read_text())
            rows = [json.loads(line) for line in (records/(tag+'.jsonl')).read_text().splitlines()]
            if not report['completed'] or report['encoder_exit_code'] != 0 or len(rows) != 720:
                raise ValueError('Incomplete native case: '+tag)
            crossed = [r['t_s'] for r in rows if r['pelvis_tilt_deg'] > 30. or
                       r['pelvis_z_m'] < report['initial_pelvis_z_m']-.15]
            result = dict(condition=tag, root_max_cm=100*report['max_root_delta_m'],
                tilt_max_deg=report['max_pelvis_tilt_deg'],
                pelvis_height_loss_cm=100*(report['initial_pelvis_z_m']-report['min_pelvis_z_m']),
                guitar_max_cm=100*report['max_guitar_delta_m'],
                wrist_max_cm=100*report['max_wrist_delta_m'],
                tail_root_speed_m_s=sum(r['root_speed_m_s'] for r in rows[-60:])/60,
                first_large_deviation_s=crossed[0] if crossed else None,
                invalid_control_ticks=report['controller_invalid_ticks'])
            results.append(result)
            probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames',
                '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_read_frames,duration',
                '-of', 'json', str(video/(tag+'.mp4'))], check=True, capture_output=True, text=True)
            meta = json.loads(probe.stdout)['streams'][0]
            if int(meta['nb_read_frames']) != 360 or abs(float(meta['duration'])-12.) > .001:
                raise ValueError('Video length differs: '+tag)
    summary = json.loads((records/'총괄.json').read_text())
    if not summary['completed'] or summary['changed_inputs']:
        raise ValueError('Native inputs changed')
    (records/'수치비교.json').write_text(json.dumps(dict(results=results,
        heuristic='기울기30도초과 또는 초기pelvis대비15cm이상하강:진단용큰이탈문턱,학습종료조건아님'),
        ensure_ascii=False, indent=2)+'\n')
    table = ['|조건|root 최대 이동(cm)|최대 기울기(°)|최대 높이 감소(cm)|기타 이동(cm)|',
             '|---|---:|---:|---:|---:|']
    labels = dict(hold='정지', right='오른팔 흔들기', left='왼팔 흔들기')
    for r in results:
        state, mode = r['condition'].split('_')
        table.append('|{} {}|{:.2f}|{:.2f}|{:.2f}|{:.2f}|'.format(
            '해제' if state == 'free' else '고정', labels[mode], r['root_max_cm'],
            r['tilt_max_deg'], r['pelvis_height_loss_cm'], r['guitar_max_cm']))
    text = '# root 해제와 팔 동작의 단기 안정성 검사\n\n'+'\n'.join(table)+'\n\n'
    text += ('각 조건12초·1회, 손가락 초기 목표 유지,2~10초 팔꿈치·손목1Hz 입력이다. '
             '의자·지면 접촉과 기존 지지 제어를 유지했으며 root 외력이나 중간 reset은 없다. '
             '기울기는 초기 pelvis의 위쪽 축 대비 변화이며 전체 yaw 회전각과는 다르다.\n\n'
             '동일한 관절 목표 입력을 사용했지만 접촉과 몸체 응답은 조건별로 달라진다. '
             '기타 이동과 인체 불안정은 별도로 해석해야 한다. '
             '짧은 외란 검사이므로 장시간 연주나 학습 정책의 안정성을 보장하지 않는다.\n\n'
             '기록에는 native body 궤적·목표각·root 이동·속도·높이·제어 유효성을 저장했다. '
             'free native Jacobian은66몸체×6×111열로 root의6자유도가 실제 추가됐음을 확인했다.\n\n'
             '독립 검수에서 Jacobian·현재pelvis FK변환·속도제한·추가root힘없음의 정합성을 확인했다. '
             '이번 실행은6조건 모두 인코더 정상 종료 후 scene 정리를 마쳤다.\n')
    (base/'결과.md').write_text(text)
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n']
    for mode in ('hold', 'right', 'left'):
        for state in ('fixed', 'free'):
            cmd += ['-i', str(video/(state+'_'+mode+'.mp4'))]
    filters = ';'.join('[{}:v]scale=640:360,setsar=1[v{}]'.format(i, i) for i in range(6))
    filters += ';'+''.join('[v{}]'.format(i) for i in range(6))
    filters += 'xstack=inputs=6:layout=0_0|640_0|0_360|640_360|0_720|640_720[out]'
    cmd += ['-filter_complex', filters, '-map', '[out]', '-an', '-c:v', 'libx264',
            '-threads', '2', '-crf', '20', '-pix_fmt', 'yuv420p', str(video/'고정_해제_6조건비교.mp4')]
    subprocess.run(cmd, check=True)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    analyze(Path(sys.argv[1]).resolve())
