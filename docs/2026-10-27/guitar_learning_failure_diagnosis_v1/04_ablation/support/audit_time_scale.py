"""Analytic audit of the sealed baseline's discounts; no training changes."""
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'baseline/trace_final/settings.json'
settings = json.loads(SOURCE.read_text())
gamma, cost_gamma, lam = (settings['ppo'][k] for k in ('gamma', 'cost_gamma', 'gae_lambda'))
candidate = math.exp(-1/(60*30))
seconds = (0, settings['horizon']/60, 1, 3, 5, 10, 20, 30)
rows = [dict(delay_s=t, reward_weight=gamma**(60*t), cost_weight=cost_gamma**(60*t),
             candidate_reward_weight=candidate**(60*t)) for t in seconds]
result = dict(scope='Analytic coefficients from sealed configuration, not observed rewards or causal gradients',
    source=str(SOURCE), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    gamma=gamma, cost_gamma=cost_gamma, gae_lambda=lam,
    candidate_gamma_not_applied=candidate,
    current_reward_half_life_s=math.log(.5)/(60*math.log(gamma)),
    candidate_reward_half_life_s=math.log(.5)/(60*math.log(candidate)),
    rows=rows, horizon_ticks=settings['horizon'],
    horizon_discount=gamma**settings['horizon'],
    direct_gae_last_lag_weight=(gamma*lam)**(settings['horizon']-1),
    interpretation='H32 bootstraps future value. Discount is not a hard lookahead cutoff. Matching gamma in PBRS is required for any later intervention; no coefficient is changed by this audit.')
out = ROOT/'04_ablation'
(out/'time_scale_audit.json').write_text(json.dumps(result, indent=2)+'\n')
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
t = np.linspace(0, 30, 601)
axes[0].plot(t, gamma**(60*t), label='현재 reward γ=.99')
axes[0].plot(t, candidate**(60*t), label='계획 후보 τ=30초 (미적용)')
axes[0].plot(t, cost_gamma**(60*t), '--', label='현재 cost γ=1')
axes[0].set(xlabel='동일 크기 점수의 지연 [초]', ylabel='할인 후 가중치', ylim=(-.03,1.06))
axes[0].axvline(3, color='grey', alpha=.4)
axes[0].text(3.4, .22, '3초 뒤 보상: 현재16.4% / 후보90.5%')
lag = np.arange(settings['horizon'])
axes[1].plot(lag/60, (gamma*lam)**lag, label='현재 reward GAE')
axes[1].plot(lag/60, (candidate*lam)**lag, label='후보 reward GAE (미적용)')
axes[1].plot(lag/60, (cost_gamma*lam)**lag, '--', label='현재 cost GAE')
axes[1].set(xlabel='H32 창 안의 TD 잔차 지연 [초]', ylabel='직접 가중치', ylim=(0,1.06))
axes[1].set_title('수집창 이후는 가치 추정으로 연결')
for ax in axes:
    ax.grid(alpha=.25)
    ax.legend(fontsize=8)
fig.suptitle('보상 시간척도 감사 — 수학적 계수, 학습 효과 검증 아님')
fig.tight_layout()
fig.savefig(out/'time_scale_audit.png', dpi=150)
print(json.dumps(result, indent=2))
