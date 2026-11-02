"""원본 프레임과 동기화된 실제 기타 자세로 프렛 셀을 화면에 투영한다.

GPU 재실행·학습 없이 원본 영상을 CPU에서 주석 처리한다. 표시는 깊이 가림을
계산한 물리 재렌더가 아닌 보조 겹침 표시이며 실제 접촉 판정을 바꾸지 않는다.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw,ImageFont

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').exists())
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'docs/2026-11-02/압현실험/동영상/13_중지3번줄6에서7프렛_800회_최고모델_seed7_손확대.mp4'
RECORD=ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/analysis/review_20261101/render_seed7_u800'
OUTPUT=SOURCE.with_name(SOURCE.stem+'_프렛영역표시.mp4')
MANIFEST=ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json'
RENDERER=ROOT/'guitar_learning/tool/demonstration/render_finger_skill.py'
FONT='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def make():
    metadata=json.loads((RECORD/'capture_metadata.json').read_text())
    episode=json.loads((RECORD/'episode_env0000.json').read_text())
    pins=json.loads((RECORD/'inputs_before.json').read_text())
    for path in (MANIFEST,RENDERER):
        if sha(path)!=pins[str(path)]:raise ValueError('원본 렌더 당시 자산·카메라 코드 SHA 불일치')
    if sha(SOURCE)!=sha(RECORD/'hand.mp4'):raise ValueError('사용자 영상과 기록 원본의 SHA 불일치')
    poses=np.load(RECORD/'poses_env0000.npz',allow_pickle=False)
    manifest=json.loads(MANIFEST.read_text());markers=dict(zip(manifest['logical_body_names'],manifest['logical_position_root_m']))
    camera=np.array([-.65,.22,.84]);target=np.array([-.27,-.09,.66]);forward=target-camera;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    width,height=metadata['width'],metadata['height'];focal=width/(2*np.tan(np.deg2rad(55)/2))
    def project(points):
        delta=points-camera;depth=delta@forward
        if (depth<=0).any():raise ValueError('카메라 뒤쪽 투영점')
        return np.column_stack((width/2+focal*(delta@right)/depth,height/2-focal*(delta@up)/depth))
    nut=np.array(markers['G:nut']);frets=np.array([nut]+[markers[f'G:fret{i}'] for i in range(1,23)])
    neck_x=(-.023,.023);plane_z=.0093
    schedule=episode['transition']['schedule'];names=metadata['body_names'];guitar=names.index('guitar/guitar')
    fps=metadata['video_fps'];count=metadata['frames']
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(SOURCE)]))['streams'][0]
    if int(probe['nb_frames'])!=count:raise ValueError('원본 프레임 수와 동기화 기록 불일치')
    reader=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-i',str(SOURCE),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    inputs=[SOURCE,RECORD/'poses_env0000.npz',RECORD/'capture_metadata.json',RECORD/'episode_env0000.json',MANIFEST,RENDERER,Path(__file__).resolve()]
    before={str(p):sha(p) for p in inputs}
    command=['ffmpeg','-v','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','-','-an','-c:v','libx264','-threads','2','-crf','18','-preset','fast','-pix_fmt','yuv420p',str(OUTPUT)]
    writer=subprocess.Popen(command,stdin=subprocess.PIPE);records=[]
    small=ImageFont.truetype(FONT,22);medium=ImageFont.truetype(FONT,26);large=ImageFont.truetype(FONT,30)
    try:
        for frame_i in range(count):
            pixels=reader.stdout.read(width*height*3)
            if len(pixels)!=width*height*3:raise ValueError('원본 프레임 누락')
            original=Image.frombytes('RGB',(width,height),pixels)
            # 원본은 매 두 번째60Hz 제어 끝점만 30fps로 저장하며 t=0 프레임이 없다.
            row=2*(frame_i+1)-1;t=float(poses['time_s'][row]);assert abs(t-metadata['frame_times_s'][frame_i])<1e-9
            body=poses['body_state'][row,guitar];position=body[:3];rotation=Rotation.from_quat(body[3:7])
            def screen(local):return project(position+rotation.apply(np.array(local)))
            polygons={}
            for fret in range(4,10):
                y0,y1=frets[fret-1,1],frets[fret,1]
                polygons[fret]=screen([[neck_x[0],y0,plane_z],[neck_x[1],y0,plane_z],[neck_x[1],y1,plane_z],[neck_x[0],y1,plane_z]])
            colors={6:(45,210,238),7:(255,198,45)}
            overlay=original.copy();paint=ImageDraw.Draw(overlay)
            for fret,color in colors.items():paint.polygon([tuple(p) for p in polygons[fret]],fill=color)
            image=Image.blend(original,overlay,.22);draw=ImageDraw.Draw(image)
            for fret,poly in polygons.items():draw.line([tuple(p) for p in poly]+[tuple(poly[0])],fill=colors.get(fret,(205,205,205)),width=3 if fret in colors else 1)
            # 단일 목표의 3번 줄 구간도 셀과 같은 좌표계에서 표시한다.
            for fret in (6,7):
                start=np.array(markers['G:string3']);end=np.array(markers['G:string3_end'])
                local=[]
                for y in (frets[fret-1,1],frets[fret,1]):
                    point=start+(y-start[1])/(end[1]-start[1])*(end-start)
                    point[2]=plane_z+.0005;local.append(point)
                points=screen(local)
                draw.line([tuple(p) for p in points],fill=colors[fret],width=5)
            draw=ImageDraw.Draw(image)
            for fret,poly in polygons.items():
                # 숫자는 넥 위쪽 가장자리에서 밖으로 빼서 손가락과 겹치지 않게 배치한다.
                edge=(poly[0]+poly[3])/2;other=(poly[1]+poly[2])/2
                if edge[1]>other[1]:edge,other=other,edge
                outward=edge-other;outward/=np.linalg.norm(outward);label=edge+outward*32
                text=f'{fret}F';box=draw.textbbox((0,0),text,font=medium);w=box[2]-box[0]
                x,y=int(label[0]-w/2),int(label[1]-16)
                draw.rounded_rectangle((x-6,y-4,x+w+6,y+31),radius=5,fill=(25,25,30));draw.text((x,y),text,font=medium,fill=colors.get(fret,(235,235,235)))
            if t<3.:phase='준비: 3번 줄 · 6프렛'
            elif t<4.5:phase='목표 A: 3번 줄 · 6프렛 유지'
            elif t<5.25:phase='전환 구간: 6 → 7프렛 (0.75초)'
            elif t<6.75:phase='목표 B: 3번 줄 · 7프렛 유지'
            else:phase='목표 종료'
            draw.rectangle((0,0,width,87),fill=(18,21,28));draw.text((20,10),phase,font=large,fill=(255,255,255));draw.text((20,51),f'실험 시각 {t:.2f}초   |   중지 · 800회 모델 · 원본과 동일한 움직임',font=small,fill=(220,225,230))
            draw.rectangle((0,height-43,width,height),fill=(18,21,28));draw.text((20,height-34),'하늘색: 6프렛     노랑: 7프렛     회색: 주변 프렛   |   영역은 손에 가려져도 보이는 보조 표시',font=small,fill=(235,235,235))
            result=np.asarray(image);writer.stdin.write(result.tobytes())
            if frame_i in (104,142,172):image.save(HERE/f'preview_{frame_i:03}.png')
            records.append(dict(frame=frame_i,pose_row=row,time_s=t,fret6_px=polygons[6].tolist(),fret7_px=polygons[7].tolist()))
        writer.stdin.close();code=writer.wait()
        if code:raise RuntimeError('ffmpeg 인코딩 실패')
    finally:
        reader.stdout.close()
        if reader.poll() is None:reader.terminate()
        reader.wait()
        if writer.poll() is None:writer.terminate();writer.wait()
    for p,v in before.items():
        if sha(Path(p))!=v:raise ValueError('제작 중 입력 변경')
    (HERE/'overlay_manifest.json').write_text(json.dumps(dict(schema='fret6_7_video_overlay.v1',source_sha256=before,output=str(OUTPUT),output_sha256=sha(OUTPUT),frames=count,fps=fps,camera_position=camera.tolist(),camera_target=target.tolist(),horizontal_fov_degrees=55,frame_mapping='pose row=2*(video frame+1)-1; same physical endpoint as original capture',scope='CPU annotation of unchanged original video; no physics rerun; overlays ignore occlusion',frame_projection=records),ensure_ascii=False,indent=2)+'\n')
    print(OUTPUT)


if __name__=='__main__':make()
