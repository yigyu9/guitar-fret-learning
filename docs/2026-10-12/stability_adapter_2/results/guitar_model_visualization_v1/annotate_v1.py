"""Annotate preserved native camera frames using actual native marker readback."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

ROOT = Path('/home/ajou/yigyu/3')
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
BOLD = Path('/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf')
WHITE, GRAY, GREEN = '#edf4fc', '#aebed0', '#35ef83'
ORANGE, CYAN = '#ffac45', '#53d9ed'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def label(draw, point, text, color=WHITE, size=25, anchor='lm'):
    draw.text(point, text, font=font(size), fill=color, anchor=anchor,
              stroke_width=2, stroke_fill='#080b10')


def dashed(draw, a, b, color=CYAN, width=3, dash=10):
    a, b = np.asarray(a), np.asarray(b)
    length = np.linalg.norm(b - a)
    for start in np.arange(0, length, dash * 1.8):
        end = min(start + dash, length)
        if length:
            draw.line([tuple(a + (b - a) * start / length),
                       tuple(a + (b - a) * end / length)], fill=color, width=width)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    data = json.loads(args.capture.read_text())
    assert data['physics_steps'] == 0 and data['inputs_unchanged']
    positions = {name: np.array(value) for name, value in data['body_positions_G_m'].items()}
    rot = Rotation.from_quat(data['guitar_root_quaternion_xyzw'])
    origin = np.array(data['guitar_root_position_W_m'])
    colors = [tuple(round(v * 255) for v in rgb) for rgb in data['colors_string_1_through_6']]
    source = ROOT / 'stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml'
    tree = ET.parse(source).getroot()
    bodies = {body.get('name'): body for body in tree.findall('.//body')}
    strike_source = ROOT / 'guitar_learning/strike.py'
    contract = {}
    for node in ast.parse(strike_source.read_text()).body:
        if isinstance(node, ast.ClassDef) and node.name == 'StrikeContract':
            for field in node.body:
                if isinstance(field, ast.AnnAssign):
                    contract[field.target.id] = ast.literal_eval(field.value)
    lo, hi = contract['allowed_y_m']
    inputs = [args.capture, source, strike_source, FONT, BOLD, Path(__file__).resolve()]
    inputs += [Path(c['raw_image']) for c in data['cameras'].values()]
    pins = {str(p.resolve()): sha(p) for p in inputs}

    def at_y(n, y):
        a, b = positions['G:string%d' % n], positions['G:string%d_end' % n]
        return a + (b - a) * (y - a[1]) / (b[1] - a[1])

    footprint = [at_y(6, lo), at_y(1, lo), at_y(1, hi), at_y(6, hi)]
    projected = {}

    def annotate(name):
        camera = data['cameras'][name]
        raw = Image.open(camera['raw_image']).convert('RGB')
        view, projection = np.array(camera['view']), np.array(camera['projection'])
        w, h = raw.size

        def project(point):
            world = origin + rot.apply(np.asarray(point))
            clip = np.r_[world, 1.] @ view @ projection
            ndc = clip[:3] / clip[3]
            x, y = (ndc[0] + 1) * w / 2., (1 - ndc[1]) * h / 2.
            return np.array([y, w - 1 - x])

        image = raw.transpose(Image.Transpose.ROTATE_90).convert('RGBA')
        layer = Image.new('RGBA', image.size)
        draw = ImageDraw.Draw(layer)
        points = [tuple(project(p)) for p in footprint]
        draw.polygon(points, fill=(255, 156, 43, 65), outline=(255, 172, 69, 255), width=4)
        if name == 'strike':
            center = np.array(data['pluck_proxy_center_G_m'])
            half = np.array(data['pluck_proxy_half_size_m'])
            corners = [center + half * [x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
            for i in range(8):
                for bit in (1, 2, 4):
                    j = i ^ bit
                    if j > i:
                        dashed(draw, project(corners[i]), project(corners[j]))
        for n, color in enumerate(colors, 1):
            a = project(positions['G:string%d' % n])
            b = project(positions['G:string%d_end' % n])
            draw.line([tuple(a), tuple(b)], fill=(*color, 245), width=3)
        if name != 'strike':
            numbers = range(1, 23) if name == 'frets' else (1, 3, 5, 7, 9, 12, 15, 17, 19, 22)
            for n in range(1, 23):
                center = positions['G:fret%d' % n]
                half = float(bodies['G:fret%d' % n].find('geom').get('size').split()[0])
                a = project(center + [-half, 0., 0.])
                b = project(center + [half, 0., 0.])
                draw.line([tuple(a), tuple(b)], fill=GREEN, width=3)
                if n in numbers:
                    left = a if a[0] < b[0] else b
                    draw.line([tuple(left), tuple(left + [-28, 0])], fill=GREEN, width=2)
                    label(draw, left + [-35, 0], str(n), GREEN, 25, 'rm')
            nut = project(positions['G:nut'])
            label(draw, nut + [-120, -4], '너트', WHITE, 24, 'rm')
            if name == 'frets':
                for n, color in enumerate(colors, 1):
                    point = project(positions['G:string%d' % n])
                    label(draw, point + [0, -35], str(n), color, 24, 'mm')
        image = Image.alpha_composite(image, layer)
        projected[name] = {key: project(value).tolist() for key, value in positions.items()}
        header, footer = 118, 128
        canvas = Image.new('RGB', (image.width, image.height + header + footer), '#080b10')
        canvas.paste(image.convert('RGB'), (0, header))
        draw = ImageDraw.Draw(canvas)
        titles = {'overview': ('현재 OM 기타', '6현 · 22프렛 · 실제 타현 Y 범위'),
                  'frets': ('22프렛 확대', '숫자 = 프렛 번호 / 위쪽 6…1 = 물리 줄 번호'),
                  'strike': ('타현 영역 확대', '주황 = 실제 Y 허용 범위 / 청록 점선 = XML 보조 박스')}
        title, subtitle = titles[name]
        draw.text((30, 20), title, font=font(35, True), fill=WHITE)
        draw.text((30, 69), subtitle, font=font(21), fill=GRAY)
        y = header + image.height + 18
        if name == 'overview':
            draw.text((30, y), '초록: 프렛 와이어 위치  |  주황: 6현의 허용 Y 범위 투영', font=font(21), fill=WHITE)
            for n, color in enumerate(colors, 1):
                x = 35 + (n - 1) * 155
                draw.line((x, y + 51, x + 25, y + 51), fill=color, width=5)
                draw.text((x + 33, y + 39), '%d번 %s' % (n, ['E4', 'B3', 'G3', 'D3', 'A2', 'E2'][n-1]), font=font(21), fill=WHITE)
        elif name == 'frets':
            draw.text((30, y), '너트→12프렛 310.682 mm / →22프렛 447.000 mm', font=font(22), fill=WHITE)
            draw.text((30, y + 39), '현재 XML에는 23·24프렛이 없습니다.', font=font(22), fill=GRAY)
        else:
            draw.text((30, y), '주황 면은 현 높이에서 본 Y 범위이며, 깊이 조건은 아래 단면에 표시합니다.', font=font(22), fill=WHITE)
            draw.text((30, y + 40), '실제 판정: 각 현 교차 + 깊이 1…15 mm + 횡속도 ≥0.05 m/s + 재무장', font=font(22), fill=GRAY)
        return canvas

    overview, frets, strike = [annotate(name) for name in ('overview', 'frets', 'strike')]
    panel = Image.new('RGB', (strike.width, strike.height + 540), '#080b10')
    panel.paste(strike, (0, 0))
    draw = ImageDraw.Draw(panel)
    top = strike.height
    draw.text((30, top + 15), '깊이 단면 — 좌표 설명도', font=font(32, True), fill=WHITE)
    draw.text((30, top + 62), '측면 렌더가 아닌 Y–Z 단면입니다. 현 높이 Z=12.3 mm 기준.', font=font(22), fill=GRAY)
    left, right, ytop, ybottom = 130, panel.width - 80, top + 130, top + 420

    def diagram(y, z):
        return (left + (y + .435) / .220 * (right - left),
                ybottom - (z + .006) / .024 * (ybottom - ytop))

    draw.rectangle((left, ytop, right, ybottom), outline='#40516a', width=2)
    z = float(positions['G:string1'][2])
    lower, upper = z - contract['max_depth_m'], z - contract['min_depth_m']
    a, b = diagram(lo, upper), diagram(hi, lower)
    draw.rectangle((a, b), fill='#71451e', outline=ORANGE, width=3)
    draw.line((diagram(-.435, z), diagram(-.215, z)), fill='#cfd9e8', width=3)
    label(draw, diagram(-.431, z) + np.array([0, -17]), '현 Z=12.3', WHITE, 21)
    center = np.array(data['pluck_proxy_center_G_m'])
    half = np.array(data['pluck_proxy_half_size_m'])
    proxy = [diagram(center[1]-half[1], center[2]+half[2]),
             diagram(center[1]+half[1], center[2]+half[2]),
             diagram(center[1]+half[1], center[2]-half[2]),
             diagram(center[1]-half[1], center[2]-half[2])]
    for a, b in zip(proxy, proxy[1:] + proxy[:1]):
        dashed(draw, a, b)
    label(draw, diagram(-.32, .004), '유효 깊이 1…15 mm', ORANGE, 24, 'mm')
    for y, text in [(lo, '−385'), (hi, '−255')]:
        x, _ = diagram(y, 0)
        draw.line((x, ybottom, x, ybottom+9), fill=ORANGE, width=2)
        label(draw, (x, ybottom+26), text, ORANGE, 22, 'mm')
    label(draw, (right, ybottom+26), 'Y (mm)', GRAY, 22, 'rm')
    draw.text((30, top+475), '점선: G:pluck_range   Y=−414…−242 / Z=−1.2…13.8 mm (판정 영역과 별개)', font=font(22), fill=CYAN)
    strike = panel
    images = {'guitar_overview.png': overview, 'fret_detail.png': frets, 'strike_detail.png': strike}
    canvas = Image.new('RGB', (2400, 1800), '#0d141e')
    draw = ImageDraw.Draw(canvas)
    draw.text((45, 26), '현재 기타 모델: 줄 · 프렛 · 타현 영역', font=font(42, True), fill=WHITE)
    draw.text((45, 84), 'Isaac Gym native camera + native markers + marker-coordinate annotations / 0 physics steps', font=font(24), fill=GRAY)
    widths = [750, 660, 900]
    x = 35
    for image, width in zip((overview, frets, strike), widths):
        scale = min(width / image.width, 1510 / image.height)
        resized = image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.LANCZOS)
        canvas.paste(resized, (x + (width-resized.width)//2, 145))
        x += width + 25
    draw.text((45, 1710), 'Color overlays show measured marker locations and the detector geometry; they do not certify sound, contact or playing success.', font=font(24), fill=GRAY)
    images['guitar_regions.png'] = canvas
    outputs = {}
    for name, image in images.items():
        path = args.out / name
        image.save(path)
        outputs[name] = dict(path=str(path.resolve()), size=list(image.size), sha256=sha(path))
    assert all(sha(p) == h for p, h in pins.items())
    metadata = dict(source_capture=str(args.capture.resolve()), input_sha256=pins, inputs_unchanged=True,
                    strike_contract=contract, footprint_G_m=[p.tolist() for p in footprint],
                    depth_bounds_G_m=[lower, upper], projected_native_markers_rotated_pixels=projected,
                    output=outputs, camera_image_rotation_degrees=90, physics_steps=0,
                    annotation_scope='Native camera images and native display markers; 2D coordinate overlays are not depth-occluded. Orange faces show the Y footprint at string height, not the full 3D valid volume. The separate depth panel is a schematic.')
    (args.out/'annotations.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n')
    print('Annotated native images saved: ' + ', '.join(images))


if __name__ == '__main__':
    main()
