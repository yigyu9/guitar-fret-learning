"""Summarize completed endpoint traces; does not interpret geometry as sound."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parents[1]
FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')


def longest(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return float(np.max(ends-starts)/60) if starts.size else 0.


def main():
    (BASE/'plots').mkdir(exist_ok=True)
    summary = dict(schema='guitar_learning.failure_diagnosis.baseline_summary.v1',
        sampling='completed60Hz endpoints; not240Hz extrema or calibrated force',
        policy='deterministic latent mean; no actual stochastic training actions reconstructed',
        limits='exact target bound tolerance1e-6rad; near target/actual bound within2degrees',
        limitations=['different new native scenes need not reproduce prior env0 outcomes',
                     'target-actual scalar differences are diagnostics, not certified native SO3 drive error',
                     'policy bias/limit residence describes a trajectory, not causal proof against control'], runs={})
    for label in ('initial', 'final'):
        folder = BASE/('trace_'+label)
        if not (folder/'trace_metadata.json').is_file():
            continue
        meta = json.loads((folder/'trace_metadata.json').read_text())
        report = json.loads((folder/'report.json').read_text())
        names, action_names = meta['joint_names'], meta['action_names']
        lower, upper = np.asarray(meta['native_lower_rad']), np.asarray(meta['native_upper_rad'])
        run = dict(evaluation_summary=report['summary'], completed=report['completed'],
            package_sources_unchanged=meta['package_sources_unchanged'], scene_closed=meta['scene_closed'], envs={})
        for env in meta['selected_envs']:
            path = folder/('trace_env%04d.npz'%env)
            data = np.load(path)
            time_s = data['score_time_s']
            row = dict(samples=len(time_s), duration_s=float(len(time_s)/60),
                all_arrays_finite=all(np.isfinite(data[k]).all() for k in data.files),
                physics_clock_contiguous=bool(np.array_equal(data['physics_step'], np.arange(1,len(time_s)+1)*4)),
                latent_equals_mean=bool(np.array_equal(data['policy_latent'], data['policy_mean'])),
                action_equals_tanh_mean_max_error=float(np.max(np.abs(data['action'][:,:33]-np.tanh(data['policy_mean'][:,:33])))),
                joints={}, fingers={})
            for finger_index, finger in enumerate(FINGERS):
                js = [i for i,n in enumerate(names) if n.startswith('LH:'+finger)]
                ac = [action_names.index(names[i]) for i in js]
                q, target, previous = data['q'][:,js], data['target'][:,js], data['previous_target'][:,js]
                action = data['action'][:,ac]
                lo, hi = lower[js], upper[js]
                requested = previous+action*(4/60)
                expected = np.clip(requested,lo,hi)
                at_low, at_high = np.abs(target-lo)<=1e-6, np.abs(target-hi)<=1e-6
                near_target = (np.minimum(np.abs(target-lo), np.abs(target-hi)) <= np.deg2rad(2))
                near_q = (np.minimum(np.abs(q-lo), np.abs(q-hi)) <= np.deg2rad(2))
                outward = ((np.abs(previous-lo)<=1e-6)&(action<0))|((np.abs(previous-hi)<=1e-6)&(action>0))
                error = np.rad2deg(np.abs(target-q))
                stats = dict(mean_target_actual_abs_error_deg=float(error.mean()),
                    target_actual_abs_error_p95_deg=float(np.percentile(error,95)),
                    mean_abs_action=float(np.abs(action).mean()),
                    mean_target_bound_fraction=float((at_low|at_high).mean()),
                    mean_target_near_bound2deg_fraction=float(near_target.mean()),
                    mean_actual_near_bound2deg_fraction=float(near_q.mean()),
                    mean_outward_at_previous_target_bound_fraction=float(outward.mean()),
                    target_reconstruction_max_error_rad=float(np.max(np.abs(expected-target))),
                    max_target_change_rad_s=float(np.max(np.abs(target-previous))*60))
                if finger != 'thumb':
                    f = finger_index-1
                    onset, end, assigned = map(np.asarray,(meta['note_onset_s'],meta['note_end_s'],meta['note_finger']))
                    audible = (((time_s[:,None]>=onset)&(time_s[:,None]<end))&(assigned[None]==finger_index)).any(1)
                    idle = data['finger_idle_weight'][:,f]
                    phases = dict(initial_preparation=time_s<3, audible=audible&(time_s>=3),
                        own_idle=(idle>=.5)&~audible&(time_s>=3),
                        preparing_or_transition=(idle<.5)&~audible&(time_s>=3))
                    stats['phase_metrics'] = {key:dict(sample_count=int(mask.sum()),
                        target_bound_fraction=float((at_low|at_high)[mask].mean()) if mask.any() else None,
                        abs_error_p95_deg=float(np.percentile(error[mask],95)) if mask.any() else None,
                        outward_fraction=float(outward[mask].mean()) if mask.any() else None,
                        mean_B_gate=float(data['finger_gate'][mask,f].mean()) if mask.any() else None,
                        mean_B_idle_weight=float(idle[mask].mean()) if mask.any() else None)
                        for key,mask in phases.items()}
                row['fingers'][finger] = stats
                for k,j in enumerate(js):
                    sign = np.sign(action[:,k])
                    run_starts = np.r_[0,np.flatnonzero(np.diff(sign)!=0)+1]
                    run_ends = np.r_[run_starts[1:],len(sign)]
                    sign_integrals = [abs(action[a:b,k].sum())*(4/60) for a,b in zip(run_starts,run_ends)]
                    row['joints'][names[j]] = dict(action_mean=float(action[:,k].mean()),
                        action_abs_mean=float(np.abs(action[:,k]).mean()),
                        target_bound_fraction=float((at_low|at_high)[:,k].mean()),
                        longest_exact_target_bound_s=longest((at_low|at_high)[:,k]),
                        longest_near_target_bound2deg_s=longest(near_target[:,k]),
                        longest_outward_command_at_target_bound_s=longest(outward[:,k]),
                        same_sign_command_max_integral_rad=float(max(sign_integrals,default=0)),
                        tracking_abs_error_p95_deg=float(np.percentile(error[:,k],95)),
                        actual_angle_min_deg=float(np.rad2deg(q[:,k].min())),
                        actual_angle_max_deg=float(np.rad2deg(q[:,k].max())))
            row['trace_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            run['envs'][str(env)] = row
            if env == 0:
                figure, axes = plt.subplots(5,3,figsize=(17,17),sharex=True)
                for f,finger in enumerate(FINGERS):
                    js=[i for i,n in enumerate(names) if n.startswith('LH:'+finger)]
                    for k,j in enumerate(js):
                        color=plt.cm.tab10(k)
                        name=names[j].split(':')[1]
                        axes[f,0].plot(time_s,data['action'][:,action_names.index(names[j])],color=color,label=name,lw=.9)
                        axes[f,1].plot(time_s,np.rad2deg(data['target'][:,j]),color=color,lw=1)
                        axes[f,1].plot(time_s,np.rad2deg(data['q'][:,j]),color=color,ls='--',lw=.8)
                        axes[f,2].plot(time_s,np.rad2deg(data['target'][:,j]-data['q'][:,j]),color=color,lw=.8)
                    axes[f,0].set_ylabel(finger+'\naction')
                    axes[f,0].legend(fontsize=6,ncol=2)
                    axes[f,0].set_ylim(-1.05,1.05)
                    axes[f,1].set_ylabel('angle (deg)')
                    axes[f,2].set_ylabel('target - actual (deg)')
                    for ax in axes[f]: ax.grid(alpha=.25)
                axes[0,0].set_title('Applied deterministic action = tanh(latent mean)')
                axes[0,1].set_title('Target solid / actual dashed (same joint color)')
                axes[0,2].set_title('Endpoint scalar tracking error')
                for ax in axes[-1]: ax.set_xlabel('score time (s)')
                figure.suptitle(label+' checkpoint, predeclared env0 first episode, free guitar, 60Hz')
                figure.tight_layout()
                figure.savefig(BASE/'plots'/(label+'_env0_control.png'),dpi=130)
                plt.close(figure)
                figure,axes=plt.subplots(4,1,figsize=(14,9),sharex=True)
                for f,finger in enumerate(FINGERS[1:]):
                    for key in ('gate','idle_weight','contact_veto','near_veto'):
                        legend = {'gate':'actual B gate', 'idle_weight':'score idle weight',
                                  'contact_veto':'raw contact diagnostic',
                                  'near_veto':'raw near diagnostic'}[key]
                        axes[f].plot(time_s,data['finger_'+key][:,f],label=legend,
                                     lw=1.8 if key == 'gate' else .9,
                                     ls='--' if key == 'idle_weight' else '-')
                    axes[f].set_ylabel(finger);axes[f].set_ylim(-.05,1.05);axes[f].grid(alpha=.25)
                axes[0].legend(ncol=4,fontsize=8);axes[-1].set_xlabel('score time(s)')
                figure.suptitle(label+' env0 independent finger B eligibility at control endpoints')
                figure.tight_layout();figure.savefig(BASE/'plots'/(label+'_env0_standby_gates.png'),dpi=130);plt.close(figure)
        summary['runs'][label] = run
    if set(summary['runs']) == {'initial', 'final'}:
        joint_names = list(summary['runs']['initial']['envs']['0']['joints'])
        figure,axes = plt.subplots(3,1,figsize=(15,11),sharex=True)
        for j,label in enumerate(('initial','final')):
            runs = list(summary['runs'][label]['envs'].values())
            x = np.arange(len(joint_names))+(j-.5)*.36
            for ax,key,scale in zip(axes,
                ('tracking_abs_error_p95_deg','longest_exact_target_bound_s','target_bound_fraction'),
                (1,1,100)):
                values = [np.mean([row['joints'][name][key] for row in runs])*scale for name in joint_names]
                ax.bar(x,values,width=.36,label=label)
        for ax,label in zip(axes,('p95 target-actual error (deg)',
                                  'longest exact target-bound run (s)',
                                  'exact target-bound residence (%)')):
            ax.set_ylabel(label);ax.grid(axis='y',alpha=.25);ax.legend()
        axes[-1].set_xticks(np.arange(len(joint_names)))
        axes[-1].set_xticklabels([n.split(':')[1] for n in joint_names],rotation=60,ha='right')
        figure.suptitle('Initial vs final: mean over predeclared env0..3 first episodes (60Hz endpoints)')
        figure.tight_layout();figure.savefig(BASE/'plots/initial_final_joint_summary.png',dpi=130);plt.close(figure)
    (BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({label:{'summary':row['evaluation_summary'],'env0_fingers':row['envs']['0']['fingers']}
                      for label,row in summary['runs'].items()},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
