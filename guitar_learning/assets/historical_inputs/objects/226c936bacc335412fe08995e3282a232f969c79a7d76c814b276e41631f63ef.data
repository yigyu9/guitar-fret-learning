#!/usr/bin/env python3
"""Compose the three saved Isaac Gym camera views for the horizontal-neck trial."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1'
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
CASES = [
    ('candidate_000', '-10° 요청'),
    ('candidate_001', '0° 요청'),
    ('candidate_002', '+10° 요청'),
]
VIEWS = [
    ('정면', 'front.png'),
    ('측면', 'side.png'),
    ('손 근접', 'images/frames/hands/00000.png'),
]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True, type=Path)
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    output = out_dir / 'horizontal_neck_initial_comparison.png'
    manifest_path = out_dir / 'artifact_manifest.json'
    if out_dir.exists() and (any(out_dir.iterdir()) or output.exists() or manifest_path.exists()):
        raise SystemExit('output directory must be absent or empty; refusing to overwrite')
    if not FONT_PATH.is_file():
        raise FileNotFoundError(FONT_PATH)

    comparison_path = PHASE / 'native/comparison.json'
    paths = [comparison_path, PHASE / 'computed_poses.json', FONT_PATH]
    case_inputs = []
    for case_id, _ in CASES:
        folder = PHASE / 'native/scene' / case_id
        case_comparison = folder / 'comparison.json'
        pose_path = folder / 'pose.json'
        view_paths = [folder / relative for _, relative in VIEWS]
        paths.extend([case_comparison, pose_path, *view_paths])
        case_inputs.append((case_id, case_comparison, pose_path, view_paths))
    before = {str(path.resolve()): sha256(path) for path in paths}

    comparison = json.loads(comparison_path.read_text())
    if comparison.get('physics_steps') != 0 or len(comparison.get('rows', [])) != 3:
        raise ValueError('expected three completed zero-step camera captures')
    if not all(comparison.get('checks', {}).values()):
        raise ValueError('native camera comparison checks did not all pass')
    labels_by_id = {case_id: label for case_id, label in CASES}
    row_by_id = {}
    for row in comparison['rows']:
        case_id = Path(row['path']).name
        if case_id not in labels_by_id or case_id in row_by_id:
            raise ValueError(f'unexpected or duplicate camera case: {case_id}')
        row_by_id[case_id] = row
    if set(row_by_id) != set(labels_by_id):
        raise ValueError('comparison case mapping mismatch')

    font = ImageFont.truetype(str(FONT_PATH), 22)
    row_font = ImageFont.truetype(str(FONT_PATH), 23)
    header_font = ImageFont.truetype(str(FONT_PATH), 20)
    case_labels = []
    for case_id, label in CASES:
        actual = float(row_by_id[case_id]['neck_elevation_deg'])
        case_labels.append(f'{label} / 실제 {actual:+.6f}°')

    # Measure text before allocating the label and column-header areas.
    probe = Image.new('RGB', (8, 8))
    draw = ImageDraw.Draw(probe)
    label_width = max(draw.textbbox((0, 0), label, font=row_font)[2] for label, _ in VIEWS) + 32
    column_width = max(432, max(draw.textbbox((0, 0), label, font=header_font)[2] for label in case_labels) + 28)
    cell_height = 243  # 16:9 fit for 1280x720 input; no cropping.
    gap = 14
    header_height = 70
    footer_height = 45
    width = label_width + len(CASES) * column_width + (len(CASES) - 1) * gap
    height = header_height + len(VIEWS) * cell_height + (len(VIEWS) - 1) * gap + footer_height
    canvas = Image.new('RGB', (width, height), '#f5f6f8')
    draw = ImageDraw.Draw(canvas)
    title = '수평 넥 초기 회전 비교 · 실제 Isaac Gym 카메라 · t=0 / physics step 0'
    draw.text((label_width, 14), title, font=font, fill='#20252b')

    mapping = []
    for col, (case_id, _) in enumerate(CASES):
        x = label_width + col * (column_width + gap)
        draw.text((x + 8, 43), case_labels[col], font=header_font, fill='#263645')
    for row_index, (view_label, _) in enumerate(VIEWS):
        y = header_height + row_index * (cell_height + gap)
        bbox = draw.textbbox((0, 0), view_label, font=row_font)
        draw.text((8, y + (cell_height - (bbox[3] - bbox[1])) // 2), view_label, font=row_font, fill='#263645')
        for col, (case_id, _) in enumerate(CASES):
            src = PHASE / 'native/scene' / case_id / VIEWS[row_index][1]
            image = Image.open(src).convert('RGB')
            if image.size != (1280, 720):
                raise ValueError(f'unexpected source dimensions {image.size}: {src}')
            image.thumbnail((column_width, cell_height), Image.Resampling.LANCZOS)
            x = label_width + col * (column_width + gap)
            px = x + (column_width - image.width) // 2
            py = y + (cell_height - image.height) // 2
            canvas.paste(image, (px, py))
            mapping.append({
                'case': case_id,
                'requested_elevation_deg': row_by_id[case_id]['requested_elevation_deg'],
                'rendered_neck_elevation_deg': row_by_id[case_id]['neck_elevation_deg'],
                'view': view_label,
                'source': str(src.resolve()),
                'source_size_px': [1280, 720],
                'sheet_box_px': [px, py, image.width, image.height],
                'crop': False,
            })
    footer = '각 칸은 원본 비율로 축소한 저장 이미지이며 crop·overlay 없이 배치했습니다.'
    draw.text((label_width, height - footer_height + 9), footer, font=header_font, fill='#49525c')

    out_dir.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format='PNG', optimize=True)
    after = {str(path.resolve()): sha256(path) for path in paths}
    if before != after:
        raise RuntimeError('input changed while composing the sheet')
    manifest = {
        'schema': 'horizontal_neck_initial_sheet_v1',
        'producer': str(Path(__file__).resolve()),
        'producer_sha256': sha256(__file__),
        'inputs_sha256_before': before,
        'inputs_sha256_after': after,
        'checks': {'three_cases_mapped': True, 'nine_views_mapped': len(mapping) == 9,
                   'zero_physics_steps': comparison['physics_steps'] == 0,
                   'images_uncropped': all(not item['crop'] for item in mapping)},
        'native_renderer_note': 'Saved Isaac Gym camera PNGs; renderer backend identity beyond CPU PhysX/software Vulkan is not asserted.',
        'layout': {'size_px': [width, height], 'row_labels': [v[0] for v in VIEWS],
                   'case_labels': case_labels, 'mapping': mapping},
        'output': {'path': str(output.resolve()), 'sha256': sha256(output), 'size_px': [width, height]},
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(output)
    print(manifest_path)


if __name__ == '__main__':
    main()
