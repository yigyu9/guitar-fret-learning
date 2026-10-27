"""Extract existing video frames; no simulation or image synthesis."""
import hashlib
import io
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

PHASE = Path(__file__).resolve().parents[1]
VIDEO = PHASE.parent/'guitar_learning_v20_A500/video_hand/final_left_hand_60fps.mp4'
FONT = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
CASES = [
    (90, '초기 대기 기회', '검지·중지·약지·소지 모두 대기 보상 허용'),
    (425, '중지·약지 중심선이 가장 가까운 표본', '중지·약지 대기 보상 꺼짐 / 소지만 허용'),
    (1398, '소지의 마지막 긴 대기 시작', '약지·소지 허용 / 검지·중지는 꺼짐'),
    (1968, '곡 끝: 네 손가락 모두 대기 허용', 'B 자세 진입은 네 손가락 모두 없음'),
]


def font(size):
    return ImageFont.truetype(FONT, size)


def main():
    width, cell_h = 800, 555
    canvas = Image.new('RGB', (width*2, cell_h*2+112), '#eff3f8')
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 15), '원영상 시점별 손 모양과 대기 보상 허용 여부', fill='#142638', font=font(34))
    draw.text((24, 63), '시간은 영상 자막의 물리 시계 기준 · 대기 허용과 B 자세 달성은 서로 다릅니다', fill='#42576a', font=font(22))
    manifest = []
    for slot, (clock_frame, title, subtitle) in enumerate(CASES):
        # Original video emits capture rows 1..end, omitting the t0 row.
        video_frame = clock_frame-1
        data = subprocess.check_output(['ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-i', str(VIDEO), '-vf', 'select=eq(n\\,%d)' % video_frame,
            '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'])
        frame = Image.open(io.BytesIO(data)).convert('RGB').resize((width, 450))
        x, y = (slot % 2)*width, 112+(slot//2)*cell_h
        canvas.paste(frame, (x, y))
        draw.text((x+16, y+462), '%.3f초 | %s' % (clock_frame/60., title), fill='#142638', font=font(24))
        draw.text((x+16, y+503), subtitle, fill='#42576a', font=font(20))
        manifest.append(dict(physical_clock_s=clock_frame/60., pose_row=clock_frame,
            video_frame=video_frame, video_pts_s=video_frame/60., title=title, subtitle=subtitle))
    canvas.save(PHASE/'original_video_keyframes.png')
    (PHASE/'support/keyframes_manifest.json').write_text(json.dumps(dict(
        video=str(VIDEO), sha256=hashlib.sha256(VIDEO.read_bytes()).hexdigest(),
        mapping='video frame n corresponds to physical clock (n+1)/60 seconds',
        frames=manifest), ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
