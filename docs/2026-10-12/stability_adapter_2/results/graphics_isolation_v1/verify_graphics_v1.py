"""Root audit of graphics isolation, numerical checkpoint adoption and native smoke."""
import hashlib,json
from pathlib import Path
import torch
import numpy as np
ROOT=Path('/home/ajou/yigyu/3')
G=ROOT/'docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1'
OLD=G.parent/'stability_support_nominal_v1/long_on_v2'
SMOKE=G/'smoke_on_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def equal(a,b):
    if torch.is_tensor(a):return torch.is_tensor(b) and a.dtype==b.dtype and a.shape==b.shape and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(tuple,list)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b

def main():
    expected=read(G/'source_before_native_v1.json')
    sources={str(Path(__file__).resolve()):sha(__file__),**expected}
    oldcp=OLD/'checkpoints/update_000241.pt'
    paths=[oldcp,SMOKE/'adopted_checkpoint.pt',SMOKE/'checkpoints/initial_000000.pt',SMOKE/'checkpoints/update_000242.pt',
        SMOKE/'report.json',SMOKE/'initial_values.json',SMOKE/'training.jsonl',SMOKE/'attempt.json',
        G/'reset_probe_v2/report.json',G/'reset_probe_v2/comparison.json',G/'reset_probe_v2.exit.json']
    for label in ('initial_000000','update_000242'):
        paths.extend([SMOKE/'evaluations'/label/'report.json',SMOKE/'evaluations'/label/'evaluation.json',
            SMOKE/'evaluations'/label/'initial_values.json',SMOKE/'evaluations'/label/'native/episode_0001/trace.json',
            SMOKE/'evaluations'/label/'native/episode_0001/controls.json'])
    paths.extend([OLD/'evaluations/update_000241/native/episode_0001/trace.json',OLD/'evaluations/update_000241/native/episode_0001/controls.json'])
    sources.update({str(p):sha(p) for p in paths})
    old,adopted,initial,updated=[torch.load(p,map_location='cpu',weights_only=True) for p in paths[:4]]
    numeric_fields=set(old)-{'abi','abi_sha256','resume_scope'}
    checks={'source_seal_unchanged':all(sha(p)==h for p,h in expected.items()),
        'old_CP_hash':sha(oldcp)=='3d45f1dac387e97d5d318baf8f1b9ea3ff0789227ace572f100fc1a9c61b5b06',
        'adopted_all_nonmetadata_exact':all(equal(old[k],adopted[k]) for k in numeric_fields),
        'initial_all_nonmetadata_exact':all(equal(old[k],initial[k]) for k in numeric_fields),
        'probe_native_exit_zero':read(G/'reset_probe_v2.exit.json')['returncode']==0,
        'probe_60_resets_and_exact_trajectory':read(G/'reset_probe_v2/report.json')['completed'] and read(G/'reset_probe_v2/report.json')['resets_completed']==60,
        'headless_full_trace_controls_exact':read(G/'reset_probe_v2/comparison.json')['trace_exact'] and read(G/'reset_probe_v2/comparison.json')['controls_exact'],
        'smoke_completed_and_input_unchanged':read(SMOKE/'report.json')['completed'] and read(SMOKE/'report.json')['inputs_unchanged'],
        'one_actual_update':updated['updates']==242 and updated['transitions']==old['transitions']+256,
        'RMS_exact':all(equal(v,updated['model'][k]) for k,v in old['model'].items() if k.startswith('obs_rms.')),
        'actor_changed':any(not equal(v,updated['model'][k]) for k,v in old['model'].items() if k.startswith('actor.')),
        'critic_changed':any(not equal(v,updated['model'][k]) for k,v in old['model'].items() if k.startswith('critic.'))}
    training_policy=read(SMOKE/'initial_values.json')['graphics_resource_policy']
    checks['training_minus1_no_render']=training_policy['creation_calls'][0]['forwarded_graphics_device_id']==-1 and not training_policy['render_lookup_counts']
    line=read_json_line(SMOKE/'training.jsonl')
    checks['actual_optimizer_and_KL_gate']=line['ppo']['optimizer_steps']>0 and 0<=line['ppo']['final_analytic_kl']<=.02 and not line['ppo']['RMS_updated']
    evaluation=[]
    for label in ('initial_000000','update_000242'):
        out=SMOKE/'evaluations'/label
        report=read(out/'report.json');native=report['native_report']
        policy=read(out/'initial_values.json')['graphics_resource_policy']
        checks[label+'_full_native']=report['completed'] and report['inputs_unchanged'] and native['full_horizon_completed'] and native['control_steps']==982 and native['physics_steps']==3928
        checks[label+'_frozen_baselines_and_guards']=native['baseline_weights_unchanged'] and not native['forbidden_calls'] and native['safety_violation'] is None
        base=out/'native/episode_0001'
        rows=read(base/'controls.json');initial_values=read(base/'initial_values.json');capture=read(base/'media/capture.json')
        sources[str(base/'initial_values.json')]=sha(base/'initial_values.json')
        sources[str(base/'media/capture.json')]=sha(base/'media/capture.json')
        groups=np.array(old['abi']['groups']);lo=np.array(old['abi']['lower']);hi=np.array(old['abi']['upper']);rates=np.array(old['abi']['rates'])
        nominal=np.array([r['nominal81_rad'] for r in rows]);teacher=np.array([r['teacher_nominal81_rad'] for r in rows])
        requested=np.array([r['requested81_rad'] for r in rows]);final=np.array([r['final81_rad'] for r in rows])
        preload=np.array(initial_values['preload']['bounded_targets_rad']);arm=groups=='arm';thumb=np.array([n.startswith('LH:thumb') for n in old['abi']['names']])
        nominal_caps=np.where(arm,.15,np.where(thumb,.10,np.inf))
        checks[label+'_nominal_guard_exact']=bool(np.array_equal(nominal,np.clip(teacher,np.maximum(lo,preload-nominal_caps),np.minimum(hi,preload+nominal_caps))))
        caps=np.array([old['abi']['residual_caps_rad'][g] for g in groups])
        previous=np.vstack([initial_values['q_ref_rad'],final[:-1]])
        rounding=2*np.spacing(np.maximum(np.abs(final),np.abs(previous)).astype(np.float32)).astype(float)+1e-10
        checks[label+'_bounds_caps_rates']=bool(np.all(np.abs(requested-nominal)<=caps+1e-10) and np.all(final>=lo-1e-8) and np.all(final<=hi+1e-8) and np.all(np.abs(final-previous)<=rates/60+rounding))
        checks[label+'_strap_calls']=native['strap_force_calls']==13*native['physics_steps']
        checks[label+'_actual_baseline_inferences']=native['baseline_actor_calls']=={'Fret':862,'Strike':862}
        checks[label+'_video_initial_endpoint']=len(capture['frames'])==492 and capture['frames'][0]['physics_step']==0 and capture['frames'][-1]['physics_step']==3928 and all(f['render_preserves_states'] for f in capture['frames'])
        checks[label+'_video_sha']=all(sha(v['path'])==v['sha256'] and v['stream']['nb_read_frames']=='492' for v in native['videos'].values())
        for v in native['videos'].values():sources[v['path']]=v['sha256']
        checks[label+'_graphics0']=policy['creation_calls'][0]['forwarded_graphics_device_id']==0 and policy['render_lookup_counts'].get('render_all_camera_sensors',0)>0
        evaluation.append({'label':label,'native':native,'graphics_resource_policy':policy})
    for filename in ('trace.json','controls.json'):
        checks['initial_recorded_'+filename+'_exact_old']=read(SMOKE/'evaluations/initial_000000/native/episode_0001'/filename)==read(OLD/'evaluations/update_000241/native/episode_0001'/filename)
    checks['audit_input_unchanged']=all(sha(p)==h for p,h in sources.items())
    result={'checks':checks,'passed':all(checks.values()),'input_sha256':sources,'actual_update':line['update'],
        'actual_transitions':line['transitions'],'final_analytic_kl':line['ppo']['final_analytic_kl'],'evaluations':evaluation,
        'probe_v1_failure':'60 reset passed; audit reference JSONs mistakenly included in learning source ABI; refused before physics rollout or PPO; originals preserved',
        'limits':'finite repeated-init/full-episode/one-update validation; not universal crash prevention or musical success certification'}
    with (G/'verification_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({'passed':result['passed'],'checks':checks,'final_analytic_kl':result['final_analytic_kl']},indent=2))
    if not result['passed']:raise AssertionError('graphics audit failed; preserve output and diagnose')

def read_json_line(path):
    lines=Path(path).read_text().splitlines();assert len(lines)==1
    return json.loads(lines[0])
if __name__=='__main__':main()
