"""CPU provenance at saved audible env0 reference endpoints; no simulation."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path('/home/ajou/yigyu/3')
PARENT=ROOT/'docs/2026-10-27/guitar_learning_failure_diagnosis_v1'
BASE=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')


def main():
    import torch
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from guitar_learning.gpu.geometry import apply,conjugate
    from guitar_learning.gpu.environment import CONTACT_CONTRACT
    from guitar_learning.gpu.wrong_press import pad_contact_cells,wrong_press_sources
    from guitar_learning.training.recording import project_source_paths
    sys.path.insert(0,str(PARENT/'02_contact_reward/support'))
    from current_contact_replay import sample_masks
    torch.set_num_threads(1)
    folder=PARENT/'03_short_learning/smoke_wrist_inc_row8_reference'
    trace_file=folder/'trace_env0_episode0.npz';a=np.load(trace_file)
    settings_file=folder/'settings.json';settings=json.loads(settings_file.read_text())
    metadata_file=PARENT/'02_contact_reward/teacher_fixed_B_export/metadata.json';metadata=json.loads(metadata_file.read_text())
    evaluation_file=folder/'evaluation.json';evaluation=json.loads(evaluation_file.read_text());env0=next(e for e in evaluation['episodes'] if e['env_id']==0)
    env=ShortEnvironment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],skill=settings['finger_skill'],device='cpu')
    selected=env.selected_index;target=env.task.targets[selected]
    targets=[dict(index=i,target_id=t.target_id,string=t.string,fret=t.fret,finger=t.finger,onset_s=t.onset_s,end_s=t.end_s,press_s=t.press_s) for i,t in enumerate(env.task.targets)]
    frame_ids=np.flatnonzero((a['source_time_s']>=target.onset_s)&(a['source_time_s']<=target.end_s))
    source_code=PARENT/'02_contact_reward/negative_snapshot_audit/support/audit_snapshots.py'
    tree=ast.parse(source_code.read_text());function=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='independent')
    function=copy.deepcopy(function)
    # Return existing intermediate raw classifications for production helper comparison.
    for name in ('normals','qualifies','vf','vn','pad_cells','assigned','nearest'):
        function.body[-1].value.keywords.append(ast.keyword(arg=name,value=ast.Name(id=name,ctx=ast.Load())))
    module=ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[]))
    namespace=dict(np=np,Rotation=Rotation,env=env,metadata=metadata,targets=targets,CONTACT_CONTRACT=CONTACT_CONTRACT)
    exec(compile(module,str(source_code),'exec'),namespace);independent=namespace['independent']
    input_files=[BASE/'precommit.json',Path(__file__),trace_file,settings_file,metadata_file,evaluation_file,source_code,folder/'inputs_before.json']
    pins={str(p.resolve()):sha(p) for p in input_files}
    original_pins=json.loads((folder/'inputs_before.json').read_text());source_matches={}
    for name in ('environment.py','simplified_finger_environment.py','wrong_press.py','fingertip_pad.py','press_surface.py','geometry.py'):
        file=ROOT/'guitar_learning/gpu'/name;source_matches[name]=original_pins.get(str(file))==sha(file)
    assert all(source_matches.values()),source_matches
    for item in env.task.provenance['provenance']:
        assert sha(item['path'])==item['sha256'];pins[item['path']]=item['sha256']
    pins.update({p:sha(p) for p in project_source_paths(list(sys.modules.items()))})
    write(BASE/'inputs_before.json',pins)
    rows=[];mismatches=0
    for frame in frame_ids:
        raw=dict(q=a['q'][frame],target=a['target'][frame],body_state=a['body_state'][frame],contact_force=a['net_body_force_n'][frame])
        env.body=torch.tensor(raw['body_state']).unsqueeze(0);env.guitar_body=env.body[:,env.guitar_index];env.guitar_q=env.guitar_body[:,3:7]
        env.local_bodies=apply(conjugate(env.guitar_q[:,None]),env.body[...,:3]-env.guitar_body[:,None,:3]);env.starts=env.local_bodies[:,env.start_indices];env.ends=env.local_bodies[:,env.end_indices];env.frets=env.local_bodies[:,env.fret_indices]
        env.loaded=torch.linalg.vector_norm(torch.tensor(raw['contact_force']).unsqueeze(0),dim=-1)>=.01
        env.surface_body_loaded=env.loaded[:,env.pad_indices][:,env.finger-1]
        r=independent(raw);positive=torch.tensor(r['positive']).unsqueeze(0)
        pad_points=torch.tensor(r['pad'],dtype=torch.float32).unsqueeze(0);pad_normals=torch.tensor(r['normals'],dtype=torch.float32).unsqueeze(0)
        cells=pad_contact_cells(pad_points,pad_normals,env.pad_valid,env.loaded[:,env.pad_indices],env.starts,env.ends,env.frets,env.press_plane)
        scope=torch.zeros(1,env.M,dtype=torch.bool);scope[0,selected]=True
        production=wrong_press_sources(qualifies=torch.tensor(r['qualifies']).unsqueeze(0),assigned=torch.tensor(r['vf']).unsqueeze(0),nearest=torch.tensor(r['vn']).unsqueeze(0),source_fingers=env.pad_fingers,surface_count=env.surface_count,pad_cells=cells,positive=positive,now=torch.tensor([a['source_time_s'][frame]],dtype=torch.float64),onset=env.onset,end=env.end,press=env.press,scope=scope,strings=env.string,frets=env.fret,fingers=env.finger,fret_count=env.frets.shape[1])
        helper=sample_masks(env,[targets[selected]],torch.tensor([selected]));p=bool(helper['positive_mask'].any());flags=r['flags'][selected];wrong=bool(flags.any());candidate=bool(p and not wrong)
        agree=(p==bool(r['positive'][selected]) and wrong==bool(production['wrong'][0,selected]) and np.array_equal(flags,production['flags'][0,selected].numpy()) and wrong==bool(a['wrong'][frame]) and candidate==bool(a['candidate'][frame]))
        mismatches+=not agree
        sources=[]
        for bi in np.flatnonzero(flags.any(-1)):
            body_index=int(env.finger_indices[bi]);body_name=metadata['body_names'][body_index]
            sources.append(dict(body=body_name,source_finger=bi//2,body_resultant_n=float(np.linalg.norm(raw['contact_force'][body_index])),causes=[name for cause,name in enumerate(('other_higher','own_wrong_fret','own_wrong_string')) if flags[bi,cause]]))
        rows.append(dict(frame=int(frame),local_time_s=float(a['time_s'][frame]),source_time_s=float(a['source_time_s'][frame]),physics_step=int(round(a['time_s'][frame]*240)),selected_target_id=target.target_id,positive=p,wrong=wrong,candidate=candidate,production_raw_agree=bool(agree),causes=[name for c,name in enumerate(('other_higher','own_wrong_fret','own_wrong_string')) if flags[:,c].any()],sources=sources,witness=r['witnesses'][selected],selected_actual_angles_rad={n:float(raw['q'][metadata['joint_names'].index(n)]) for n in settings['song']['short_learning']['learned_action_names']},selected_target_angles_rad={n:float(raw['target'][metadata['joint_names'].index(n)]) for n in settings['song']['short_learning']['learned_action_names']}))
    cause_counts={name:sum(name in row['causes'] for row in rows) for name in ('other_higher','own_wrong_fret','own_wrong_string')}
    changed=[p for p,v in pins.items() if not Path(p).is_file() or sha(p)!=v]
    result=dict(schema='reference_env0_wrong_source_audit.v1',completed=not changed and mismatches==0,gpu_used=False,source_files_unchanged=not changed,changed_inputs=changed,measurement_sources_match_capture=source_matches,
        source=str(trace_file),source_sha256=sha(trace_file),condition='incremental fixed-wrist v2 selected4 finite reference; not policy learning',selected_target=targets[selected],episode_summary=env0,saved_audible_endpoints=len(rows),cause_endpoint_counts=cause_counts,independent_mismatches=int(mismatches),rows=rows,
        limits=['saved60Hz audible endpoints only; no240Hz provenance between endpoints','actual native q/body/force unchanged; no force/pose synthesis','body net load cannot identify contact partner or string pressure','one prescribed reference does not establish irreducibility or trained policy ability','position env0 successful raw belongs to a different condition'])
    write(BASE/'results.json',result);write(BASE/'inputs_after.json',dict(verified=not changed,changed_paths=changed,input_pins=pins))
    if not result['completed']:raise RuntimeError('Raw/provenance/source mismatch')
    print(json.dumps(dict(completed=True,audible_endpoints=len(rows),cause_counts=cause_counts,mismatches=int(mismatches)),indent=2))


if __name__=='__main__':main()
