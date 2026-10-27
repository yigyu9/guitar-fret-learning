#!/usr/bin/env python3
"""Archive the five confirmed native cases as Korean image/video documentation."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, shutil, subprocess

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1')
ART = BASE / 'artifacts_v1'
VID = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1')
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
ANALYSIS = BASE / 'native_analysis_v3.json'
CASES = [
    ('native_hold_v1', 'hold_v1', '기본 위치 제어', 'native_hold_v1'),
    ('native_hold_v2', 'hold_v2', '높은 위치 제어 게인', 'native_hold_v2'),
    ('native_hold_v3', 'hold_v3', '낮춘 명시 게인', 'native_hold_v3'),
    ('native_hold_v4', 'hold_v4', '손목 준비 과제 포함', 'native_hold_v4'),
    ('native_pair_v1', 'pair_v1', '두 체크포인트 연결', 'native_pair_v1'),
]
CASE_DIRS = [BASE / x[0] for x in CASES]
FRAME_SPECS = [
    (BASE/'native_hold_v4/media/frames/hands/00000.png', 0, 'hold4 손 화면 · 0.00초'),
    (BASE/'native_hold_v4/media/frames/hands/00060.png', 480, 'hold4 손 화면 · 2.00초'),
    (BASE/'native_hold_v4/media/frames/hands/00150.png', 1200, 'hold4 손 화면 · 5.00초'),
    (BASE/'native_pair_v1/media/frames/hands/00000.png', 0, '연결 실행 손 화면 · 0.00초'),
    (BASE/'native_pair_v1/media/frames/hands/00060.png', 480, '연결 실행 손 화면 · 2.00초'),
    (BASE/'native_pair_v1/media/frames/hands/00073.png', 584, '연결 종료 손 화면 · 2.433초'),
    (BASE/'native_hold_v4/media/frames/whole_body/00000.png', 0, 'hold4 전신 시작 프레임'),
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def statrec(path):
    p = Path(path); st = p.stat()
    return {'sha256': sha(p), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns}

def ffprobe(path):
    cmd = ['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(path)]
    data = json.loads(subprocess.check_output(cmd, text=True))
    s = data['streams'][0]
    return {k:s[k] for k in ['width','height','avg_frame_rate','nb_read_frames','duration']}

def title_font(size): return ImageFont.truetype(str(FONT), size)

def make_panel(out, title, items):
    # items: image path, image caption
    W, H, pad, gap, title_h, caption_h = 1780, 470, 28, 18, 58, 42
    cell_w = (W - 2*pad - 2*gap)//3
    im_h = 315
    canvas = Image.new('RGB', (W,H), '#f1f3f6')
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 10), title, font=title_font(30), fill='#162334')
    for i,(src,caption) in enumerate(items):
        x = pad + i*(cell_w+gap)
        draw.rounded_rectangle((x, title_h, x+cell_w, H-18), radius=8, fill='white', outline='#c8d0da', width=2)
        draw.text((x+12,title_h+7), caption, font=title_font(21), fill='#10243a')
        img = Image.open(src).convert('RGB')
        img.thumbnail((cell_w-18, im_h), Image.Resampling.LANCZOS)
        y = title_h+caption_h + max(0,(im_h-img.height)//2)
        canvas.paste(img,(x+(cell_w-img.width)//2,y))
    canvas.save(out, format='PNG', optimize=True)

def make_crop(src, out):
    im = Image.open(src).convert('RGB')
    crop = im.crop((365, 270, 760, 535)).resize((790,530), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB',(830,640),'#f1f3f6')
    d=ImageDraw.Draw(canvas)
    d.text((20,12),'실제 native 손 카메라의 시작 프레임을 2D로 확대한 crop',font=title_font(23),fill='#162334')
    canvas.paste(crop,(20,55))
    d.text((20,590),'새 시점·부위 검출·접촉 판정을 추가하지 않은 이미지 자르기',font=title_font(18),fill='#34495e')
    canvas.save(out,format='PNG',optimize=True)

# Direct inputs include source run records, captures/frames, source videos, and font.
inputs = [ANALYSIS, FONT]
for d in CASE_DIRS:
    inputs += [d/'report.json', d/'initial_verification.json', d/'initial_values.json', d/'trace.json', d/'media/capture.json', d/'media/whole_body.mp4', d/'media/hands.mp4']
for p,_,_ in FRAME_SPECS:
    inputs.append(p)
inputs = list(dict.fromkeys(inputs))
inputs_before = {str(p):statrec(p) for p in inputs}

analysis = json.loads(ANALYSIS.read_text())
assert set(analysis['cases']) == {c[0] for c in CASES}
for dname,name,label,case_key in CASES:
    d=BASE/dname
    report=json.loads((d/'report.json').read_text())
    assert report['training_updates']==0 and report['strap_enabled'] is False
    assert int(report['physics_steps']) == int(analysis['cases'][case_key]['physics_steps'])
    assert len(json.loads((d/'media/capture.json').read_text())['frames']) == int(report['videos']['hands']['stream']['nb_read_frames'])

# Verify capture metadata links each selected frame to its native-frame hash and step.
for p,step,_ in FRAME_SPECS:
    case = next(d for d in CASE_DIRS if d in p.parents)
    cap = json.loads((case/'media/capture.json').read_text())
    entry = next(x for x in cap['frames'] if x['physics_step']==step)
    assert entry['image_sha256'][str(p)] == sha(p), (p,step)

make_panel(ART/'native_hold4_hands_t0_2_5_v1.png','손목 준비 과제 hold4 · 실제 native 손 카메라',[
    (FRAME_SPECS[0][0],'시작 · step 0 · 0.00초'),
    (FRAME_SPECS[1][0],'준비 종료 · step 480 · 2.00초'),
    (FRAME_SPECS[2][0],'5초 관찰 종료 · step 1200 · 5.00초'),
])
make_panel(ART/'native_pair_hands_t0_2_end_v1.png','두 체크포인트 연결 · 실제 native 손 카메라',[
    (FRAME_SPECS[3][0],'시작 · step 0 · 0.00초'),
    (FRAME_SPECS[4][0],'준비 종료 · step 480 · 2.00초'),
    (FRAME_SPECS[5][0],'source 종료 · step 584 · 2.433초'),
])
make_crop(FRAME_SPECS[0][0], ART/'native_hold4_hand_close_crop_v1.png')

# Byte-exact copies of all 5 cases x 2 views, preserving the source files.
VID.mkdir(parents=True,exist_ok=True)
records=[]
for dname,case_id,label,analysis_key in CASES:
    d=BASE/dname
    for view in ['whole_body','hands']:
        src=d/'media'/f'{view}.mp4'
        dest_dir=VID/case_id
        dest_dir.mkdir(parents=True,exist_ok=True)
        dest=dest_dir/f'{view}.mp4'
        src_before=statrec(src)
        shutil.copyfile(src,dest)
        src_after=statrec(src)
        copy_hash=sha(dest)
        assert src_before['sha256']==src_after['sha256']==copy_hash
        probe=ffprobe(dest)
        records.append({
            'case':case_id,'label':label,'view':view,
            'source':str(src),'source_sha256':src_before['sha256'],
            'destination':str(dest),'copy_sha256':copy_hash,'bytes':dest.stat().st_size,
            'ffprobe':probe,
        })
manifest={'videos':records}
(VID/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

# Korean index links all exact video copies.
index_lines=['# 왼손 넥 근접 초기 배치 · 영상 색인 V1','',
             '기존 native 실행에서 만든 MP4 10개를 재인코딩 없이 byte-exact 복사했습니다. hold_v2는 1.833초 안전 중단으로 짧은 부분 영상이며, 나머지 hold_v1/v3/v4는 5초 관찰, pair_v1은 2.433초의 source 종료 영상입니다. 재생 길이는 30fps 영상 프레임 기준이며 물리 경과 시간과 다를 수 있습니다. source/copy SHA-256 및 ffprobe는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/manifest_v1.json)에 기록했습니다.','']
for dname,case_id,label,_ in CASES:
    d=BASE/dname
    cdata=json.loads((d/'report.json').read_text())
    index_lines += [f'## {case_id} · {label}','']
    index_lines.append(f"물리 경과 {cdata['physics_seconds']:.6f}초, {cdata['physics_steps']} step, 완료={str(cdata['completed']).lower()}, 종료=`{cdata['stop_reason']}`.")
    if case_id=='hold_v2': index_lines.append('속도 안전 검사에서 중단된 부분 실행이며 5초 결과가 아닙니다.')
    if case_id=='pair_v1': index_lines.append('두 체크포인트 연결 뒤 첫 source 종료 조건에서 끝났으며 곡 완주가 아닙니다.')
    index_lines.append('')
    for view,title in [('whole_body','전신'),('hands','왼손·기타 넥 방향 확대')]:
        r=next(x for x in records if x['case']==case_id and x['view']==view)
        q=r['ffprobe']
        index_lines.append(f"- [{title} MP4]({r['destination']}) — {q['nb_read_frames']}프레임, {q['avg_frame_rate']}fps, 재생 {q['duration']}초")
    index_lines.append('')
(VID/'INDEX_V1.md').write_text('\n'.join(index_lines)+'\n',encoding='utf-8')

# Korean result brief: use only parent-confirmed metrics and native_analysis_v3 values.
case=analysis['cases']
README=f'''# 왼손을 기타 넥 가까이에 둔 초기 배치와 실제 실행 기록

이 자료는 왼손 33개 관절로 이루어진 초기 배치 후보 하나를 두고, native hold 네 조건과 두 체크포인트 연결 한 조건을 기록합니다. 다섯 조건은 초기 native 전체 상태가 같았고, 새 물리 실행·모델 변경·학습은 수행하지 않았습니다. strap은 꺼져 있고 기타는 자유 상태였으며 root와 하체는 고정됐습니다. 기타에 힘을 직접 가하거나 런타임 자세를 덮어쓰지 않았습니다.

## 초기 손 배치

사용자 요청은 왼손 손바닥을 기타 넥 쪽에 두되 손가락 면 방향을 구분하는 것이었습니다. `LH:palm`은 기타 기준 +X(넥 쪽), 엄지는 −Z(기타 뒤쪽), 검지·중지·약지·새끼손가락은 +Z(현 앞쪽)를 향하도록 놓았습니다. 이 표기는 초기 점과 면의 배치 방향이지 연주 가능한 그립 판정이 아닙니다.

시작 native 자세에서 선택된 source collision facet까지 계산한 signed plane gap은 아래와 같습니다.

| 시작 부위 | 선택된 면 | source facet gap |
|---|---|---:|
| 손바닥 | underside | 12.56884 mm |
| 엄지 | back | 11.14977 mm |
| 검지 | strings_front | 4.93175 mm |
| 중지 | strings_front | 7.95631 mm |
| 약지 | strings_front | 10.29301 mm |
| 새끼손가락 | strings_front | 6.81150 mm |

![hold4 시작 손과 넥의 native 이미지 crop](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/native_hold4_hand_close_crop_v1.png)

이 거리는 선택된 source facet의 평면 간격입니다. 손바닥 패드나 지지면 전체를 식별한 값이 아니며 PhysX cooked 형상의 전체 최단거리·관통 인증도 아닙니다.

## 네 가지 정지 관찰

| 실행 | 제어 변경과 실제 경과 | 손목·손 결과 | 해석 |
|---|---|---|---|
| hold_v1 | 기존 위치 제어, 5.0초 | 끝점 손바닥 오차 133.93 mm | 손이 처져 초기 근접 배치를 유지하지 못함 |
| hold_v2 | 높은 위치 제어 게인을 외부화, 1.833333초 | `L_Elbow_y` 속도 −100.095 rad/s에서 안전 검사 중단 | 부분 실행이며 5초 완료로 세지 않음 |
| hold_v3 | 낮춘 명시 게인, 5.0초 | 끝점 손바닥 오차 77.10 mm | hold_v1보다 작지만 넥 위치 유지에는 부족 |
| hold_v4 | 사람 손목 관절에 제한된 준비 과제 추가, 5.0초 | 손목 오차 끝 17.00048 mm, 최대 17.01819 mm | 이 과제의 정지 관찰만 개선. 기타 접촉/지지 성공은 아님 |

hold_v4에서 손목 task는 인간 관절 토크 계산에 쓰인 가상 힘 요청이며 최대 요청 30 N입니다. 기타에 가해진 힘이나 접촉력 측정값이 아닙니다. 종료점의 source facet 간격은 손바닥 31.53746 mm, 현 앞 손가락 약 14.45–17.49 mm, 엄지 3.36285 mm로 기록됐습니다. 왼손–기타 endpoint 접촉 표시는 1200개 표본 중 0개였습니다. 이는 기록된 표본 범위이며 모든 물리 substep의 연속 비접촉 증명은 아닙니다. 기타 바디 bounding-box 중심은 9.29564 mm 이동했고 전체 SO(3) 방향 변화는 2.834565°였습니다.

![hold4 손 카메라의 0, 2, 5초 실제 native 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/native_hold4_hands_t0_2_5_v1.png)

손 카메라 이미지는 Isaac Gym native 렌더입니다. 기타 줄은 깊이 테스트된 시각 표시이며 물리 현의 굵기나 진동을 표현하지 않습니다.

## 두 체크포인트 연결 점검

두 체크포인트를 등록해 연결한 조건은 같은 시작 상태에서 2초 준비 구간 동안 추론을 대기한 뒤 동시 추론을 시작했습니다. 26개 paired inference tick 뒤 총 물리 2.433333초, 584 step에서 첫 source 종료 조건으로 멈췄습니다. 분석은 종료를 `wrong_crossing_count_termination`으로 기록하며, 종료 시 손목·finger-back 안전 표식은 false, Fret `goal_finished` false, 실제 press 및 target hit false였습니다. 기록된 joint-resolved event는 2건, 현 crossing counter는 4건입니다. 따라서 이 실행은 음악 완주나 음악 품질 평가가 아닙니다.

![체크포인트 연결 실행의 시작·준비 종료·종료 native 손 화면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/native_pair_hands_t0_2_end_v1.png)

종료 시 기타 바디 bounding-box 중심은 33.0647 mm, 전체 SO(3) 방향은 11.2172° 변했습니다. 손목 위치 과제 오차는 88.67049 mm였습니다. 이 연결 시험에서 hold4의 정지 결과를 재현하지 못했습니다.

## 원본 영상과 세부 기록

각 조건의 전신 및 왼손·넥 방향 카메라 영상은 아래 두 파일에서 확인할 수 있습니다. 모든 MP4는 원본 byte 그대로 복사했으며 재인코딩하지 않았습니다.

![hold4 전신 native 영상 · 5초 정지 관찰](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v4/whole_body.mp4)

![체크포인트 연결 전신 native 영상 · source 종료까지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/pair_v1/whole_body.mp4)

- [10개 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/INDEX_V1.md)
- [원본·복사본 SHA-256 및 ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/manifest_v1.json)
- [기준 분석 `native_analysis_v3.json`]({BASE}/native_analysis_v3.json)
- [연결 실행 보고서]({BASE}/native_pair_v1/report.json)

**해석 범위:** 다섯 조건은 짧은 초기배치·제어 진단입니다. hold4의 한 번의 5초 정지 실행을 반복 재현성, 연주 중 손 위치 유지, 힘 분담, 해부학적 패드 접촉 또는 cooked 형상 안전의 인증으로 해석하지 않습니다. 다음 후보는 기타 기준 왼손 READY 상태를 준비 구간에 만들되, 손목·손가락 안전 제한을 유지하는 것입니다. 그 후속 시험은 이 자료에 포함되지 않습니다.
'''
(ART/'README_V1.md').write_text(README,encoding='utf-8')

# Verify every input is stable after rendering and exact copies.
inputs_after={str(p):statrec(p) for p in inputs}
assert inputs_before==inputs_after, 'an input changed during archive build'
# Preserve the before/after proof for all source and helper inputs.
output_files=sorted([p for p in ART.iterdir() if p.is_file() and p.name!='provenance_v1.json']+[VID/'manifest_v1.json',VID/'INDEX_V1.md'])
prov={
 'task':'확정된 native 자료의 그림·한국어 설명·원본 영상 byte-exact 보관',
 'physics_runs':0,'training_updates':0,'video_reencodes':0,
 'video_copy_count':len(records),'image_derivation':'선택된 실제 native 캡처 프레임 조합 및 hold4 시작 손 화면의 2D crop만',
 'inputs_before_after':{str(p):{'before':inputs_before[str(p)],'after':inputs_after[str(p)],'unchanged':inputs_before[str(p)]==inputs_after[str(p)]} for p in inputs},
 'producer':{'path':str(Path(__file__)),'sha256':sha(Path(__file__)),'bytes':Path(__file__).stat().st_size},
 'font':{'path':str(FONT),'sha256':sha(FONT),'bytes':FONT.stat().st_size},
 'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in output_files},
 'video_manifest_rows':records,
}
(ART/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'images':[str(p) for p in ART.glob('*.png')], 'video_count':len(records),'outputs':prov['outputs'],'producer_sha256':sha(Path(__file__)),'provenance_sha256':sha(ART/'provenance_v1.json')},ensure_ascii=False))
