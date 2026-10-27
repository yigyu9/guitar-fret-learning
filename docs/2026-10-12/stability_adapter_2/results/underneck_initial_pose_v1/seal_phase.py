"""Root-only final evidence preservation; no physical or task success inference."""
from pathlib import Path
import json,hashlib,re,sys,ast
P=Path(__file__).resolve().parent
A=P.parents[4]/'stability_adapter_2'
# Derive workspace by known docs ancestor instead of a mutable cwd.
A=next(parent for parent in P.parents if (parent/'stability_adapter_2/AGENTS.md').is_file())/'stability_adapter_2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
expected_review=sys.argv[1]
assert sha(P/'review.md')==expected_review
assert not (P/'final_verification.json').exists() and not (P/'artifact_inventory.json').exists()
input_checks={}
for f in sorted(P.rglob('attempt.json')):
    d=read(f);errors=[p for p,h in d['input_sha256'].items() if sha(p)!=h]
    assert not errors,(str(f),errors)
    input_checks[str(f.relative_to(P))]=len(d['input_sha256'])
for f in [P/'analysis.json']:
    for source,h in read(f)['inputs_sha256'].items():assert sha(source)==h
source_manifest=read(P/'source_final/manifest.json')
for s in source_manifest['snapshots']:
    assert sha(s['snapshot_path'])==s['sha256']
    if s['original_path']!=str(A/'PLAN.md'):assert sha(s['original_path'])==s['sha256']
delta=read(P/'source_final_review_delta/manifest.json')
assert sha(delta['original_path'])==sha(delta['snapshot_path'])==delta['sha256']
figure_checks={}
for folder,producer in [('initial_views_v1','build_initial_montage.py'),('hold_compare_v5','plot_hold_comparison.py'),('hold_compare_v5_v2','plot_hold_comparison_v2.py')]:
    d=read(P/'figures'/folder/'manifest.json')
    for field in ['inputs_sha256','input_sha256','outputs_sha256','output_sha256']:
        for source,h in d.get(field,{}).items():assert sha(source)==h
    assert sha(P/'figures'/producer)==d['producer_sha256']
    figure_checks[folder]=True
links={}
for n in ['README.md','CHANGED_FILES.md']:
    count=0
    for link in re.findall(r'\]\((/[^)]+)\)',(P/n).read_text()):
        assert Path(re.sub(r':\d+$','',link)).exists(),link
        count+=1
    links[n]=count
trial_checks={}
for n in ['physics_off','physics_follow','physics_hold','physics_hold_v5']:
    d=read(P/n/'report.json');assert d['completed'] and d['physics_steps']==1200 and d['frame_count']==151
    assert all(d['checks'].values()) and all(read(P/n/'initial_audit.json')['checks'].values())
    assert d['source_clear'] and not d['strap_force_enabled'] and not d['strap_visible']
    videos=read(P/n/'images/videos.json')
    for v in videos.values():
        assert sha(v['path'])==v['sha256'] and int(v['stream']['nb_read_frames'])==151
        assert v['stream']['avg_frame_rate']=='30/1' and abs(float(v['stream']['duration'])-5.033333)<1e-6
    trial_checks[n]={'physics_steps':1200,'pose_samples':len(read(P/n/'trace.json')),'frames_per_view':151,'views':list(videos),'report_checks':d['checks']}
assert 'Ran 4 tests' in (P/'hold_cpu_tests_v5.log').read_text() and '\nOK\n' in (P/'hold_cpu_tests_v5.log').read_text()
analysis=read(P/'analysis.json');assert analysis['hold_v4_vs_v5_trace_exact'] and analysis['hold_v4_vs_v5_controls_exact']
for n in trial_checks:assert analysis[n]['initial_common_fields_exact_with_OFF']
for p in A.glob('underneck_*.py'):ast.parse(p.read_text())
for p in [A/'bounded_arm_hold.py',A/'tests/test_bounded_arm_hold.py',A/'tests/test_underneck_trial_guard_v5.py']:ast.parse(p.read_text())
verification={'technical_evidence_checks_passed':True,'task_success_certificate':False,'initial_native_pose_and_5s_environment_created':True,
    'three_face_contact_maintenance_achieved':False,'music_or_training_executed':False,
    'final_trial':'physics_hold_v5','native_runtime':'Isaac Gym CPU PhysX with Mesa software Vulkan; no CUDA training qualification',
    'review_sha256':expected_review,'main_current_sha256':{str(A/n):sha(A/n) for n in ['PLAN.md','README.md','CURRENT_FILES.md']},
    'all_recorded_attempt_input_checks':input_checks,'figure_manifest_checks':figure_checks,'local_result_link_checks':links,
    'trial_checks':trial_checks,'CPU_tests_passed':4,'source_snapshot_manifest_sha256':sha(P/'source_final/manifest.json'),
    'main_review_delta_manifest_sha256':sha(P/'source_final_review_delta/manifest.json'),
    'analysis_sha256':sha(P/'analysis.json'),'result_docs_sha256':{n:sha(P/n) for n in ['README.md','CHANGED_FILES.md']},
    'known_limitations':['Initial proxy distance and zero source volume intersections do not certify cooked PhysX clearance/anatomical pads.',
        'Selected hold improves drift but palm/index/middle maintenance missing in 150 contact samples; dominant thumb/pinky rows.',
        '3 of151 pose samples are below user height box by up to0.661337mm; whole rotation-envelope containment and playing accuracy untested.',
        'Contact sample unions and all-step body-pair row counts are separate; positive raw lambda is not calibrated force in Newtons.',
        'Bounded PI is initial-angle diagnostic, not final fret/strike control. Float32 submitted rate/cap have ULP differences.',
        'search_060 omitted producer own initial hash; v4 force-setter guard test failed, fixed and passed in final v5. Rejected/failure originals preserved.',
        'source_final is bounded direct package snapshot plus external origin hashes, not standalone full recursive replay closure.']}
(P/'final_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
files=[]
for p in sorted(P.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc' or p.name=='artifact_inventory.json':continue
    files.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
(P/'artifact_inventory.json').write_text(json.dumps({'scope':'All current phase files excluding this inventory and bytecode/cache; exact whole videos/native frames included. Review/document/source inputs remain frozen.','file_count':len(files),'files':files},indent=2)+'\n')
assert sha(P/'review.md')==expected_review
print(json.dumps({'technical_checks':True,'task_success_certificate':False,'trial_count':len(trial_checks),'inventory_files':len(files),'review_sha256':expected_review}))
