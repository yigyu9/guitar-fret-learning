"""Command-feasible desiredactual bounds; finite fixed-e16 Motion2 inherited."""
from pathlib import Path
from types import FunctionType
from unittest.mock import patch
import numpy as np
from . import motion_v2 as previous_motion
from .motion_v2 import Motion as PreviousMotion,arm_checks
from .motion_v1 import stage_at
from guitar_learning.native.paths import read, sha

BIAS_BOUNDS_MODE='finite_desired_actual_intersect_command_bounds_held_plus_e16_v1'
DIAGNOSTIC_SHA='8e678b16e461cc97245322ca1497e95f757e16801b855687f68674b496b853c7'


def transformed_bounds(lower,upper,qref,arm,error):
    assert len(arm)==12 and error.shape==(12,) and np.isfinite(error).all()
    lo,hi=lower.copy(),upper.copy()
    lo[arm]=np.maximum.reduce([lower[arm],lower[arm]+error,qref[arm]-.8+error])
    hi[arm]=np.minimum.reduce([upper[arm],upper[arm]+error,qref[arm]+.8+error])
    effective_lo=np.maximum(lo[arm]+1e-6,qref[arm]-.8);effective_hi=np.minimum(hi[arm]-1e-6,qref[arm]+.8)
    assert np.isfinite(np.r_[effective_lo,effective_hi]).all() and np.all(effective_lo+1e-8<effective_hi-1e-8),'Empty transformed/interior interval'
    return lo,hi,effective_lo,effective_hi


