"""One original note/row, actual 240Hz clock and unmodified nine-term ledger.

Diagnostic phrase offsets align the original press time with local3s; original
onset/end/required and physical/wrist terminations remain unchanged. Only each
row's first episode counts. Later normal API resets keep the batch runnable.
"""
import argparse
import copy
import json
from pathlib import Path
import time
from current_contact_replay import sample_masks

ROOT=Path('/home/ajou/yigyu/3')
BASE=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--geometry',type=Path,required=True)
    p.add_argument('--mode',choices=('fixed','free'),required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--other-fingers',choices=('B',),default='B')
    args=p.parse_args()
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.simplified_finger_environment import SimplifiedFingerEnvironment,REWARD_TERMS
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.finger_reward import B_PREPARATION_INPUT_DEGREES,B_PREPARATION_SPREAD_DEGREES
    from guitar_learning.training.start import settings_document
    from guitar_learning.training.recording import active_source_paths
    from guitar_learning.tool.validation.press_acquisition import sha,write,trajectory_actions
    torch.set_num_threads(1)
    candidates=json.loads((args.geometry/'candidates.json').read_text());goals=candidates['goals'];n=len(goals)
    rows=torch.arange(n,device='cuda:0');indices=torch.tensor([g['source_note_index'] for g in goals],device='cuda:0')
    pins=json.loads((args.geometry/'inputs_before.json').read_text())
    if any(sha(k)!=v for k,v in pins.items()):raise ValueError('Geometry sources changed')
    pins.update({str(q.resolve()):sha(q) for q in active_source_paths(ROOT/'guitar_learning')})
    pins.update({str(q.resolve()):sha(q) for q in (Path(__file__),args.geometry/'candidates.json',args.geometry/'targets.json')})
    pins.update({str(q.resolve()):sha(q) for q in Path(__file__).parent.glob('*.py')})
    args.out.mkdir(parents=True,exist_ok=False);write(args.out/'inputs_before.json',pins)
    settings=settings_document(num_envs=n,size='large',updates=1)
    protocol=dict(diagnostic_only=True,training_success=False,guitar_mode=args.mode,other_fingers='B',
        comparison='actual original-note clock/ledger; not static midpoint and not full-song evaluation',
        scope='one original target per precommitted row; b1; source press maps to local3s via explicit phrase offset',
        preparation='0.5s reference hold then simultaneous2s source-q/B ramp, bounded point+wrist feedback from2.5s to original note end',
        terminations='physical and wrist unchanged; first episode includes failure; resets only after completed boundaries',
        state_writes='normal prepared episode resets only; finite39 actions thereafter')
    write(args.out/'settings.json',protocol)
    scene=None;trace=[];control=[];episodes=[None]*n;failure=None;started=time.monotonic();report=None
    try:
        scene=GpuScene(n,'left',device='cuda:0',out=args.out,diagnostic_guitar_mode=args.mode)
        controller=BatchedController(scene,finger_action_mode='incremental')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(controller.contract)
        class SelectedNoteEnvironment(SimplifiedFingerEnvironment):
            def _reset_scope(self,ids):
                super()._reset_scope(ids)
                chosen=indices[ids]
                self.focus_mask[ids]=False;self.focus_mask[ids,chosen]=True
                self.finger_weights[ids]=self.focus_mask[ids].to(self.finger_weights.dtype)
                self.score_offset[ids]=self.press[chosen]-3.
                self.view_first[ids]=self.press[chosen];self.view_last[ids]=self.end[chosen]
                self.duration_ticks[ids]=torch.ceil((self.end[chosen]-self.score_offset[ids]+settings['song']['tail_s'])*60-1e-9).long()
                self.recovery_mask[ids]=self.focus_mask[ids]
                for finger in range(1,5):
                    owned=self.focus_mask[ids]&(self.finger==finger)[None]
                    last=self.end.expand(len(ids),-1).masked_fill(~owned,-torch.inf).amax(-1)
                    last=torch.where(owned.any(-1),last,self.view_first[ids])
                    future=(self.finger==finger)[None]&~self.focus_mask[ids]&(self.press[None]>=last[:,None])
                    following=self.press.expand(len(ids),-1).masked_fill(~future,torch.inf).argmin(-1)
                    has=future.any(-1);self.recovery_mask[ids[has],following[has]]=True
                for row in ids.cpu().tolist():self.phrase_ids[row]='diagnostic-original-note-%d'%indices[row].item()
        env=SelectedNoteEnvironment(metadata,bundle=candidates['bundle'],song=settings['song'],skill=settings['finger_skill'],device='cuda:0')
        sample=scene.snapshot();controller.reset(rows,sample);env.reset(rows,sample)
        write(args.out/'metadata.json',metadata);write(args.out/'contract.json',env.contract)
        write(args.out/'scope.json',dict(indices=indices.tolist(),target_ids=[g['target_id'] for g in goals],
            original_press_s=env.press[indices].tolist(),original_onset_s=env.onset[indices].tolist(),original_end_s=env.end[indices].tolist(),
            original_required_s=env.required[indices].tolist(),score_offset_s=env.score_offset.tolist(),duration_ticks=env.duration_ticks.tolist(),
            focus_mask=env.focus_mask.tolist(),recovery_mask=env.recovery_mask.tolist(),reward_terms=list(REWARD_TERMS),approach_gamma=env.approach_gamma))
        reference=controller.reference[controller.active];requested=torch.tensor([g['q_target105'] for g in goals],device='cuda:0')[:,controller.active]
        release=reference.expand(n,-1).clone();initial=controller.target[:,controller.active].clone()
        for row,goal in enumerate(goals):
            for f,name in enumerate(('index','middle','ring','pinky')):
                if f+1==goal['finger']:continue
                values=(B_PREPARATION_INPUT_DEGREES[f][0],B_PREPARATION_SPREAD_DEGREES[f],B_PREPARATION_INPUT_DEGREES[f][1],B_PREPARATION_INPUT_DEGREES[f][2])
                for suffix,degrees in zip(('1_x','1_z','2','3'),values):
                    channel=ACTIVE_NAMES.index('LH:'+name+suffix);requested[row,channel]=release[row,channel]=degrees*np.pi/180
        incremental=torch.tensor([name.startswith('LH:') for name in ACTIVE_NAMES],device='cuda:0')
        first_live=np.ones(n,dtype=bool);last_valid=scene.efforts.clone();maximum_ticks=int(env.duration_ticks.max().item())
        for tick in range(maximum_ticks+2):
            local=env._local_time();end_local=env.end[indices]-env.score_offset
            ramp=((local+1/60-.5)/2).clamp(0,1).float()
            nominal=initial+(requested-initial)*ramp[:,None]
            release_fraction=((local+1/60-end_local)/2).clamp(0,1).float()
            nominal=nominal+(release-requested)*release_fraction[:,None]
            actions=trajectory_actions(nominal,controller.target[:,controller.active],reference,controller.action_low,controller.action_high,incremental,max_speed=1.)
            actions[:,33:]=0;env.begin_control(actions);target=controller.targets(actions,sample)
            before_potential=env.before_surface_potential.clone();accepted=first_live.copy()
            for sub in range(4):
                efforts=controller.efforts(sample);checks=controller.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):raise RuntimeError('Invalid support controller')
                env.invalidate_control(~checks['chest_normal_defined'])
                efforts=torch.where(env.control_invalid[:,None],last_valid,efforts);last_valid.copy_(efforts)
                sample=scene.step(target,efforts);env.substep(sample)
                masks=sample_masks(env,goals,indices)
                trace.append(dict(physics_step=np.asarray(scene.physics_steps),episode_step=env.clock.cpu().numpy(),valid=accepted.copy(),
                    score_time_s=env._score_time().cpu().numpy(),candidate=env.candidate[rows,indices].cpu().numpy(),
                    positive_before_wrong=(env.contact_facing[rows,indices]&env.surface_body_loaded[rows,indices]).cpu().numpy(),
                    wrong=env.wrong[rows,indices].cpu().numpy(),wrist_excess_m=env.guide['delta'].abs().amax(-1).cpu().numpy(),
                    wrist_failure=(env.wrist_failure|env.wrist_severe_failure).cpu().numpy(),
                    body_force_n=masks['assigned_distal_body_force_n'].cpu().numpy()))
            observation,reward,cost,done,_,completed=env.end_control()
            control.append(dict(physics_step=np.asarray(scene.physics_steps),valid=accepted.copy(),
                local_time_s=env._local_time().cpu().numpy(),score_time_s=env._score_time().cpu().numpy(),
                candidate=env.candidate[rows,indices].cpu().numpy(),q105_rad=scene.q.cpu().numpy(),target105_rad=target.cpu().numpy(),action39=actions.cpu().numpy(),
                reward=reward.cpu().numpy(),cost=cost.cpu().numpy(),done=done.cpu().numpy(),
                potential_before=before_potential.cpu().numpy(),potential_after=env._surface_potential().cpu().numpy(),
                note_clean_s=env.note['clean'][rows,indices].cpu().numpy(),note_wrong_s=env.note['wrong'][rows,indices].cpu().numpy(),
                note_missing_s=env.note['missing'][rows,indices].cpu().numpy(),note_best_streak_s=env.note['best_clean_streak'][rows,indices].cpu().numpy(),
                contact_progress=env.note['contact_progress'][rows,indices].cpu().numpy(),
                performance_paid=env.note['performance_paid'][rows,indices].cpu().numpy(),performance_settled=env.note['performance_settled'][rows,indices].cpu().numpy(),
                achieved=env.note['left'][rows,indices].cpu().numpy(),
                **{'reward_'+key:env.episode_reward_terms[key].cpu().numpy() for key in REWARD_TERMS}))
            for episode in completed:
                row=episode['env_id']
                if first_live[row]:episodes[row]=episode;first_live[row]=False
            if tick%60==0:print('ledger tick',tick+1,'first_alive',int(first_live.sum()),flush=True)
            if not first_live.any():break
            reset_ids=done.nonzero().flatten()
            if len(reset_ids):
                sample=scene.reset(reset_ids);last_valid[reset_ids]=0;controller.reset(reset_ids,sample);env.reset(reset_ids,sample)
        report=dict(completed=all(v is not None for v in episodes),protocol=protocol,episodes=episodes,control_ticks=tick+1,
            physics_steps=scene.physics_steps,no_song_ledger_payments=False,training_success=False)
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        for name,records in (('trace240.npz',trace),('control60.npz',control)):
            if records:np.savez_compressed(args.out/name,**{k:np.stack([v[k] for v in records]) for k in records[0]})
        if scene:scene.close()
        changed=[p for p,v in pins.items() if sha(p)!=v]
        report=dict(report or {},completed=bool(report and report['completed'] and not failure and not changed and scene and scene.diagnostics['closed']),
            failure=failure,changed_inputs=changed,scene=scene.diagnostics if scene else None,wall_s=time.monotonic()-started)
        write(args.out/'report.json',report)
    if not report['completed']:raise RuntimeError('Ledger diagnostic audit failed')
    print('COMPLETE ledger',args.out,flush=True)

if __name__=='__main__':main()
