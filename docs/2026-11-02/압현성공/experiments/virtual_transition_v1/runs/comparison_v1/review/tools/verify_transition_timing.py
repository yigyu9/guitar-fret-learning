"""기존 확률 행동 진단을 그대로 재실행하며32환경의 실제 접촉 시각만 관찰한다."""
if __name__=='__main__':
    import isaacgym

import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT))
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.training import finger_skill_runner as runner


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    trace=args.out.with_name(args.out.name+'_all_env_contacts.jsonl.gz')
    helper=Path(__file__).with_name('evaluate_stochastic.py')
    spec=importlib.util.spec_from_file_location('sampled_diagnostic',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original_step,original_pins=FingerSkillEnvironment.substep,runner._pins
    with gzip.open(trace,'xt') as stream:
        def observe(env,snapshot):
            original_step(env,snapshot)
            stream.write(json.dumps(dict(time_s=env._score_time().tolist(),
                episode_ids=env.finger_control_diagnostics.episode_id.tolist(),
                candidate=env.candidate.tolist(),wrong=env.wrong.tolist()))+'\n')
        def pins(settings,out,extra=()):return original_pins(settings,out,list(extra)+[Path(__file__).resolve()])
        FingerSkillEnvironment.substep,runner._pins=observe,pins
        try:module.main()
        finally:FingerSkillEnvironment.substep,runner._pins=original_step,original_pins


if __name__=='__main__':main()
