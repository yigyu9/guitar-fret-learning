"""Overlay the recorded world-space target polygon on saved Gym camera frames."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PHASE = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def vec3(value):
    return [float(x) for x in value]


def project(point, camera):
    eye, target = vec3(camera['eye']), vec3(camera['target'])
    forward = [target[i] - eye[i] for i in range(3)]
    norm = math.sqrt(sum(x*x for x in forward))
    forward = [x / norm for x in forward]
    world_up = [0.0, 0.0, 1.0]
    right = [forward[1]*world_up[2] - forward[2]*world_up[1],
             forward[2]*world_up[0] - forward[0]*world_up[2],
             forward[0]*world_up[1] - forward[1]*world_up[0]]
    rnorm = math.sqrt(sum(x*x for x in right))
    right = [x / rnorm for x in right]
    up = [right[1]*forward[2] - right[2]*forward[1],
          right[2]*forward[0] - right[0]*forward[2],
          right[0]*forward[1] - right[1]*forward[0]]
    rel = [float(point[i]) - eye[i] for i in range(3)]
    depth = sum(rel[i] * forward[i] for i in range(3))
    if depth <= 0:
        raise ValueError('world point is behind recorded camera')
    width, height = int(camera['width']), int(camera['height'])
    tan_h = math.tan(math.radians(float(camera['horizontal_fov_deg'])) / 2.0)
    tan_v = tan_h * height / width
    px = width / 2.0 + sum(rel[i] * right[i] for i in range(3)) / (depth * tan_h) * width / 2.0
    py = height / 2.0 - sum(rel[i] * up[i] for i in range(3)) / (depth * tan_v) * height / 2.0
    return px, py


def quat_rotate(q, v):
    x, y, z, w = q
    # q * [v,0] * conjugate(q), with xyzw ordering.
    uv = [y*v[2]-z*v[1], z*v[0]-x*v[2], x*v[1]-y*v[0]]
    uuv = [y*uv[2]-z*uv[1], z*uv[0]-x*uv[2], x*uv[1]-y*uv[0]]
    return [v[i] + 2.0*(w*uv[i] + uuv[i]) for i in range(3)]


def world_contact_points(probe):
    entry = next(item for item in probe['contacts'][0]['contacts']
                 if item.get('body0_name') == 'guitar/guitar' and item.get('body1_name') == 'human/LH:palm')
    state = probe['states'][1]
    body = state['guitar_body_states'][0]['pose']
    p, q = body['p'], body['r']
    pos = [p[k] for k in ('x', 'y', 'z')]
    quat = [q[k] for k in ('x', 'y', 'z', 'w')]
    raw = probe['contacts'][0]['contacts']
    points = []
    for contact in raw:
        if contact.get('body0_name') == 'guitar/guitar' and contact.get('body1_name') == 'human/LH:palm':
            local = contact['localPos0']
            offset = quat_rotate(quat, [local[k] for k in ('x', 'y', 'z')])
            points.append([pos[i] + offset[i] for i in range(3)])
    return points


def load_record(rel):
    path = PHASE / rel
    data = json.loads(path.read_text())
    return path, data


def annotate(rel_probe, image_key, label, output, contact_points=()):
    probe_path, probe = load_record(rel_probe)
    image_meta = probe['images'][image_key]
    input_image = Path('/home/ajou/yigyu/3') / image_key
    camera_name = 'blue_front' if 'front' in Path(image_key).name else 'blue_side'
    camera = probe['camera_specs'][camera_name]
    poly = [project(p, camera) for p in image_meta['target_polygon_W_m']]
    base = Image.open(input_image).convert('RGBA')
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.polygon(poly, fill=(0, 220, 230, 75), outline=(0, 255, 255, 245), width=4)
    draw.line(poly + [poly[0]], fill=(0, 255, 255, 245), width=4)
    for index, point in enumerate(contact_points, start=1):
        px, py = project(point, camera)
        radius = 9
        draw.ellipse((px-radius, py-radius, px+radius, py+radius), fill=(255, 55, 55, 210), outline=(255, 255, 255, 255), width=2)
        draw.line((px-radius-4, py, px+radius+4, py), fill=(255, 255, 255, 255), width=2)
        draw.line((px, py-radius-4, px, py+radius+4), fill=(255, 255, 255, 255), width=2)
        draw.text((px+10, py-16), str(index), fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(80, 0, 0, 255))
    merged = Image.alpha_composite(base, layer).convert('RGB')
    banner = Image.new('RGB', (merged.width, 42), (24, 30, 40))
    ImageDraw.Draw(banner).text((18, 11), label, fill='white')
    out = Image.new('RGB', (merged.width, merged.height + banner.height), 'white')
    out.paste(banner, (0, 0)); out.paste(merged, (0, banner.height))
    output.parent.mkdir(parents=True, exist_ok=True)
    out.save(output, quality=95)
    return {'source_probe': str(probe_path), 'source_image': str(input_image), 'camera': camera_name,
            'projection': 'look-at basis + recorded horizontal FOV (world coordinates in meters; output pixels)',
            'physics_step': image_meta['physics_step'], 'target_polygon_W_m': image_meta['target_polygon_W_m'],
            'contact_points_count': len(contact_points), 'output': str(output), 'output_sha256': sha(output)}


def contact_points():
    _, probe = load_record('facet_native_first/probe.json')
    assert len(probe['contacts']) == 1 and probe['contacts'][0]['physics_step'] == 1
    matches = [c for c in probe['contacts'][0]['contacts']
               if c.get('body0_name') == 'guitar/guitar' and c.get('body1_name') == 'human/LH:palm']
    if len(matches) != 4:
        raise ValueError(f'expected the recorded four-point palm manifold, got {len(matches)}')
    return world_contact_points(probe)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f'output directory is not empty: {args.out_dir}')
    args.out_dir.mkdir(parents=True, exist_ok=True)
    steps = contact_points()
    frames = [
        ('baseline_camera/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/baseline_camera/blue_front_000.png', 'baseline step 0', 'baseline_front.png', ()),
        ('facet_native_first/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_native_first/blue_front_000.png', 'new facet step 0', 'facet_initial_front.png', ()),
        ('facet_native_first/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_native_first/blue_front_001.png', 'new facet step 1; four recorded contact points', 'facet_step1_front.png', steps),
        ('facet_native_short/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_native_short/blue_front_024.png', 'new facet step 24 (0.1 s)', 'facet_step24_front.png', ()),
    ]
    records = []
    for rp, img, label, name, points in frames:
        records.append(annotate(rp, img, label, args.out_dir/name, points))
    # Matching side-view frames make the camera-angle comparison independently inspectable.
    sides = [
        ('baseline_camera/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/baseline_camera/blue_side_000.png', 'baseline step 0 — side', 'baseline_side.png', ()),
        ('facet_native_first/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_native_first/blue_side_000.png', 'new facet step 0 — side', 'facet_initial_side.png', ()),
        ('facet_native_first/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_native_first/blue_side_001.png', 'new facet step 1 — side', 'facet_step1_side.png', steps),
        ('facet_native_short/probe.json', 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_native_short/blue_side_024.png', 'new facet step 24 (0.1 s) — side', 'facet_step24_side.png', ()),
    ]
    for rp, img, label, name, points in sides:
        records.append(annotate(rp, img, label, args.out_dir/name, points))
    grid_records = []
    for view in ('front', 'side'):
        names = [f'{stem}_{view}.png' for stem in ('baseline', 'facet_initial', 'facet_step1', 'facet_step24')]
        tiles = [Image.open(args.out_dir/name).convert('RGB') for name in names]
        w, h = tiles[0].size
        grid = Image.new('RGB', (w*2, h*2), 'white')
        for i, tile in enumerate(tiles):
            grid.paste(tile, ((i % 2)*w, (i // 2)*h))
        path = args.out_dir/f'comparison_{view}.png'
        grid.save(path)
        grid_records.append({'output': str(path), 'output_sha256': sha(path), 'tile_names': names})
    input_paths = sorted({item[key] for item in records for key in ('source_probe', 'source_image')})
    manifest = {'schema':'palm-neck-side-overlay-v1',
        'source_description':'saved Isaac Gym native camera PNGs with explanatory projection overlay; no simulation or native renderer call',
        'source_records':records,'comparison_figures':grid_records,
        'input_sha256':{path:sha(path) for path in input_paths},
        'producer_path':str(Path(__file__).resolve()),'producer_sha256':sha(__file__),
        'output_sha256':{str(p):sha(p) for p in sorted(args.out_dir.glob('*.png'))},
        'projection_method':'For each recorded camera, forward=(target-eye)/norm, right=forward×world_up, up=right×forward; perspective projection uses recorded horizontal FOV and image aspect ratio. World points and polygon vertices are meters; projected coordinates are pixels.',
        'marker_semantics':'Cyan polygon marks target area and can overlay occluded surfaces. Red numbered crosses mark the four raw step-1 contact positions after transforming guitar-local localPos0 through the saved guitar body-0 pose. These are explanatory overlays, not rendered geometry or independent contact measurements.'}
    (args.out_dir/'overlay_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'out_dir':str(args.out_dir),'frames':len(records),'figures':len(grid_records),'contact_markers':len(steps)}))

if __name__ == '__main__':
    main()
