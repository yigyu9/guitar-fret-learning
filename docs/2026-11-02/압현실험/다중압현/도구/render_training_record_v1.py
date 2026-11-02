"""CPU-only visualization of recorded measurements; no physics or policy replay."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT/'학습_인접2지_v1'
RUN = STUDY/'로그/parallel_v1/pilot_env2'
TRACE = RUN/'J/finger_control_trace.jsonl.gz'
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
OUT = ROOT/'video/인접2지_실제학습기록_v1.mp4'
LOG = ROOT/'로그/결과영상_v1'
ANALYSIS = ROOT/'분석/결과영상_v1'
FPS = 24
SPEED = .5


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    LOG.mkdir(parents=True, exist_ok=False)
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    inputs = {str(p): sha(p) for p in (TRACE, RUN/'job_report.json', RUN/'J/episodes.jsonl', RUN/'J/final.pt', Path(__file__))}
    job = json.loads((RUN/'job_report.json').read_text())
    assert job['completed'] and sha(RUN/'J/final.pt') == job['checkpoint_sha256']
    with gzip.open(TRACE, 'rt') as stream:
        rows = [r for line in stream if (r := json.loads(line))['env_id'] == 0 and r['episode_id'] == 0]
    episodes = [json.loads(line) for line in (RUN/'J/episodes.jsonl').read_text().splitlines()]
    episode = next(r['episode'] for r in episodes if r['episode']['env_id'] == 0 and r['episode_id'] == 0)
    assert episode['reason'] == 'timeline_complete' and len(rows) == episode['steps']*4
    times = np.array([r['episode_time_s'] for r in rows])
    steps = [r['episode_physics_step'] for r in rows]
    assert steps == list(range(1, len(rows)+1))
    assert np.allclose(times, np.arange(1, len(rows)+1)/240., rtol=0, atol=1e-10)
    assert len({tuple(r['joint_names']) for r in rows}) == 1
    distances = {}
    for finger in ('index', 'middle'):
        distances[finger] = np.array([next((t['pad_distance_m']*1000 for t in r['targets']
            if t['finger'] == finger and t['target_present']), np.nan) for r in rows])
    actual = np.array([r['actual_rad'] for r in rows])
    names = rows[0]['joint_names']
    plt.rcParams.update({'font.family': FontProperties(fname=FONT).get_name(),
                         'font.size': 13, 'axes.unicode_minus': False})
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor='#101827')
    axes = [fig.add_axes([.065, .30, .45, .39]), fig.add_axes([.605, .30, .35, .39])]
    for ax in axes:
        ax.set_facecolor('#172338')
        ax.tick_params(colors='#cad5e4')
        for spine in ax.spines.values():
            spine.set_color('#506079')
        ax.set_xlim(0, times[-1])
        ax.axvspan(3.3, 4.8, color='#2eccad', alpha=.12)
        ax.set_xlabel('실제 에피소드 시간 (초)', color='#cad5e4')
        ax.grid(alpha=.12, color='white')
    colors = ('#57afff', '#42d5ac')
    for finger, label, color in zip(('index', 'middle'), ('검지 · 3번 줄', '중지 · 2번 줄'), colors):
        axes[0].plot(times, distances[finger], color=color, label=label, linewidth=2)
        for joint, dash, label_joint in (('1_x', '-', 'MCP'), ('2', '--', 'PIP'), ('3', ':', 'DIP')):
            index = names.index('LH:'+finger+joint)
            axes[1].plot(times, np.rad2deg(actual[:, index]-actual[0, index]),
                         dash, color=color, linewidth=1.2, label=label[:2]+' '+label_joint)
    axes[0].set_ylim(0, max(60., max(np.nanmax(d) for d in distances.values())*1.1))
    axes[0].set_title('패드와 목표 구간 사이 거리 (mm)', color='white', pad=14)
    axes[1].set_title('실제 굽힘 관절각 변화 (도)', color='white', pad=14)
    for ax in axes:
        ax.legend(fontsize=10, loc='upper left', facecolor='#172338', labelcolor='white')
    fig.canvas.draw()
    base = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
    plt.close(fig)
    fonts = {size: ImageFont.truetype(FONT, size) for size in (18, 21, 24, 31, 38)}
    def text(draw, xy, value, size=21, fill='#d9e3f1'):
        draw.text(xy, value, font=fonts[size], fill=fill)
    intro, replay, outro = 48, math.ceil(times[-1]/SPEED*FPS), 72
    count = intro+replay+outro
    command = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-n',
               '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', str(FPS),
               '-i', '-', '-an', '-c:v', 'libx264', '-threads', '1', '-preset', 'fast',
               '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT)]
    mapping = []
    with (LOG/'ffmpeg.stderr.log').open('xb') as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors)
        try:
            for frame in range(count):
                requested = max(0., min(times[-1], (frame-intro)/FPS*SPEED))
                index = max(0, min(len(rows)-1, int(np.searchsorted(times, requested, side='right'))-1))
                row, t = rows[index], times[index]
                image = base.copy(); draw = ImageDraw.Draw(image)
                text(draw, (60, 22), '인접 두 손가락 · 실제 학습 기록', 31, 'white')
                text(draw, (60, 72), '검지–중지 | 3·2번 줄, 6·6프렛 | 2환경 · 20업데이트 · 1,280전이', 21)
                text(draw, (60, 111), '환경 0 / 첫 완료 에피소드 · 0.5배속 · 카메라 촬영 및 최종 정책 재생 아님', 18, '#f7ca79')
                for ax in axes:
                    x, y = ax.transData.transform((t, ax.get_ylim()[0]))
                    top = 720-ax.transAxes.transform((0, 1))[1]
                    draw.line((x, top, x, 720-y), fill='#ffffff', width=2)
                phase = '준비 구간' if t < 3.3 else ('공통 유지 평가창' if t <= 4.8 else '마무리 구간')
                text(draw, (62, 570), f'실제 시간 {t:4.2f} / {times[-1]:.2f}초  ·  {phase}', 24, 'white')
                values = []
                for finger, label in (('index', '검지'), ('middle', '중지')):
                    distance = distances[finger][index]
                    values.append(label+(' 목표 비활성' if not np.isfinite(distance) else f' 거리 {distance:.1f}mm'))
                text(draw, (62, 612), '   |   '.join(values)+'   ·   녹색 영역: 공통 1.5초 창', 21)
                text(draw, (62, 656), '학습 중 동시 성공 0/2 · 최종 고정 평가 미실시 · 실제 현 압력/음향 판정 아님', 21, '#f7ca79')
                if frame < intro or frame >= intro+replay:
                    draw.rounded_rectangle((300, 248, 980, 421), radius=16, fill='#0a1120', outline='#506079', width=2)
                    title = '저장된 측정 기록을 재생합니다' if frame < intro else '아직 동시 압현 성공은 확인되지 않았습니다'
                    text(draw, (330, 272), title, 24, 'white')
                    text(draw, (330, 322), '240Hz 실제 관절각·거리 기록 / 전신 궤적 재현 아님', 21)
                    text(draw, (330, 362), '정식 6과제 학습: 기존 단일 검사 완료 후 실행 대기', 21)
                if frame == intro+int(4.0/SPEED*FPS):
                    image.save(ANALYSIS/'대표프레임.png')
                process.stdin.write(image.tobytes())
                mapping.append({'frame':frame, 'trace_row':index, 'episode_physics_step':row['episode_physics_step'], 'episode_time_s':t})
        finally:
            process.stdin.close()
            code = process.wait()
    assert code == 0
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,avg_frame_rate,nb_read_frames,duration', '-of', 'json', str(OUT)]))
    stream = probe['streams'][0]
    assert (stream['width'],stream['height'],stream['avg_frame_rate'],int(stream['nb_read_frames'])) == (1280,720,'24/1',count)
    assert abs(float(stream['duration'])-count/FPS) < .002
    assert all(sha(path) == value for path,value in inputs.items())
    (LOG/'frame_mapping.json').write_text(json.dumps(mapping, indent=2))
    report = {'completed':True, 'source_pins':inputs, 'source_unchanged':True, 'video':str(OUT),
              'video_sha256':sha(OUT), 'probe':probe, 'episode_selection':'predeclared env0 episode0; first completed training episode',
              'trace_rows':len(rows), 'actual_duration_s':float(times[-1]), 'speed':SPEED,
              'physics_reexecuted':False, 'gpu_used':False, 'final_checkpoint_evaluated':False,
              'scope':'Recorded joint angles and target distances only; not native camera pixels or whole-body replay',
              'training_episode_summary':job['simultaneous_summary']}
    (LOG/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
