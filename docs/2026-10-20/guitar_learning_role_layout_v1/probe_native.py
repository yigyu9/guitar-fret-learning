"""Small deterministic native/reset record for dependency migration parity."""
from isaacgym import gymapi  # Must precede NumPy and project runtime imports.
import argparse
import json
from pathlib import Path
import numpy as np
from guitar_learning.runtime.prepared_reset_v1 import BASELINE_CONFIG
from guitar_learning.runtime.headless_session import HeadlessPreparedSession


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    config = json.loads(BASELINE_CONFIG.read_text())
    session = HeadlessPreparedSession(config, args.out/'scene', physics_threads=1)
    try:
        scene = session.scene
        samples = [scene.native()]
        target = scene.target.astype(float).copy()
        for _ in range(3):
            session.submit_policy_target(target)
            for _ in range(4):
                session.integrate()
            samples.append(scene.native())
        result = dict(samples=samples, loaded_assets=scene.loaded_assets,
            joint_names=scene.names, human_body_names=scene.human_bodies,
            guitar_body_names=scene.guitar_bodies,
            human_root_fixed=scene.human_root_fixed, guitar_root_fixed=scene.guitar_root_fixed,
            guitar_gravity_disabled=scene.guitar_gravity_disabled,
            pd={name:scene.pd_properties[name].tolist() for name in scene.pd_properties.dtype.names},
            target105=target.tolist(), physics_steps=scene.steps,
            modules={name:str(getattr(module,'__file__','')) for name,module in __import__('sys').modules.items()
                if name.startswith(('guitar_learning','stability_adapter_2','tab2body'))})
        (args.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print('Native parity probe complete: 3 policy ticks / 12 physics steps',flush=True)
    finally:
        session.close()


if __name__=='__main__': main()
