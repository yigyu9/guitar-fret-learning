from pathlib import Path
import json,hashlib,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1';art=P/'artifacts';target=P/'artifact_revised_preserved'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=A/'make_palm_witness_artifacts.py';recovered=Path('/tmp/make_palm_witness_artifacts_reconstructed.py');saved=A/'make_palm_witness_artifacts_v1_recovered.py'
assert sha(source)=='4c4b2ccfbaedd9606747cad537777a69829c1d280cebe975360dca29d0095c2a'
assert sha(recovered)=='61ea48b82aed0f27d3c005c17bedfc9b3edec157d55b7f6cdc712a18b95161fe'
assert sha(art/'recovered_v1/palm_witness_diagnostics.png')=='db6c6964dacc0c816272be17179b33813144b6692bd97dde1b4b3f412bfde68f'
assert not saved.exists() and not (P/'artifact_revision_preservation.json').exists()
shutil.copy2(recovered,saved);shutil.copy2(saved,art/'recovered_v1/producer_source.py')
paths=[source]+[p for p in art.iterdir() if p.is_file()];target.mkdir(exist_ok=True);records={}
for p in paths:
 d=target/p.name
 if d.exists():assert sha(p)==sha(d)
 else:shutil.copy2(p,d)
 assert sha(p)==sha(d);records[str(p)]={'snapshot':str(d),'sha256':sha(d)}
shutil.copy2(__file__,P/'artifact_recovery_seal_producer.py')
(P/'artifact_revision_preservation.json').write_text(json.dumps({'scope':'exact retrospective archive of revised set and SHA-verified reconstruction of original source/PNG; no new physics', 'original_source_sha256':sha(saved),'original_png_sha256':sha(art/'recovered_v1/palm_witness_diagnostics.png'),'recovered_source_path':str(saved),'recovered_png_path':str(art/'recovered_v1/palm_witness_diagnostics.png'),'original_execution_manifest_log_metadata_byte_recovery_verified':False,'recovery_manifest_scope':'new manifest from recovery run, not original execution manifest; original source/PNG SHA were observed by root before overwrite','recovery_execution_scope':'Luna reports re-render with no native; complete independent local stdout execution capture was not retained','revised':records},indent=2)+'\n')
print('revised5files/source and original source/PNG SHA verified',len(records))
