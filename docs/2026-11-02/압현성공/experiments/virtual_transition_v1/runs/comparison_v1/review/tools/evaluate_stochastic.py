"""동일 최종 모델에서 행동 표본화만 켜는 읽기 전용32환경 진단."""
if __name__ == '__main__':
    import isaacgym

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT))
import torch
from guitar_learning.training import finger_skill_runner as runner
from guitar_learning.portability import localize


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    runtime=Path(__file__).resolve().parents[4]/'tools/transition_runtime.py'
    spec=importlib.util.spec_from_file_location('transition_diagnostic_runtime',runtime)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    checkpoint=args.checkpoint.resolve()
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    runner._validate_pins(payload['metadata'])
    settings=localize(payload['metadata']['settings'])
    class SampledPolicy:
        def __init__(self,policy):self.policy,self.phase=policy,policy.phase
        def __call__(self,*inputs):return self.policy(*inputs)
        def act(self,*inputs):return self.policy.act(*inputs,deterministic=False)
    with module.transition_runtime(settings):
        old_policy,old_pins=runner._DeterministicPolicy,runner._pins
        def pins(current,out,extra=()):return old_pins(current,out,list(extra)+[Path(__file__).resolve()])
        runner._DeterministicPolicy,runner._pins=SampledPolicy,pins
        try:
            report,_=runner.evaluate_checkpoint(checkpoint,args.out,num_envs=32,scope='full_song',max_episodes=32)
        finally:runner._DeterministicPolicy,runner._pins=old_policy,old_pins
    report['evaluation_action_mode']='stochastic Gaussian tanh sample; no optimizer update'
    report['diagnostic_scope']='one fixed final checkpoint, first32 episodes; saved RNG restored by official loader; no production default change'
    report['diagnostic_script_sha256']=module.natural.digest(Path(__file__).resolve())
    (args.out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    if not report.get('completed') or report.get('failure'):raise RuntimeError('진단 평가 미완료')


if __name__=='__main__':main()
