"""Fit one hand actor to a verified native trajectory; no PPO updates."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--role', choices=('left', 'right'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=2000)
    parser.add_argument('--batch-size', type=int, default=120)
    parser.add_argument('--learning-rate', type=float, default=3e-4)
    parser.add_argument('--std', type=float, default=.02)
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    import os
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    import isaacgym
    import math, random
    import numpy as np
    import torch
    from guitar_learning.imitation.imitation import load_dataset, fit_actor, save_initialization
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.imitation.imitation_io import pin_inputs, verify_inputs
    from guitar_learning.training.recording import write, digest
    if not math.isfinite(args.std) or not math.exp(-5) <= args.std <= math.exp(2):
        raise ValueError('std within policy latent Gaussian bounds required')
    torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    data = load_dataset(args.dataset, args.role)
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    pinned = pin_inputs(data['manifest']); write(out/'inputs_before.json', pinned)
    write(out/'settings.json', dict(dataset=str(args.dataset.resolve()), role=args.role,
        steps=args.steps, batch_size=args.batch_size, learning_rate=args.learning_rate,
        std=args.std, seed=args.seed, device='cuda:0', size='medium', mode='Actor_only_BC_no_PPO_updates'))
    model = SpecialistPolicy(505, size='medium', contract=data['contract'], role=args.role).to('cuda:0')
    with torch.no_grad(): model.log_std.fill_(math.log(args.std))
    before = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    with (out/'fit.jsonl').open('x') as stream:
        def progress(row):
            stream.write(json.dumps(row)+'\n'); stream.flush()
            print('[imitation] role=%s step=%d mse=%.8g max_error=%.6f' %
                  (args.role, row['step'], row['training_mse'], row['max_abs_error']), flush=True)
        fit = fit_actor(model, data, steps=args.steps, lr=args.learning_rate,
                        batch_size=args.batch_size, seed=args.seed, log_callback=progress)
    changed = [k for k, v in model.state_dict().items() if not torch.equal(before[k], v.detach().cpu())]
    prefixes = ('actor_encoders.'+args.role+'.', 'actor_heads.'+args.role+'.')
    if any(not k.startswith(prefixes) for k in changed):
        raise RuntimeError('nonselected actor/critic/std changed during BC')
    checkpoint = out/'actor_initialization.pt'
    save_initialization(model, checkpoint, dataset_manifest=data['manifest'], fit_result=fit)
    write(out/'report.json', dict(completed=True, role=args.role, fit=fit, changed_model_keys=changed,
        checkpoint=dict(path=str(checkpoint), sha256=digest(checkpoint)),
        source_unchanged=verify_inputs(pinned), ppo_updates=0,
        scope='one captured trajectory training fit only; native deterministic validation is separate'))


if __name__ == '__main__': main()
