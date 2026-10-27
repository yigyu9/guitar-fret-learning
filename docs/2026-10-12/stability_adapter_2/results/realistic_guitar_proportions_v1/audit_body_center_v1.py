"""Distinguish the tapered body's true envelope center, mid-depth point and COM."""
from pathlib import Path
import hashlib,json
import numpy as np
import trimesh
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    path=R/'stability_adapter_2/assets/realistic_guitar_v1/manifest.json';m=json.loads(path.read_text());inputs={str(Path(__file__)):sha(__file__),str(path):sha(path)};bounds=[]
    for e in m['meshes'][:2]:
        inputs[e['path']]=sha(e['path']);mesh=trimesh.load(e['path'],force='mesh');bounds.append(mesh.bounds+np.array(m['legacy_body_reference_G_m']))
    bounds=np.array(bounds);low=bounds[:,0].min(0);high=bounds[:,1].max(0);center=(low+high)/2;declared=np.array(m['body_envelope_center_G_m']);assert abs(center[2]-(m['body_front_plane_G_z_m']-max(m['new_body_depth_range_m'])/2))<1e-9
    propspath=P/'native_realistic_v2/native_properties.json';inputs[str(propspath)]=sha(propspath);props=json.loads(propspath.read_text());body=next(e for e in props['applied'] if e['name']=='G:body');com=np.array(m['legacy_body_reference_G_m'])+np.array(body['COM_body_m'])
    result={'passed':all(sha(p)==h for p,h in inputs.items()),'input_sha256':inputs,'body_bounds_G_m':[low.tolist(),high.tolist()],'actual_envelope_center_G_m':center.tolist(),'body_mid_length_depth_reference_G_m':declared.tolist(),'native_G_body_COM_G_m':com.tolist(),'correction':'The frozen manifest field body_envelope_center_G_m was computed with mean depth: it is a mid-length depth reference, not the true bounding-envelope center. Actual tapered envelope center uses maximum depth. Preserve manifest/verification_v1; use this companion and verification_v2 for center analyses.','scope':'body geometric envelope center is neither legacy body-origin marker nor whole-guitar aggregate COM; native G:body COM is an applied proxy property, not measured hollow wood COM'}
    with (P/'body_center_audit_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2));assert result['passed']
if __name__=='__main__':main()
