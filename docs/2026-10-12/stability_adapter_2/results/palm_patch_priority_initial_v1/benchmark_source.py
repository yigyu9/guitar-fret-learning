"""Check early separation penalties against the consumed dense formula on real source meshes."""
import ast,hashlib,json,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'palm_patch_priority_initial_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    output=PHASE/'separation_benchmark.json';assert not output.exists()
    from .environment import np
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .build_fixed_lower_asset import ASSET
    from .source_separation_penalty import separation_penalty
    from scipy.spatial import ConvexHull
    old=ROOT/'stability_adapter_2/search_support_plane_initial.py';source=ROOT/'stability_adapter_2/search_palm_patch_priority.py'
    inputs={str(p):sha(p) for p in [Path(__file__).resolve(),old,source,ROOT/'stability_adapter_2/source_separation_penalty.py',ROOT/'stability_adapter_2/PALM_PATCH_PRIORITY_EXECUTION.md',ROOT/'stability_adapter_2/PALM_PATCH_PRIORITY_INITIAL_PLAN.md']}
    wide=read(BASE/'three_face_wider_hand_initial_v1/proposal.json');support=read(BASE/'three_face_support_plane_initial_v1/proposal.json');inputs.update(wide['input_sha256']);inputs.update(support['input_sha256'])
    for p in [BASE/'three_face_wider_hand_initial_v1/proposal.json',BASE/'three_face_support_plane_initial_v1/proposal.json']:inputs[str(p)]=sha(p)
    node=next(n for n in ast.walk(ast.parse(old.read_text())) if isinstance(n,ast.FunctionDef) and n.name=='separating_gap');scope={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),str(old),'exec'),scope);dense=scope['separating_gap']
    checks={}
    for name in ('bounds','certified_distance','footprint','graph_distance'):
        pick=lambda s:next(n for n in ast.walk(ast.parse(s)) if isinstance(n,ast.FunctionDef) and n.name==name)
        checks[name+'_AST_unchanged']=ast.dump(pick(old.read_text()),include_attributes=False)==ast.dump(pick(source.read_text()),include_attributes=False)
    init=read(BASE/'three_face_support_loss_v1/native/saved_finger_targets/initial_values.json');props=read(BASE/'three_face_support_loss_v1/native/saved_finger_targets/shape_properties.json');gn=[r['body'] for r in props['actors']['guitar']['body_ranges']];hn=init['human_body_names'];config=read(ROOT/'stability_adapter_2/config.json');config['humanoid_asset']=str(ASSET)
    cases=[('wide_near17',next(r for r in wide['rejected'] if r['label']=='old_near17')),('support_near17',next(r for r in support['rejected'] if r['label']=='old_near17')),('overlap_uniform0',next(r for r in wide['rejected'] if r['label']=='uniform_0'))];samples=[];dense_seconds=fast_seconds=0.
    for label,row in cases:
        state=row['source_state'];scene=SimpleNamespace(config=config,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:hn if actor==0 else gn),bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
        model,data,shapes=build_probe(scene);meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes};hulls={}
        def hull(actor,body):
            key=(actor,body)
            if key not in hulls:
                geom=next(s['geom_id'] for s in shapes if s['actor']==actor and s['body']==body);vertices=meshes[geom].vertices;hulls[key]=(vertices,ConvexHull(vertices).equations)
            return hulls[key]
        specs=[(('human',a),('human',b)) for a,b in support['rejected'][0]['soft_observed_self_pairs']]+[(('human',h),('guitar',g)) for h,g in row['soft_source_pairs']]+[(('human',h),('guitar','guitar')) for h in ('LH:thumb3','LH:palm')]
        for pair in specs:
            va,pa=hull(*pair[0]);vb,pb=hull(*pair[1])
            for clearance in (.0001,.0003):
                start=time.perf_counter();expected=max(0.,clearance-dense(va,pa,vb,pb));dense_seconds+=time.perf_counter()-start
                start=time.perf_counter();actual=separation_penalty(va,pa,vb,pb,clearance);fast_seconds+=time.perf_counter()-start
                assert abs(expected-actual)<1e-12
                samples.append(dict(seed=label,pair=pair,clearance_m=clearance,dense_penalty_m=expected,new_penalty_m=actual))
    checks['real_seed_all_penalties_dense_equivalent']=len(samples)==150
    checks['nonzero_penalties_not_shortcut']=any(s['new_penalty_m']>0 for s in samples)
    checks['zero_penalty_cases_covered']=any(s['new_penalty_m']==0 for s in samples)
    checks['inputs_unchanged']=all(sha(p)==h for p,h in inputs.items());assert all(checks.values())
    output.write_text(json.dumps(dict(checks=checks,input_sha256=inputs,samples=samples,dense_seconds=dense_seconds,shortcut_seconds=fast_seconds,scope='read-only actual source mesh150 penalty comparisons at two clearances/3poses, not full optimization benchmark or cooked contact; zero shortcut uses a subset of same face planes so dense maximum is no smaller'),indent=2)+'\n')
    print(json.dumps(dict(checks=checks,samples=len(samples),dense_seconds=dense_seconds,shortcut_seconds=fast_seconds),indent=2))
if __name__=='__main__':main()
