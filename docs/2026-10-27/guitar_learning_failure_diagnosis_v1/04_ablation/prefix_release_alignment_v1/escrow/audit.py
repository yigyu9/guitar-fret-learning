"""CPU only: proposed A-success escrow alongside unchanged prescribed ledgers."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parents[1] / 'prefix_release_objective_v1'


def fresh():
    return dict(seen=False, pending=0., paid=0., expired=False, failed=False)


def settle(state, *, now, end, achieved=False, released=False, release_s=0.,
           failed=False, reset=False, ended=False, budget=.25):
    """One episode/one original control. No reward or native state is changed."""
    assert budget >= 0
    if reset:
        return fresh(), 0., state['pending']  # Old pending is forfeited, never transferred.
    s = dict(state); payout = forfeited = 0.
    s['failed'] |= failed
    if achieved and not s['seen']:
        s['seen'] = True
        s['pending'] = budget
    if s['pending']:
        if s['failed'] or ended:
            forfeited = s['pending']; s['pending'] = 0.; s['expired'] = True
        elif released and end <= release_s <= end + .1 and release_s <= now:
            payout = s['pending']; s['pending'] = 0.; s['paid'] += payout
        elif now > end + .1:
            forfeited = s['pending']; s['pending'] = 0.; s['expired'] = True
    assert 0 <= s['pending'] + s['paid'] <= budget
    return s, payout, forfeited


def checks():
    end = 3.; tested = []
    def run(name, events, paid, expired=False):
        s = fresh(); total = 0.
        for e in events:
            s, p, _ = settle(s, end=end, **e); total += p
        assert total == paid and s['paid'] == paid and s['expired'] == expired, name
        tested.append(name); return s
    earned = dict(now=2.95, achieved=True)
    run('unachieved_release', [dict(now=3.02, released=True, release_s=3.02)], 0.)
    run('before_end', [earned, dict(now=3.02, released=True, release_s=2.99), dict(now=3.11)], 0., True)
    for t in (3., 3.02, end + .1):
        run('valid_inclusive_' + str(t), [earned, dict(now=t, released=True, release_s=t)], .25)
    run('after_deadline', [earned, dict(now=3.11, released=True, release_s=3.100000001)], 0., True)
    run('future_timestamp', [earned, dict(now=3.01, released=True, release_s=3.02), dict(now=3.11)], 0., True)
    run('same_control_achievement_release', [dict(now=3., achieved=True, released=True, release_s=3.)], .25)
    run('same_control_failure_suppresses', [earned, dict(now=3.02, released=True, release_s=3.02, failed=True)], 0., True)
    run('failure_latches', [earned, dict(now=3.01, failed=True), dict(now=3.02, achieved=True, released=True, release_s=3.02)], 0., True)
    run('end_forfeits_pending', [earned, dict(now=3.01, ended=True)], 0., True)
    paid = run('repeated_release_once', [earned] + [dict(now=3.02, achieved=True, released=True, release_s=3.02)] * 4, .25)
    after, p, _ = settle(paid, now=3.04, end=end, failed=True)
    assert after['paid'] == .25 and p == 0 and after['failed']; tested.append('future_failure_no_clawback')
    states = [fresh(), fresh()]
    for i in range(2): states[i], _, _ = settle(states[i], end=end, **earned)
    states[0], p, lost = settle(states[0], now=3.01, end=end, reset=True, released=True, release_s=3.01)
    assert states[0] == fresh() and p == 0 and lost == .25 and states[1]['pending'] == .25
    tested.append('partial_reset_forfeits_only_selected_episode')
    events = [dict(now=2.5 + i / 60, achieved=i >= 1) for i in range(64)]
    for i in range(32,64): events[i].update(released=True, release_s=events[32]['now'])
    s = fresh(); whole = []
    for e in events: s, p, _ = settle(s, end=end, **e); whole.append(p)
    s = fresh(); chunked = []
    for part in (events[:32], events[32:]):
        for e in part: s, p, _ = settle(s, end=end, **e); chunked.append(p)
    assert whole == chunked and sum(whole) == .25; tested.append('H32_boundary_memory_preserved')
    for b in (.5, 1., 2.):
        s, p, _ = settle(fresh(), now=3., end=end, achieved=True, released=True, release_s=3., budget=.25*b)
        assert p == s['paid'] == .25*b
    tested.append('budget_025b_once')
    return tested


def main():
    out = HERE / 'results.json'; assert not out.exists() and not out.is_symlink()
    tested = checks()
    import numpy as np
    import torch
    sys.path.insert(0, str(HERE.parents[5]))
    from guitar_learning.gpu.environment import TensorSongEnvironment
    torch.set_num_threads(1)
    spec = importlib.util.spec_from_file_location('original_prefix_reward_escrow', ORIGINAL/'audit.py')
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    controls = []; original_end = TensorSongEnvironment.end_control; original_open = Path.open
    class MemoryOnly(io.StringIO):
        def close(self): pass
    sink = MemoryOnly()
    def capture_open(path, *args, **kwargs):
        if path == ORIGINAL/'results.json' and args == ('x',): return sink
        return original_open(path, *args, **kwargs)
    def observe(env):
        before = torch.stack([env.episode_reward_terms[k].clone() for k in old.TERMS], -1)
        result = original_end(env)
        controls.append(dict(now=env._score_time().cpu().tolist(), clock=env.clock.cpu().tolist(),
            achieved=env.note['left'][:, [4,7,8]].cpu().tolist(), released=env.note['released'][:,4].cpu().tolist(),
            release_s=env.note['release_s'][:,4].cpu().tolist(), failed=env.invalid.cpu().tolist(), ended=result[3].cpu().tolist(),
            paid5=(torch.stack([env.episode_reward_terms[k] for k in old.TERMS], -1)-before).numpy().copy()))
        return result
    with patch.object(Path, 'open', capture_open), patch.object(TensorSongEnvironment, 'end_control', observe), contextlib.redirect_stdout(io.StringIO()):
        old.main()
    base = json.loads(sink.getvalue()); original = json.loads((ORIGINAL/'results.json').read_text())
    assert {k:v for k,v in base.items() if k != 'input_sha256'} == {k:v for k,v in original.items() if k != 'input_sha256'}
    assert {str(Path(k).resolve()):v for k,v in base['input_sha256'].items()} == {str(Path(k).resolve()):v for k,v in original['input_sha256'].items()}
    assert len(controls) == 354, len(controls)
    values = np.stack([x['paid5'] for x in controls]).astype(np.float64); assert np.array_equal(values[:,0], values[:,1])
    end = base['source_targets'][0]['end_s']; rows = []; ledger = []
    for i, name in enumerate(old.CASES):
        state = fresh(); before = np.zeros(3, bool); original_A = []; proposed_A = []; original_B = []; events = []
        for tick, c in enumerate(controls):
            new = np.asarray(c['achieved'][i]) & ~before; before = np.asarray(c['achieved'][i])
            paid3 = .25 * new * (not c['failed'][i]); assert values[tick,i,2] == paid3.sum()
            state, pay, lost = settle(state, now=c['now'][i], end=end, achieved=bool(before[0]), released=c['released'][i], release_s=c['release_s'][i], failed=c['failed'][i], ended=c['ended'][i])
            original_A.append(float(paid3[0])); original_B.append(paid3[1:].tolist()); proposed_A.append(pay)
            events.append(dict(control=tick+1,clock=c['clock'][i],source_time_s=c['now'][i],base_A_paid=float(paid3[0]),new_A_paid=pay,forfeited=lost,**state))
        new_values = values[:,i].copy(); new_values[:,2] += np.asarray(proposed_A)-original_A
        B = np.asarray(original_B); np.testing.assert_array_equal(new_values[:,2]-proposed_A, B.sum(-1))
        np.testing.assert_array_equal(new_values[:,[0,1,3,4]], values[:,i][:,[0,1,3,4]])
        assert np.array_equal(values[:,i,2]-original_A, B.sum(-1)) and sum(proposed_A) <= sum(original_A)
        row = dict(case=name,base_A_paid=sum(original_A),new_A_paid=sum(proposed_A),B7_B8_paid=B.sum(0).tolist(),
            base_sum5=float(values[:,i].sum()),new_sum5=float(new_values.sum()),final=state,
            pending_controls=[e['control'] for e in events if e['pending']],paid_controls=[e['control'] for e in events if e['new_A_paid']],
            base_A_paid_controls=[e['control'] for e in events if e['base_A_paid']],base_released=base['cases'][i]['released'])
        rows.append(row); ledger.append(events)
    assert rows[0]['new_A_paid'] == .25 and rows[1]['new_A_paid'] == 0
    paths = [Path(__file__), HERE/'PLAN.md', HERE.parent/'PLAN.md', ORIGINAL/'audit.py', ORIGINAL/'results.json', *map(Path, base['input_sha256'])]
    pins = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    assert all(pins[str(Path(p).resolve())] == h for p,h in base['input_sha256'].items())
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    result = dict(CPU_only=True,GPU_executed=False,scope='prescribed labels only; original ledger retained, proposed payment separate; no native/RL/source changes',
        budget_A=.25,source_A_end_s=end,source_A_deadline_s=end+.1,control_hz=60,physics_hz=240,cases=rows,escrow_controls=ledger,checks=tested,
        assertions=dict(original_audit_result_exact=True,original_same_clean_wrong_tick_exact=True,other4terms_tick_exact=True,B7_B8_tick_exact=True,total_budget_not_increased=True),input_sha256=pins)
    with out.open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(rows,ensure_ascii=False))


if __name__ == '__main__': main()
