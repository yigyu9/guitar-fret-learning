"""Native zero-action shadow: observe new wrist rules without ending on them.

Diagnostic only. Physical failures still end episodes; this never trains/saves a model.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path('/home/ajou/yigyu/3')
sys.path.insert(0, str(ROOT))
FOLDER = Path(__file__).resolve().parent


def main():
    manifest = json.loads((FOLDER/'source_manifest.json').read_text())
    def check():
        assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
    check()
    import isaacgym
    import torch
    from guitar_learning.training.start import settings_document
    from guitar_learning.training.gpu_pool import GpuPool
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    settings = settings_document('left', physics='gpu', size='large', num_envs=24,
        horizon=32, updates=8, learning_family='finger-skill')
    out = FOLDER.parent/'shadow'
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    pool = None
    records = []
    try:
        pool = GpuPool(settings, out)
        env = pool.environment
        phrases = env.catalog.phrases
        assert len(phrases) == 24
        records = [dict(env_id=i, phrase_id=p.phrase_id, duration_ticks=p.duration_ticks,
            selected_indices=list(p.target_indices), first_normal_s=None, first_severe_s=None,
            maximum_excess_m=0., normal_before_3_75=False, end=None) for i, p in enumerate(phrases)]
        # Only the new wrist end mask is bypassed in this separate diagnostic.
        # Normal scene/control/reset/physical checks remain live and unmodified.
        with patch.object(env.sampler, 'next', side_effect=itertools.cycle(phrases)), \
                patch.object(env, '_control_failures', side_effect=lambda: env.tick_failure.any(-1)):
            pool.reset()
            assert env.phrase_ids == [p.phrase_id for p in phrases]
            action = torch.zeros(24, 39, device=pool.scene.device)
            seen = set()
            for tick in range(max(p.duration_ticks for p in phrases)+2):
                obs, reward, cost, terminated, truncated, episodes = pool.step(action)
                assert all(bool(torch.isfinite(obs[key]).all()) for key in obs)
                assert bool(torch.isfinite(reward).all() & torch.isfinite(cost).all())
                now = env._local_time().tolist()
                excess = env.guide['delta'].abs().amax(-1).tolist()
                normal, severe = env.wrist_failure.tolist(), env.wrist_severe_failure.tolist()
                for i, row in enumerate(records):
                    if i in seen:
                        continue
                    row['maximum_excess_m'] = max(row['maximum_excess_m'], excess[i])
                    if normal[i] and row['first_normal_s'] is None:
                        row['first_normal_s'] = now[i]
                        row['normal_before_3_75'] = now[i] < 3.75-1e-9
                    if severe[i] and row['first_severe_s'] is None:
                        row['first_severe_s'] = now[i]
                done = (terminated | truncated).nonzero().flatten()
                for i in done.tolist():
                    if i not in seen:
                        row = records[i]
                        row['end'] = dict(local_s=now[i], physical_failure=bool(env.tick_failure[i].any()),
                            natural=bool(truncated[i]), control_ticks=tick+1)
                        seen.add(i)
                if len(seen) == 24:
                    break
                if done.numel():
                    pool.reset(done)
                if tick % 120 == 0:
                    print('shadow tick', tick, 'finished', len(seen), flush=True)
            assert len(seen) == 24
            assert not any(r['normal_before_3_75'] for r in records)
    finally:
        if pool is not None:
            pool.close()
    check()
    report = dict(schema='guitar_learning.v25_wrist_shadow.v1', completed=True,
        source_files=len(manifest), policy='zero action; no trained checkpoint',
        override='new wrist failures recorded but not applied; original physical failures active',
        simulator_count=1, native_environments=24, closed=True, finite=True,
        wall_s=time.monotonic()-started, records=records,
        normal_would_fail=sum(r['first_normal_s'] is not None for r in records),
        severe_would_fail=sum(r['first_severe_s'] is not None for r in records),
        actual_physical_failures=sum(r['end']['physical_failure'] for r in records))
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('SHADOW_COMPLETE', report['normal_would_fail'], report['severe_would_fail'], flush=True)


if __name__ == '__main__':
    main()
