"""Exercise readonly Fret ABI/tensor seams against a preserved real native snapshot."""
from .environment import ROOT, np
from .run_fret_native_connection_v2 import CHECKPOINT, GOAL, HAND_TARGETS, json_plain
from .fret_native_view_v2 import create_fret_view
from .strike_native_view import state_rows
from tab2body.tools.fret_rollout_contract import verify_rollout_model
from tab2body.learning.fret_v2_model import FretV2ActorCritic
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
import argparse
import json
import torch


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    source=ROOT/'docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/initial_values.json'
    data=json.loads(source.read_text());state=data['native_initial_state']
    fields=list(data['PD_properties'][0]);dtype=[(k,'?' if k=='hasLimits' else ('i4' if k=='driveMode' else 'f4')) for k in fields]
    props=np.array([tuple(r[k] for k in fields) for r in data['PD_properties']],dtype=dtype)
    class FakeGym:
        def get_actor_dof_properties(self,*args):return props.copy()
        def __getattr__(self,n):raise AssertionError('unexpected simulator call '+n)
    env=SimpleNamespace(names=data['joint_names'],human_bodies=data['human_body_names'],guitar_bodies=data['guitar_body_names'],
        initial_q=np.array(data['initial_angles_rad'],dtype=np.float32),target=np.array(data['initial_angles_rad'],dtype=np.float32),
        lower=np.array(data['native_lower_rad'],dtype=np.float32),upper=np.array(data['native_upper_rad'],dtype=np.float32),
        pose=json.loads((ROOT/'tab2body/assets/seated_pose.json').read_text()),gym=FakeGym(),env=None,human=None,
        self_collision_policy=data['self_collision_policy'])
    def refresh(view,owner):
        view.dof_state.copy_(torch.tensor([[r['pos'],r['vel']] for r in state['human_dof_states']]))
        h,g=state_rows(state['human_body_states']),state_rows(state['guitar_body_states'])
        view.body_state.copy_(torch.cat([h,g]));view.root_state.copy_(torch.stack([h[0],g[0]]))
        view.contact_force.zero_()  # explicitly mock observation input; not measured force
    checkpoint=torch.load(CHECKPOINT,map_location='cpu',weights_only=True)
    with patch('stability_adapter_2.strike_native_view.refresh_native',refresh):
        view,payload=create_fret_view(env,checkpoint,GOAL,HAND_TARGETS)
    model=FretV2ActorCritic(420,30,6,init_std=payload['model']['policy_init_std']);verify_rollout_model(view,model,payload)
    model.load_state_dict(checkpoint['model'],strict=True);model.eval()
    view.preparation_remaining.zero_()
    before=view.dof_state.clone();bodies=view.body_state.clone();roots=view.root_state.clone()
    obs=view.strict_observation()
    with torch.no_grad():action=model.act(obs,deterministic=True)[0]
    view.cache_policy_actions(action)
    checks={'contract':True,'finite420':obs.shape==(1,420) and bool(torch.isfinite(obs).all()),
        'finite30':action.shape==(1,30) and bool(torch.isfinite(action).all()),
        'cached_actions_preserve_state':torch.equal(before,view.dof_state) and torch.equal(bodies,view.body_state),
        'cached_target_profile':bool(((view.pd_target[view.ctrl_idx]>=view.ctrl_lo[0])&(view.pd_target[view.ctrl_idx]<=view.ctrl_hi[0])).all())}
    # Current-guitar observation must respond to a copied 10mm guitar translation.
    view.body_state[view.n_hbody:,:3]+=torch.tensor([.01,0.,0.]);view.root_state[1,:3]+=torch.tensor([.01,0.,0.])
    shifted=view.strict_observation();delta=float((shifted-obs).abs().max())
    checks['moving_guitar_observation']=delta>.001
    view.body_state.copy_(bodies);view.root_state.copy_(roots)
    view.progress_buf+=1
    result=view.evaluate_after_physics()
    checks['postphysics_tail_returns']=len(result)==4 and result[2].shape==(1,)
    checks['postphysics_tail_preserves_state']=torch.equal(before,view.dof_state) and torch.equal(bodies,view.body_state)
    for forbidden in (lambda:view.step(action),lambda:view.apply_actions(action),lambda:view.reset(),lambda:view.step_physics()):
        try:forbidden()
        except RuntimeError:pass
        else:raise AssertionError('shared physics guard lost')
    checks['shared_physics_guards']=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({'checks':checks,'scope':'mock simulator on preserved native t0; no physical rollout; contact forces mocked zero',
        'observation_translation_max_delta':delta,'source_info':json_plain(result[3])},indent=2)+'\n')
    assert all(checks.values()),checks
    print(checks)


if __name__=='__main__':main()
