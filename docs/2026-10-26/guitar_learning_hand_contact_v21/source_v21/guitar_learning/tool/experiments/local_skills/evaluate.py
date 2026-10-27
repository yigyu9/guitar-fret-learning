"""Execute the fitted policy, with no teacher, under the original quality gate."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

from guitar_learning.training.monitoring import available_memory_bytes, LowMemoryError


def evaluate(settings,args):
    import isaacgym
    from guitar_learning.tool.evaluation import evaluate_musical_quality
    from guitar_learning.quality import musical_quality_transfer, musical_quality_environment
    from guitar_learning.imitation.imitation import dataset_manifest
    from guitar_learning.training.recording import write
    from guitar_learning.tool.experiments.local_skills.learning import GATE_SCHEMA, apply_actor_initialization, contract_digest, load_initialization, successful_episode
    if type(args.episodes) is not int or not 1 <= args.episodes <= 4:
        raise ValueError('bounded1..4 policy-only evaluation episodes required')
    started=time.monotonic();cleanup_errors=[];existed=args.out.exists()
    original_build=musical_quality_environment.build_environment
    def check_memory(gib):
        if available_memory_bytes() < gib*1024**3:raise LowMemoryError('local evaluation memory guard %.1f GiB'%gib)
    class GuardedEnvironment:
        def __init__(self,env):self.env=env;self.case_started=time.monotonic();self.ticks=0
        def __getattr__(self,name):return getattr(self.env,name)
        def check_time(self):
            now=time.monotonic()
            if now-started>3000 or now-self.case_started>600:raise TimeoutError('local evaluation case/total wall guard')
        def reset(self):
            self.case_started=time.monotonic();self.ticks=0;self.check_time();check_memory(6.)
            value=self.env.reset();self.check_time();return value
        def step(self,action):
            self.check_time()
            if self.ticks%60==0:check_memory(6.)
            value=self.env.step(action);self.ticks+=1;self.check_time();return value
        def close(self):
            primary=sys.exc_info()[1]
            try:self.env.close()
            except BaseException as error:
                cleanup_errors.append(dict(type=type(error).__name__,message=str(error)))
                if primary is None:raise
    def guarded_build(*positional,**kwargs):
        check_memory(8.)
        if time.monotonic()-started>3000:raise TimeoutError('local evaluation total wall guard')
        return GuardedEnvironment(original_build(*positional,**kwargs))
    try:
        with patch.object(musical_quality_transfer,'apply_actor_initialization',apply_actor_initialization), \
                patch.object(musical_quality_environment,'build_environment',guarded_build):
            result=evaluate_musical_quality.evaluate(settings,args)
        if time.monotonic()-started>3000:
            raise TimeoutError('local evaluation total wall guard, including output serialization')
    except BaseException as error:
        if not existed:
            try:
                args.out.mkdir(parents=True,exist_ok=True)
                write(args.out/'local_skill_evaluation_failure.json',dict(completed=False,
                    failure=dict(type=type(error).__name__,message=str(error)),cleanup_errors=cleanup_errors,
                    scope='policy-only evaluation failed; no native gate issued'))
            except OSError as secondary:
                print('secondary local evaluation record error: '+str(secondary),file=sys.stderr,flush=True)
        raise
    # PPO evaluation remains useful, but cannot certify another BC artifact.
    if args.initialization is not None:
        checkpoint=Path(settings['actor_initialization']).resolve();payload=load_initialization(checkpoint)
        files=dict(result=args.out/'musical_quality_result.json',evaluation_metrics=args.out/'evaluation_metrics.json',
                   inputs_before=args.out/'inputs_before.json')
        manifest=dataset_manifest(files.values())
        episodes=result.get('episodes',[])
        gate=dict(schema=GATE_SCHEMA,role=result['role'],checkpoint=str(checkpoint),
            checkpoint_sha256=dataset_manifest([checkpoint])[str(checkpoint)],
            contract_sha256=contract_digest(payload['architecture']['contract']),
            source_checkpoint_sha256=payload['source_checkpoint_sha256'],dataset_manifest=payload['dataset_manifest'],
            artifacts={k:dict(path=str(p.resolve()),sha256=manifest[str(p.resolve())]) for k,p in files.items()},
            passed=(result.get('completed') is True and result.get('source_unchanged') is True
                and result.get('kind')=='actor_migration' and result.get('requested_episodes')==4
                and len(episodes)==4 and all(successful_episode(e,result['role']) for e in episodes)),
            scope='four policy-only original quality/safety episodes; no teacher or learned-performance claim from fit')
        write(args.out/'local_skill_gate.json',gate)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--initialization',type=Path);source.add_argument('--run',type=Path)
    parser.add_argument('--settings',type=Path);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--episodes',type=int,default=4);args=parser.parse_args()
    if args.settings is None:
        if args.run is None:parser.error('--initialization requires --settings')
        args.settings=args.run/'settings.json'
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    import isaacgym
    from guitar_learning.tool.experiments.local_skills.learning import settings_document
    evaluate(settings_document(json.loads(args.settings.read_text())),args)


if __name__=='__main__':main()
