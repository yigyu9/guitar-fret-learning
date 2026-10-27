"""Read-only ledger statistics and analytic examples, without policy training."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parent
RUN = ROOT / 'docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/pilot_b16_v4'
paths = [Path(__file__).resolve(), RUN / 'metrics.jsonl', RUN / 'report.json', RUN / 'config.json',
         ROOT / 'stability_adapter_2/fresh_learning_v1/policy.py',
         ROOT / 'stability_adapter_2/fresh_learning_v1/ppo.py',
         ROOT / 'stability_adapter_2/fresh_music_v1/run_v4.py']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = {str(p): sha(p) for p in paths}
records = [json.loads(line) for line in (RUN / 'metrics.jsonl').open()]
report = json.loads((RUN / 'report.json').read_text())
config = json.loads((RUN / 'config.json').read_text())
threshold = config['ppo']['target_kl']
assert report['completed'] and report['performed_updates'] == len(records) == 16
assert [r['update'] for r in records] == list(range(1, 17))
stats = {}
for key in ('approx_kl', 'clip_fraction', 'grad_norm'):
    values = [r['losses'][key] for r in records]
    assert all(math.isfinite(x) for x in values)
    stats[key] = dict(first=values[0], minimum=min(values), maximum=max(values))
sigma = math.exp(-3)
analytic = dict(scope='Illustrative equal-variance Gaussian calculation, not observed policy mean changes',
                latent_sigma=sigma, dimensions=54, illustrative_mean_shift_per_dimension=.01,
                illustrative_joint_kl=54*.01**2/(2*sigma**2),
                rms_mean_shift_for_joint_kl_003=sigma*math.sqrt(.06/54),
                gamma_099_at_1_second_60hz=.99**60,
                gae_residual_weight_at_1_second_60hz=(.99*.95)**60)
after = {str(p): sha(p) for p in paths}
assert before == after
with (OUT / 'optimizer_audit.json').open('x') as stream:
    json.dump(dict(source_run=str(RUN), source_song='00_SS1-68-E_comp',
                   scope='No evidence of performance on newly selected song', updates=len(records),
                   target_kl=threshold, updates_exceeding_target_kl=sum(r['losses']['approx_kl']>threshold for r in records),
                   statistics=stats, analytic_examples=analytic,
                   input_sha256_before=before, input_sha256_after=after, inputs_unchanged=True),
              stream, indent=2, ensure_ascii=False, allow_nan=False)
print('Verified 16 update records; no training executed.')
