"""CPU-only original reference function replay on saved precontrol clocks/targets."""
from pathlib import Path
import importlib.util
import json
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v


def main():
    audit=module('label_existing_actual_guard',HERE/'analyze.py');audit.preflight()
    out=HERE/'results_v1/label_replay.json';assert not out.exists()
    probe=module('label_original_recovery_probe',HERE.parent/'probe.py');native=probe.source;sys.path.insert(0,str(probe.grid.ROOT))
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    inputs={}
    def track(p):p=Path(p);inputs[str(p)]=probe.grid.sha(p);return p
    def read(p):return probe.grid.read(track(p))
    config=read(native.HERE/'cpu_inputs/settings.json');short=config['song']['short_learning'];ids=short['learned_action_indices']
    reference_path=native.parent.base.pre.INPUTS['index'][1];reference=runner.read_reference(track(reference_path),short)
    assert [reference['selected_targets_rad'][n] for n in short['learned_action_names']]==short['reference_release_schedule']['reference_selected_rad']
    contract=read(probe.COLLECT/'training_contract.json')['action']['target_contract'];joint_names=contract['joint_names']
    active=torch.tensor([joint_names.index(n) for n in contract['action_order']]);selected=active[ids]
    ref105=torch.tensor(contract['reference105_rad'],dtype=torch.float32);ref39=ref105[active]
    low=torch.tensor(contract['action_lower_rad'],dtype=torch.float32);high=torch.tensor(contract['action_upper_rad'],dtype=torch.float32)
    incremental=torch.zeros(39,dtype=torch.bool);incremental[17:33]=True
    extra=native.parent.support();track(native.parent.HERE/'learning.py');track(extra.timing.__file__);track(native.HERE/'imitation.py');track(Path(__file__))
    from guitar_learning.tool.validation import press_acquisition
    track(press_acquisition.__file__)
    result={}
    for stage in ('collect','evaluate'):
        folder=probe.output(stage);data=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));n=len(data['clock'])
        target=ref105[None].repeat(n,1);target[:,selected]=torch.from_numpy(data['old_target_rad'])
        fake=SimpleNamespace(spec=short,teacher_reference=ref39,incremental_mask=incremental,
            controller=SimpleNamespace(target=target,active=active,action_low=low,action_high=high),
            environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(data['start_clock']).to(torch.float64)/240.))
        expected=extra.reference_action(fake,reference)[:,ids].numpy();label=data['requested_reference_action' if stage=='collect' else 'requested_NN_action']
        difference=label-expected
        if stage=='collect':np.testing.assert_array_equal(expected,label)
        g=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False));col=(data['start_clock']//4).astype(int);env=data['env_id']
        eligible=g['eligible'][col,env];counterfactual_DIP_blocked=eligible&(expected[:,3]>0)
        phases=[]
        for j in range(6):
            mask=data['phase']==j;delta=difference[mask]
            phases.append(dict(phase=j,samples=int(mask.sum()),rms_request_minus_reference4=np.sqrt(np.mean(delta**2,axis=0)).tolist(),
                mean_requested4=label[mask].mean(0).tolist(),mean_reference_at_saved_oldtarget4=expected[mask].mean(0).tolist(),
                opposite_sign_counts4=((label[mask]*expected[mask])<0).sum(0).tolist(),
                potential_positive_DIP_guard_holds=int(counterfactual_DIP_blocked[mask].sum()),
                integrated_request_minus_reference_rad_by_env={str(i):(difference[mask&(env==i)].sum(0)*(4/60)).tolist() for i in range(4)}))
        result[stage]=dict(reference_reproduction_exact=stage=='collect',max_abs_request_difference=float(abs(difference).max()),phases=phases,
            scope='Original reference function on saved oldtarget/clock; NN corrective request is offline only and may be held by unchanged DIP guard')
    ref=dict(np.load(track(probe.COLLECT/'observations4.npz'),allow_pickle=False));nn=dict(np.load(track(probe.output('evaluate')/'observations4.npz'),allow_pickle=False))
    assert np.array_equal(ref['env_id'],nn['env_id']) and np.array_equal(ref['start_clock'],nn['start_clock'])
    joint_ids=[joint_names.index(n) for n in short['learned_action_names']]
    stages={}
    for j in range(6):
        m=nn['phase']==j;state=nn['state'][m]-ref['state'][m];target=nn['old_target_rad'][m]-ref['old_target_rad'][m]
        stages[str(j)]=dict(samples=int(m.sum()),scaled_state_L2_p50_p95_max=np.percentile(np.linalg.norm(state,axis=1),[50,95,100]).tolist(),
            pretarget_difference_mean_deg=np.rad2deg(target).mean(0).tolist(),pretarget_difference_max_abs_deg=np.rad2deg(abs(target)).max(0).tolist())
    result['same_clock_observation_shift']=stages
    result['input_sha256']=inputs;result['limits']=['NN資料再計算ではreferenceを実行せずlabelだけCPU評価; native/学習/新資料追加なし',
        '다른35축oldtarget은selected4 계산에 영향을 주지 않아reference105로 채웠다; 원함수selected4의원자료exact재현으로확인',
        'corrective label이guard에서막힐수있고 reference 동작의회복/physics성공은보장하지않음',
        '4환경동일clock관측/목표 차이이며 원인증명·환경전체일반화가아님']
    # Korean report only; no new training dataset or altered policy is written.
    result['limits'][0]='NN 관측에서는 원reference를 실행하지 않고 CPU요청만 계산했다; native/학습/추가자료수집0'
    probe.grid.write(out,result);print(json.dumps(dict(reference_exact=result['collect']['reference_reproduction_exact'],NN_corrective_request_max_difference=result['evaluate']['max_abs_request_difference'])))


if __name__=='__main__':main()
