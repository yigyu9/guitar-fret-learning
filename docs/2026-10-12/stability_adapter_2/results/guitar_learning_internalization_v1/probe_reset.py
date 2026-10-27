"""Two real reset episodes through one migrated native scene, no legacy reads."""
import isaacgym
import argparse
import json
from pathlib import Path
from guitar_learning.prepared_reset_v1 import BASELINE_CONFIG
from guitar_learning.persistent_session import PersistentHeadlessPreparedSession

parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
args.out.mkdir(exist_ok=False,parents=True)
config=json.loads(BASELINE_CONFIG.read_text())
session=PersistentHeadlessPreparedSession(config,args.out/'episode_000')
try:
    initial=session.scene.native()
    identities=session._native_identities()
    target=session.scene.target.astype(float).copy()
    session.submit_policy_target(target)
    for _ in range(4):session.integrate()
    session.reset_episode(config,args.out/'episode_001')
    restored=session.scene.native()
    assert initial==restored
    assert identities==session._native_identities()
    assert session.scene.forbidden_calls==[]
    assert session.scene.persistent_native_calls['create_sim']==1
    assert session.scene.persistent_native_calls['create_env']==1
    result=dict(completed=True,episodes=2,physics_steps_before_reset=4,
        reset_native_state_exactly_equal=True,scene_identity_unchanged=True,
        diagnostics=session.prepared_reset_description['persistent_reset'])
finally:session.close()
result['closed_lifecycle']=json.loads((args.out/'persistent_lifecycle.json').read_text())
(args.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('Migrated persistent scene reset passed',flush=True)
