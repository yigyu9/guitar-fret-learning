"""Create a separate guitar MJCF whose actor origin is the body-box center."""
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'tab2body/assets/guitar_asset.xml'
ASSET = ROOT/'stability_adapter_2/assets/guitar_asset_body_root_v2.xml'


def vector(element):
    return [float(v) for v in element.get('pos', '0 0 0').split()]


def main():
    if ASSET.exists() or ASSET.with_suffix('.json').exists():
        raise FileExistsError('preserve the existing derived asset')
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    tree = ET.parse(SOURCE)
    model = tree.getroot()
    model.set('model', 'guitar_asset_body_root_v2')
    model.find('compiler').set('meshdir', os.path.relpath(SOURCE.parent/'mesh', ASSET.parent))
    guitar = model.find('worldbody/body')
    center = vector(guitar.find("body[@name='G:body']"))
    shifted = []
    for child in guitar:
        assert child.tag in ('body', 'geom'), child.tag
        old = vector(child)
        new = [p-c for p, c in zip(old, center)]
        child.set('pos', ' '.join(format(p, '.12g') for p in new))
        shifted.append({'tag': child.tag, 'name': child.get('name'), 'old_m': old, 'new_m': new})
    assert vector(guitar.find("body[@name='G:body']")) == [0., 0., 0.]
    header = '<!-- Separate body-centered guitar v2. Original model is preserved.\n'
    header += '  Old root -> body center offset: 0 -0.4 -0.0217 m.\n'
    header += '  World placement: p_new = p_old + R(q) * offset; q_new = q_old.\n'
    header += '  Body names/axes/geometry are preserved; geometry-less string markers\n'
    header += '  retain the original runtime mass/inertia requirements. -->\n'
    ASSET.write_text(header + ET.tostring(model, encoding='unicode') + '\n')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha
    ASSET.with_suffix('.json').write_text(json.dumps({
        'source': str(SOURCE), 'source_sha256': source_sha,
        'asset_sha256': hashlib.sha256(ASSET.read_bytes()).hexdigest(),
        'old_root_to_new_root_m': center, 'shifted_elements': shifted,
        'root_definition': 'G:body geometric center, not total center of mass',
        'world_pose_conversion': 'p_new=p_old+R(q)*c; q_new=q_old',
        'root_local_point_conversion': 'point_new=point_old-c',
        'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    }, indent=2) + '\n')
    print(ASSET)


if __name__ == '__main__':
    main()
