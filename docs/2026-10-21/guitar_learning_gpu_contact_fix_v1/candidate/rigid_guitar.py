"""Pinned compound guitar plus original logical marker states.

Conditional candidate:89 uniformly configured collision shapes; two proxy
collisions are intentionally excluded. Staging does not authorize adoption.
"""
import hashlib
import json
from pathlib import Path

import torch

from guitar_learning.gpu.geometry import apply, multiply


_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASSET_DIR = Path(__file__).resolve().parents[1] / 'assets/gpu_rigid_guitar_v1'
_MANIFEST_SHA256 = '7d6364593f2a8b15a91d690a4b9822f7857bf41f3efba0ff0a7252db50295001'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _body_row(row):
    return ([row['pose']['p'][a] for a in 'xyz'] + [row['pose']['r'][a] for a in 'xyzw'] +
            [row['vel'][kind][a] for kind in ('linear', 'angular') for a in 'xyz'])


class RigidGuitar:
    """One physical guitar body;39 logical bodies with original COM velocities."""
    def __init__(self, contract, device):
        manifest_path = _ASSET_DIR / 'manifest.json'
        if _sha(manifest_path) != _MANIFEST_SHA256:
            raise ValueError('Compound guitar manifest SHA mismatch')
        self.manifest = json.loads(manifest_path.read_text())
        self.asset_path = _ASSET_DIR / 'guitar_compound.xml'
        if _sha(self.asset_path) != self.manifest['asset_sha256']:
            raise ValueError('Compound guitar asset SHA mismatch')
        for relative, expected in self.manifest['source_sha256'].items():
            source = (_REPO_ROOT / relative).resolve()
            if _sha(source) != expected or contract['source_sha256'].get(str(source)) != expected:
                raise ValueError('Compound guitar source SHA mismatch: ' + relative)
        initial, saved = contract['initial'], contract['state']
        if (initial['guitar_body_names'] != self.manifest['logical_body_names'] or
                initial['guitar_properties']['applied'] != self.manifest['source_body_properties'] or
                _body_row(saved['guitar_body_states'][0]) != self.manifest['source_prepared_root']):
            raise ValueError('Compound guitar requires the pinned logical guitar contract')
        self.body_properties = self.manifest['body_properties']
        self.shape_properties = self.manifest['shape_properties']
        self.human_count = len(initial['human_body_names'])
        self.logical_count = len(initial['guitar_body_names'])
        self.device = torch.device(device)
        def tensor(value):
            return torch.tensor(value, dtype=torch.float32, device=self.device)
        self.prepared_root = tensor(self.manifest['prepared_root'])
        self._offsets = tensor(self.manifest['logical_position_root_m'])
        self._rotations = tensor(self.manifest['logical_quaternion_root_xyzw'])
        self._logical_com = tensor([r['COM_body_m'] for r in self.manifest['source_body_properties']])
        self._compound_com = tensor(self.body_properties[0]['COM_body_m'])

    def expand(self, native):
        """Expand[N,human+guitar1+chair,13] without host transfers or native writes.

        Native linear velocities are COM velocities. Every virtual guitar link
        therefore gets velocity at its own original COM, rather than origin.
        """
        if (native.ndim != 3 or native.shape[1:] != (self.human_count + 2, 13) or
                native.device != self.device or native.dtype != self.prepared_root.dtype):
            raise ValueError('Aligned float32 native compound-body state required')
        root = native[:, self.human_count:self.human_count + 1]
        guitar = root.expand(-1, self.logical_count, -1).clone()
        guitar[..., :3] = root[..., :3] + apply(root[..., 3:7], self._offsets[None])
        guitar[..., 3:7] = multiply(root[..., 3:7], self._rotations[None])
        original_com = guitar[..., :3] + apply(guitar[..., 3:7], self._logical_com[None])
        compound_com = root[..., :3] + apply(root[..., 3:7], self._compound_com)
        guitar[..., 7:10] = root[..., 7:10] + torch.cross(
            root[..., 10:13].expand_as(original_com), original_com - compound_com, dim=-1)
        return torch.cat((native[:, :self.human_count], guitar, native[:, -1:]), dim=1)
