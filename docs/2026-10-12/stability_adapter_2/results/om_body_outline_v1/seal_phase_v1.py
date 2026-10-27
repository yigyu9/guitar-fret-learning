"""Audit exterior-only extraction and preservation before sealing the small stage."""
from pathlib import Path
import hashlib
import json
import numpy as np

R = Path('/home/ajou/yigyu/3')
A = R/'stability_adapter_2'
P = R/'docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1'
B = P.parent/'acoustic_guitar_appearance_v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name,data):
    path=P/name
    assert not path.exists()
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


one,two=read(P/'outline_v1.json'),read(P/'outline_v2.json')
assert one['passed'] and two['passed'] and one['outline_body_xy_m']==two['outline_body_xy_m']
for data,image in [(one,'body_outline_comparison.png'),(two,'body_outline_comparison_v2.png')]:
    assert all(sha(path)==value for path,value in data['input_sha256'].items())
    assert sha(P/image)==data['output_image_sha256']
assert sha(P/'OM_acoustic_guitar.dxf')==read(P/'download.json')['sha256']
assert len(two['source_entities'])==16 and two['native_runs']==two['asset_changes']==0
assert two['max_join_gap_mm']<1e-8 and two['source_closure_gap_mm']<.02
v=np.asarray(two['outline_body_xy_m'])
assert np.array_equal(v[0],v[-1]) and np.isfinite(v).all()
mirror=v.copy();mirror[:,0]*=-1
dist=np.linalg.norm(v[:,None,:]-mirror[None,:,:],axis=2)
symmetry_error=float(max(dist.min(0).max(),dist.min(1).max()))
assert symmetry_error<1e-8
v=v[np.r_[True,np.linalg.norm(np.diff(v,axis=0),axis=1)>1e-12]]
cross=lambda u,w:u[...,0]*w[...,1]-u[...,1]*w[...,0]
intersections=0
for i in range(len(v)-2):
    j=np.arange(i+2,len(v)-1)
    if i==0:j=j[j<len(v)-2]
    a,b=v[i],v[i+1];c,d=v[j],v[j+1]
    hits=(cross(b-a,c-a)*cross(b-a,d-a)<-1e-20)&(cross(d-c,a-c)*cross(d-c,b-c)<-1e-20)
    intersections+=int(hits.sum())
assert intersections==0

main=read(P/'main_append_v1.json');paths={e['path'] for e in main}
for e in main:
    assert sha(e['snapshot'])==e['before_sha256'] and sha(e['path'])==e['after_sha256']
    assert Path(e['path']).read_bytes().startswith(Path(e['snapshot']).read_bytes())
prior=read(B/'artifact_inventory_v1.json')['files']
for e in prior:
    original=next(m['snapshot'] for m in main if m['path']==e['path']) if e['path'] in paths else e['path']
    assert sha(original)==e['sha256'],e['path']
previous=read(B/'final_verification_v1.json')
assert previous['passed'] and sha(B/'artifact_inventory_v1.json')==previous['inventory_sha256']
assert sha(B/'source_final_v1.json')==previous['source_final_sha256']
review=P/'review_final_v1.md';assert review.is_file() and review.stat().st_size>0
sources=[A/'OM_BODY_OUTLINE_PLAN_V1.md',A/'extract_om_body_outline_v1.py',A/'extract_om_body_outline_v2.py',Path(__file__).resolve(),review]
sources += [Path(path) for path in paths]
save('source_final_v1.json',{str(path):sha(path) for path in sources})
files={f for f in P.rglob('*') if f.is_file()}|set(sources)
inventory=[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(files)]
save('artifact_inventory_v1.json',{'files':inventory})
save('final_verification_v1.json',{'passed':True,'source_inputs_exact':True,'outline_v1_v2_exact':True,
    'symmetry_pointset_error_m':symmetry_error,'strict_edge_intersections':intersections,
    'prior_preserved_files':len(prior),'native_runs':0,'asset_changes':0,
    'review_sha256':sha(review),'source_final_sha256':sha(P/'source_final_v1.json'),
    'inventory_sha256':sha(P/'artifact_inventory_v1.json')})
print(json.dumps({'passed':True,'prior_files_preserved':len(prior),'symmetry_error_m':symmetry_error}))
