"""Add photographic-style visual meshes; preserve prior guitar collision geometry."""
from pathlib import Path
import hashlib
import os
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import ConvexHull
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'stability_adapter_2/assets/realistic_guitar_v1'
OUT = ROOT / 'stability_adapter_2/assets/acoustic_appearance_v2'
RESULT = ROOT / 'docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    manifest = json.loads((BASE / 'manifest.json').read_text())
    inputs = {str(p): sha(p) for p in BASE.iterdir() if p.is_file()}
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    tree = ET.parse(BASE / 'guitar_asset.xml')
    root = tree.getroot()
    asset = root.find('asset')
    for mesh in asset.findall('mesh'):
        path = (BASE / mesh.get('file')).resolve()
        inputs[str(path)] = sha(path)
        mesh.set('file', os.path.relpath(path, OUT))
    bodies = {b.get('name'): b for b in root.findall('./worldbody//body')}
    length, width = manifest['new_body_length_m'], manifest['new_body_max_width_m']
    profile = np.array(manifest['half_width_profile_t_m'])
    # A dense, shape-preserving interpolation is visual only; no collider is recooked.
    t = np.linspace(0, 1, 161)
    w = PchipInterpolator(profile[:, 0], profile[:, 1])(t)
    outline = np.r_[np.c_[w, length / 2 - t * length],
                    np.c_[-w[::-1], length / 2 - t[::-1] * length]]
    n = 1536
    rng = np.random.default_rng(20261012)
    x = np.arange(n)[None, :]
    y = np.arange(n)[:, None]
    grain = 3 * np.sin(x * .18 + .5 * np.sin(y * .008)) + 1.4 * np.sin(x * .77)
    grain = grain + rng.normal(0, .6, (n, n))
    def wood(name, rgb):
        arr = np.clip(np.array(rgb)[None, None, :] + grain[:, :, None], 0, 255).astype('uint8')
        image = Image.fromarray(arr)
        image.save(OUT / name)
        return image
    front = wood('spruce.png', [222, 184, 124])
    wood('mahogany.png', [111, 57, 30])
    wood('rosewood.png', [48, 31, 22])
    draw = ImageDraw.Draw(front)
    def pixel(xy):
        return ((xy[0] / width + .5) * n, (.5 - xy[1] / length) * n)
    poly = [pixel(p) for p in outline]
    draw.line(poly + poly[:1], fill=(53, 30, 16), width=17, joint='curve')
    inner = [pixel(p * .984) for p in outline]
    draw.line(inner + inner[:1], fill=(236, 216, 166), width=8, joint='curve')
    center = np.array([0., .103])
    for radius, color in [(.057, (64, 38, 23)), (.055, (218, 185, 126)),
                          (.053, (60, 37, 24)), (.051, (213, 180, 124)),
                          (.048, (27, 19, 14)), (.044, (16, 12, 9))]:
        p0, p1 = pixel(center + [-radius, radius]), pixel(center + [radius, -radius])
        draw.ellipse([*p0, *p1], fill=color)
    bridge = [(-.083, -.037), (-.058, -.003), (.058, -.003), (.083, -.037),
              (.045, -.057), (-.045, -.057)]
    draw.polygon([pixel(p) for p in bridge], fill=(45, 28, 17))
    draw.line([pixel([-.043, -.017]), pixel([.043, -.017])], fill=(231, 216, 175), width=7)
    for xx in np.linspace(-.026, .026, 6):
        px, py = pixel([xx, -.032]);draw.ellipse([px-4, py-4, px+4, py+4], fill=(210, 194, 159))
    front.save(OUT / 'spruce.png')
    (OUT / 'wood.mtl').write_text(''.join(
        f'newmtl {name}\nKa 0.3 0.3 0.3\nKd 1 1 1\nKs 0.12 0.12 0.12\nNs 30\nmap_Kd {texture}\n\n'
        for name, texture in [('front', 'spruce.png'), ('side', 'mahogany.png'), ('neck', 'rosewood.png')]))

    def obj(name, vertices, faces, materials, uv):
        lines = ['mtllib wood.mtl']
        lines += ['v %.9f %.9f %.9f' % tuple(v) for v in vertices]
        last = None
        for face, material in zip(faces, materials):
            if material != last:lines.append('usemtl ' + material);last = material
            ids = []
            for index in face:
                lines.append('vt %.8f %.8f' % tuple(uv(vertices[index], material)))
                ids.append(str(index + 1) + '/' + str(len(ids_all) + 1));ids_all.append(1)
            lines.append('f ' + ' '.join(ids))
        path = OUT / name
        path.write_text('\n'.join(lines) + '\n')
        return path
    # Front/back fans plus smoothly sampled sides; separate per-face UVs avoid seams.
    count = len(outline)
    back = .02 - np.interp((length/2 - outline[:, 1])/length, [0, 1], manifest['new_body_depth_range_m'])
    vertices = np.r_[np.c_[outline, np.full(count, .0205)], np.c_[outline, back],
                     [[0, 0, .0205], [0, 0, float(back.mean())]]]
    faces, materials = [], []
    for i in range(count):
        j = (i + 1) % count
        faces += [[2*count, j, i], [2*count+1, count+i, count+j],
                  [i, j, count+j], [i, count+j, count+i]]
        materials += ['front', 'side', 'side', 'side']
    ids_all = []
    body_mesh = obj('visual_body.obj', vertices, faces, materials,
        lambda p, material: [p[0]/width+.5, p[1]/length+.5] if material == 'front'
        else [p[1]/length+.5, (p[2]+.1)/.13])

    def visual(body, mesh_name, file, pos=None):
        ET.SubElement(asset, 'mesh', name=mesh_name, file=os.path.relpath(file, OUT))
        fields = dict(type='mesh', mesh=mesh_name, contype='0', conaffinity='0',
                      group='1', density='0', rgba='1 1 1 1')
        if pos is not None:fields['pos'] = pos
        ET.SubElement(body, 'geom', fields)
    # Keep every original physical mesh and transform; hide only its visual attachment.
    for name in ['guitar', 'G:body']:
        for geom in bodies[name].findall('geom'):
            if geom.get('type') == 'mesh':geom.set('rgba', '0 0 0 0')
    visual(bodies['G:body'], 'visual_body', body_mesh)
    for label, file in [('neck1', ROOT/'tab2body/assets/mesh/guitar_neck1.obj'),
                        ('neck2', ROOT/'tab2body/assets/mesh/guitar_neck2.obj'),
                        ('headstock', BASE/'headstock.obj')]:
        lines = file.read_text().splitlines()
        v = np.array([[float(a) for a in line.split()[1:4]] for line in lines if line.startswith('v ')])
        f = [[int(a.split('/')[0])-1 for a in line.split()[1:]] for line in lines if line.startswith('f ')]
        ids_all = []
        path = obj('visual_'+label+'.obj', v, f, ['side' if label=='headstock' else 'neck']*len(f),
                   lambda p, material: [p[0]/.09+.5, p[1]/.62+.5])
        visual(bodies['guitar'], 'visual_'+label, path)
    for yy in np.linspace(.272, manifest['total_length_m']-.4-length/2-.025, 3):
        for sign in [-1, 1]:
            ET.SubElement(bodies['guitar'], 'geom', type='sphere', size='.008',
                pos=f'{sign*.048} {yy} -.014', rgba='.65 .65 .62 1',
                contype='0', conaffinity='0', group='1', density='0')
    output = OUT/'guitar_asset.xml';tree.write(output, encoding='unicode')
    old = ET.parse(BASE/'guitar_asset.xml').getroot()
    clean = lambda g: {k:v for k,v in g.attrib.items() if k != 'rgba'}
    checks = {'body_names_frames_exact': [b.attrib for b in old.findall('./worldbody//body')] == [b.attrib for b in root.findall('./worldbody//body')],
        'all_original_geom_physics_exact': all([clean(g) for g in b.findall('geom')] ==
            [clean(g) for g in bodies[b.get('name')].findall('geom')[:len(b.findall('geom'))]] for b in old.findall('./worldbody//body')),
        'all_added_geoms_visual_only': all(g.get('contype') == g.get('conaffinity') == '0' and g.get('density') == '0'
            for b in old.findall('./worldbody//body') for g in bodies[b.get('name')].findall('geom')[len(b.findall('geom')):]),
        'inputs_preserved': all(sha(path) == value for path,value in inputs.items())}
    assert all(checks.values()), checks
    result = dict(manifest)
    result.update(checks=checks, input_sha256=inputs, asset=str(output), asset_sha256=sha(output),
        visual_only=True, meshes=[dict(path=str(p), sha256=sha(p)) for p in OUT.iterdir() if p.is_file() and p!=output],
        physics_reference_asset=str(BASE/'guitar_asset.xml'),
        scope='smooth visual shell, procedural wood and painted soundhole/bridge; colliders unchanged; native validation pending')
    (OUT/'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    (RESULT/'build_v2.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(checks))


if __name__ == '__main__':
    main()
