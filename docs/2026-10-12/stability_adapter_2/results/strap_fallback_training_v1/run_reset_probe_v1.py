"""Real finite-velocity terminal -> fresh-scene collector reset; no optimization."""
import json
from pathlib import Path
import traceback

BASE = Path(__file__).resolve().parent
OUT = BASE/'reset_probe_v1'
CP = BASE/'smoke_off_v1/checkpoints/update_000012.pt'


def main():
    OUT.mkdir(exist_ok=False)
    # Native library first; copied source views and learner follow it.
    from stability_adapter_2.dual_music_scene_v1 import DualMusicScene
    from stability_adapter_2.deadline_native_v3 import NativeDeadlineEnvironment
    from stability_adapter_2.run_deadline_training_v4 import input_closure, learning_abi, sha, save
    from stability_adapter_2.deadline_ppo_v1 import DeadlinePPO
    from stability_adapter_2.joint_policy_v1 import JointActorCritic
    import numpy as np
    import torch
    torch.set_num_threads(1); torch.manual_seed(103); np.random.seed(103)
    inputs = input_closure()
    inputs[str(CP)] = sha(CP); inputs[str(Path(__file__).resolve())] = sha(__file__)
    save(OUT/'attempt.json', {'input_sha256': inputs, 'mode': 'actual deterministic collector reset diagnostic',
         'native_control_count': 300, 'optimization_updates_added': 0, 'strap_enabled': False})
    env = None; failure = None; result = {}
    try:
        env = NativeDeadlineEnvironment(recording=True, output=OUT/'native', strap_enabled=False)
        obs = env.reset()
        trainer = DeadlinePPO(JointActorCritic(825, env.scene.contract.groups).cuda(), learning_abi(env, inputs))
        trainer.load(CP, restore_rng=False)
        before = {k: v.clone() for k, v in trainer.model.state_dict().items()}
        original_sample = trainer.model.sample
        trainer.model.sample = lambda tensor, deterministic=False: original_sample(tensor, deterministic=True)
        trainer._collection_env, trainer._collection_obs = env, np.array(obs, copy=True)
        batch = trainer.collect(env, 300)
        terminated = torch.nonzero(batch['terminated'][:, 0]).flatten().cpu().tolist()
        unchanged = all(torch.equal(value, trainer.model.state_dict()[key]) for key, value in before.items())
        result = {'terminal_transition_indices_zero_based': terminated,
                  'finite_velocity_fatal_episodes': [r for r in env.episode_reports
                      if r['stop_reason'] == 'finite_joint_velocity_safety'],
                  'episode_count': env.episode, 'last_scene_control_tick': env.tick,
                  'last_scene_physics_steps': env.scene.steps, 'new_scene_is_ready': env._ready,
                  'physical_reset_observed': bool(terminated) and env.episode > 1,
                  'batch_transitions': int(batch['reward'].shape[0]), 'reward_all_finite': bool(torch.isfinite(batch['reward']).all()),
                  'model_and_RMS_unchanged': unchanged, 'optimization_updates_added': 0,
                  'loaded_checkpoint_updates': trainer.updates, 'loaded_checkpoint_transitions': trainer.transitions,
                  'rollout_mode': 'deterministic diagnostic; no PPO optimization or fabricated states'}
        assert unchanged and result['reward_all_finite']
        if result['physical_reset_observed']:
            assert env.scene.steps == env.tick*4
            assert env.tick == 300-terminated[-1]-1
            assert env.initial == env.scene.contract.reference['native_initial_state']
    except BaseException as error:
        failure = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
        print(failure['traceback'], flush=True)
    finally:
        if env is not None:
            try: env.close()
            except BaseException as error:
                if failure is None: failure = {'type': type(error).__name__, 'message': str(error)}
        stable = inputs == {p: sha(p) for p in inputs}
        save(OUT/'report.json', dict(result, failure=failure, inputs_unchanged=stable,
             probe_completed=failure is None and stable, episode_reports=env.episode_reports if env else [],
             production_training_certified=False))
    if failure or not stable: raise RuntimeError(failure or 'input changed')


if __name__ == '__main__': main()
