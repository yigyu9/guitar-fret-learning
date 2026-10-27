from pathlib import Path
import ast, hashlib, json, re, shutil

R=Path('/home/ajou/yigyu/3'); A=R/'stability_adapter_2'
D=R/'docs/2026-10-12/stability_adapter_2'; B=D/'results'
P=B/'coupled_support_source_v1'; PREV=B/'body9_strap_minus4mm_v1'
checks={}; cache={}
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    p=Path(p)
    if str(p) not in cache:
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''): h.update(b)
        cache[str(p)]=h.hexdigest()
    return cache[str(p)]
def check(name,value):
    assert value,name
    checks[name]=True
def closure(values): return all(sha(p)==h for p,h in values.items())

m=read(P/'model.json')
check('conditional_model5_checks_264_rows_4_samples',len(m['checks'])==5 and all(m['checks'].values()) and len(m['validation'])==264 and len(m['samples'])==4 and all(r['passed'] for r in m['validation']))
check('model_inputs_and_copies_exact',closure(m['input_sha256']) and all(sha(A/s)==sha(P/s) for s in ['coupled_support_source.py','check_coupled_support_model.py']))
check('model_execution0_tool_capture_limitation_retained',read(P/'model_execution.json')['observed_exit_code']==0 and 'no complete local stdout' in read(P/'model_execution.json')['stdout_capture'])
for suffix in ['', '_v2', '_v3']:
    data=read(P/('search'+suffix+'.json')); exe=read(P/('search_execution'+suffix+'.json'))
    source=A/('search_coupled_support_source'+suffix+'.py')
    check('search'+suffix+'_execution_inputs_source_log_exact',all(data['checks'].values()) and closure(data['input_sha256']) and exe['exit_code']==0 and exe['source_sha256_before']==exe['source_sha256_after']==sha(source)==sha(P/('search_source'+suffix+'.py')) and exe['log_sha256']==sha(P/('search'+suffix+'.log')))
    check('search'+suffix+'_source_only',data['native_initializations']==data['physics_steps']==exe['native_initializations']==exe['physics_steps']==0)
for version in ['v1','v2']:
    folder=P/('search_'+version+'_preserved')
    check(version+'_originals_preserved',len(list(folder.iterdir()))==5 and all(sha(f)==sha(P/f.name) for f in folder.iterdir()))
d=read(P/'search_v3.json'); rows=d['rows']
check('v3_7_checks_4baseline12proposals',len(d['checks'])==7 and len(rows)==16 and len([r for r in rows if r['fraction']==0])==4)
check('v3_all110_sameleft_nonadjacent',all(r['same_left_nonadjacent_pair_count']==110 for r in rows))
check('v3_only_halfsecond_quarter_passes',[(r['step'],r['fraction']) for r in rows if r['source_direction_screen_passed']]==[(120,.25)])
init=read(B/'body9_strap_minus2mm_v1/native/initial_values.json')
controls=[json.loads(s) for s in (B/'body9_strap_minus2mm_v1/native/controls.jsonl').read_text().splitlines()]
indices=[init['human_joint_names'].index(n) for n in d['selected_names']]
for n,r in enumerate(rows):
    base=controls[0 if r['step']==0 else r['step']-1]['final_target_rad']
    check('row'+str(n)+'_original_base_held63_delta',r['base_target_rad']==base and all(r['final_target_rad'][j]==base[j] for j in range(81) if j not in indices) and all(abs(r['final_target_rad'][j]-base[j]-r['delta_rad'][k])<1e-14 for k,j in enumerate(indices)) and r['PD_and_actual_delta_bounds'])
    upper=min(v['distance_m'] for v in r['patch_distance_intervals']['LH:palm'])
    check('row'+str(n)+'_patch_interval_gate',r['palm_patch_approach_certified']==(upper<r['baseline_palm_patch_lower_m']-1e-9))

counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy()
counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,expected in counts.items():
    inventory=read(B/name/'artifact_inventory.json')
    check('preserved_phase_'+name,len(inventory)==expected and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inventory.items()))
protected=read(B/'palm_neck_side_v1/preservation_reference/protected_original_stat.json')
check('legacy87_stat_exact',len(protected)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in protected.items()))
aug=read(B/'palm_neck_side_v1/preservation_reference/aug19_sha256.json')
check('aug19_49_sha_exact',len(aug)==49 and closure(aug))
before=read(P/'journal_and_design_before.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:
    b=p.read_bytes()[:before[str(p)]['size']]
    check('append_only_'+p.name,hashlib.sha256(b).hexdigest()==before[str(p)]['sha256'])
check('consumed_prior_learning_plan_unchanged',sha(A/'PLAYING_PRIOR_ADAPTATION_PLAN.md')==before[str(A/'PLAYING_PRIOR_ADAPTATION_PLAN.md')]['sha256'])
check('no_new_native_video_collection',len(list((D/'videos').glob('*.mp4')))==126)
artifact=read(P/'artifacts/artifact_manifest.json'); art_exe=read(P/'artifacts/artifact_execution.json')
check('artifact_all_inputs_outputs_exact',artifact['inputs_sha256_before']==artifact['inputs_sha256_after'] and closure(artifact['inputs_sha256_before']) and closure(artifact['outputs_sha256']))
check('artifact_execution0_source_log_exact',art_exe['exit_code']==art_exe['native_calls']==0 and art_exe['producer_sha256_before']==art_exe['producer_sha256_after']==artifact['producer_sha256']==sha(A/'make_coupled_support_artifacts.py') and art_exe['log_sha256']==sha(P/'artifacts/artifact_execution.log') and art_exe['manifest_sha256']==sha(P/'artifacts/artifact_manifest.json'))
check('artifact_source_scope_16placements1pass',artifact['source_geometry_only'] and artifact['placement_count']==16 and artifact['source_screen_pass_count']==1 and all(artifact[k]==0 for k in ['native_calls','native_initializations','physics_steps','model_inference_calls','training_updates']))
sources=['coupled_support_source.py','check_coupled_support_model.py','search_coupled_support_source.py','search_coupled_support_source_v2.py','search_coupled_support_source_v3.py','make_coupled_support_artifacts.py']
for s in sources:
    ast.parse((A/s).read_text(),feature_version=(3,8))
check('all_new_python38_syntax',True)
check('independent_review_recorded',(P/'review.md').is_file())
check('actual_graphic_QA_recorded',(P/'ROOT_VERIFICATION_NOTES.md').is_file() and 'QA' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
for p in list(P.glob('*.md'))+[A/'PLAYING_RESIDUAL_EVALUATION.md',A/'COUPLED_SUPPORT_SOURCE_DECISION.md']:
    for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',p.read_text()):
        q=Path(target)
        if q.name=='final_verification.json' and q.parent==P: continue
        check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
shutil.copy2(__file__,P/'root_final_audit_producer.py')
files=[A/s for s in sources]+[A/s for s in ['COUPLED_SUPPORT_SOURCE_EXECUTION.md','COUPLED_SUPPORT_SOURCE_CORRECTION.md','COUPLED_SUPPORT_SELF_SCREEN.md','COUPLED_SUPPORT_SOURCE_DECISION.md','PLAYING_RESIDUAL_EVALUATION.md','README.md','PLAN.md']]+[D/'VISUAL_REPORT.md']+list(P.glob('*.md'))
manifest={}
for p in files:
    dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps({'checks':checks,'counts':{'checks':len(checks),'previous_inventories':counts,'native_initializations':0,'physics_steps':0,'actor_inference_calls':0,'training_updates':0},'source_snapshot_manifest_sha256':sha(P/'source_final_manifest.json')},ensure_ascii=False,indent=2)+'\n')
inventory={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'protected_previous_phases':len(counts),'inventory':len(inventory),'native':0,'physics_steps':0}))
