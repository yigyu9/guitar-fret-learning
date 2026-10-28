"""Bounded distal-sample audit. Actual reads require both root-completed children."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=HERE.parents[5]
MODES=('reference','noisy_reference')


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value


def complete(parent,commands):
    assert parent['completed'] is True and parent['returncode']==0 and len(parent['children'])==2
    assert set(commands)==set(MODES)
    for mode,child in zip(MODES,parent['children']):
        assert child['job']==mode and child['returncode']==0 and child['argv']==commands[mode]


def reappearance(clocks,candidate):
    ever_on=False;off_after_on=False;result=[]
    for clock,on in zip(clocks,candidate):
        if on:
            if off_after_on:result.append(int(clock))
            ever_on=True;off_after_on=False
        elif ever_on:off_after_on=True
    return result


def self_check():
    commands={m:['python','probe.py','--execute',m] for m in MODES}
    parent=dict(completed=True,returncode=0,children=[dict(job=m,returncode=0,argv=commands[m]) for m in MODES]);complete(parent,commands)
    bad=[dict(parent,completed=False),dict(parent,returncode=1),dict(parent,children=parent['children'][:1]),dict(parent,children=parent['children'][::-1])]
    for key,value in (('job','other'),('returncode',1),('argv',['foreign'])):
        p=copy.deepcopy(parent);p['children'][0][key]=value;bad.append(p)
    for p in bad:
        try:complete(p,commands)
        except AssertionError:pass
        else:raise AssertionError('Incomplete/foreign native accepted')
    assert reappearance([692,696,700],[False,True,True])==[]
    assert reappearance([692,696,700,704,708],[True,False,True,False,True])==[700,708]
    assert not any(x in sys.modules for x in ('numpy','torch','isaacgym'))
    module('clearance_analysis_fixture',HERE/'self_check.py').check()
    print('완료guard PASS: 두 조건/argv/실패 거부; actual자료 읽기0')


def geometry_audit(d,static,surface,offset,np,torch):
    n=len(d['env_id']);assert 0<n<=232 and d['points_G'].shape==(n,128,3) and d['normals_G'].shape==(n,128,3)
    assert static['source_valid'].shape==(4,128) and static['source_valid'].dtype==bool and static['source_valid'].all()
    assert static['local_points'].shape==static['local_normals'].shape==(128,3)
    assert d['first_attempt'].all() and np.isin(d['env_id'],range(4)).all()
    np.testing.assert_array_equal(d['clock'],d['start_clock']+4)
    assert ((d['clock']>=692)&(d['clock']<=920)&(d['clock']%4==0)).all()
    np.testing.assert_allclose(d['time_s'],d['clock']/240,rtol=0,atol=1e-12)
    np.testing.assert_allclose(d['source_time_s'],d['time_s']+offset,rtol=0,atol=1e-12)
    valid=d['valid_snapshot']
    # Producer also tests all4 distal13 states; only index3/guitar7 are stored.
    assert not (valid&d['reset_body_snapshot']).any()
    assert np.isfinite(d['distal_pose'][valid]).all() and np.isfinite(d['guitar_pose'][valid]).all()
    for env in range(4):
        rows=np.flatnonzero(d['env_id']==env);clocks=d['clock'][rows]
        if len(rows):
            np.testing.assert_array_equal(clocks,np.arange(692,clocks[-1]+1,4));assert len(rows)<=58
            assert not d['prior_failure'][rows].any() and not d['post_failure'][rows][:-1].any()
    # Independent double-precision rotation matrices, using saved world xyzw poses.
    def rotation(q):
        x,y,z,w=q.T
        return np.stack([1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)],-1).reshape(-1,3,3)
    ids=np.flatnonzero(valid);b=d['distal_pose'][ids].astype('float64');g=d['guitar_pose'][ids].astype('float64')
    for name in ('points_G','normals_G','starts_G','ends_G','frets_G','body_force_n'):
        assert np.isfinite(d[name][ids]).all(),name
    rb,rg=rotation(b[:,3:]),rotation(g[:,3:]);local=static['local_points'].astype('float64');normal=static['local_normals'].astype('float64')
    world=np.einsum('nij,pj->npi',rb,local)+b[:,None,:3]
    expected=np.einsum('nji,npj->npi',rg,world-g[:,None,:3])
    expected_normal=np.einsum('nji,npj->npi',rg,np.einsum('nij,pj->npi',rb,normal))
    pose_error=float(np.max(abs(expected-d['points_G'][ids]))) if len(ids) else 0.
    normal_error=float(np.max(abs(expected_normal-d['normals_G'][ids]))) if len(ids) else 0.
    numerical=8*np.finfo(np.float32).eps
    np.testing.assert_allclose(expected,d['points_G'][ids],rtol=numerical,atol=numerical)
    np.testing.assert_allclose(expected_normal,d['normals_G'][ids],rtol=numerical,atol=numerical)
    residual={};cached={}
    if len(ids):
        tensor=lambda x:torch.from_numpy(np.ascontiguousarray(x))
        points=torch.zeros(len(ids),4,128,3);normals=torch.zeros_like(points);points[:,0]=tensor(d['points_G'][ids]);normals[:,0]=tensor(d['normals_G'][ids])
        loaded=torch.zeros(len(ids),4,dtype=torch.bool);loaded[:,0]=tensor(d['body_loaded'][ids])
        sample,aggregate,_=surface.geometry(points,normals,tensor(static['source_valid']),tensor(d['starts_G'][ids]),tensor(d['ends_G'][ids]),tensor(d['frets_G'][ids]),loaded,tensor(static['plane']),2,4)
        for prefix,values in (('point_',sample),('aggregate_',aggregate)):
            for key,value in values.items():
                a=value.numpy();saved=d[prefix+key][ids]
                if a.dtype==bool or key=='sample_index':np.testing.assert_array_equal(a,saved)
                else:np.testing.assert_allclose(a,saved,rtol=numerical,atol=numerical);residual[prefix+key]=float(np.max(abs(a-saved)))
        for key in ('distance','normal_cos','signed_height','position_geometry','facing_geometry','positive'):
            a=aggregate[key].numpy();saved=d['cached_'+key][ids]
            if a.dtype==bool:np.testing.assert_array_equal(a,saved)
            else:np.testing.assert_allclose(a,saved,rtol=numerical,atol=numerical);cached[key]=float(np.max(abs(a-saved)))
        np.testing.assert_array_equal(d['cached_sample_index'][ids],d['aggregate_sample_index'][ids])
        np.testing.assert_array_equal(d['candidate'][ids],d['cached_positive'][ids]&~d['wrong'][ids])
        from guitar_learning.gpu.environment import CONTACT_CONTRACT
        measured=torch.linalg.vector_norm(tensor(d['body_force_n'][ids]),dim=-1).numpy()>=CONTACT_CONTRACT['force_threshold_n']
        np.testing.assert_array_equal(measured,d['body_loaded'][ids])
    for key in ('distance','normal_cos','signed_height','lateral'):assert np.isnan(d['point_'+key][~valid]).all()
    for key in ('position_geometry','facing_geometry','positive','in_cell'):assert not d['point_'+key][~valid].any()
    for key in ('distance','normal_cos','signed_height'):assert np.isnan(d['aggregate_'+key][~valid]).all()
    for key in ('position_geometry','facing_geometry','positive'):assert not d['aggregate_'+key][~valid].any()
    assert (d['aggregate_sample_index'][~valid]==-1).all()
    safe=valid&~d['prior_failure']&~d['post_failure']
    rows=[]
    for env in range(4):
        take=np.flatnonzero((d['env_id']==env)&safe);c=d['candidate'][take];clocks=d['clock'][take]
        reappear=reappearance(clocks,c)
        ranges={key:[int(d['point_'+key][take].sum(1).min()),int(d['point_'+key][take].sum(1).max())] if len(take) else None for key in ('in_cell','position_geometry','facing_geometry','positive')}
        rows.append(dict(sample_count_ranges=ranges,env_id=env,stored_rows=int((d['env_id']==env).sum()),valid_before_failure_rows=len(take),candidate_count=int(c.sum()),wrong_count=int(d['wrong'][take].sum()),loaded_count=int(d['body_loaded'][take].sum()),released_latch_count=int(d['released'][take].sum()),candidate_reappearance_after_saved_false_clocks=reappear,first_saved_released_clock=next((int(k) for k,r in zip(clocks,d['released'][take]) if r),None)))
    return dict(rows=n,valid_rows=int(valid.sum()),invalid_rows=int((~valid).sum()),failure_endpoint_rows=int((d['prior_failure']|d['post_failure']).sum()),per_env=rows,pose_max_abs_m=pose_error,normal_max_abs=normal_error,geometry_max_abs=residual,cached_max_abs=cached,numerical_tolerance=numerical,scope='arithmetic tolerance only; no clearance/success threshold; failed endpoints retained and censored from event counts'),safe


def phase3(d,safe,np):
    result=[];transitions=[]
    def snapshot(k):
        nearest=int(d['aggregate_sample_index'][k]);witness=np.flatnonzero(d['point_positive'][k])
        return dict(clock=int(d['clock'][k]),distance_mm=float(d['aggregate_distance'][k]*1000),signed_height_mm=float(d['aggregate_signed_height'][k]*1000),normal_cos=float(d['aggregate_normal_cos'][k]),position=bool(d['aggregate_position_geometry'][k]),facing=bool(d['aggregate_facing_geometry'][k]),loaded=bool(d['body_loaded'][k]),candidate=bool(d['candidate'][k]),nearest_sample=nearest,nearest_is_facing=bool(d['point_facing_geometry'][k,nearest]),first_positive_sample=int(witness[0]) if len(witness) else None)
    for env in range(4):
        rows=np.flatnonzero((d['env_id']==env)&safe);selected=rows[(d['time_s'][rows]>3.2703)&(d['time_s'][rows]<=3.712)]
        stats=dict(env_id=env,endpoints=len(selected))
        for k in ('aggregate_position_geometry','aggregate_facing_geometry','body_loaded','candidate'):stats[k]=int(d[k][selected].sum())
        for label,key in (('min_finite_distance_mm','aggregate_distance'),('nearest_signed_height_mm','aggregate_signed_height'),('all128_signed_height_mm','point_signed_height')):
            stats[label+'_min_median_max']=np.quantile(d[key][selected]*1000,[0,.5,1]).tolist() if len(selected) else None
        stats['positive_with_nearest_not_facing']=int((d['aggregate_positive'][selected]&~d['point_facing_geometry'][selected,d['aggregate_sample_index'][selected]]).sum())
        result.append(stats)
        for previous,current in zip(rows[:-1],rows[1:]):
            if d['clock'][current]-d['clock'][previous]==4 and 3.2703<d['time_s'][current]<=3.712 and d['released'][current] and not d['candidate'][previous] and d['candidate'][current]:transitions.append(dict(env_id=env,before=snapshot(previous),after=snapshot(current)))
    return dict(local_window_s=[3.2703,3.712],per_env=result,released_candidate_rising_pairs=transitions,scope='phase3 N hold/wrist movement; consecutive saved60Hz endpoints only; geometric gates retained does not mean stationary geometry or identified force partner')


def actual():
    parent=read(BASE/'01_launcher.json');commands=read(BASE/'cpu_inputs/commands.json');complete(parent,commands)
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    sys.path.insert(0,str(ROOT));import numpy as np;import torch
    torch.set_num_threads(1);assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    source=module('clearance_analysis_source',BASE/'surface.py');pins={}
    from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
    pad=load_fingertip_pad()
    def pin(path):path=Path(path).resolve();pins[str(path)]=sha(path);return path
    def load(path):return read(pin(path))
    def npz(path):
        with np.load(pin(path),allow_pickle=False) as archive:return {k:archive[k] for k in archive.files}
    for p in (Path(__file__),HERE/'PLAN.md',HERE/'self_check.py',BASE/'surface.py',BASE/'probe.py',BASE/'cpu_checks.py',BASE/'01_launcher.json',BASE/'cpu_inputs/commands.json'):pin(p)
    seal=load(BASE/'preparation_seal.json');review=load(BASE/'review.json');assert review['verdict']=='PASS' and not review['findings']
    for p in (BASE/'surface.py',BASE/'probe.py',BASE/'cpu_checks.py',BASE/'review.json'):assert seal['input_pins'][str(p)]==sha(p)
    prior=BASE.parent/'index_prefix_reference_noise_v1/analysis/results_v1/review.json';r=load(prior);assert r['verdict']=='PASS' and not r['findings'] and seal['input_pins'][str(prior)]==sha(prior)
    for p,h in pad['contract']['source_sha256'].items():assert sha(pin(p))==h
    pin(ROOT/'guitar_learning/gpu/fingertip_pad.py');pin(ROOT/'guitar_learning/gpu/geometry.py');pin(ROOT/'guitar_learning/gpu/press_surface.py');pin(ROOT/'guitar_learning/gpu/environment.py')
    results={};datasets={}
    for mode,child in zip(MODES,parent['children']):
        assert load(BASE/('01_'+mode+'_launcher.json'))==child
        folder=BASE/'runs'/mode;report=load(folder/'clearance_report.json')
        assert report['schema']=='diagnostic.index_release_distal_samples.v1' and report['mode']==mode and report['completed'] and report['failure'] is None and all(report['checks'].values())
        assert all(report[k]==0 for k in ('model_loads','NN_constructors','PPO_updates','fit_steps'))
        native=load(folder/'diagnostic_report.json');assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and native['failure'] is None
        assert not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
        after=load(folder/'diagnostic_inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        meta=load(folder/'surface_metadata.json');assert meta['clock_window']==[692,920] and meta['A_source_index']==4 and meta['physical_string']==3 and meta['fret']==4 and meta['endpoint_stride']==4
        assert meta['source_sha256'][str(BASE/'surface.py')]==sha(BASE/'surface.py')
        contract=load(folder/'training_contract.json');offset=contract['task']['short_learning']['view']['score_offset_s']
        d=npz(folder/'release_clearance4.npz');static=npz(folder/'surface_static.npz')
        assert meta['pad_contract']==pad['contract']
        for key,expected in (('local_points',pad['points_local'][0]),('local_normals',pad['normals_local'][0]),('source_valid',pad['valid'])):np.testing.assert_array_equal(static[key],expected)
        np.testing.assert_array_equal(static['plane'],np.asarray(contract['observation']['surface_geometry']['press_surface']['plane_G'],dtype=static['plane'].dtype))
        audit,safe=geometry_audit(d,static,source,offset,np,torch)
        assert report['rows']==audit['rows'];results[mode]=dict(audit=audit,phase3=phase3(d,safe,np),native_checks=report['checks'],clock_window=meta['clock_window'],sample_contract=meta['pad_contract']);datasets[mode]=(d,safe)
    out.mkdir();(out/'comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    timeline(datasets,out/'timeline.png',np)
    lines=['# 검지 말단 이산 표본 여유','', '각 조건은 원128환경 평가를 보존한 새 측정이다. 상세 기하는 env0..3·A press부터 B press 직후까지 저장된60Hz 끝점만 사용했다. 새 clearance 판정은 만들지 않았다.','', '|조건|환경|저장/유효행|candidate|loaded|release latch|후보 재등장 clock|','|---|---|---|---|---|---|---|']
    for mode in MODES:
        for r in results[mode]['audit']['per_env']:lines.append('|{}|{}|{}/{}|{}|{}|{}|{}|'.format(mode,r['env_id'],r['stored_rows'],r['valid_before_failure_rows'],r['candidate_count'],r['loaded_count'],r['released_latch_count'],r['candidate_reappearance_after_saved_false_clocks']))
    lines+=['','## N 유지·손목 이동: 원 phase3','', '3.2703초 초과부터3.712초까지 조건별4환경×26끝점이다. 기하/방향 통과와 부하/후보를 분리했다.','', '|조건|환경|기하/방향|loaded/candidate|최소 유한셀거리 min/median/max mm|nearest signedheight min/median/max mm|','|---|---|---|---|---|---|']
    fmt=lambda x:'/'.join('{:.3f}'.format(v) for v in x) if x else '없음'
    for mode in MODES:
        for r in results[mode]['phase3']['per_env']:lines.append('|{}|{}|{}/{}|{}/{}|{}|{}|'.format(mode,r['env_id'],r['aggregate_position_geometry'],r['aggregate_facing_geometry'],r['body_loaded'],r['candidate'],fmt(r['min_finite_distance_mm_min_median_max']),fmt(r['nearest_signed_height_mm_min_median_max'])))
    lines+=['', '같은 구간의 전체128표본 signedheight 최소/중앙/최대는 무잡음 네환경에서 각각 약 −0.272~−0.270 /3.861~3.914 /12.566~12.590mm였다. 이 분포는 nearest height와 다르며 음수height를 이격 여유로 해석하지 않는다.','', '## 해제 latch 뒤 phase3 후보 재등장','', '|조건|환경|clock 전→후|finite거리 mm 전→후|signedheight mm 전→후|cos 전→후|position/facing 전→후|loaded 전→후|nearest ID 전→후|','|---|---|---|---|---|---|---|---|---|']
    for mode in MODES:
        for row in results[mode]['phase3']['released_candidate_rising_pairs']:
            a,b=row['before'],row['after'];lines.append('|{}|{}|{}→{}|{:.4f}→{:.4f}|{:.4f}→{:.4f}|{:.3f}→{:.3f}|{}/{}→{}/{}|{}→{}|{}→{}|'.format(mode,row['env_id'],a['clock'],b['clock'],a['distance_mm'],b['distance_mm'],a['signed_height_mm'],b['signed_height_mm'],a['normal_cos'],b['normal_cos'],int(a['position']),int(a['facing']),int(b['position']),int(b['facing']),int(a['loaded']),int(b['loaded']),a['nearest_sample'],b['nearest_sample']))
    lines+=['', '무잡음8건·잡음6건의 저장 전후 쌍에서 기하·방향 통과는 유지되고 loaded는0→1이었다. 거리는 실제로 변했으므로 기하가 고정됐다는 뜻은 아니다. 이 구간에서 positive인데 nearest가 facing을 실패한 끝점은0개였으나, 일반적으로 nearest와 any-sample witness는 독립이다. positive 표본ID도 JSON에 별도로 보존했다.','', '가까운 지정 표본 기하가 남은 상태의 부하 토글이 관찰됐다. 충분한 전체피부 이격 후 재접촉이나 원 접촉상대/힘 원인은 이 자료로 확정할 수 없다.']
    lines+=['','거리·signedheight·cos·셀/방향·말단부하·candidate는 분리했다. 원native released latch는 연속무접촉 인증이 아니다. 표본법선이 불리하거나 height가 음수인 상태를 이격으로 합치지 않는다. nearest 표본과 any-sample witness가 다를 수 있다.','', 'valid_snapshot은 producer의 네 distal13 상태 유한성 검사를 재사용한다. 저장된 index3/guitar7의 유한성과 reset 제외를 확인했으며 미저장 다른 distal13 상태의 판정을 역복원하지 않았다. 몸체 순힘은 접촉쌍·현 압력이 아니며, 전체피부·다른마디·다른124환경의 기하·240Hz 연속성은 미확인이다. 실패 끝점은 보존하고 사건 집계에서는 실패 시점부터 제외했다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    assert all(sha(p)==h for p,h in pins.items())
    (out/'verification.json').write_text(json.dumps(dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=pins,verified_input_sha256={p:h for p,h in pins.items() if p in seal['input_pins'] and seal['input_pins'][p]==h},scope='direct inputs only; original native input/close/callback audits reused; no128 ledger re-audit/model load'),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({m:results[m]['audit']['per_env'] for m in MODES},ensure_ascii=False))


def timeline(datasets,path,np):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(11,7.5),sharex=True)
    for j,mode in enumerate(MODES):
        d,safe=datasets[mode];m=(d['env_id']==0)&safe;x=d['time_s'][m]
        axes[0,j].plot(x,d['aggregate_distance'][m]*1000,label='min finite-cell distance')
        axes[0,j].plot(x,d['aggregate_signed_height'][m]*1000,label='nearest signed height');axes[0,j].set_ylabel('mm');axes[0,j].set_title(mode+' env0')
        axes[1,j].plot(x,d['aggregate_normal_cos'][m],label='nearest normal cos')
        axes[1,j].plot(x,d['point_in_cell'][m].sum(1)/128,label='in-cell samples /128',ls='--')
        axes[1,j].plot(x,d['point_facing_geometry'][m].sum(1)/128,label='same-point facing /128',ls=':');axes[1,j].set_ylim(-.05,1.05);axes[1,j].set_ylabel('cos / fraction')
        for k,key in enumerate(('candidate','body_loaded','released')):axes[2,j].scatter(x[d[key][m]],np.full(int(d[key][m].sum()),k),s=13)
        axes[2,j].set_yticks(range(3));axes[2,j].set_yticklabels(['candidate','body loaded','released latch']);axes[2,j].set_ylim(-.5,2.5);axes[2,j].set_xlabel('saved local endpoint s')
        for row in range(3):
            ax=axes[row,j];ax.grid(alpha=.2)
            for t,label in ((3.1703,'A end'),(3.832,'B press')):ax.axvline(t,color='grey',ls=':');axes[0,j].annotate(label,(t,1),xycoords=('data','axes fraction'),ha='right',va='bottom',fontsize=8) if row==0 else None
        axes[0,j].legend(fontsize=8);axes[1,j].legend(fontsize=8)
    fig.suptitle('Index3 finite source samples: geometry and native flags (60Hz)');fig.tight_layout();fig.savefig(path,dpi=130);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--self-check',action='store_true');g.add_argument('--root-completed',action='store_true');args=p.parse_args()
    if args.self_check:self_check()
    else:actual()
