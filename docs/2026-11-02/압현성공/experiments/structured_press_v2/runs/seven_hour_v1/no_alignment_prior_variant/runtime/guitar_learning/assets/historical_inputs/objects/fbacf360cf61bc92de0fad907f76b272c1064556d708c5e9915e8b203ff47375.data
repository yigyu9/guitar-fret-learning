"""Reuse the frozen physics foundation with an explicit horizon and read-only hook."""
from .learning_scene_v2 import LearningScene
from .environment_contract_v1 import EnvironmentContract
import json
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]/'docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/trace.json'


def preload_targets(contract, factor):
    if factor not in (0., .5, 1.): raise ValueError('declared preload conditions only')
    rows = json.loads(BASE.read_text())
    q = np.array([r['q_rad'] for r in rows if r['physics_step'] >= 480])
    error = contract.q_ref-np.median(q,axis=0)
    caps = np.array([.15 if g=='arm' else .05 if g=='finger' else 0. for g in contract.groups])
    correction=np.clip(factor*error,-caps,caps)
    desired=np.clip(contract.q_ref+correction,contract.effective_lower,contract.effective_upper)
    return desired, {'factor':factor,'baseline':str(BASE),'median_error_rad':error.tolist(),
                     'requested_correction_rad':correction.tolist(),'bounded_targets_rad':desired.tolist()}


class DualMusicScene(LearningScene):
    def __init__(self, horizon_s):
        self.after_physics=None
        contract=EnvironmentContract()
        if not np.isfinite(horizon_s) or horizon_s <= 2: raise ValueError('physical horizon must exceed preparation')
        contract.config['diagnostic_seconds']=float(horizon_s)
        super().__init__(contract)

    def step_physics(self):
        super().step_physics()
        if self.after_physics is not None: self.after_physics(self)
