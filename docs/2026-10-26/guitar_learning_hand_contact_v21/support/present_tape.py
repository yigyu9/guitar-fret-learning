"""Label two native action replays; do not change or synthesize physics pixels."""
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

PHASE = Path(__file__).resolve().parents[1]


def main():
    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    header = Image.new('RGB', (2560, 110), '#172026')
    draw = ImageDraw.Draw(header)
    title = ImageFont.truetype(font_path, 37)
    small = ImageFont.truetype(font_path, 24)
    draw.text((30, 10), '원래 충돌 필터', font=title, fill='white')
    draw.text((1310, 10), '손가락 사이 충돌 적용', font=title, fill='white')
    draw.text((30, 66), '같은 A500 행동 기록 재생 · 새 학습/정책 평가가 아님 · 실제 GPU PhysX 카메라',
              font=small, fill='#c6d4dd')
    header_path = PHASE/'support'/'tape_header.png'
    header.save(header_path)
    out = PHASE/'action_tape_collision_comparison.mp4'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
        '-i', str(PHASE/'action_tape_source_filters'/'native_oblique.mp4'),
        '-i', str(PHASE/'action_tape_selective_filters'/'native_oblique.mp4'),
        '-loop', '1', '-framerate', '30', '-i', str(header_path),
        '-filter_complex', '[0:v][1:v]hstack=inputs=2:shortest=1[views];[2:v][views]vstack=inputs=2:shortest=1[v]',
        '-map', '[v]', '-shortest', '-r', '30', '-an', '-c:v', 'libx264', '-threads', '2',
        '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', str(out)], check=True)
    result = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,nb_read_frames,duration',
        '-of', 'json', str(out)], check=True, capture_output=True, text=True)
    (PHASE/'support'/'tape_video_validation.json').write_text(result.stdout)
    data = json.loads(result.stdout)['streams'][0]
    if data['nb_read_frames'] != '984' or data['r_frame_rate'] != '30/1':
        raise ValueError('Expected984native frames per replay at30fps')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-sseof', '-0.1',
        '-i', str(out), '-frames:v', '1', str(PHASE/'action_tape_collision_final.png')], check=True)


if __name__ == '__main__':
    main()
