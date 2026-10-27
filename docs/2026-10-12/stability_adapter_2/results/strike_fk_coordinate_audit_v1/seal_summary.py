"""Seal reviewed saved-trajectory FK audit, without native or music certification."""
import hashlib
import json
from pathlib import Path
import shutil
phase=Path(__file__).resolve().parent
root=phase.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review_sha='63e8e792d0ec2a1415086f1c22f611c79c2ad1826e3e1d0876cfd71c8cc1980c'
assert sha(phase/'review.md')==review_sha
before=json.loads((phase/'analysis/inputs_before.json').read_text())['sha256']
assert len(before)==6 and all(sha(Path(p))==h for p,h in before.items())
assert json.loads((phase/'analysis/inputs_after.json').read_text())['unchanged']
summary=json.loads((phase/'analysis/summary.json').read_text())
assert summary['samples']==151 and len(summary['groups'])==8 and not summary['music_success']
copies=phase/'source_final';copies.mkdir(exist_ok=False)
manifest=[]
for name in ('analyze_strike_fk_coordinates.py','underneck_initial_search.py','STRIKE_FK_COORDINATE_AUDIT_PLAN.md','assets/humanoid_fixed_lower.xml'):
    src=root/'stability_adapter_2'/name;assert sha(src)==before[str(src)]
    target=copies/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target);manifest.append({'source':str(src),'copy':str(target),'sha256':sha(src)})
(copies/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
inventory={str(p.relative_to(phase)):sha(p) for p in sorted(phase.rglob('*')) if p.is_file() and p.name not in ('artifact_inventory.json','final_verification.json')}
(phase/'artifact_inventory.json').write_text(json.dumps({'sha256':inventory},indent=2)+'\n')
(phase/'final_verification.json').write_text(json.dumps({'review_sha256':review_sha,'analysis_input_hashes_exact':True,'samples':151,'groups':8,'artifact_count':len(inventory),'inventory_sha256':sha(phase/'artifact_inventory.json'),'new_physics_steps':0,'music_success':False,'import_before_sealing_certified':False,'scope':'helperimport occurs before internalmanifest; actualFKcalls/XML/rawreads aftermanifest and posthashunchanged. Savednative81 observedtrajectoryaudit only, no unobserveddirectionJacobian certificate.'},indent=2)+'\n')
print('sealed observed-trajectory FK audit',len(inventory),'artifacts')
