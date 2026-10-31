"""원본33축 draw를 보존하고 선택 그룹만 표본을 실행하는 고정 모델 진단."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import reward_trace_probe as trace
import frozen_sampling_probe as frozen
import expected_angle_probe as expected


def groups(config):
    start=17+4*('index','middle','ring','pinky').index(config['finger'])
    result=dict(goal=list(range(start,start+4)),arm=list(range(12)))
    result['other']=[i for i in range(33) if i not in result['goal']+result['arm']]
    result['all']=list(range(33))
    if sorted(result['goal']+result['arm']+result['other'])!=result['all']:raise ValueError('그룹 분할 오류')
    return result


class GroupPolicy:
    def __init__(self,policy,selected,record):self.policy,self.phase,self.selected,self.record=policy,policy.phase,selected,record
    def __call__(self,*inputs):return self.policy(*inputs)
    def act(self,*inputs):
        import torch
        # 원본은39 shape 중 활성33만 draw한다. 모든 그룹에서 같은 draw를 소비한다.
        result=self.policy.act(*inputs,deterministic=False)
        active=self.policy._active_mask()
        if active.nonzero().flatten().tolist()!=list(range(33)):raise ValueError('BASE free33 필요')
        old_action,old_latent=result['action'],result['latent']
        if self.selected!=list(range(33)):
            latent=result['mean'].clone();latent[...,self.selected]=old_latent[...,self.selected]
            latent[...,~active]=old_latent[...,~active]
            action=old_action.clone();action[...,active]=latent[...,active].tanh()
            result.update(action=action,latent=latent,logp=self.policy.log_probability(result['mean'],result['log_std'],latent))
        if (not torch.equal(result['action'][...,~active],old_action[...,~active]) or
            not torch.equal(result['latent'][...,~active],old_latent[...,~active]) or
            not torch.equal(result['action'][...,active],result['latent'][...,active].tanh()) or
            not all(torch.isfinite(result[k]).all() for k in ('action','latent','logp'))):raise ValueError('그룹 실행 계약 실패')
        self.record['act_calls']+=1
        return result


@contextmanager
def context(official,selected):
    original=official._DeterministicPolicy,official._pins
    record=dict(act_calls=0)
    def pins(settings,out,extra=()):return original[1](settings,out,list(extra)+[Path(__file__).resolve()])
    official._DeterministicPolicy=lambda policy:GroupPolicy(policy,selected,record)
    official._pins=pins
    try:yield record
    finally:official._DeterministicPolicy,official._pins=original


def run(checkpoint,out,group):
    if out.exists():raise FileExistsError('기존 진단 출력은 덮어쓸 수 없음: '+str(out))
    sys.path.insert(0,str(trace.STUDY/'runtime'))
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        import torch
        from guitar_learning.tool.experiments import structured_press as sp
        from guitar_learning.training import finger_skill_runner as official
        payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
        if payload['identity']['architecture']['schema']!=sp.StructuredPolicy.schema:raise ValueError('저장 BASE만 허용')
        _,_,catalog=expected.codec(payload,sp)
        selection=groups(payload['metadata']['settings']['structured_press'])
        files=[checkpoint,Path(__file__).resolve(),Path(trace.__file__),Path(frozen.__file__),Path(expected.__file__),catalog,trace.PROTOCOL]
        before={str(p.resolve()):trace.digest(p) for p in files}
        record={}
        try:
            with context(official,selection[group]) as record:trace.run(checkpoint,out,'base')
        finally:
            frozen.annotate(out,before)
            if (out/'summary.json').exists():
                facts=dict(policy_mode='original_stochastic_all33' if group=='all' else 'hybrid_group_sampling',
                    sampling_group=group,selected_axes=selection[group],group_partition=selection,
                    sampling_scope='원본 활성33 draw 후 선택 그룹만 실행; 나머지 활성축은 latent mean',
                    original_stochastic_policy_unchanged=group=='all',deterministic_policy_unchanged=False,
                    source_distribution_unchanged=True,native_draw_axes=33,returned_action_shape=39,
                    all_groups_same_native_rng_consumption=True,diagnostic_group_record=record,
                    logp_scope='선택 latent의 원래 Gaussian 밀도 기록; hybrid 분포 밀도가 아니며 PPO에 사용하지 않음',
                    interpretation='고정 모델의 그룹별 실행 진단; 새 학습/일반화/물리 기댓값 아님')
                report_path=out/'native/report.json';summary_path=out/'summary.json'
                summary=json.loads(summary_path.read_text())
                if report_path.exists():
                    report=json.loads(report_path.read_text());report.update(facts)
                    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
                    if summary.get('completed'):summary['output_sha256'][str(report_path)]=trace.digest(report_path)
                summary.update(facts);summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
                (out/'SUMMARY.md').write_text('# 그룹별 고정 표본 실행 진단\n\n그룹: '+group+'\n\n원본33축 난수 draw를 매번 모두 소비하고 선택 그룹 외 활성축은 latent mean을 실행한다. inactive6은 보존한다. all은 원래 stochastic 실행이며 나머지는 hybrid 진단이다. 가중치·분포·물리·학습은 바꾸지 않는다.\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--group',choices=('all','goal','arm','other'),required=True)
    args=parser.parse_args()
    import isaacgym
    run(args.checkpoint.resolve(),args.out.resolve(),args.group)
