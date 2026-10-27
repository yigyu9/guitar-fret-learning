from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3')
DOCS = ROOT / 'docs/2026-10-19/stability_adapter_2'
P = DOCS / 'results/right_arm_wrap_forward_v1'
B = DOCS / 'results/right_arm_wrap_upright_v1'
BASE = B / 'native_wrap55_static'
SEL = P / 'native_elbow10_static'
REJ = P / 'native_forward5_static'
A = P / 'artifacts_v1'
V = DOCS / 'video/right_arm_wrap_forward_v1'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
sha = lambda b: hashlib.sha256(b).hexdigest()
fsha = lambda p: sha(Path(p).read_bytes())

# All files consumed below are explicitly required and SHA-pinned before any source read.
source_paths = [
    P/'arm_final_v2.json', P/'timelines_final_v1.json', P/'waist_final_v1.json', P/'guitar_comparison_v1.json',
    ROOT/'stability_adapter_2/analyze_right_arm_wrap_forward_v3.py',
    ROOT/'stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py',
    ROOT/'stability_adapter_2/analyze_right_arm_wrap_waist_v1.py',
    ROOT/'stability_adapter_2/compare_right_arm_wrap_forward_guitar_v1.py',
    ROOT/'stability_adapter_2/initial_pose_noise_v1.py', FONT,
    DOCS/'results/waist_straighten_v1/artifact_inventory_v1.json',
    DOCS/'results/waist_straighten_v1/final_verification_v1.json',
    DOCS/'results/waist_straighten_v1/native_add8_static/report.json',
    DOCS/'results/waist_straighten_v1/native_add8_static/media/videos.json',
]
for run in [BASE, SEL, REJ]:
    source_paths += [run/'initial_values.json', run/'report.json', run/'media/capture.json', run/'media/videos.json']
    source_paths += [run/'media/whole_body.mp4', run/'media/hands.mp4']
source_frames = [
    BASE/'media/frames/whole_body/00000.png', BASE/'media/frames/hands/00000.png',
    SEL/'media/frames/whole_body/00000.png', SEL/'media/frames/hands/00000.png',
]
for run in [SEL]:
    for view in ['whole_body', 'hands']:
        source_frames += [run/'media/frames'/view/f'{i:05d}.png' for i in [0, 60, 150]]
source_frames += [REJ/'media/frames/whole_body/00000.png', REJ/'media/frames/whole_body/00019.png']
producer_paths = [
    ROOT/'stability_adapter_2/analyze_right_arm_wrap_forward_v3.py',
    ROOT/'stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py',
    ROOT/'stability_adapter_2/analyze_right_arm_wrap_waist_v1.py',
    ROOT/'stability_adapter_2/compare_right_arm_wrap_forward_guitar_v1.py',
    A/'build_artifacts_v1.py',
]
required = source_paths + source_frames + producer_paths
missing = [str(p) for p in required if not p.is_file()]
if missing:
    raise FileNotFoundError('Required provenance inputs missing: ' + ', '.join(missing))
inputs_before = {p: fsha(p) for p in dict.fromkeys(source_paths + source_frames)}
producers_before = {p: fsha(p) for p in dict.fromkeys(producer_paths)}

# Confirm baseline MP4 hashes against its sealed inventory and native run metadata.
inv = json.loads((DOCS/'results/waist_straighten_v1/artifact_inventory_v1.json').read_text())['files']
inv_map = {x['path']: x for x in inv}
base_video_claims = json.loads((BASE/'media/videos.json').read_text())
for view in ['whole_body', 'hands']:
    media = BASE/'media'/f'{view}.mp4'
    claim = base_video_claims[view]
    inventory_record = inv_map[str(media)]
    if fsha(media) != claim['sha256'] or claim['sha256'] != inventory_record['sha256']:
        raise ValueError(f'Baseline source MP4 does not match sealed records: {media}')

# Native whole-body and hands camera matrices must both match before paired initial views are shown.
base_cap = json.loads((BASE/'media/capture.json').read_text())
sel_cap = json.loads((SEL/'media/capture.json').read_text())
cameras = {}
for view in ['whole_body', 'hands']:
    x = base_cap['frames'][0]['cameras'][view]
    y = sel_cap['frames'][0]['cameras'][view]
    cameras[view] = {
        'view_matrix_exact': x['view_matrix'] == y['view_matrix'],
        'projection_matrix_exact': x['projection_matrix'] == y['projection_matrix'],
    }
    if not all(cameras[view].values()):
        raise ValueError(f'Paired initial {view} camera matrices do not match')

