"""Summaries of static geometric/load candidates, never song success."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BASE=Path(__file__).resolve().parents[1]


def main():
    summary=dict(schema='guitar_learning.current_contact_static_comparison.v1',
        scope='static source-note midpoint and selected-one-note scope; current positive/wrongv2; no song ledger payment or acoustic success',
        teacher='diagnostic bounded actions only; not a learned policy',runs={})
    for folder in sorted(list(BASE.glob('static_*'))+list(BASE.glob('teacher_*'))):
        if not folder.is_dir() or not (folder/'report.json').exists():continue
        report=json.loads((folder/'report.json').read_text())
        if not report.get('completed'):continue
        data=np.load(folder/'trace240.npz')
        result=dict(completed=report['completed'],wall_s=report['wall_s'],
            physical_failures=sum(g['failure'] is not None for g in report['goals']),
            wrist_shadow_rows=sum(g['wrist_shadow_failure_time_s'] is not None for g in report['goals']),
            same_sample_predicate_mismatches=sum(g['same_sample_predicate_mismatch_count'] for g in report['goals']),
            changed_inputs=report['changed_inputs'],scene_closed=report['scene']['closed'],
            finite_trace_arrays=all(bool(np.isfinite(data[k]).all()) for k in data.files),
            physics_clock_contiguous=bool(np.array_equal(data['physics_step'],np.arange(1,len(data['physics_step'])+1))),
            fingers={},goals=report['goals'])
        for f,name in enumerate(('index','middle','ring','pinky'),1):
            goals=[g for g in report['goals'] if g['finger']==f]
            result['fingers'][name]=dict(targets=len(goals),
                maximum_uninterrupted_hold_candidate_s=max(g['best_hold_contact_streak_s'] for g in goals),
                maximum_any_phase_candidate_s=max(g['best_static_contact_streak_s'] for g in goals),
                hold50ms_rows=[g['row'] for g in goals if g['best_hold_contact_streak_s']+1e-12>=.05],
                minimum_any_phase_pad_distance_mm=min(g['minimum_actual_distance_m'] for g in goals if g['minimum_actual_distance_m'] is not None)*1000)
        summary['runs'][folder.name]=result
    (BASE/'support/static_comparison.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    figure,axes=plt.subplots(2,1,figsize=(13,9),sharex=True)
    labels=list(summary['runs']);width=.8/max(len(labels),1);x=np.arange(4)
    for i,label in enumerate(labels):
        fingers=summary['runs'][label]['fingers']
        position=x+(i-(len(labels)-1)/2)*width
        axes[0].bar(position,[f['maximum_uninterrupted_hold_candidate_s'] for f in fingers.values()],width,label=label)
        axes[1].bar(position,[len(f['hold50ms_rows']) for f in fingers.values()],width,label=label)
    axes[0].set_ylabel('Best uninterrupted candidate in hold (s)')
    axes[1].set_ylabel('Targets with >=50ms hold candidate / 6')
    axes[1].set_xticks(x);axes[1].set_xticklabels(['index','middle','ring','pinky'])
    axes[0].legend(fontsize=8,ncol=2)
    for ax in axes:ax.grid(axis='y',alpha=.25)
    figure.suptitle('Static current-geometry/load candidates; no song reward or learned success\nWrist failures are shadow-only in these reachability diagnostics')
    figure.tight_layout();figure.savefig(BASE/'support/static_comparison.png',dpi=140);plt.close(figure)
    print(json.dumps({k:{'physical_failures':v['physical_failures'],'fingers':v['fingers']}
        for k,v in summary['runs'].items()},indent=2))


if __name__=='__main__':main()
