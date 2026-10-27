"""Immutable checkpoints and full-song evaluation movies for the noon pilot."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def input_closure():
    from .environment_contract_v1 import EnvironmentContract
    from .dual_music_scene_v1 import BASE
    from .build_fixed_lower_asset import MANIFEST, REFERENCE
    from .joint_learning_observation_v1 import BUNDLE
    suffixes = ('.py','.json','.xml','.md','.obj','.stl','.mtl','.png','.urdf')
    paths = {str(p) for name in ('stability_adapter_2', 'tab2body')
             for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix in suffixes}
    paths.update(EnvironmentContract().inputs)
    paths.update(json.loads(MANIFEST.read_text())['input_sha256'])
    paths.update(str(REFERENCE/n) for n in ('report.json','states.json'))
    paths.update(str(p) for p in BUNDLE.rglob('*.json'))
    paths.add(str(BASE))
    paths.update(str(ROOT/p) for p in (
        'fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt',
        'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt',
        'strike/02_physical_control/pick-grip-reference.json'))
    return {p:sha(p) for p in sorted(paths)}


def learning_abi(env, closure):
    abi = env.abi()
    abi['action_dimension'] = 81
    abi['source_sha256'] = {p:h for p,h in closure.items() if Path(p).suffix not in ('.md','.pt')}
    return abi


class TrainingDeadline(Exception):
    pass


class DeadlineBoundedEnvironment:
    def __init__(self, env, stop_at):
        self.env, self.stop_at = env, stop_at

    def require_training_ready(self): self.env.require_training_ready()

    def _check(self):
        if time.time() >= self.stop_at: raise TrainingDeadline('planned training cutoff reached')

    def reset(self):
        self._check()
        return self.env.reset()

    def step(self, action):
        self._check()
        return self.env.step(action)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--device', choices=('cpu','cuda'), default='cuda')
    parser.add_argument('--eval', action='store_true')
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--stop-at', default='2026-10-12T11:40:00+09:00')
    parser.add_argument('--interval-minutes', type=float, default=30.)
    parser.add_argument('--rollout-steps', type=int, default=256)
    parser.add_argument('--max-updates', type=int)
    args = parser.parse_args()
    if args.interval_minutes <= 0 or args.rollout_steps <= 0:
        parser.error('positive interval and rollout required')
    stop_at = datetime.fromisoformat(args.stop_at).timestamp()
    video_deadline = datetime.fromisoformat('2026-10-12T11:59:00+09:00').timestamp()
    if args.eval:
        def interrupted(signum, frame): raise InterruptedError('evaluation interrupted; preserve partial native frames')
        signal.signal(signal.SIGTERM, interrupted)
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    # Must precede Torch imports, including imported training/view helpers.
    from .dual_music_scene_v1 import DualMusicScene
    from .deadline_native_v1 import NativeDeadlineEnvironment
    from .deadline_ppo_v1 import DeadlinePPO, PPOConfig
    from .joint_policy_v1 import JointActorCritic, digest
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(103); np.random.seed(103)
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; execute in GPU-access environment')
    closure = input_closure()
    if args.checkpoint: closure[str(args.checkpoint.resolve())] = sha(args.checkpoint)
    save(out/'attempt.json', {'started_utc':datetime.now(timezone.utc).isoformat(),
         'input_sha256':closure,'args':dict(vars(args), out=str(out), checkpoint=str(args.checkpoint) if args.checkpoint else None),
         'physical_backend':'CPU PhysX', 'learning_device':args.device})
    env = None; failure = None; trainer = None; evaluation_failures = []
    summaries = []; last_saved = None
    def evaluate(checkpoint, label):
        target = out/'evaluations'/label
        target.parent.mkdir(parents=True, exist_ok=True)
        log = target.parent/(label+'.log')
        with log.open('x') as stream:
            remaining = video_deadline-time.time()-20
            if remaining <= 0: raise TrainingDeadline('video deadline reached')
            proc = subprocess.Popen([sys.executable,'-u','-m','stability_adapter_2.run_deadline_training_v3',
                         '--eval','--out',str(target),'--checkpoint',str(checkpoint),
                         '--device',args.device], env=os.environ.copy(), stdout=stream, stderr=subprocess.STDOUT)
            timed_out = False
            try:
                returncode = proc.wait(timeout=min(600., remaining))
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.terminate()
                try: returncode = proc.wait(timeout=15.)
                except subprocess.TimeoutExpired:
                    proc.kill(); returncode = proc.wait(timeout=5.)
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try: proc.wait(timeout=15.)
                    except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5.)
        record = {'label':label,'checkpoint':str(checkpoint),'output':str(target),
                  'returncode':returncode,'timed_out':timed_out,'log':str(log)}
        summaries.append(record)
        save(out/'evaluation_records'/('record_'+str(len(summaries)).zfill(4)+'.json'),record)
        if returncode or timed_out: evaluation_failures.append(record)

    try:
        env = NativeDeadlineEnvironment(recording=args.eval, output=out/'native' if args.eval else None,
                                        seed=103, baseline_device='cpu')
        obs = env.reset()
        abi = learning_abi(env, closure)
        model = JointActorCritic(820, env.scene.contract.groups).to(args.device)
        trainer = DeadlinePPO(model, abi, PPOConfig())
        if args.checkpoint: trainer.load(args.checkpoint, restore_rng=not args.eval)
        save(out/'learning_abi.json',{'payload':abi,'sha256':digest(abi)})
        save(out/'initial_values.json',env.metadata)
        if args.eval:
            if not args.checkpoint: raise ValueError('evaluation requires checkpoint')
            model.eval(); total_reward = 0.; steps = 0
            while True:
                tensor = torch.as_tensor(obs, device=args.device, dtype=torch.float32)[None]
                sample = model.sample(tensor, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(sample['action'][0].cpu().numpy())
                total_reward += reward; steps += 1
                if steps%60 == 0: print('evaluation_seconds',steps/60,flush=True)
                if terminated or truncated: break
            save(out/'evaluation.json',{'total_reward':total_reward,'control_steps':steps,
                 'terminated':terminated,'truncated':truncated,'updates':trainer.updates,
                 'transitions':trainer.transitions,'RMS_updated':False,'deterministic':True,
                 'checkpoint_sha256':sha(args.checkpoint)})
        else:
            (out/'evaluation_records').mkdir()
            log = (out/'training.jsonl').open('x', buffering=1)
            try:
                checkpoint = out/'checkpoints'/'initial_000000.pt'
                trainer.save(checkpoint); last_saved=checkpoint
                evaluate(checkpoint, 'initial_000000')
                if evaluation_failures: raise RuntimeError('initial native evaluation failed; see preserved evaluation log')
                next_save = time.monotonic()+args.interval_minutes*60
                started = time.monotonic()
                # Keep the validated physical scene already created; do not repeat initial reset.
                bounded = DeadlineBoundedEnvironment(env, stop_at)
                trainer._collection_env,trainer._collection_obs = bounded,np.array(obs,copy=True)
                while time.time() < stop_at:
                    model.train()
                    t0 = time.monotonic()
                    batch = trainer.collect(bounded,args.rollout_steps)
                    bounded._check()
                    result = trainer.update(batch)
                    if result['optimizer_steps']==0:
                        raise RuntimeError('no optimizer update accepted')
                    entry = {'utc':datetime.now(timezone.utc).isoformat(),'update':trainer.updates,
                         'transitions':trainer.transitions,'wall_s':time.monotonic()-started,
                         'rollout_and_update_s':time.monotonic()-t0,
                         'reward_mean':float(batch['reward'].mean()),
                         'reward_min':float(batch['reward'].min()),'reward_max':float(batch['reward'].max()),
                         'ppo':result, 'last_info':getattr(env,'last_info',{}),
                         'completed_episodes':getattr(env,'episode_reports',[])}
                    log.write(json.dumps(entry,ensure_ascii=False,allow_nan=False)+'\n')
                    print('update',trainer.updates,'transitions',trainer.transitions,
                          'reward',entry['reward_mean'],flush=True)
                    due = time.monotonic() >= next_save
                    early = trainer.updates==1
                    final = (args.max_updates is not None and trainer.updates>=args.max_updates) or time.time()>=stop_at
                    if due or early or final:
                        label = 'update_'+str(trainer.updates).zfill(6)
                        checkpoint=out/'checkpoints'/(label+'.pt')
                        trainer.save(checkpoint);last_saved=checkpoint
                        evaluate(checkpoint,label)
                        if due:
                            while next_save <= time.monotonic(): next_save+=args.interval_minutes*60
                        if evaluation_failures: raise RuntimeError('checkpoint evaluation failed; training stopped with checkpoints preserved')
                    if final: break
                # A stop between rollouts still produces an evaluation of the latest parameters.
                if trainer.updates and last_saved.name != 'update_'+str(trainer.updates).zfill(6)+'.pt':
                    label='final_'+str(trainer.updates).zfill(6)
                    last_saved=out/'checkpoints'/(label+'.pt');trainer.save(last_saved);evaluate(last_saved,label)
            finally:
                log.close()
    except TrainingDeadline as error:
        print('scheduled cutoff',str(error),flush=True)
        if trainer is not None and trainer.updates and time.time() < video_deadline-30:
            label='cutoff_'+str(trainer.updates).zfill(6)
            last_saved=out/'checkpoints'/(label+'.pt')
            trainer.save(last_saved)
            try: evaluate(last_saved,label)
            except BaseException as final_error:
                failure={'type':type(final_error).__name__,'message':str(final_error),'traceback':traceback.format_exc()}
    except BaseException as error:
        failure={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
        print(failure['traceback'],flush=True)
    finally:
        if env:
            try: env.close()
            except BaseException as error:
                if failure is None: failure={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
        unchanged=all(sha(p)==h for p,h in closure.items())
        save(out/'report.json',{'completed':failure is None and unchanged and not evaluation_failures,
              'failure':failure,'inputs_unchanged':unchanged,
              'native_report':getattr(env,'last_report',None),'evaluations':summaries,
              'updates':trainer.updates if trainer else 0,'transitions':trainer.transitions if trainer else 0,
              'last_checkpoint':str(last_saved) if last_saved else None,
              'profile':'deadline_pilot_v1','production_reward_certified':False,
              'physical_backend':'CPU PhysX','learning_device':args.device,
              'stop_at':args.stop_at,'interval_minutes':args.interval_minutes})
    if failure or not unchanged or evaluation_failures:
        raise RuntimeError(failure or 'input closure/evaluation failed')


if __name__ == '__main__': main()