font = ImageFont.truetype(str(FONT), 18)
def gallery(path, panels, title, size=(520, 292)):
    width, height = size
    top, bottom, gap = 42, 32, 16
    canvas = Image.new('RGB', (gap + (width+gap)*len(panels), top+height+bottom), 'white')
    draw = ImageDraw.Draw(canvas)
    draw.text((gap, 12), title, fill='black', font=font)
    for j, (src, label) in enumerate(panels):
        frame = Image.open(src).convert('RGB').resize((width, height), Image.Resampling.LANCZOS)
        x = gap + j*(width+gap)
        canvas.paste(frame, (x, top))
        draw.text((x, top+height+6), label, fill='black', font=font)
    canvas.save(path)

base_whole = BASE/'media/frames/whole_body/00000.png'
sel_whole = SEL/'media/frames/whole_body/00000.png'
base_hands = BASE/'media/frames/hands/00000.png'
sel_hands = SEL/'media/frames/hands/00000.png'
gallery(A/'initial_whole_comparison_v1.png', [(base_whole, '기준 wrap55 · t=0.000 s'), (sel_whole, '전방 10mm · t=0.000 s')], '실제 native 전신 초기 프레임 · 카메라 행렬 일치')
gallery(A/'initial_hands_comparison_v1.png', [(base_hands, '기준 wrap55 · t=0.000 s'), (sel_hands, '전방 10mm · t=0.000 s')], '실제 native 손·기타 초기 프레임 · 카메라 행렬 일치')

def crop_upper(src, dst):
    im = Image.open(src).convert('RGB')
    im.crop((390, 125, 930, 555)).save(dst)
for sec, frame in [(0, 0), (2, 60), (5, 150)]:
    crop_upper(SEL/'media/frames/whole_body'/f'{frame:05d}.png', A/f'selected_upper_crop_{sec}s_v1.png')
sel_whole_panels = [(SEL/'media/frames/whole_body'/f'{i:05d}.png', f'전방 10mm · t={t}.000 s · native frame {i}') for t, i in [(0,0),(2,60),(5,150)]]
gallery(A/'selected_whole_0_2_5_v1.png', sel_whole_panels, '선택 정지 실행의 실제 native 전신 원프레임')
gallery(A/'selected_upper_crop_0_2_5_v1.png', [(A/f'selected_upper_crop_{t}s_v1.png', f't={t}.000 s · 같은 native whole-body crop') for t in [0,2,5]], '전신 native 프레임 상체 crop · 동일 ROI', size=(360, 371))
wave_panels = [(REJ/'media/frames/whole_body'/f'{i:05d}.png', f'거절 partial · t={t}.000 s · frame {i}') for t,i in [(0,0),(2,60),(5,150)] if (REJ/'media/frames/whole_body'/f'{i:05d}.png').exists()]
# Rejected partial is shorter than 2s; retain its true endpoint, do not fabricate later frames.
rejected_cap = json.loads((REJ/'media/capture.json').read_text())
rejected_last = rejected_cap['frames'][-1]
rejected_frame_path = REJ/'media/frames/whole_body'/f"{rejected_last['physics_step']//8:05d}.png"
if not rejected_frame_path.exists():
    rejected_frame_path = REJ/'media/frames/whole_body'/f'{len(rejected_cap["frames"])-1:05d}.png'
wave_panels = [(REJ/'media/frames/whole_body/00000.png', '거절 partial · t=0.000 s · frame 0'), (rejected_frame_path, f"실제 종료 · t={rejected_last['time_s']:.6f} s · physics step {rejected_last['physics_step']}")]
gallery(A/'rejected_forward5_available_frames_v1.png', wave_panels, '거절 partial 원프레임만 표시 · 이후 시점 미생성', size=(520,292))