class Motion(PreviousMotion):
    def __init__(self,scene,fk):
        assert scene.cfg['ready_hand_bias_bounds_mode']==BIAS_BOUNDS_MODE
        path=Path(scene.cfg['ready_hand_bias_bounds_diagnostic']).resolve()
        assert scene.cfg['ready_hand_bias_bounds_diagnostic_sha256']==DIAGNOSTIC_SHA and sha(path)==DIAGNOSTIC_SHA
        result=read(path);seed='held_plus_e16'
        assert result['inputs_unchanged'] is True and result['first3844'][seed]['passed'] is True
        assert set(result['grid_runs'])=={'native_baseline_v8','native_repeat_v8'}
        for case in result['grid_runs'].values():
            assert case['expected_samples']==719 and case['all_rows_by_seed'][seed] is True
            assert [r['step'] for r in case['rows']]==list(range(3844,6720,4))
            assert all(r['time_s']==r['step']/240 and r['seeds'][seed]['passed'] is True for r in case['rows'])
        assert result['source_geometry_computed'] is False and result['new_native_steps']==0
        assert result['actual_dynamic_tracking_validated'] is False and result['final_adoption_eligible'] is False
        super().__init__(scene,fk)
        self.bias_diagnostic=str(path);self.bias_proof=None

    def apply(self,named):
        self.bias_proof=None;s=self.s
        if s.steps<=3840:return super().apply(named)
        original=previous_motion.solve_left;code=original.__code__;wrist=original.__globals__['solve_wrist'];state=s.native()
        applies=bool(s.steps>3840 and stage_at(self.plan,s.steps/240)=='gripped')
        def bounded(fk,q,indices,lower,upper,qref,goal,rotation,seed):
            error=np.array(self.reference16['e16_12_rad']);lo,hi,elo,ehi=transformed_bounds(lower,upper,qref,indices,error)
            mapped=seed+error;optimizer_seed=np.clip(mapped,elo+1e-8,ehi-1e-8);other=np.setdiff1d(np.arange(105),indices)
            proof=dict(mode=BIAS_BOUNDS_MODE,applies=True,solver_calls=0,request_scope='postMotion_preFoot_preRate',
                diagnostic=self.bias_diagnostic,diagnostic_sha256=DIAGNOSTIC_SHA,arm_indices105=indices.tolist(),e16_12_rad=error.tolist(),
                original_lower12_rad=lower[indices].tolist(),original_upper12_rad=upper[indices].tolist(),
                transformed_lower12_rad=lo[indices].tolist(),transformed_upper12_rad=hi[indices].tolist(),
                effective_lower12_rad=elo.tolist(),effective_upper12_rad=ehi.tolist(),held_seed12_rad=seed.tolist(),mapped_seed12_rad=mapped.tolist(),optimizer_seed12_rad=optimizer_seed.tolist(),
                seed_projection_scope='Original optimizer start projection only; no final target clipping',
                solver_call_scope='Bounded gripped maintenance only; parent IK inherited',
                bounds_copy_other93_exact=bool(lo[other].tobytes()==lower[other].tobytes() and hi[other].tobytes()==upper[other].tobytes()))
            self.bias_proof=proof
            def observe(*args):
                proof['solver_calls']+=1;answer=wrist(*args);proof['desired64_rad']=answer[0].tolist();return answer
            namespace=original.__globals__.copy();namespace['solve_wrist']=observe
            assert all(namespace[k] is (observe if k=='solve_wrist' else v) for k,v in original.__globals__.items())
            clone=FunctionType(code,namespace,original.__name__,original.__defaults__,original.__closure__)
            desired,fit=clone(fk,q,indices,lo,hi,qref,goal,rotation,mapped);raw=np.array(proof['desired64_rad'])
            command_raw=desired-error;command=command_raw.astype(np.float32).astype(float)
            guards=dict(raw_desired=arm_checks(raw,s,indices),raw_desired_effective=bool(np.all(raw>=elo) and np.all(raw<=ehi)),
                desiredF32_transformed=bool(np.all(desired>=lo[indices]) and np.all(desired<=hi[indices])))
            proof.update(desiredF32_rad=desired.tolist(),command_raw12_rad=command_raw.tolist(),commandF32_rad=command.tolist(),guards=guards,
                original_code_object_unchanged=original.__code__ is code,original_wrist_binding_unchanged=original.__globals__['solve_wrist'] is wrist,
                cloned_code_object_same=clone.__code__ is code,only_copied_wrist_global_changed=all(namespace[k] is (observe if k=='solve_wrist' else v) for k,v in original.__globals__.items()))
            assert proof['solver_calls']==1 and all(guards['raw_desired'].values()) and guards['raw_desired_effective'] and guards['desiredF32_transformed']
            assert proof['bounds_copy_other93_exact'] and proof['original_code_object_unchanged'] and proof['original_wrist_binding_unchanged'] and proof['cloned_code_object_same'] and proof['only_copied_wrist_global_changed']
            return desired,fit
        try:
            if applies:
                with patch.object(previous_motion,'solve_left',bounded):result=super().apply(named)
            else:result=super().apply(named)
        finally:
            assert previous_motion.solve_left is original and original.__code__ is code and original.__globals__['solve_wrist'] is wrist
            assert s.native()==state
            if self.bias_proof is not None:self.bias_proof.update(binding_restored=True,state_preserved=True)
        if s.steps>3840:
            if applies and not self.info['hand_maintenance']['boundary']:
                assert self.bias_proof is not None
                hm=self.info['hand_maintenance'];assert np.array_equal(hm['desired_actual12_rad'],self.bias_proof['desiredF32_rad'])
                assert np.array_equal(hm['raw_command12_rad'],self.bias_proof['command_raw12_rad']) and np.array_equal(hm['command12_rad'],self.bias_proof['commandF32_rad'])
                hm['bias_bounds']=self.bias_proof
            else:
                assert self.bias_proof is None
                self.info['hand_maintenance']['bias_bounds']=dict(mode=BIAS_BOUNDS_MODE,applies=False,solver_calls=0,request_scope='postMotion_preFoot_preRate',binding_restored=True,state_preserved=True,solver_call_scope='Bounded maintenance only; parent IK inherited')
        return result
