"""Diagnostic zero actions: paired 240Hz wrist predicates and active-rule smoke.

Only shadow disables wrist termination; physical/control failures remain live.
No policy training or musical improvement is measured.
"""
import hashlib
import itertools
import json
from pathlib import Path
import time
from unittest.mock import patch

ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parent.parent


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def main():
    import isaacgym
    import torch
    from guitar_learning.training.recording import active_source_paths
    from guitar_learning.training.start import settings_document
    from guitar_learning.training.gpu_pool import GpuPool
    torch.set_num_threads(1)
    torch.manual_seed(7)
    torch.backends.cuda.matmul.allow_tf32 = False
    def census():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(active_source_paths(ROOT/'guitar_learning'))}
    original = census()
    write(OUT/'support/native_source_manifest.json', original)
    reports = {}
    for mode in ('shadow', 'active'):
        assert census() == original
        folder = OUT/('native_'+mode)
        folder.mkdir(exist_ok=False)
        settings = settings_document('left', physics='gpu', size='large', num_envs=24,
            horizon=32, updates=8, learning_family='finger-skill')
        write(folder/'settings.json', settings)
        pool = None
        started = time.monotonic()
        records, first_episodes = [], []
        try:
            pool = GpuPool(settings, folder)
            env = pool.environment
            phrases = env.catalog.phrases
            assert len(phrases) == 24
            write(folder/'contract.json', pool.contract)
            records = [dict(env_id=i, phrase_id=p.phrase_id, duration_ticks=p.duration_ticks,
                selected_indices=list(p.target_indices), original_first=None, longer_first=None,
                recovery_first=None, severe_first=None, original_then_release_s=None,
                maximum_excess_240hz_m=0., recovered_band_samples=0, end=None)
                for i, p in enumerate(phrases)]
            seen = set()
            old_active = [False]*24
            old_elapsed = [0.]*24
            original_safety = env._safety
            def snapshot(i, now, excess):
                audible = env.focus_mask[i] & (env._score_time()[i] >= env.onset) & (env._score_time()[i] < env.end)
                return dict(local_s=now, excess_m=excess,
                    delta_G_m=env.guide['delta'][i].tolist(),
                    audible_indices=audible.nonzero().flatten().tolist(),
                    audible_frets=env.fret[audible].tolist(),
                    audible_candidates=(env.candidate[i,audible] & ~env.wrong[i,audible]).tolist(),
                    recovery_elapsed_s=float(env.wrist_elapsed[i]))
            def safety():
                original_safety()
                now = env._local_time().tolist()
                excess = env.guide['delta'].abs().amax(-1).tolist()
                current, severe = env.wrist_failure.tolist(), env.wrist_severe_failure.tolist()
                elapsed = env.wrist_elapsed.tolist()
                for i, row in enumerate(records):
                    if i in seen:
                        continue
                    x, t = excess[i], now[i]
                    row['maximum_excess_240hz_m'] = max(row['maximum_excess_240hz_m'], x)
                    old_active[i] = t+1e-12 >= 3 and (old_active[i] or x > .03) and x > .02
                    old_elapsed[i] = old_elapsed[i]+1/240 if old_active[i] else 0.
                    if old_active[i] and x <= .03:
                        row['recovered_band_samples'] += 1
                    for name, triggered in (('original_first',old_elapsed[i]+1e-12 >= .75),
                            ('longer_first',old_elapsed[i]+1e-12 >= 1.5),
                            ('recovery_first',current[i]), ('severe_first',severe[i])):
                        if triggered and row[name] is None:
                            row[name] = snapshot(i,t,x)
                    if row['original_first'] is not None and x <= .02 and row['original_then_release_s'] is None:
                        row['original_then_release_s'] = t
                    assert elapsed[i] >= 0 and elapsed[i] <= old_elapsed[i]+1e-9
            failure_patch = (patch.object(env, '_control_failures', side_effect=lambda: env.tick_failure.any(-1))
                             if mode == 'shadow' else patch.object(env, '_control_failures', wraps=env._control_failures))
            with patch.object(env.sampler, 'next', side_effect=itertools.cycle(phrases)), failure_patch:
                pool.reset()
                assert env.phrase_ids == [p.phrase_id for p in phrases]
                action = torch.zeros(24,39,device=pool.scene.device)
                with patch.object(env, '_safety', side_effect=safety), (folder/'trace_60hz.jsonl').open('w') as trace:
                    for tick in range(max(p.duration_ticks for p in phrases)+2):
                        obs,reward,cost,terminated,truncated,episodes = pool.step(action)
                        assert all(bool(torch.isfinite(v).all()) for v in obs.values())
                        assert bool(torch.isfinite(reward).all() & torch.isfinite(cost).all())
                        trace.write(json.dumps(dict(tick=tick+1, alive=[i for i in range(24) if i not in seen],
                            excess_m=env.guide['delta'].abs().amax(-1).tolist(),
                            old_elapsed_s=old_elapsed, recovery_elapsed_s=env.wrist_elapsed.tolist()))+'\n')
                        now = env._local_time().tolist()
                        for ep in episodes:
                            i=ep['env_id']
                            if i in seen:
                                continue
                            row=records[i]
                            physical=bool(env.tick_failure[i].any())
                            row['end']=dict(local_s=now[i],physical_failure=physical,
                                natural=not physical and tick+1 == row['duration_ticks'],
                                actual_reason=('physical_failure' if physical else
                                    'timeline_complete' if tick+1 == row['duration_ticks'] else 'wrist_failure'),
                                control_ticks=tick+1)
                            if mode=='active':
                                diag=ep['wrist_termination']
                                assert diag['schema']=='guitar_learning.wrist_termination_diagnostics.v2'
                                components=ep['cost_components']
                                assert abs(sum(components.values())-ep['cost']) < 1e-4
                                assert components['termination_base']==(5. if ep['reason']=='terminal_failure' else 0.)
                                if ep['termination']['wrist_outside']:
                                    assert diag['elapsed_s']+1e-9 >= 1.5
                            first_episodes.append(ep)
                            seen.add(i)
                        if len(seen)==24:
                            break
                        done=(terminated|truncated).nonzero().flatten()
                        if done.numel():
                            pool.reset(done)
                        if tick%120==0:
                            print(mode,'tick',tick,'first episodes finished',len(seen),flush=True)
                    assert len(seen)==24
        finally:
            if pool is not None:
                pool.close()
        audit=pool.scene.diagnostics
        assert audit['closed'] and audit['physx_use_gpu'] and audit['use_gpu_pipeline']
        assert census()==original
        write(folder/'first_episodes.json',first_episodes)
        report=dict(completed=True, policy='zero actions, no learned policy; no musical performance conclusion',
            mode=mode, sampling_hz=240, trace_hz=60, source_files=len(original), unchanged_source=True,
            finite=True, closed=audit['closed'], simulator_count=audit['simulator_count'],
            native_environments=audit['environment_count'], wall_s=time.monotonic()-started,
            original_would_fail=sum(r['original_first'] is not None for r in records),
            longer_would_fail=sum(r['longer_first'] is not None for r in records),
            recovery_would_fail=sum(r['recovery_first'] is not None for r in records),
            severe_would_fail=sum(r['severe_first'] is not None for r in records),
            actual_physical_failures=sum(r['end']['physical_failure'] for r in records),
            actual_natural_ends=sum(r['end']['natural'] for r in records),
            actual_wrist_ends=sum(r['end']['actual_reason']=='wrist_failure' for r in records), records=records)
        write(folder/'report.json',report)
        reports[mode]={k:v for k,v in report.items() if k!='records'}
        print(mode,'COMPLETE',reports[mode],flush=True)
    write(OUT/'native_checks.json',dict(completed=True, unchanged_source=census()==original, reports=reports))


if __name__=='__main__':
    main()
