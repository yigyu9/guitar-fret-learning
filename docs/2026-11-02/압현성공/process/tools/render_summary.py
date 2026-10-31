"""실제 물리 기록에서 100ms 진단 접촉에 성공한 목표만 영상으로 모은다.

저장된 자세를 그대로 그리며 물리를 다시 실행하거나 성공 판정을 바꾸지 않는다.
100ms 진단 접촉은 곡의 음 길이별 달성·음향 성공을 뜻하지 않는다.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent/'guitar_learning').is_dir())
FINGERS = {1: 'index', 2: 'middle', 3: 'ring', 4: 'pinky'}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def render_successes(source, out, video_out, rows_filter=None):
    """실패 전 유효 기록의 성공 영상을 출력하고 증거 프레임을 모은다."""
    os.environ['MUJOCO_GL'] = 'osmesa'
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import numpy as np
    from PIL import Image, ImageDraw
    from guitar_learning.tool.validation import press_acquisition as press

    report = json.loads((source/'report.json').read_text(encoding='utf-8'))
    rows = tuple(report['settings']['representative_rows'])
    if rows_filter is not None:
        rows_filter = frozenset(rows_filter)
        if not rows_filter <= set(rows):
            raise ValueError('Selected row has no recorded poses')
    poses = np.load(source/'poses60.npz', allow_pickle=False)
    trace = np.load(source/'trace240.npz', allow_pickle=False)
    if poses['valid'].shape[1] != len(rows) or trace['valid'].shape[1] != len(rows):
        raise ValueError('Recorded row count does not match the declared row mapping')
    press.REPRESENTATIVE_ROWS = rows
    out.mkdir(parents=True, exist_ok=True)
    video_out.mkdir(parents=True, exist_ok=True)
    manifest = dict(source=str(source.resolve()), guitar_mode=report['settings']['guitar_mode'],
        success_definition='At least100ms continuous current diagnostic contact before first safety failure; not song achievement',
        rendering='Exact recorded physical body poses; zero new physics steps',
        source_sha256={name: hashlib.sha256((source/name).read_bytes()).hexdigest()
                       for name in ('report.json', 'poses60.npz', 'trace240.npz', 'metadata.json')},
        selected_rows=sorted(rows_filter) if rows_filter is not None else list(rows),
        successes=[], excluded=[])
    cards = []
    for goal in report['goals']:
        row = goal['row']
        if rows_filter is not None and row not in rows_filter:
            continue
        if not goal['diagnostic_hold_100ms'] or goal['failure'] is not None:
            manifest['excluded'].append(dict(row=row, reason='Less than100ms diagnostic contact or safety failure'))
            continue
        if row not in rows:
            raise ValueError('Successful row has no recorded poses: %d'%row)
        slot = rows.index(row)
        valid = poses['valid'][:, slot].astype(bool)
        frames = int(valid.sum())
        if frames < 1 or not valid[:frames].all() or valid[frames:].any():
            raise ValueError('Only a contiguous pre-failure pose prefix may be rendered')
        # 안전한60Hz 자세 기록 범위 안에서 접촉이 확인된 성공만 채택한다.
        times = trace['physics_step']/240.
        eligible = trace['valid'][:, slot].astype(bool) & (times <= poses['tick'][frames-1]/60.)
        streak = np.where(eligible, trace['streak'][:, slot], -1.)
        peak = int(streak.argmax())
        if streak[peak]+1e-12 < .1:
            manifest['excluded'].append(dict(row=row, reason='100ms not supported inside safely rendered pose prefix'))
            continue
        name = '%s_s%d_f%d'%(FINGERS[goal['finger']], goal['physical_string'], goal['fret'])
        destination = out/name
        if destination.exists():
            raise FileExistsError('Preserve existing media; use a fresh output directory: '+str(destination))
        press.render_replay(source, destination, row=row)
        timestamp = float(times[peak])
        # 마지막 프레임 경계의 반올림 때문에 ffmpeg가 빈 출력을 내지 않게 한다.
        seek_time = max(0., min(timestamp, (frames-1.25)/60.))
        image_path = destination/'contact_evidence.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(seek_time), '-i', str(destination/'hand.mp4'),
                        '-frames:v', '1', str(image_path)], check=True)
        with Image.open(image_path) as image:
            card = image.convert('RGB').resize((480, 270))
        caption = '%s | streak %.3fs | t %.3fs'%(name, streak[peak], timestamp)
        ImageDraw.Draw(card).rectangle((0, 245, 480, 270), fill='black')
        ImageDraw.Draw(card).text((6, 250), caption, fill='white')
        cards.append(card)
        # 최종 video에는 영상만 두고 증거 이미지·렌더 메타데이터는 process에 남긴다.
        final_videos = {}
        for view in ('hand', 'full'):
            final = video_out/(name+'_'+view+'.mp4')
            if final.exists():
                raise FileExistsError(str(final))
            (destination/(view+'.mp4')).replace(final)
            final_videos[view] = str(final.resolve())
        render_path = destination/'render.json'
        render_data = json.loads(render_path.read_text())
        render_data['final_video_paths'] = final_videos
        for item in render_data['videos']:
            view = Path(item['path']).stem
            item['path'] = final_videos[view]
        write(render_path, render_data)
        manifest['successes'].append(dict(row=row, finger=FINGERS[goal['finger']],
            physical_string=goal['physical_string'], fret=goal['fret'],
            source_note_index=goal['source_note_index'], best_contact_streak_s=goal['best_contact_streak_s'],
            evidence_time_s=timestamp, evidence_video_seek_s=seek_time,
            rendered_pre_failure_frames=frames, failure=goal['failure'],
            success_before_failure=goal['failure'] is not None,
            videos=final_videos,
            evidence_frame=str(image_path.resolve())))
        write(out/'manifest.json', manifest)
    if cards:
        columns = min(4, len(cards))
        montage = Image.new('RGB', (columns*480, ((len(cards)+columns-1)//columns)*270), 'black')
        for index, card in enumerate(cards):
            montage.paste(card, ((index % columns)*480, (index//columns)*270))
        montage.save(out/'success_montage.png')
    write(out/'manifest.json', manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Recorded replay directory')
    parser.add_argument('--out', type=Path, required=True, help='Process rendering evidence directory')
    parser.add_argument('--video-out', type=Path, required=True, help='Final MP4-only directory')
    parser.add_argument('--rows', type=int, nargs='+', help='Render only the selected recorded row IDs')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    result = render_successes(args.source.resolve(), args.out.resolve(), args.video_out.resolve(), rows_filter=args.rows)
    print(json.dumps(dict(successes=len(result['successes']), excluded=len(result['excluded'])), ensure_ascii=False))


if __name__ == '__main__':
    main()
