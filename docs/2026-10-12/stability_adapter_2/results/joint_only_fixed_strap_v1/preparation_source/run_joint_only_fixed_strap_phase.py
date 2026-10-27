"""Preserve and execute one explicitly selected stage of the fixed-LA experiment."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['preparation','native','analysis']);stage=ap.parse_args().stage
    module={'preparation':'prepare_joint_only_fixed_strap','native':'run_palm_witness_initial_diagnostic','analysis':'analyze_joint_only_fixed_strap'}[stage]
    assert not (P/(stage+'_execution.json')).exists() and not (P/(stage+'.log')).exists()
    paths=[Path(__file__).resolve(),A/(module+'.py'),A/'JOINT_ONLY_FIXED_STRAP_PLAN.md']
    cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.'+module]
    if stage=='native':
        assert not (P/'native').exists()
        trial=A/'trials/joint_only_fixed_strap_v1/palm_witness_original_LA.json';proposal=P/'proposal.json'
        data=json.loads(proposal.read_text());assert all(data['checks'].values()) and sha(trial)==data['rows'][0]['trial_sha256']
        paths += [trial,proposal]+[Path(p) for p in data['input_sha256']]+[A/n for n in ['run_small_wrist_recorded_diagnostic.py','near_contact_initial_audit.py','strap_trial_recording.py','warmstart_targets.py']]
        assert sha(A/'run_palm_witness_initial_diagnostic.py')=='2f6565f3e5bf79b682a5704fcbbaf5978ff925c53fd6a130a92f46e145bdd380'
        assert sha(A/'run_small_wrist_recorded_diagnostic.py')=='34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6'
        cmd += ['--trial',str(trial),'--proposal',str(proposal),'--out',str(P/'native')]
    if stage=='analysis':
        assert not (P/'analysis.json').exists()
        paths += [P/'preparation.json',P/'proposal.json',P/'native_execution.json']
        for folder in [P/'native',P.parent/'small_wrist_motion_v1/native']:
            paths += [folder/n for n in ['initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','capture.json','report.json','videos.json']]
        paths += [A/n for n in ['analyze_small_wrist_motion.py','analyze_body9_strap_minus4mm.py','analyze_body9_strap_fine.py','strap.py','warmstart_targets.py']]
    before={str(p):sha(p) for p in paths};snapshot=P/(stage+'_source');snapshot.mkdir(exist_ok=False)
    for p in paths:
        if p.suffix=='.py' or p.name=='JOINT_ONLY_FIXED_STRAP_PLAN.md':shutil.copy2(p,snapshot/p.name)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_small_wrist',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
    started=time.monotonic()
    with (P/(stage+'.log')).open('xb') as log:result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    after={str(p):sha(p) for p in paths}
    (P/(stage+'_execution.json')).write_text(json.dumps(dict(command=cmd,environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MUJOCO_GL','MPLBACKEND','MPLCONFIGDIR','PYTHONPATH','LD_LIBRARY_PATH']},exit_code=result.returncode,wall_seconds=time.monotonic()-started,input_sha256_before=before,input_sha256_after=after,log_sha256=sha(P/(stage+'.log'))),indent=2)+'\n')
    print((P/(stage+'.log')).read_text()[-4500:]);assert result.returncode==0 and before==after
if __name__=='__main__':main()
