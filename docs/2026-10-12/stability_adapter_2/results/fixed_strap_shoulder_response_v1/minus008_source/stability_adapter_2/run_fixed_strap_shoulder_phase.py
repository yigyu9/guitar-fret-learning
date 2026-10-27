"""Preserve and run a single stage of the current fixed-LA shoulder probe."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['preparation','minus008','plus008','analysis']);stage=ap.parse_args().stage
    module='prepare_fixed_strap_shoulder_response' if stage=='preparation' else 'analyze_fixed_strap_shoulder_response' if stage=='analysis' else 'run_palm_witness_initial_diagnostic'
    assert not (P/(stage+'_execution.json')).exists() and not (P/(stage+'.log')).exists()
    paths=[Path(__file__).resolve(),A/(module+'.py'),A/'FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.'+module]
    if stage in ['minus008','plus008']:
        assert not (P/stage).exists();proposal=P/'proposal.json';data=json.loads(proposal.read_text());row=next(r for r in data['rows'] if r['label']==stage);trial=Path(row['trial_path']);assert all(data['checks'].values()) and sha(trial)==row['trial_sha256'] and all(sha(p)==h for p,h in data['input_sha256'].items())
        paths += [proposal,trial]+[Path(p) for p in data['input_sha256']]+[A/n for n in ['run_small_wrist_recorded_diagnostic.py','near_contact_initial_audit.py','strap_trial_recording.py','warmstart_targets.py']]
        assert sha(A/'run_palm_witness_initial_diagnostic.py')=='2f6565f3e5bf79b682a5704fcbbaf5978ff925c53fd6a130a92f46e145bdd380' and sha(A/'run_small_wrist_recorded_diagnostic.py')=='34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6'
        cmd += ['--trial',str(trial),'--proposal',str(proposal),'--out',str(P/stage)]
    if stage=='analysis':
        paths += [P/n for n in ['preparation.json','proposal.json','minus008_execution.json','plus008_execution.json','minus008/initial_grip_audit.json','plus008/initial_grip_audit.json']]
        paths += [A/n for n in ['analyze_small_wrist_motion.py','analyze_body9_strap_minus4mm.py','analyze_body9_strap_fine.py','warmstart_targets.py','strap.py','build_fixed_lower_asset.py']]
        for folder in [P/'minus008',P/'plus008',P.parent/'joint_only_fixed_strap_v1/native']:
            paths += [folder/n for n in ['initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','capture.json','report.json','videos.json']]
    before={str(p):sha(p) for p in paths};snapshot=P/(stage+'_source');snapshot.mkdir(exist_ok=False);manifest={}
    for p in dict.fromkeys(paths):
        if p.suffix=='.py' or p.name=='FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md':
            dest=snapshot/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(dest)==before[str(p)];manifest[str(p)]=dict(snapshot=str(dest),sha256=before[str(p)])
    (P/(stage+'_source_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_small_wrist',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');started=time.monotonic()
    with (P/(stage+'.log')).open('xb') as log:result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    after={str(p):sha(p) for p in paths};(P/(stage+'_execution.json')).write_text(json.dumps(dict(command=cmd,environment={k:env[k] for k in ['MUJOCO_GL','MPLBACKEND','MPLCONFIGDIR','PYTHONPATH','LD_LIBRARY_PATH','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},exit_code=result.returncode,wall_seconds=time.monotonic()-started,input_sha256_before=before,input_sha256_after=after,log_sha256=sha(P/(stage+'.log'))),indent=2)+'\n')
    print((P/(stage+'.log')).read_text()[-3500:]);assert result.returncode==0 and before==after
if __name__=='__main__':main()
