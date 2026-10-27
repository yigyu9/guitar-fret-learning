"""CPU geometry-only checks; no native scene or actual contact assertion."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
import torch

from surfaces import BASE,CONDITIONS,load_surfaces,dual_geometry,source_paths
from run_pair import ROOT,jobs
from guitar_learning.gpu.thumb_support import thumb_support_geometry
from guitar_learning.tool.validation.thumb_contact_probe import approach_gap
import surfaces as surface_module


def main():
    if torch.cuda.is_available():raise RuntimeError('CUDA_VISIBLE_DEVICES must be empty for CPU test')
    torch.set_num_threads(1)
    pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths()}
    surfaces=load_surfaces();a,b=[surfaces[c] for c in CONDITIONS]
    for key in ('points_local','normals_local','valid'):np.testing.assert_array_equal(a[key],b[key])
    assert b['rear_vertices'].shape==(4,3) and b['plane'].shape==(4,)
    np.testing.assert_allclose(b['plane'],[0,0,-1,-.008],atol=1e-12,rtol=0)
    np.testing.assert_allclose(b['rear_vertices']@b['plane'][:3]+b['plane'][3],0,atol=1e-12)
    assert sorted(np.unique(b['rear_vertices'][:,1]))==[-.241803,.217197]
    normal=torch.tensor([[[0.,0.,1.]]],dtype=torch.float64);valid=torch.tensor([True]);center=torch.tensor([.04112050979751025],dtype=torch.float64)
    force=torch.tensor([[0.,0.,-.02]],dtype=torch.float64)
    rows=[]
    for point_surface in CONDITIONS:
        p=surfaces[point_surface]['plane'];y=float(center[0]);z=-(p[1]*y+p[3])/p[2]
        point=torch.tensor([[[0.,y,z]]],dtype=torch.float64)
        for primary in CONDITIONS:
            s=surfaces[primary]
            measured=dual_geometry(thumb_support_geometry,surfaces,point,normal,valid,center,
                torch.tensor(s['rear_vertices']),torch.tensor(s['plane']),net_force_guitar=force)
            direct=thumb_support_geometry(point,normal,valid,center,torch.tensor(s['rear_vertices']),torch.tensor(s['plane']),net_force_guitar=force)
            for key,value in direct.items():torch.testing.assert_close(measured[key],value,atol=0,rtol=0)
            result={c:bool(measured['comparison_'+c+'_contact_candidate'][0]) for c in CONDITIONS}
            assert result[point_surface] and not result[CONDITIONS[1-CONDITIONS.index(point_surface)]]
            rows.append(dict(synthetic_point_on=point_surface,primary=primary,candidates=result))
            zero=dual_geometry(thumb_support_geometry,surfaces,point,normal,valid,center,
                torch.tensor(s['rear_vertices']),torch.tensor(s['plane']),net_force_guitar=torch.zeros_like(force))
            assert not any(bool(zero['comparison_'+c+'_contact_candidate'][0]) for c in CONDITIONS)
    assert abs(min(approach_gap(t) for t in np.arange(0,15,1/60))+.0003)<1e-15
    assert ROOT==Path('/home/ajou/yigyu/3')
    plan=jobs(BASE/'CPU_NOT_EXECUTED')
    assert len(plan)==2 and [j['condition'] for j in plan]==list(CONDITIONS)
    assert all(Path(j['args'][4]).is_absolute() for j in plan)
    original_base=surface_module.BASE
    with tempfile.TemporaryDirectory(dir=str(BASE),prefix='cpu-seal-') as temp:
        fake=Path(temp);entry=fake/'input.txt';entry.write_text('original')
        (fake/'frozen_sources.json').write_text(json.dumps(dict(source_pins={str(entry):hashlib.sha256(entry.read_bytes()).hexdigest()})))
        try:
            surface_module.BASE=fake;surface_module.validate_freeze()
            entry.write_text('changed')
            try:surface_module.validate_freeze()
            except ValueError:pass
            else:raise AssertionError('Changed frozen input accepted')
        finally:surface_module.BASE=original_base
    for p in (BASE/'support').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    # Importing/formatting jobs and both surface helpers did not initialize CUDA/Isaac.
    assert 'isaacgym' not in sys.modules
    changed=[p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    assert not changed
    result=dict(completed=True,GPU_used=False,primary_measurement_exactly_preserved=True,
        patch_points_normals_valid_unchanged=True,face_only_neck1_plane_correct=True,finite_neck1_bounds_correct=True,
        same_actual_synthetic_point_force_compared_by_both_geometries=rows,zero_load_candidates_false=True,
        source_approach_min_gap_m=-.0003,depth_schedule_unchanged=True,root_and_jobs_valid=True,
        frozen_input_changes_rejected=True,
        source_pins=pins,changed_inputs=changed,syntax_valid=True,
        scope='synthetic force is used only for CPU predicate checks; not native contact/pressure or learning evidence')
    (BASE/'cpu_self_test.json').write_text(json.dumps(result,indent=2)+'\n')
    (BASE/'dry_run.json').write_text(json.dumps(dict(jobs=plan,GPU_executed=False),indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_pins','same_actual_synthetic_point_force_compared_by_both_geometries')},indent=2))


if __name__=='__main__':main()
