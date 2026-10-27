#!/usr/bin/env python3
"""Render sealed initial-pose bank values and native frame panels only."""
from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFont

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-12')
D = BASE / 'stability_adapter_2/results/initial_pose_noise_v1'
ART = D / 'artifacts_v1'
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
FONT_SHA = '48a28e97b34fc8e5b157657633670cd1b7de126cfc414da65ce9c3d5bc8be733'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

if sha(FONT_PATH) != FONT_SHA:
    raise RuntimeError('NanumGothic SHA does not match pin')
analysis = json.loads((D / 'analysis_v1.json').read_text())
font = ImageFont.truetype(str(FONT_PATH), 21)
small = ImageFont.truetype(str(FONT_PATH), 19)
title = ImageFont.truetype(str(FONT_PATH), 29)

# Bank values plus reference and the first explicit discrete-noise sample.
W, pad = 2360, 36
head_h, row_h = 60, 58
table_h = head_h + row_h * (len(analysis['rows']) + 1) + 80
ref_h = 42 + 620
img1 = Image.new('RGB', (W, pad * 2 + table_h + ref_h), 'white')
d = ImageDraw.Draw(img1)
d.text((pad, pad), '초기 pose noise: 검증된 5개 discrete bank와 native 시작 프레임', font=title, fill='#111111')
d.text((pad, pad + 45), 'translation은 world mm, rotation은 world rotvec 각 성분 deg(Euler 아님); 연속 uniform 분포가 아님', font=small, fill='#333333')
y0 = pad + 82
cols = [pad, pad+70, pad+470, pad+900, pad+1220, pad+1510, pad+1850]
headers = ['index','Δposition W (mm)','rotation-vector W (deg)','SO(3) jitter (deg)','max arm Δq (deg)','max native palm error (mm)']
for x, label in zip(cols, headers): d.text((x, y0), label, font=small, fill='#111111')
d.line((pad, y0+34, W-pad, y0+34), fill='#555555', width=2)
for i, r in enumerate(analysis['rows']):
    y = y0 + 43 + i*row_h
    t = ', '.join(f'{v:.3f}' for v in r['translation_W_mm'])
    rot = ', '.join(f'{v:+.3f}' for v in r['world_rotvec_component_deg'])
    vals = [str(r['bank_index']), t, rot, f"{r['SO3_jitter_magnitude_deg']:.4f}", f"{r['max_arm_q_change_deg']:.4f}", f"{r['max_native_palm_position_error_mm']:.9f}"]
    for x, value in zip(cols, vals): d.text((x, y), value, font=small, fill='#111111')
    if r['source_clear'] and r['fixed_body_head_finger_q_exact']:
        d.text((W-pad-170, y), 'source clear · fixed q exact', font=ImageFont.truetype(str(FONT_PATH), 14), fill='#315c37')
note_y = y0 + 43 + len(analysis['rows'])*row_h + 10
d.text((pad, note_y), 'proposal 32개 중 27개는 absolute rotation envelope에서 reject. source hull 검사이며 native cooked clearance 인증은 아님.', font=small, fill='#333333')
d.text((pad, note_y+31), 'eval_noise_1은 bank index 1 / trial 17을 고정 선택. 학습 reset은 검증 bank에서 discrete with-replacement로 선택.', font=small, fill='#333333')

before = BASE/'stability_adapter_2/results/parallel_collection_v1/long_v1/evaluations/cutoff_000320/native/episode_0001/media/frames/whole_body/00000.png'
noise_media = D/'eval_noise_1_v1/native/episode_0001/media'
cap = json.loads((noise_media/'capture.json').read_text())
noisy = noise_media/'frames/whole_body/00000.png'
declared = cap['frames'][0]['image_sha256'][str(noisy)]
if sha(noisy) != declared: raise RuntimeError('eval 1 frame zero SHA mismatch')
label_y = note_y + 78
d.text((pad, label_y), '기준과 noisy reset의 실제 Isaac Gym native 전신 frame 0 비교 (CP320 원본은 noise 적용 전 reference)', font=font, fill='#111111')
box_y = label_y + 42
for col, (label, source) in enumerate([('CP320 원본 physical 초기 frame 0', before), ('새 CP smoke + bank index 1, frame 0', noisy)]):
    x = pad + col*(W//2)
    d.text((x, box_y), label, font=small, fill='#222222')
    im = Image.open(source).convert('RGB')
    im.thumbnail((W//2-pad, 560), Image.Resampling.LANCZOS)
    img1.paste(im, (x, box_y+35))
img1.save(ART/'initial_noise_bank_and_native_reference_v1.png', optimize=True)

# Eval 1 and eval 4 whole-body and hands at capture-verified times 0, 5 s, final.
evals = [('noise eval 1 · 고정 index 1', 'eval_noise_1_v1'), ('noise eval 4 · 고정 index 4', 'eval_noise_4_v1')]
times = [('0초', 0, '00000'), ('5초', 150, '00150'), ('마지막 16.366667초', 491, '00491')]
views = [('전신', 'whole_body'), ('손', 'hands')]
pw, ph, lh, margin = 720, 405, 46, 24
img2 = Image.new('RGB', (margin*2+pw*3, margin*2+(ph+lh)*4), 'white')
d2 = ImageDraw.Draw(img2)
for vr, (vlabel, view) in enumerate(views):
    for er, (elabel, ev) in enumerate(evals):
        media = D/ev/'native/episode_0001/media'
        capture = json.loads((media/'capture.json').read_text())
        for col, (tlabel, idx, frame_id) in enumerate(times):
            if abs(capture['frames'][idx]['time_s'] - [0,5,16.366666666666667][col]) > 1e-9:
                raise RuntimeError(f'capture time mismatch at {ev} frame {idx}')
            p = media/'frames'/view/f'{frame_id}.png'
            digest = capture['frames'][idx]['image_sha256'][str(p)]
            if sha(p) != digest: raise RuntimeError(f'frame SHA mismatch: {p}')
            x, y = margin+col*pw, margin+(vr*2+er)*(ph+lh)
            im = Image.open(p).convert('RGB'); im.thumbnail((pw,ph),Image.Resampling.LANCZOS)
            tile=Image.new('RGB',(pw,ph),'white'); tile.paste(im,((pw-im.width)//2,(ph-im.height)//2))
            img2.paste(tile,(x,y+lh)); d2.text((x+8,y+8),f'{elabel} · {vlabel} · {tlabel}',font=small,fill='#111111')
img2.save(ART/'noise_eval1_eval4_native_frames_v1.png', optimize=True)
print(json.dumps({
 'font_sha256':FONT_SHA,
 'reference_panel_sha256':sha(ART/'initial_noise_bank_and_native_reference_v1.png'),
 'native_eval_panel_sha256':sha(ART/'noise_eval1_eval4_native_frames_v1.png'),
},ensure_ascii=False))
