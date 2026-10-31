"""739D measured state, authored targets and detector memory; no teacher actions."""
import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from .dual_music_clock_v1 import JointMusicClock, BUNDLE
from .environment_contract_v1 import EnvironmentContract


ROOT = Path(__file__).resolve().parents[1]
BLOCKS = (('physical_core',548),('joint_music',28),('target_crossing_delta_s',6),
          ('required_strings',6),('direction_down_up',2),('event_start_end_delta_s',2),
          ('measured_press_cells',132),('pick_detector_state',6),('pick_rearm_progress',6),
          ('previous_pick_tip_G',3))


def compose(physical, music, cells, detector_state, rearm_progress, previous_tip):
    event, time = music.current(), music.time()
    required, timing, direction, boundaries = np.zeros(6),np.zeros(6),np.zeros(2),np.zeros(2)
    if event is not None:
        for target in event.string_targets:
            if target.string in event.strike.audible_strings:
                required[target.string] = 1
                timing[target.string] = event.score_time_s+target.traversal_offset_s-time
        direction[0 if event.strike.direction=='down' else 1] = 1
        boundaries[:] = [event.score_time_s-time,event.traversal_end_time_s-time]
    values = (physical,music.observation(),timing,required,direction,boundaries,
              np.asarray(cells).reshape(-1),detector_state,rearm_progress,previous_tip)
    blocks,manifest,offset = [],[],0
    for (name,size),value in zip(BLOCKS,values):
        value = np.asarray(value,dtype=np.float32)
        if value.shape != (size,) or not np.isfinite(value).all():
            raise ValueError('finite real observation required: '+name)
        if name=='measured_press_cells' and not np.isin(value,[0,1]).all():
            raise ValueError('binary measured press cells required')
        blocks.append(value)
        manifest.append({'name':name,'offset':offset,'length':size,'dtype':'float32'})
        offset += size
    return np.concatenate(blocks), {'version':'upper81_music739_v1','dimension':offset,'blocks':manifest,
                                    'teacher_action_inputs':False,'future_actual_outcome_inputs':False}


class JointMusicMeasurement:
    def __init__(self, scene):
        import torch
        from .fret_native_view_v2 import create_fret_view
        from . import strike_native_view
        from .dual_strike_evaluator_v1 import DualStrikeView
        from .dual_strike_contract_guard_v1 import verify_strike_inputs,verify_strike_view
        from .run_joint_hold import native_state
        self.scene, self.music = scene, JointMusicClock()
        fcp=ROOT/'fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt'
        scp=ROOT/'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt'
        fg=BUNDLE/'training/fret_training.json';ht=BUNDLE/'training/hand_position_targets.json'
        sg=BUNDLE/'training/strike_plan.json';grip=ROOT/'strike/02_physical_control/pick-grip-reference.json'
        before=native_state(scene)
        fc=torch.load(fcp,map_location='cpu',weights_only=True)
        sc=torch.load(scp,map_location='cpu',weights_only=True)
        checked=verify_strike_inputs(sc,sg,grip)
        self.fret,fp=create_fret_view(scene,fc,fg,ht)
        with patch.object(strike_native_view,'NativeStrikeView',DualStrikeView):
            self.strike=strike_native_view.create_view(scene,sc,sg,grip)
        verify_strike_view(checked,self.strike)
        if native_state(scene)!=before: raise AssertionError('measurement creation changed physics')
        self.music.dwell_s=self.fret.reward_fn.press_hold_min_frames/60
        self.detector=copy.deepcopy(self.strike.detector)
        self.detector.rearm_min_frames*=4
        self.inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (fcp,scp,fg,ht,sg,grip)}
        self.samples=[]
        self.refresh()
        self.cells,self.sounding,self.previous_tip=self.geometry()
        self.music.sounding=self.sounding.copy()
        self.scene.after_physics=self.measure

    def refresh(self):
        from .strike_native_view import refresh_native
        from .run_joint_hold import native_state
        before=native_state(self.scene)
        for view in (self.fret,self.strike): refresh_native(view,self.scene)
        if native_state(self.scene)!=before: raise AssertionError('measurement refresh changed physics')

    def geometry(self):
        import torch
        from tab2body.full.readiness import evaluate_sounding_fret_readiness
        cells=self.fret.reward_fn.refresh_press_state()
        readiness=evaluate_sounding_fret_readiness(cells,torch.tensor(self.music.targets())[None])
        tip=self.strike.to_guitar_frame(self.strike.hbody_pos('RH:pick')[:,None])[:,0]
        return cells[0].numpy().copy(),readiness.effective_sounding_fret[0].numpy().copy(),tip.clone()

    def measure(self, owner):
        self.refresh()
        self.cells,self.sounding,tip=self.geometry()
        start,end=self.strike.string_segments_g()
        result=self.detector.step(self.previous_tip,tip,start,end,dt=1/240)
        releases=[(s,float(result['subframe_t'][0,s]),int(result['direction'][0,s]),
                   bool(result['zone_allowed'][0,s])) for s in range(6) if bool(result['release'][0,s])]
        self.music.update(owner.steps,self.sounding,releases)
        self.previous_tip=tip
        self.samples.append({'physics_step':owner.steps,'sounding_fret':self.sounding.tolist(),
                             'press_cells':np.argwhere(self.cells).tolist(),
                             'raw_release':result['release'][0].tolist(),
                             'zone_allowed':result['zone_allowed'][0].tolist(),
                             'detector_state':self.detector.state[0].tolist(),
                             'wait_frames':self.detector.wait_frames[0].tolist()})

    def observe(self, physical):
        if self.music.physics_step!=self.scene.steps: raise AssertionError('observation timestamp mismatch')
        rearm=(self.detector.wait_frames[0].numpy()/self.detector.rearm_min_frames).clip(0,1)
        observation,manifest=compose(physical,self.music,self.cells,self.detector.state[0].numpy(),rearm,
                                     self.previous_tip[0].numpy())
        manifest['physical_manifest']=self.scene.observation_manifest
        return observation,manifest


TRAINING_BLOCKERS = ('SO3_allowed_set_distance_not_certified','continuous_hold_and_dropout_ledger_not_certified',
                     'fatal_scheduled_tail_and_discount_not_certified','distal_press_pad_contract_not_certified',
                     'reward_v5_terms_and_measurement_masks_not_certified')


def require_native_training_ready():
    raise RuntimeError('native joint PPO disabled until reward contract closes: '+', '.join(TRAINING_BLOCKERS))
