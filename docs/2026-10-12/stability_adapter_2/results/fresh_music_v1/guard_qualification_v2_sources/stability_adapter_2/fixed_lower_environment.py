"""Physically fixed lower links; ordinary dynamic upper-body joints and free guitar."""
from pathlib import Path

from .environment import InitialEnvironment, np
from .build_fixed_lower_asset import ASSET, MANIFEST, REFERENCE, read, sha, pose


class FixedLowerEnvironment(InitialEnvironment):
    instance = None

    def __init__(self, initial_settings=None):
        FixedLowerEnvironment.instance = self
        manifest = read(MANIFEST)
        if sha(ASSET)!=manifest['asset_sha256'] or not all(manifest['checks'].values()):
            raise ValueError('fixed lower asset manifest mismatch')
        for path, expected in manifest['input_sha256'].items():
            if sha(Path(path))!=expected:
                raise ValueError('fixed lower asset input changed: '+path)
        # These 24 coordinates are encoded into fixed links, no longer live DOFs.
        settings = dict(initial_settings or {})
        settings['joint_angles_rad'] = {name:value for name,value in settings.get('joint_angles_rad',{}).items()
            if name not in manifest['removed_joint_names']}
        super().__init__(settings)
        try:
            reference = read(REFERENCE/'report.json')
            previous = read(REFERENCE/'states.json')[0]
            expected = dict(zip(reference['human_body_names'],previous['human_body_states']))
            actual = self.bodies(self.human)
            errors = {}
            for name in self.human_bodies:
                p,q = pose(expected[name]); bp,bq = pose(actual[self.human_bodies.index(name)])
                q /= np.linalg.norm(q); bq /= np.linalg.norm(bq)
                errors[name] = {'position_m':float(np.linalg.norm(p-bp)),
                    'rotation_deg':float(np.degrees(2*np.arccos(np.clip(abs(q@bq),0,1))))}
            self.initial_pose_errors = errors
            self.lock_checks = {'81_live_dofs':len(self.names)==81,'66_main_9_torso':len(self.main_indices)==66 and len(self.torso_indices)==9,
                'no_live_lower_dofs':len(self.leg_indices)==0,
                'remaining_dof_name_order_preserved':self.names==[n for n in reference['human_joint_names'] if n not in manifest['removed_joint_names']],
                'all_body_names_preserved':self.human_bodies==reference['human_body_names'],
                'human_root_fixed':self.human_root_fixed,
                'guitar_free_with_gravity':not self.guitar_root_fixed and not self.guitar_gravity_disabled,
                'initial_body_poses_match':max(e['position_m'] for e in errors.values())<1e-5 and max(e['rotation_deg'] for e in errors.values())<.01}
            # Baseline C02 initialization supplies unchanged upper reference angles;
            # selected trial initialization is validated separately in the wrapper.
            if not all(v for k,v in self.lock_checks.items() if k!='initial_body_poses_match'):
                raise AssertionError(self.lock_checks)
        except Exception:
            self.close()
            raise

    def _create_scene(self):
        self.config['humanoid_asset'] = str(ASSET)
        super()._create_scene()
