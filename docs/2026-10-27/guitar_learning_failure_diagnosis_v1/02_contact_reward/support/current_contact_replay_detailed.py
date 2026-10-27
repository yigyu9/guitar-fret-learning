"""Add read-only native force/pose fields to the preserved static replay."""
import hashlib
import json
from pathlib import Path
import sys

import current_contact_replay as replay

original_masks = replay.sample_masks


def detailed_masks(env,goals,indices):
    import torch
    result=original_masks(env,goals,indices)
    rows=torch.arange(len(goals),device=env.device)
    body=env.pad_indices[env.finger[indices]-1]
    result.update(assigned_distal_body_force_n=torch.linalg.vector_norm(env.snapshot['contact_force'][rows,body],dim=-1),
        assigned_distal_body_state=env.body[rows,body],guitar_root_state=env.guitar_body,
        wrist_shadow_elapsed_s=env.wrist_elapsed,wrist_shadow_severe_elapsed_s=env.wrist_severe_elapsed)
    return result


if __name__=='__main__':
    replay.sample_masks=detailed_masks
    replay.main()
    out=Path(sys.argv[sys.argv.index('--out')+1])
    payload=dict(change='read-only extra force/pose/timer fields; action, trajectory, predicates unchanged',
        launcher=str(Path(__file__).resolve()),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        base_script=str(Path(replay.__file__).resolve()),base_script_sha256=hashlib.sha256(Path(replay.__file__).read_bytes()).hexdigest())
    (out/'diagnostic_logging_adapter.json').write_text(json.dumps(payload,indent=2)+'\n')
