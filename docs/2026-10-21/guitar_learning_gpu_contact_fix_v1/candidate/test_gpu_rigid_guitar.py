"""CPU checks of compound mass, original marker frames and COM velocities."""
import copy
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract


candidate = Path(__file__).with_name('rigid_guitar.py')
if candidate.exists():
    spec = importlib.util.spec_from_file_location('candidate_rigid_guitar', candidate)
    rigid = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rigid)
    rigid._ASSET_DIR = candidate.parent / 'assets'
    rigid._REPO_ROOT = next(p for p in candidate.parents if (p / 'guitar_learning').is_dir())
else:
    import guitar_learning.gpu.rigid_guitar as rigid


def pose(row):
    return (np.array([row['pose']['p'][a] for a in 'xyz']),
            Rotation.from_quat([row['pose']['r'][a] for a in 'xyzw']))


class RigidGuitarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_prepared_reset_contract()
        cls.guitar = rigid.RigidGuitar(cls.contract, 'cpu')

    def test_aggregate_preserves_mass_com_and_kinetic_energy(self):
        source = self.contract['initial']['guitar_properties']['applied']
        states = self.contract['state']['guitar_body_states']
        p0, r0 = pose(states[0])
        merged = self.guitar.body_properties[0]
        mass = sum(row['mass_kg'] for row in source)
        centers, inertias = [], []
        for row, state in zip(source, states):
            p, r = pose(state)
            centers.append(r0.inv().apply(p + r.apply(row['COM_body_m']) - p0))
            rotation = (r0.inv() * r).as_matrix()
            inertias.append(rotation @ np.array(row['inertia_COM_kg_m2']) @ rotation.T)
        center = sum(row['mass_kg'] * c for row, c in zip(source, centers)) / mass
        self.assertAlmostEqual(merged['mass_kg'], mass, places=12)
        np.testing.assert_allclose(merged['COM_body_m'], center, atol=1e-14)
        inertia = np.array(merged['inertia_COM_kg_m2'])
        self.assertTrue((np.linalg.eigvalsh(inertia) > 0).all())
        rng = np.random.RandomState(219)
        for _ in range(32):
            v, omega = rng.randn(3), rng.randn(3)
            direct = 0.
            for row, c, local_i in zip(source, centers, inertias):
                body_v = v + np.cross(omega, c - center)
                direct += .5 * row['mass_kg'] * np.dot(body_v, body_v) + .5 * omega @ local_i @ omega
            aggregate = .5 * mass * np.dot(v, v) + .5 * omega @ inertia @ omega
            self.assertAlmostEqual(direct, aggregate, places=12)

    def test_prepared_state_reconstructs_original_markers_and_velocities(self):
        saved = self.contract['state']
        logical = torch.tensor([rigid._body_row(r) for kind in ('human', 'guitar', 'chair')
                                for r in saved[kind + '_body_states']], dtype=torch.float32)
        native = torch.cat((logical[:66], self.guitar.prepared_root[None], logical[-1:]))[None].repeat(2, 1, 1)
        before = native.clone()
        expanded = self.guitar.expand(native)
        self.assertEqual(tuple(expanded.shape), (2, 106, 13))
        torch.testing.assert_close(expanded, logical.expand(2, -1, -1), atol=2e-7, rtol=0)
        self.assertTrue(torch.equal(native, before))
        self.assertTrue(torch.equal(expanded[:, :66], native[:, :66]))
        self.assertTrue(torch.equal(expanded[:, -1], native[:, -1]))

    def test_arbitrary_rigid_motion_gives_each_original_com_velocity(self):
        native = torch.zeros(2, 68, 13)
        native[:, :66] = 17.
        native[:, -1] = 23.
        root_q = Rotation.from_rotvec([.3, -.2, .8]).as_quat()
        native[0, 66] = torch.tensor([1., 2., .5, *root_q, .4, -.1, .2, 1., -2., .3])
        native[1, 66] = torch.tensor([-2., .4, 1.1, *root_q, -.2, .6, .1, -.3, 1., .8])
        expanded = self.guitar.expand(native).numpy()
        states = self.contract['state']['guitar_body_states']
        source = self.contract['initial']['guitar_properties']['applied']
        p0, r0 = pose(states[0])
        for env in range(2):
            root = native[env, 66].numpy()
            rotation = Rotation.from_quat(root[3:7])
            compound_com = root[:3] + rotation.apply(self.guitar.body_properties[0]['COM_body_m'])
            for index, (state, prop) in enumerate(zip(states, source)):
                p, r = pose(state)
                expected_p = root[:3] + rotation.apply(r0.inv().apply(p - p0))
                expected_r = rotation * r0.inv() * r
                com = expected_p + expected_r.apply(prop['COM_body_m'])
                velocity = root[7:10] + np.cross(root[10:13], com - compound_com)
                actual = expanded[env, 66 + index]
                np.testing.assert_allclose(actual[:3], expected_p, atol=4e-7)
                np.testing.assert_allclose(actual[7:10], velocity, atol=8e-7)
                np.testing.assert_allclose(actual[10:13], root[10:13], atol=0)
                self.assertLess((Rotation.from_quat(actual[3:7]).inv() * expected_r).magnitude(), 3e-7)
        self.assertTrue(np.all(expanded[:, :66] == 17.))
        self.assertTrue(np.all(expanded[:, -1] == 23.))

    def test_asset_has89_uniform_colliders_and_final_location_mesh_paths(self):
        xml = ET.parse(self.guitar.asset_path).getroot()
        self.assertEqual(len(xml.findall('.//body')), 1)
        geoms = xml.findall('./worldbody/body/geom')
        self.assertEqual(len(geoms), 101)
        self.assertEqual(sum(g.get('contype', '1') != '0' for g in geoms), 89)
        self.assertEqual(len(self.guitar.shape_properties), 89)
        unique = {tuple(sorted(row.items())) for row in self.guitar.shape_properties}
        self.assertEqual(len(unique), 1)
        self.assertEqual(self.guitar.shape_properties[0]['filter'], 4096)
        final = rigid._REPO_ROOT / self.guitar.manifest['final_asset_directory']
        for mesh in xml.findall('./asset/mesh'):
            self.assertTrue((final / mesh.get('file')).resolve().is_file())
        self.assertIn('chair/ground', self.guitar.manifest['proxy_collision_policy'])
        self.assertEqual(len(self.guitar.manifest['source_body_properties']), 39)

    def test_tampered_asset_or_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for name in ('guitar_compound.xml', 'manifest.json'):
                shutil.copyfile(rigid._ASSET_DIR / name, folder / name)
            with patch.object(rigid, '_ASSET_DIR', folder):
                (folder / 'guitar_compound.xml').write_bytes((folder / 'guitar_compound.xml').read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'asset SHA'):
                    rigid.RigidGuitar(self.contract, 'cpu')
                (folder / 'manifest.json').write_bytes((folder / 'manifest.json').read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'manifest SHA'):
                    rigid.RigidGuitar(self.contract, 'cpu')

    def test_changed_source_contract_and_wrong_native_layout_are_rejected(self):
        changed = copy.deepcopy(self.contract)
        changed['state']['guitar_body_states'][0]['vel']['linear']['x'] += .001
        with self.assertRaisesRegex(ValueError, 'pinned logical'):
            rigid.RigidGuitar(changed, 'cpu')
        with self.assertRaisesRegex(ValueError, 'compound-body state'):
            self.guitar.expand(torch.zeros(2, 106, 13))


if __name__ == '__main__':
    unittest.main()