# Copy baseline, selected complete, and rejected partial source videos byte-exactly.
video_runs = [
    ('baseline_wrap55_static', BASE, '이전 선택 기준, 5초 완료'),
    ('native_elbow10_static', SEL, '전방 10mm, elbow 목표 정지, 5초 완료'),
    ('native_forward5_static', REJ, '전방 5mm 후보, 기타 안전 변위로 partial'),
]
timeline = json.loads((P/'timelines_final_v1.json').read_text())
video_copies = []
for run_id, run_dir, label in video_runs:
    case_id = run_id if run_id != 'baseline_wrap55_static' else 'native_wrap55_static'
    case = timeline['cases'].get(case_id)
    report = json.loads((run_dir/'report.json').read_text())
    for view, view_label in [('whole_body','전신'),('hands','손·기타 확대')]:
        src = run_dir/'media'/f'{view}.mp4'
        dest = V/f'{run_id}_{view}.mp4'
        shutil.copyfile(src, dest)
        source_hash, copied_hash = fsha(src), fsha(dest)
        if source_hash != copied_hash:
            raise ValueError(f'Copy hash mismatch: {src}')
        stream = json.loads(subprocess.check_output([
            'ffprobe','-v','error','-count_frames','-select_streams','v:0',
            '-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dest)
        ]))['streams'][0]
        completed = bool(report.get('completed', False)) if case is None else bool(case.get('completed_5s', False))
        steps = report.get('physics_steps') if case is None else case.get('physics_steps')
        controls = report.get('control_steps') if case is None else case.get('control_steps')
        elapsed = (steps / 240.0) if steps is not None else None
        failure = None if case is None else case.get('failure')
        video_copies.append({
            'run':run_id,'label':label,'view':view_label,'source':str(src),'path':str(dest),
            'source_sha256':source_hash,'copy_sha256':copied_hash,'byte_exact':True,'bytes':dest.stat().st_size,
            'completed_5s':completed,'physics_steps':steps,'control_steps':controls,'physics_seconds':elapsed,
            'failure':failure,'ffprobe':stream
        })

# Validate selected native pixels against capture.json hashes, then close the before/after pin set.
for frame_path in source_frames:
    if '/frames/' not in str(frame_path):
        continue
    run_dir = next(r for r in [BASE, SEL, REJ] if str(frame_path).startswith(str(r)))
    cap = json.loads((run_dir/'media/capture.json').read_text())
    stem = int(frame_path.stem)
    view = frame_path.parent.name
    row = next((x for x in cap['frames'] if x['physics_step'] == stem*8), None)
    if row is None or row['image_sha256'].get(str(frame_path)) != fsha(frame_path):
        raise ValueError(f'Native frame/capture SHA mismatch: {frame_path}')

source_records=[]
for path, before in inputs_before.items():
    after=fsha(path)
    if before != after: raise ValueError(f'Input changed during packaging: {path}')
    source_records.append({'path':str(path),'sha256_before':before,'sha256_after':after,'unchanged':True})
producer_records=[]
for path, before in producers_before.items():
    after=fsha(path)
    if before != after: raise ValueError(f'Producer changed during packaging: {path}')
    producer_records.append({'path':str(path),'sha256_before':before,'sha256_after':after,'unchanged':True})
derived_images=[{'path':str(path),'sha256':fsha(path)} for path in sorted(A.glob('*.png'))]
manifest={
    'purpose':'native images and byte-exact MP4 copies; no simulation rerun or re-encoding',
    'camera_comparison':cameras,
    'baseline_video_hashes_crosschecked_against':['waist_straighten_v1/artifact_inventory_v1.json','waist_straighten_v1/native_add8_static/report.json','waist_straighten_v1/native_add8_static/media/videos.json'],
    'native_source_inputs':source_records,'producers':producer_records,'video_copies':video_copies,'derived_images':derived_images,
}
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(A/'provenance_v1.json').write_text(json.dumps({
    'purpose':'explicit pre/post SHA pins for every directly consumed raw file, helper, baseline video, and font',
    'native_source_inputs':source_records,'producers':producer_records,
    'font':{'path':str(FONT),'sha256_before':inputs_before[FONT],'sha256_after':fsha(FONT)},
    'manifest_path':str(V/'manifest_v1.json'),'manifest_sha256':fsha(V/'manifest_v1.json')
},ensure_ascii=False,indent=2)+'\n')
