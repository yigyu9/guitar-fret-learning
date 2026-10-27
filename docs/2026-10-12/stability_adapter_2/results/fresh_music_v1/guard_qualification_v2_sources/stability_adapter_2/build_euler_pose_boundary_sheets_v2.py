"""Rebuild Korean-labeled sheets from the preserved native boundary captures."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1'
PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
CELL = (480, 270)
ROW_GUTTER, TITLE_H, COLUMN_H = 180, 48, 44
VIEWS = ('front', 'side', 'hands')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def centered(draw, box, text, font, fill):
    left, top, right, bottom = box
    bounds = draw.textbbox((0, 0), text, font=font)
    width, height = bounds[2]-bounds[0], bounds[3]-bounds[1]
    draw.text((left+(right-left-width)/2-bounds[0],
               top+(bottom-top-height)/2-bounds[1]), text, font=font, fill=fill)


def case_index(rows):
    indexed = {row['id']: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError('duplicate native case id')
    return indexed


def source_images(case):
    folder = Path(case['folder'])
    return {'front': folder/'front.png', 'side': folder/'side.png',
            'hands': folder/'images/frames/hands/00000.png'}


def expected_hash(case, view, path):
    if view in ('front', 'side'):
        expected = case['native_camera_sha256'].get(str(path.resolve()))
        if expected is None:
            raise ValueError(f'{case["id"]}/{view}: native camera hash missing')
        return expected
    capture = read(Path(case['folder'])/'images/capture.json')
    frames = capture.get('frames', [])
    if len(frames) != 1 or frames[0].get('physics_step') != 0:
        raise ValueError(f'{case["id"]}: hand image is not a single t=0 capture')
    for recorded, digest in frames[0].get('image_sha256', {}).items():
        if Path(recorded).resolve() == path.resolve():
            return digest
    raise ValueError(f'{case["id"]}/hands: source image hash missing')


def load_images(rows):
    cache, sources = {}, {}
    for case in rows:
        cache[case['id']], sources[case['id']] = {}, {}
        for view, path in source_images(case).items():
            path = path.resolve()
            if not path.is_file() or sha(path) != expected_hash(case, view, path):
                raise ValueError(f'{case["id"]}/{view}: native source missing or hash mismatch')
            with Image.open(path) as source:
                image = source.convert('RGB')
                image.thumbnail(CELL, Image.Resampling.LANCZOS)
                if image.size != CELL:
                    raise ValueError(f'{case["id"]}/{view}: unexpected aspect ratio {image.size}')
                cache[case['id']][view] = image.copy()
            sources[case['id']][view] = {'path': str(path), 'sha256': sha(path)}
    return cache, sources


def build_sheet(kind, rows, view, labels, cache, out):
    width = ROW_GUTTER + len(labels)*CELL[0]
    height = TITLE_H + COLUMN_H + len(rows)*CELL[1]
    sheet = Image.new('RGB', (width, height), (242, 244, 247))
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(str(FONT), 24)
    column_font = ImageFont.truetype(str(FONT), 19)
    row_font = ImageFont.truetype(str(FONT), 18)
    title = ('위치 경계' if kind == 'position' else '회전 경계')+' — '+view+' view'
    centered(draw, (ROW_GUTTER, 0, width, TITLE_H), title, title_font, (20, 28, 38))
    for col, label in enumerate(labels):
        x = ROW_GUTTER + col*CELL[0]
        centered(draw, (x, TITLE_H, x+CELL[0], TITLE_H+COLUMN_H), label,
                 column_font, (25, 35, 45))
    mapping = []
    for row_idx, (axis, slots) in enumerate(rows):
        y = TITLE_H + COLUMN_H + row_idx*CELL[1]
        centered(draw, (0, y, ROW_GUTTER, y+CELL[1]), axis, row_font, (25, 35, 45))
        for col, case_id in enumerate(slots):
            x = ROW_GUTTER + col*CELL[0]
            if case_id is None:
                draw.rectangle((x, y, x+CELL[0]-1, y+CELL[1]-1), fill=(232, 235, 239))
                centered(draw, (x, y, x+CELL[0], y+CELL[1]), '상한 미지정', row_font,
                         (85, 93, 103))
                continue
            sheet.paste(cache[case_id][view], (x, y))
            mapping.append({'axis': axis, 'column': labels[col], 'case_id': case_id,
                            'source_image': str(source_images_by_id[case_id][view]),
                            'source_image_sha256': source_hashes_by_id[case_id][view]['sha256']})
    sheet.save(out, format='PNG', optimize=False)
    return mapping


def main():
    if not FONT.is_file():
        raise FileNotFoundError(FONT)
    native = read(SOURCE_PHASE/'comparison.json')
    if native.get('case_count') != 12 or native.get('physics_steps') != 0 \
            or not all(native.get('checks', {}).values()):
        raise ValueError('native comparison is incomplete or did not remain at zero physics steps')
    rows = native.get('rows', [])
    if len(rows) != 12 or not all(all(row['checks'].values()) for row in rows):
        raise ValueError('per-case native checks failed')
    indexed = case_index(rows)
    cache, sources = load_images(rows)
    global source_images_by_id, source_hashes_by_id
    source_images_by_id = {case_id: source_images(case) for case_id, case in indexed.items()}
    source_hashes_by_id = sources

    PHASE.mkdir(parents=True, exist_ok=False)
    image_dir = PHASE/'images'
    image_dir.mkdir()
    position_rows = [
        ('X (m)', ['position_x_min', 'reference', 'position_x_max']),
        ('Y (m)', ['position_y_min', 'reference', 'position_y_max']),
        ('Z (m)', ['position_z_min', 'reference', None]),
    ]
    rotation_rows = [
        ('Euler X (deg)', ['rotation_x_min', 'reference', 'rotation_x_max']),
        ('Euler Y (deg)', ['rotation_y_min', 'reference', 'rotation_y_max']),
        ('Euler Z (deg)', ['rotation_z_min', 'reference', 'rotation_z_max']),
    ]
    sheet_records = {}
    for kind, axis_rows, labels in (
            ('position', position_rows, ['하한', '기준값', '상한']),
            ('rotation', rotation_rows, ['하한', '기준값', '상한'])):
        for view in VIEWS:
            path = image_dir/f'{kind}_{view}.png'
            mapping = build_sheet(kind, axis_rows, view, labels, cache, path)
            sheet_records[str(path.resolve())] = {'sha256': sha(path), 'cells': mapping}

    inputs = [Path(__file__).resolve(), (SOURCE_PHASE/'comparison.json').resolve(), FONT.resolve()]
    input_hashes = {str(path): sha(path) for path in inputs}
    for by_view in sources.values():
        for record in by_view.values():
            input_hashes[record['path']] = record['sha256']
    if any(sha(path) != digest for path, digest in input_hashes.items()):
        raise RuntimeError('a verified source changed during sheet generation')
    write(PHASE/'visualization.json', {
        'source_phase': str(SOURCE_PHASE.resolve()),
        'source_comparison_sha256': sha(SOURCE_PHASE/'comparison.json'),
        'source_native_images_sha256': sources, 'font': str(FONT.resolve()),
        'font_sha256': sha(FONT), 'input_sha256': input_hashes,
        'physics_steps': 0, 'case_count': len(rows), 'sheets': sheet_records,
        'checks': {'source_images_verified': True, 'native_zero_physics_steps': True,
                   'case_images_have_expected_dimensions': True,
                   'korean_font_used': True}})

    doc = ['# 기타 위치·회전 범위 경계 이미지', '',
        '제시한 각 위치·회전 경계에서 기타가 어떻게 보이는지 정적 장면으로 비교한 자료입니다. 캡처는 Isaac Gym native camera로 만들었고 물리 step은 0입니다. 이미지는 배치의 시각적 검토용이며 접촉·관통·안정성 판정을 뜻하지 않습니다.', '',
        '범위 해석: X `[-0.50, -0.15] m`, Y `[-0.15, 0.15] m`, Z `>=0.65 m`, 월드 기준 extrinsic Euler XYZ X `[45,90]°`, Y `[50,100]°`, Z `[135,180]°`입니다. 입력의 X 역순은 오름차순 구간으로 정리했습니다. Z에는 상한이 없어 하한만 표시했습니다.', '',
        '각 비교는 한 좌표만 바꾸고 나머지는 기준값에 둡니다. 기준 위치는 `(-0.325, 0, 0.65) m`, 기준 회전은 `(67.5, 75, 157.5)°`입니다. 위치 시트의 Z 하한과 기준은 같은 위치 포즈이며, 상한 칸은 지정되지 않은 상태를 나타냅니다. 모든 축을 함께 경계에 놓는 조합은 이번 이미지에 포함하지 않았습니다.', '',
        '## 위치 경계', '',
        f'![정면 시점 위치 경계]({image_dir / "position_front.png"})', '',
        f'![측면 시점 위치 경계]({image_dir / "position_side.png"})', '',
        f'![손 시점 위치 경계]({image_dir / "position_hands.png"})', '',
        '## 회전 경계', '',
        f'![정면 시점 회전 경계]({image_dir / "rotation_front.png"})', '',
        f'![측면 시점 회전 경계]({image_dir / "rotation_side.png"})', '',
        f'![손 시점 회전 경계]({image_dir / "rotation_hands.png"})', '',
        '## 경계 포즈 값', '', '| 케이스 | 위치 X,Y,Z (m) | Euler X,Y,Z (deg) |', '|---|---:|---:|']
    for row in rows:
        doc.append('| `%s` | `%s` | `%s` |' % (
            row['id'], ', '.join(f'{v:.3f}' for v in row['position_W_m']),
            ', '.join(f'{v:.1f}' for v in row['euler_xyz_world_deg'])))
    doc += ['', f'원본 12개 native 장면과 포즈·상태 기록: [{SOURCE_PHASE}/native]({SOURCE_PHASE}/native).',
            '시트의 한글은 나눔고딕으로 렌더링했으며, 원본 카메라 프레임은 잘라내거나 기하를 보정하지 않고 축소해 배치했습니다.']
    (PHASE/'README.md').write_text('\n'.join(doc)+'\n', encoding='utf-8')
    print(f'created {PHASE}')


if __name__ == '__main__':
    main()
