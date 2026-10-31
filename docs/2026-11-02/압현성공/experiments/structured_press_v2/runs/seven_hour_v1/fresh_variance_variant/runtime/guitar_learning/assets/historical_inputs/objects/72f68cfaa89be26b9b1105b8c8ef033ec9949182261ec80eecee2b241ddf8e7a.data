"""Fresh validated noisy resets; exact native references and one PD owner."""
import copy
from unittest.mock import patch
from .deadline_native_v8 import NativeDeadlineEnvironment as Previous
from .initial_pose_noise_v1 import PoseBank,RANGES

class NativeInitialNoiseEnvironment(Previous):
    def __init__(self,bank_path,bank_index=None,**kwargs):
        super().__init__(**kwargs)
        self.bank=PoseBank(bank_path,self.seed);self.bank_index=bank_index
    def reset(self):
        from . import dual_music_scene_v1 as dual
        from .environment_contract_v1 import EnvironmentContract
        entry,selection=self.bank.sample(self.bank_index)
        old_preload=dual.preload_targets
        baseline=EnvironmentContract()
        base_target,base_record=old_preload(baseline,1.)
        correction=base_target-baseline.q_ref
        def preload(contract,factor):
            if factor!=1.:raise ValueError('noise version preserves factor1 preload')
            desired=contract.q_ref+correction
            desired=desired.clip(contract.effective_lower,contract.effective_upper)
            record=copy.deepcopy(base_record)
            record.update(noise_preload_rule='sample q_ref + original fixed-reference preload correction',bounded_targets_rad=desired.tolist(),requested_correction_rad=correction.tolist())
            return desired,record
        with patch.object(dual,'EnvironmentContract',lambda:EnvironmentContract(entry['config_path'])),patch.object(dual,'preload_targets',preload):
            obs=super().reset()
        self.noise_selection={**selection,'entry':entry}
        self.metadata['initial_pose_noise']=copy.deepcopy(self.noise_selection)
        self.metadata['physical_initial_noise']=True
        if self.output:
            from .initial_pose_noise_v1 import save
            save(self.run_output/'initial_noise_selection.json',{'selection':self.noise_selection,'preload':self.preload_record,'actual_initial':self.initial})
        return obs
    def abi(self):
        abi=super().abi()
        for e in self.bank.data['entries']:
            config=self.bank.data['configs'][e['config_path']]
            for p in (e['config_path'],config['initial_candidate'],config['native_reference']):abi['inputs'].pop(p,None)
        abi['inputs'].update(self.bank.inputs)
        abi.update(version='stability_support_nominal825_initial_noise_v1',initial_pose_noise={'ranges':RANGES,'bank':str(self.bank.path.resolve()),'sampling':'uniform discrete validated poses with replacement','body_head_finger_noise':False,'preload':'original fixed-reference correction + sample q_ref','state_writes':'reset construction only'})
        return abi
