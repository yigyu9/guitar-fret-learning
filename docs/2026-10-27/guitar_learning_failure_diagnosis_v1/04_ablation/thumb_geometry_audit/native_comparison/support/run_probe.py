"""Docs-only fixed-guitar paired thumb probe; unchanged original15s protocol."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--surface',choices=('current_all_vertices','face_only_playing_neck1'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--video',action='store_true')
    args=parser.parse_args()
    out=args.out.resolve()
    if out.exists():raise FileExistsError(str(out))
    import isaacgym
    import numpy as np
    import torch
    from surfaces import load_surfaces,dual_geometry,source_paths,validate_freeze
    from guitar_learning.gpu import scene as scene_module,thumb_support
    from guitar_learning.tool.validation import thumb_contact_probe as probe,hand_contact_probe
    pins=validate_freeze();surfaces=load_surfaces();selected=surfaces[args.surface]
    pins.update(selected['contract']['source_sha256'])
    original_scene,original_load,original_geometry,original_paths=(scene_module.GpuScene,
        thumb_support.load_thumb_support,thumb_support.thumb_support_geometry,hand_contact_probe.physics_source_paths)
    created=[];failure=None;output_identity=None
    def fixed_scene(*values,**kwargs):
        kwargs['diagnostic_guitar_mode']='fixed'
        value=original_scene(*values,**kwargs);created.append(value);return value
    def geometry(*values,**kwargs):return dual_geometry(original_geometry,surfaces,*values,**kwargs)
    scene_module.GpuScene=fixed_scene
    thumb_support.load_thumb_support=lambda:selected
    thumb_support.thumb_support_geometry=geometry
    def source_paths_for_new_output(root):
        nonlocal output_identity
        # The base probe invokes this only after its exclusive mkdir succeeds.
        stat=out.stat();output_identity=(stat.st_dev,stat.st_ino)
        return original_paths(root)|set(map(Path,pins))
    hand_contact_probe.physics_source_paths=source_paths_for_new_output
    previous_argv=sys.argv
    sys.argv=[str(Path(probe.__file__).resolve()),'--out',str(out),'--mode','contact','--controls','900']+(['--video'] if args.video else [])
    try:
        probe.main()  # Original -0.3mm schedule, limits, PD, gravity, fail guards and protocol.
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        sys.argv=previous_argv
        scene_module.GpuScene,thumb_support.load_thumb_support=original_scene,original_load
        thumb_support.thumb_support_geometry,hand_contact_probe.physics_source_paths=original_geometry,original_paths
        if output_identity is not None and out.is_dir() and (out.stat().st_dev,out.stat().st_ino)==output_identity:
            changed=[p for p,h in pins.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
            report_path=out/'report.json';base=json.loads(report_path.read_text()) if report_path.exists() else {}
            if report_path.exists():(out/'base_probe_report.json').write_text(report_path.read_text())
            capture={};checks={};scene=created[0] if created else None
            raw=out/'physics_env0000.npz'
            if raw.exists():
                with np.load(raw) as a:
                    names=base['native_joint_names'];ids=base['thumb_joint_indices'];target=a['target'][:,ids]
                    control=target[3::4];reference=target[0]
                    capture=dict(physical_endpoints=len(target),finite=all(np.isfinite(a[k]).all() for k in a.files if a[k].dtype.kind not in 'US'),
                        max_target_excursion_deg=float(np.rad2deg(np.abs(target-reference).max())),
                        max_target_change_per_control_deg=float(np.rad2deg(np.abs(np.diff(np.vstack((reference,control)),axis=0)).max())),
                        max_abs_qd_rad_s=float(np.abs(a['qd']).max()),scene_fixed_guitar_translation_max_m=float(a['guitar_translation'].max()),
                        scene_fixed_guitar_rotation_max_rad=float(a['guitar_rotation'].max()),
                        same_point_metric_scope='both geometry conditions evaluated at primary selected physical point with identical actual thumb3 force',
                        conditions={})
                    point=a['thumb_selected_point'];force=a['thumb_force_G']
                    for condition,surface in surfaces.items():
                        p=np.asarray(surface['plane']);unit=p[:3]/np.linalg.norm(p[:3]);offset=p[3]/np.linalg.norm(p[:3])
                        gap=point@unit+offset;load=np.maximum(force@unit,0)
                        prefix='thumb_comparison_'+condition+'_'
                        checks[condition]=dict(gap_max_error=float(np.max(np.abs(gap-a[prefix+'signed_gap']))),
                            normal_load_max_error=float(np.max(np.abs(load-a[prefix+'normal_load']))),
                            normal_load_close=bool(np.allclose(load,a[prefix+'normal_load'],atol=2e-5,rtol=2e-6)))
                        capture['conditions'][condition]=dict(candidate_samples=int(a[prefix+'contact_candidate'].sum()),
                            signed_gap_range_m=[float(a[prefix+'signed_gap'].min()),float(a[prefix+'signed_gap'].max())],
                            normal_load_max_N=float(a[prefix+'normal_load'].max()),normal_cos_range=[float(a[prefix+'normal_cos'].min()),float(a[prefix+'normal_cos'].max())])
                    capture['within_original_request_bounds']=capture['max_target_excursion_deg']<=15.0001 and capture['max_target_change_per_control_deg']<=.5001
                    if scene:
                        lower,upper=scene.lower[ids].cpu().numpy(),scene.upper[ids].cpu().numpy()
                        capture['native_target_limit_excess_max_rad']=float(np.maximum(np.maximum(lower-target,target-upper),0).max())
                        capture['target_at_native_limit_fraction_per_thumb_joint']=((target-lower<=1e-5)|(upper-target<=1e-5)).mean(0).tolist()
                        capture['target_at_15deg_excursion_fraction_per_thumb_joint']=(np.abs(target-reference)>=np.deg2rad(15)-1e-5).mean(0).tolist()
            diagnostics=scene.diagnostics if scene else None
            closed=bool(diagnostics and diagnostics['closed'])
            valid=bool(failure is None and base.get('completed') and not changed and closed and capture.get('finite')
                and capture.get('physical_endpoints')==3600 and capture.get('within_original_request_bounds')
                and capture.get('native_target_limit_excess_max_rad',1)<2e-6
                and diagnostics.get('diagnostic_guitar_mode')=='fixed'
                and diagnostics.get('physics_steps')==3600 and diagnostics.get('environment_count')==1
                and diagnostics.get('physx_use_gpu') and diagnostics.get('use_gpu_pipeline')
                and diagnostics.get('diagnostic_guitar_asset',{}).get('requested_disable_gravity') is False
                and (not args.video or (base.get('frames')==450 and base.get('video_encoder_exit')==0))
                and all(c['gap_max_error']<2e-7 and c['normal_load_close'] for c in checks.values()))
            result=dict(schema='diagnostic.thumb_rear_geometry_comparison.v1',completed=valid,failure=failure,
                condition=args.surface,physical_asset_unchanged=True,native_candidate_contract='new diagnostic geometry input; original thresholds and resultant-load proxy; not learned music performance',
                scope='one fixed guitar035 native environment; thumb5 finite control; no policy or actor-state overwrite',
                original_probe_scope_correction='base report says free guitar; this wrapper requests fixed for both conditions, same physical asset/gravity',
                original_approach_minimum_gap_m=-.0003,controls=900,source_pins=pins,source_pins_unchanged=not changed,changed_inputs=changed,
                surface_contract=selected['contract'],source_geometries={k:dict(rear_vertices=v['rear_vertices'].tolist(),plane=v['plane'].tolist()) for k,v in surfaces.items()},
                raw_capture=capture,independent_same_point_checks=checks,scene_closed=closed,scene=diagnostics,base_probe=base)
            result['native_PD_sha256']=(hashlib.sha256(json.dumps(
                {key:scene.pd_properties[key].tolist() for key in scene.pd_properties.dtype.names},
                sort_keys=True,separators=(',',':')).encode()).hexdigest() if scene else None)
            report_path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            if failure is None and not valid:raise RuntimeError('Native geometry comparison audit failed')


if __name__=='__main__':main()
