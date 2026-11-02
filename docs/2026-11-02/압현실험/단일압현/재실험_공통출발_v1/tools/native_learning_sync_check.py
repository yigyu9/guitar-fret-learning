"""학습 성과와 분리한2환경 native 수집기 장벽 검사.

환경0의 정책 episode만64tick로 줄여 먼저 종료시키고, 환경1은300tick로
유지한다.400tick 수집으로 기다림·배치reset·재운반을 실제 물리에서 확인한다.
보상·제어·물리 실패 임계값은 바꾸지 않으며 학습이나 checkpoint를 만들지 않는다.
"""
if __name__=='__main__':import isaacgym
import argparse
import copy
import importlib.util
import json
import traceback
import pprint
from pathlib import Path
import sys
import torch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('learning_sync_runtime',HERE/'learning_runtime.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)


class HoldPolicy:
    def __init__(self,pool):self.pool=pool
    def __call__(self,*inputs):
        zero=inputs[0].new_zeros(len(inputs[0]));return dict(reward_value=zero,cost_value=zero)
    def act(self,*inputs):
        result=self(*inputs)
        action=self.pool.environment.hold_action.clone();action[:,33:]=0
        latent=torch.atanh(action.clamp(-.999999,.999999))
        result.update(action=action,latent=latent,mean=latent,log_std=torch.zeros_like(latent),logp=latent.new_zeros(len(latent)))
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('catalog','provenance','evidence','out'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--case',required=True)
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    pool=None;failure=None;records=[];waiting_checks=0;first_note=None
    with m.configuration(args.catalog,args.provenance,args.case,args.evidence) as (config,row):
        settings=m.build_settings(config,row,num_envs=2)
        m.transport.write(out/'settings.json',m.portable(settings))
        with m.runtime(config):
            pins=m.runner._pins(settings,out,[Path(__file__).resolve()]);m.transport.write(out/'inputs_before.json',pins)
            try:
                pool=m.LearningPool(settings,out)
                original_prepare=pool.prepare
                def prepare():
                    needed=pool.needs_preparation
                    original_prepare()
                    if needed:
                        pool.environment.duration_ticks[0]=64
                        if int(pool.environment.duration_ticks[1])!=300:raise AssertionError('원래300tick episode 필요')
                pool.prepare=prepare
                collector=m.Collector(HoldPolicy(pool),pool)
                def record(tick,reward,cost,terminated,truncated,episodes):
                    nonlocal waiting_checks,first_note
                    native=pool.scene.snapshot()['physics_step']
                    if not torch.equal(native-pool.environment.preparation_physics_offset,pool.environment.clock):
                        raise AssertionError('native/정책 offset 정합 실패')
                    if tick==63:
                        first_note={key:value[0].clone() for key,value in pool.environment.note.items()}
                    if 64<=tick<299:
                        if not bool(pool.waiting[0]) or bool(pool.waiting[1]):raise AssertionError('조기종료 대기 마스크 오류')
                        if not all(torch.equal(value,pool.environment.note[key][0]) for key,value in first_note.items()):
                            raise AssertionError('종료된 원장 변경')
                        if float(reward[0])!=0. or float(cost[0])!=0.:raise AssertionError('대기 reward/cost 오염')
                        waiting_checks+=1
                    for episode in episodes:
                        try:
                            encoded=json.dumps(episode,allow_nan=False)
                        except BaseException:
                            (out/'execution_failure.txt').write_text(traceback.format_exc())
                            (out/'invalid_episode_repr.txt').write_text(pprint.pformat(episode))
                            raise
                        with (out/'episodes.jsonl').open('a') as stream:stream.write(encoded+'\n')
                    records.extend(copy.deepcopy(episodes))
                buffer,episodes=collector.collect(400,transition_callback=record)
                counts=buffer['valid'].sum(0).tolist()
                if counts!=[128,400]:raise AssertionError('유효분모 오류: '+str(counts))
                if [e['env_id'] for e in records]!=[0,1,0]:raise AssertionError('종료episode 중복·누락')
                if len(pool.preparation_records)!=2:raise AssertionError('재운반 횟수 오류')
                if waiting_checks!=235:raise AssertionError('대기 검사 길이 오류')
                if bool((buffer['valid'][1:]&~buffer['valid'][:-1]).any()):raise AssertionError('GAE prefix 위반')
                m.ppo.compute_decision_gae(buffer['reward'],buffer['reward_value'],buffer['next_reward_value'],buffer['terminated'],
                    buffer['truncated'],buffer['duration'],buffer['valid'],.99,.98)
            except BaseException as error:failure=dict(type=type(error).__name__,message=str(error))
            finally:
                if pool:
                    try:pool.close()
                    except BaseException as error:failure=failure or dict(type='CleanupError',message=str(error))
            changed=[path for path,sha in pins.items() if not Path(path).is_file() or m.transport.digest(path)!=sha]
    report=dict(schema=m.SCHEMA+'.native_sync_check',completed=failure is None and not changed,
        failure=failure,changed_inputs=changed,case=args.case,diagnostic_only=True,training_updates=0,
        excluded_from_training_and_success_denominators=True,policy_ticks=400,waiting_checks=waiting_checks,
        valid_decisions=counts if failure is None else None,episodes=records,
        preparation_batches=len(pool.preparation_records) if pool else 0,reset_calls=pool.scene.reset_calls if pool else None)
    try:
        m.transport.write(out/'report.json',report)
    except BaseException:
        (out/'execution_failure.txt').write_text(traceback.format_exc())
        (out/'diagnostic_payload_repr.txt').write_text(pprint.pformat(report))
        raise
    if failure or changed:raise RuntimeError('동기 수집기 검증 실패; report.json 확인')


if __name__=='__main__':main()
