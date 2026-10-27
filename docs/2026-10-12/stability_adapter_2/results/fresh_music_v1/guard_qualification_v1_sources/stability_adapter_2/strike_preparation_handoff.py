"""Seed source control history without changing the prepared event or lane."""
import torch


def seed_source_history(view, applied_targets):
    geometry = [v.clone() for v in view._current_target_geometry()]
    view.pd_target.copy_(torch.tensor(applied_targets.copy()))
    view.prev_action.copy_(view.actions_for_pd_targets(view.pd_target[view.ctrl_idx][None]))
    view._previous_tip_g.copy_(view.to_guitar_frame(view.hbody_pos('RH:pick')[:, None])[:, 0])
    view._previous_tip_valid.fill_(True)
    unchanged = all(torch.equal(a, b) for a, b in zip(geometry, view._current_target_geometry()))
    if not unchanged:
        raise RuntimeError('preparation handoff changed source target geometry')
    return unchanged
