#!/usr/bin/env python3
"""Compose existing native frames and exact-copy the completed v2 MP4s."""
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3')
ART = ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1'
VID = ROOT/'docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1'
P = ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
OLD = ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side/media'
NEW = P/'native_v2/front160mm/media'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def snap(path: Path) -> dict:
    st=path.stat()
    return {'sha256':sha(path),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
def font(size: int):
    return ImageFont.truetype(str(FONT), size=size)
def draw_center(draw, x, y, text, f, fill):
    box=draw.textbbox((0,0), text, font=f)
    draw.text((x-(box[2]-box[0])/2, y), text, font=f, fill=fill)
def place_fit(canvas: Image.Image, path: Path, xywh):
    x,y,w,h=xywh
    im=Image.open(path).convert('RGB')
    im.thumbnail((w,h),Image.Resampling.LANCZOS)
    px=x+(w-im.width)//2; py=y+(h-im.height)//2
    canvas.paste(im,(px,py))
    return (px,py,im.width,im.height)

def main():
    ART.mkdir(parents=True,exist_ok=True); VID.mkdir(parents=True,exist_ok=True)
    outputs=[ART/'initial_pose_pair.png',ART/'native_v2_timeline_0_2_5s.png',ART/'README_V1.md',
             ART/'provenance_v1.json',VID/'front160mm_whole_body.mp4',VID/'front160mm_hands.mp4',
             VID/'manifest_v1.json',VID/'README.md']
    if any(p.exists() for p in outputs):
        raise FileExistsError('refusing to overwrite an existing phase artifact')
    sources=[
        ROOT/'stability_adapter_2/AGENTS.md',ROOT/'stability_adapter_2/README.md',ROOT/'stability_adapter_2/EXPERIMENT_WORKFLOW.md',
        P/'analysis_v1/verification.json',P/'analysis_v1/posture_shape_trace.json',
        P/'native_v1/front160mm/failure.json',P/'native_v1/front160mm/attempt.json',
        P/'native_v2/front160mm/report.json',P/'native_v2/front160mm/attempt.json',
        P/'native_v2/front160mm/initial_values.json',P/'native_v2/front160mm/media/capture.json',
        P/'native_v2/front160mm/media/videos.json',P/'native_v2/front160mm/media/effort_configuration.json',
        P/'reference.jpeg',OLD/'initial_native.png',NEW/'initial_native.png',
        NEW/'frames/whole_body/00000.png',NEW/'frames/whole_body/00060.png',NEW/'frames/whole_body/00150.png',
        NEW/'whole_body.mp4',NEW/'hands.mp4',FONT,
    ]
    before={str(p):snap(p) for p in sources}
    helper_before=snap(Path(__file__).resolve())
    verification=json.loads((P/'analysis_v1/verification.json').read_text())
    case=verification['cases']['front160mm']
    if not verification.get('passed'):
        raise RuntimeError('authoritative verification is not passed')
    videos=json.loads((NEW/'videos.json').read_text())
    capture=json.loads((NEW/'capture.json').read_text())
    assert [(x['physics_step'],x['time_s']) for x in capture['frames'] if x['physics_step'] in (0,480,1200)] == [(0,0.0),(480,2.0),(1200,5.0)]

    # Side-by-side actual native initial images; each retains its own camera.
    old_img=OLD/'initial_native.png'; new_img=NEW/'initial_native.png'
    im1=Image.open(old_img); im2=Image.open(new_img)
    if im1.size != im2.size:
        raise RuntimeError(f'initial frame sizes differ: {im1.size} vs {im2.size}')
    iw,ih=im1.size
    margin=32; header=88; footer=154
    canvas=Image.new('RGB',(margin*3+iw*2,margin*2+header+ih+footer),(247,249,252))
    d=ImageDraw.Draw(canvas)
    draw_center(d,canvas.width//2,18,'실제 native 초기 장면 비교',font(38),(24,38,58))
    draw_center(d,margin+iw//2,header-36,'이전 native 11 · 교차 팔 자세',font(27),(34,49,67))
    draw_center(d,margin*2+iw+iw//2,header-36,'새 native 2 · front160mm · 전완 지지 자세',font(27),(34,49,67))
    y=margin+header
    canvas.paste(im1.convert('RGB'),(margin,y)); canvas.paste(im2.convert('RGB'),(margin*2+iw,y))
    fy=y+ih+16
    d.rounded_rectangle((margin,fy,canvas.width-margin,fy+footer-18),radius=14,fill=(229,235,243))
    d.text((margin+20,fy+13),'각각의 실행이 저장한 실제 0초 native 캡처입니다. 카메라/초기 자세가 다른 정성 참고 비교이며 정밀한 3D 복원이나 정량 픽셀 비교가 아닙니다.',font=font(22),fill=(31,44,62))
    d.text((margin+20,fy+56),'사용자 사진은 참고용이며 정확한 3D 재구성이 아닙니다. 화면상 겹침은 실제 PhysX 관통·여유를 보증하지 않습니다.',font=font(22),fill=(31,44,62))
    pair_path=ART/'initial_pose_pair.png'; canvas.save(pair_path,optimize=True)

    # Three actual whole_body frames saved by the native renderer.
    frame_paths=[NEW/'frames/whole_body/00000.png',NEW/'frames/whole_body/00060.png',NEW/'frames/whole_body/00150.png']
    frames=[Image.open(p).convert('RGB') for p in frame_paths]
    if len({im.size for im in frames}) != 1:
        raise RuntimeError('timeline source frames have inconsistent dimensions')
    fw,fh=frames[0].size
    scale_w=640; scale_h=round(fh*scale_w/fw)
    gap=24; outer=28; th=72; foot=118
    w=outer*2+scale_w*3+gap*2; h=outer+th+scale_h+foot+outer
    panel=Image.new('RGB',(w,h),(247,249,252)); pd=ImageDraw.Draw(panel)
    draw_center(pd,w//2,14,'native 2 · 실제 whole_body 프레임',font(34),(24,38,58))
    for i,(img,label) in enumerate(zip(frames,['0초','2초','5초'])):
        x=outer+i*(scale_w+gap)
        draw_center(pd,x+scale_w//2,th-30,label,font(25),(34,49,67))
        fitted=img.resize((scale_w,scale_h),Image.Resampling.LANCZOS)
        panel.paste(fitted,(x,outer+th))
    fy=outer+th+scale_h+14
    pd.rounded_rectangle((outer,fy,w-outer,fy+foot-10),radius=12,fill=(229,235,243))
    pd.text((outer+16,fy+12),'실제 native 캡처 0·2·5초. 물리 구간은 5.000초이고 MP4 재생 길이는 5.033333초입니다.',font=font(20),fill=(31,44,62))
    pd.text((outer+16,fy+50),'전완 접촉이 관측됐지만 기타는 크게 이동·회전했습니다. 시각적 겹침은 PhysX 관통 검증이 아닙니다.',font=font(20),fill=(31,44,62))
    timeline_path=ART/'native_v2_timeline_0_2_5s.png'; panel.save(timeline_path,optimize=True)

    manifest_items=[]
    labels={'whole_body':'전신 whole_body','hands':'손 hands'}
    for view in ('whole_body','hands'):
        entry=videos[view]
        src=Path(entry['path'])
        dst=VID/f'front160mm_{view}.mp4'
        src_before=snap(src)
        shutil.copyfile(src,dst)
        src_after=snap(src); copy=snap(dst)
        if src_before != src_after or src_before['sha256'] != copy['sha256'] or src_before['bytes'] != copy['bytes']:
            raise RuntimeError(f'exact video copy or source immutability check failed: {src}')
        stream=entry['stream']
        manifest_items.append({'source':str(src),'source_sha256_before':src_before['sha256'],
            'source_sha256_after':src_after['sha256'],'destination':str(dst),'copy_sha256':copy['sha256'],
            'bytes':copy['bytes'],'label':'native 2 · front160mm','view':view,'fps':stream['avg_frame_rate'],
            'duration_seconds':stream['duration'],'frames':int(stream['nb_read_frames']),
            'physics_seconds':5.0,'mp4_copy':'byte-exact; no re-encoding'})
    (VID/'manifest_v1.json').write_text(json.dumps({'schema_version':1,'videos':manifest_items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    # Concise Korean documentation; roots retain top-level README ownership.
    old_native='/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side'
    new_native=str(P/'native_v2/front160mm')
    readme=f'''# Natural right-arm · native 2 front160mm\n\n이 정리는 전완 지지 형태의 실제 native 캡처와 5초 결과를 보존합니다. 앞선 native 11의 교차 팔 자세는 5초 정지 유지 후보였지만 연주 자세로는 자연스럽지 않아 채택하지 않았습니다. 사용자 사진은 정성 참고용이며 정확한 3D 복원 기준이 아닙니다.\n\n![이전 native 11과 새 native 2의 실제 초기 렌더 비교]({ART/'initial_pose_pair.png'})\n\n![새 native 2 실제 0초·2초·5초 whole_body 캡처]({timeline_path})\n\n## 조건과 관측\n\n새 native 2 `front160mm`는 root와 하체를 고정하고, 스트랩을 끈 상태에서 왼팔·왼손을 기타에서 떼고 왼손 grip 없이 기타를 자유롭게 두었습니다. 오른팔 초기 자세의 shoulder scalar q를 조정하고 손목 목표 조정 제한은 ±0.35 rad로 두었으며, 팔은 전완을 이용하는 지지 형태입니다. 기타를 고정하거나 손에 강제 부착하지 않았고 음악 actor·policy 호출은 0입니다.\n\n| 항목 | 결과 |\n|---|---:|\n| 물리 실행 | 1,200 physics step / 300 control / 5.000초 |\n| 영상 | 151 frame / 30 fps / 5.033333초 재생 |\n| 초기 대비 기타 body bounding-box 중심 이동 | {case['final_body_bbox_centre_change_mm']:.3f} mm |\n| 초기 대비 actor-root 위치 이동 | {case['final_root_position_change_mm']:.3f} mm |\n| 초기 대비 전체 SO(3) 회전 | {case['final_rotation_change_deg']:.3f}° |\n| 2→5초 body 중심 이동 / 회전 변화 | {case['body_centre_2_to_5s_mm']:.3f} mm / {case['rotation_2_to_5s_deg']:.3f}° |\n| 오른 전완 접촉 표본 | {case['endpoints']['right_forearm_presence']}/1200 (240 Hz physics endpoint) |\n| 오른상완 접촉 표본 | {case['endpoints']['right_upper_arm_presence']}/1200 |\n| 왼팔·왼손 / Head 접촉 | {case['endpoints']['left_arm_hand_presence']}/1200 / {case['endpoints']['head_presence']}/1200 |\n| 최소 elbow-outside-shoulder 형상값 | {case['min_elbow_outside_shoulder_m']*1000:.3f} mm |\n| shoulder scalar q 최대 편차 | {case['max_right_scalar_q_deviation_deg']['R_Shoulder_x']:.2f}° (`R_Shoulder_x` DOF scalar) |\n\n팔 형상은 이전 교차 팔 자세보다 정성적으로 달라졌지만 기타는 5초 동안 크게 이동하고 회전했습니다. 따라서 이 결과는 자연스러운 팔 모양 후보의 시각·초기 정지 진단이지 기타 유지 성공이 아닙니다. `R_Shoulder_x`의 suffix를 world 회전축으로 해석하지 않습니다. elbow-outside 값은 기록된 형상 field이며 해부학적 적합성 판정이 아닙니다. 접촉 존재 횟수는 접촉력·모멘트 기여를 측정한 값이 아니며, 영상에서 보이는 겹침만으로 실제 PhysX 관통을 보증할 수 없습니다.\n\n새 phase native 1은 point-Jacobian velocity mismatch 검증으로 약0.125초에 중단되어 완전 5초 시험이 아닙니다. native 3은 12 mm 상향 human-target 비교가 진행 중이며 이 문서에서는 결과나 선택을 주장하지 않습니다.\n\n## 실제 영상과 기록\n\n![새 native 2 전신 영상]({VID/'front160mm_whole_body.mp4'})\n\n![새 native 2 손 영상]({VID/'front160mm_hands.mp4'})\n\n- [전신 영상 manifest·source/copy SHA]({VID/'manifest_v1.json'})\n- [원래 user reference.jpeg]({P/'reference.jpeg'})\n- [analysis verification]({P/'analysis_v1/verification.json'}) · [posture/shape trace]({P/'analysis_v1/posture_shape_trace.json'})\n- [native 2 report]({new_native}/report.json) · [initial values]({new_native}/initial_values.json) · [capture metadata]({new_native}/media/capture.json)\n- [입력·출력 SHA provenance]({ART/'provenance_v1.json'})\n\n이 파일과 그림은 완료된 캡처·검증 자료를 정리한 것입니다. 새 native 실행, 물리 변경, 재인코딩은 없었습니다.\n'''
    (ART/'README_V1.md').write_text(readme,encoding='utf-8')
    video_readme=f'''# Native 2 front160mm 영상\n\n아래 두 MP4는 [원본 native capture]({new_native}/media/capture.json)에서 보존한 파일을 byte-exact 복사했습니다. 재인코딩은 하지 않았습니다. 각각 151 frame, 30 fps, 5.033333초이며 물리 실행은 5.000초입니다.\n\n![front160mm 전신 카메라 영상]({VID/'front160mm_whole_body.mp4'})\n\n![front160mm 손 카메라 영상]({VID/'front160mm_hands.mp4'})\n\n[원본/복사 SHA manifest]({VID/'manifest_v1.json'}) · [phase README]({ART/'README_V1.md'})\n'''
    (VID/'README.md').write_text(video_readme,encoding='utf-8')

    after={str(p):snap(p) for p in sources}
    helper_after=snap(Path(__file__).resolve())
    if before != after:
        raise RuntimeError('one or more source inputs changed during artifact creation')
    if helper_before != helper_after:
        raise RuntimeError('producer changed during its own run')
    copy_records=[]
    for item in manifest_items:
        s=Path(item['source']); d=Path(item['destination'])
        copy_records.append({'source':str(s),'source_sha256_before':item['source_sha256_before'],
            'source_sha256_after':item['source_sha256_after'],'destination':str(d),
            'copy_sha256':item['copy_sha256'],'bytes':item['bytes']})
    outputs=[pair_path,timeline_path,ART/'README_V1.md',VID/'README.md',VID/'manifest_v1.json',*map(Path,[x['destination'] for x in copy_records])]
    prov={'schema_version':1,'scope':'확정 native 2 결과의 그림·문서·영상 exact-copy; native/physics/training 0회',
          'inputs_before':before,'inputs_after':after,'producer_sha256_before':helper_before['sha256'],
          'producer_sha256_after':helper_after['sha256'],'source_immutability_verified':before==after,
          'video_exact_copy_records':copy_records,
          'video_copy_count':len(copy_records),'video_reencoding_count':0,
          'outputs_sha256_bytes':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs],
          'render_notes':{'initial_pair':'two actual saved initial_native.png images side by side; independent camera projections',
                          'timeline_frames':[{'path':str(p),'time_s':t} for p,t in zip(frame_paths,[0,2,5])],
                          'visual_overlap_is_physx_clearance_proof':False},
          'self_hash_note':'이 provenance 파일은 자기 자신의 SHA를 포함하지 않으며 root 보존 감사에서 별도 해시한다.'}
    (ART/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'outputs':len(outputs),'video_count':len(copy_records),'video_bytes':sum(x['bytes'] for x in copy_records),
                      'producer_sha256':helper_after['sha256'],'provenance_sha256':sha(ART/'provenance_v1.json')},ensure_ascii=False))

if __name__=='__main__':
    main()
