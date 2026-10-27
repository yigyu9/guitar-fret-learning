"""Preserve the baseline source capsule distances used in the comparison."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from stability_adapter_2.om_axilla_source_geometry_v3 import CapsuleBodyDistance
from stability_adapter_2.upper_arm_static_geometry_v1 import ASSET
P=Path(__file__).resolve().parent;R=P.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 candidate=R/'docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v5/right4_close_support/candidate.json';geometry=R/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json';c=json.loads(candidate.read_text());g=json.loads(geometry.read_text());files=[Path(__file__).resolve(),candidate,geometry,ASSET,Path(g['asset'])]+[Path(m['path'])for m in g['meshes']];inputs={str(f):sha(f)for f in files};poses={n:(np.array(v['p']),Rotation.from_quat(v['q']))for n,v in c['predicted_human_poses'].items()};d=CapsuleBodyDistance(g['asset'],ASSET);rows={str(f):d.measure(poses,'R_Shoulder',np.array(c['position_W_m']),Rotation.from_quat(c['quaternion_xyzw']),f)for f in [.2,.35,.65,1.]};assert all(sha(Path(p))==h for p,h in inputs.items())
 with (P/'baseline_source_probe_v1.json').open('x')as out:json.dump({'input_sha256':inputs,'shoulder_capsule_fraction_limits':rows,'scope':'source analytic distances only, not native cooked clearance or actual contact'},out,indent=2)
 print(rows['0.35']['gap_m']*1000)
if __name__=='__main__':main()
