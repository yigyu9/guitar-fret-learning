"""NoNN noisy-reference128; original reference/codec/evaluator, root-only native."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('reference_noise_original',HERE.parent/'index_prefix_goal_exploration_precheck_v1/probe.py')
on=importlib.util.module_from_spec(s);sys.modules[s.name]=on;s.loader.exec_module(on)
goal=on.source;parent=goal.parent;grid,cap=on.grid,on.cap
SCHEMA='diagnostic.index_prefix_reference_noise.execution.v1'
MODE='noisy_reference'


def output():return HERE/'runs'/MODE


def evidence():
    _,paths,_=on.gate()
    for review in (goal.HERE/'reference_analysis/results_v1/review.json',HERE.parent/'index_prefix_goal_guard_off_v1/analysis/results_v1/review.json'):
        paths.update(parent.base.reviewed(review))
    return paths|{HERE/'probe.py',HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md',on.HERE/'cpu_verification.json'}


def gate(require_review=True):
    paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json') and all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def std4(like):
    # Same formula -> float32 log -> exp path as the reviewed NN execution override.
    import torch
    sigma=grid.read(on.EXPLORATION/'comparison.json')['candidate_sigma4']
    raw=like.new_tensor(sigma).log();assert bool(((raw>=-5)&(raw<=2)).all())
    return raw.clamp(-5,2).exp()


def perturb(raw,selected,noise):
    import torch
    mean=raw[:,selected];assert bool(torch.isfinite(mean).all() & (mean.abs()<1).all())
    latent=mean.atanh();result=raw.clone();result[:,selected]=(latent+noise).tanh()
    return result,(latent.tanh()-mean).abs()


@contextmanager
def execution_scope(approved,audit):
    # Entered only after original IsaacGym import, never during the stdlib gate.
    import random
    import numpy as np
    import torch
    codec=goal.support();extra=parent.support();old=(goal.output,goal.gate,codec.execution_scope)
    @contextmanager
    def scoped(producer,stage,seal,paths,observed):
        assert stage=='reference';audit['original_observed']=observed
        with old[2](producer,stage,seal,paths,observed):
            prior=parent.base.effort_scope
            @contextmanager
            def caps(*args):
                with prior(*args) as runner:
                    previous=(extra.reference_action,runner._evaluate,codec.convert)
                    def reference(pool,value):
                        raw=previous[0](pool,value);selected=pool.spec['learned_action_indices'];assert pool.num_envs==128 and selected==[17,18,19,20]
                        std=std4(raw);before=on.rng();noise=torch.distributions.Normal(torch.zeros_like(raw[:,selected]),std.expand_as(raw[:,selected])).sample()
                        assert on.rng()!=before;noisy,residual=perturb(raw,selected,noise);epsilon=noise/std
                        audit['calls']+=1;audit['RNG_advances']+=1;audit['stream'].update(noise.detach().cpu().numpy().tobytes())
                        audit['effective_std4']=std.detach().cpu().tolist();audit['roundtrip_max_abs_raw']=max(audit['roundtrip_max_abs_raw'],float(residual.max()))
                        audit['epsilon_sum']+=epsilon.double().sum(0).cpu().numpy();audit['epsilon_square_sum']+=epsilon.double().square().sum(0).cpu().numpy()
                        for i in range(4):
                            if bool(pool.first[i]):audit['noise_rows'].append(dict(env_id=i,start_clock=int(pool.environment.clock[i]),raw_reference=raw[i,selected].detach().cpu().numpy().copy(),
                                scaled_noise=noise[i].detach().cpu().numpy().copy(),epsilon_standardized=epsilon[i].detach().cpu().numpy().copy(),raw_noisy_goal=noisy[i,selected].detach().cpu().numpy().copy()))
                        return noisy
                    def convert(*a,**k):audit['conversion_calls']+=1;return previous[2](*a,**k)
                    def evaluate(pool,policy,spec,args,out):
                        assert args.control=='reference' and args.episodes==pool.num_envs==128
                        random.seed(7);np.random.seed(7);torch.manual_seed(7);audit['seed_after_pool_ready']=True
                        return previous[1](pool,policy,spec,args,out)
                    extra.reference_action=reference;runner._evaluate=evaluate;codec.convert=convert
                    try:yield runner
                    finally:
                        extra.reference_action,runner._evaluate,codec.convert=previous
                        audit['callback_aliases_restored']=(extra.reference_action,runner._evaluate,codec.convert)==previous
            parent.base.effort_scope=caps
            try:yield
            finally:parent.base.effort_scope=prior
    goal.output=lambda stage:output() if stage=='reference' else old[0](stage);goal.gate=lambda stage:approved;codec.execution_scope=scoped
    try:yield
    finally:
        goal.output,goal.gate,codec.execution_scope=old
        audit['producer_aliases_restored']=(goal.output,goal.gate,codec.execution_scope)==old


def finish(audit,completed,failure):
    import numpy as np
    out=output();secondary=None
    try:
        rows=audit['noise_rows']
        if rows:
            with (out/'reference_noise4.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
    except BaseException as error:secondary=error
    old=grid.read(out/'goal_codec_report.json') if (out/'goal_codec_report.json').is_file() else {}
    checks=dict(original_reference_complete=old.get('completed') is True,NN_constructors_zero=old.get('NN_constructors')==0,reference_calls_exact=old.get('reference_calls')==audit['calls'],
        sampling_once=audit['calls']>0 and audit['calls']==audit['RNG_advances']==audit['conversion_calls'],seed_after_pool_ready=audit.get('seed_after_pool_ready',False),
        aliases_restored=audit.get('callback_aliases_restored',False) and audit.get('producer_aliases_restored',False),typed_noise_saved=secondary is None and (out/'reference_noise4.npz').is_file(),no_checkpoint_written=not list(out.glob('*.pt')))
    count=audit['calls']*128
    value=dict(schema=SCHEMA,completed=completed and all(checks.values()),failure=failure,checks=checks,calls=audit['calls'],RNG_advances=audit['RNG_advances'],conversion_calls=audit['conversion_calls'],
        Gaussian_shape_per_call=[128,4],normal_noise_stream_sha256=audit['stream'].hexdigest(),effective_std4=audit.get('effective_std4'),seed=7,
        epsilon_standardized_mean=(audit['epsilon_sum']/count).tolist() if count else None,epsilon_standardized_rms=np.sqrt(audit['epsilon_square_sum']/count).tolist() if count else None,
        zero_noise_roundtrip_max_abs_raw=audit['roundtrip_max_abs_raw'],NN_constructors=old.get('NN_constructors'),model_loads=0,PPO_updates=0,fit_steps=0,guard_enabled=True,
        original_reference_model_RNG_frozen_is_not_sampling_audit=True,noise_injected_at='reference rawgoal after original encode',
        scope='NoNN reference hook after original encode; original Normal(zeros[128,4],effective_std4).sample once per60Hz control. epsilon_standardized=scaled_noise/std includes float rounding, not separately redrawn primitive epsilon. Other35 action columns unchanged by noise; source contract/metadata preserved with this declared execution override. Normal timeline354 calls; original early completion/reset behavior unchanged.')
    try:grid.write(out/'reference_noise_report.json',value)
    except BaseException as error:
        if secondary is not None:print('Secondary noise report error: '+repr(error),file=sys.stderr);raise secondary from None
        raise
    if secondary is not None:raise secondary
    if failure is None and not all(checks.values()):raise RuntimeError('Noisy reference audit failed')


def launch():
    cap.reject_existing(output());approved=gate();audit=dict(calls=0,RNG_advances=0,conversion_calls=0,stream=hashlib.sha256(),noise_rows=[],roundtrip_max_abs_raw=0.)
    failure=None;completed=False
    try:
        import isaacgym  # Full stdlib gate before numerical scope, same native import order.
        import numpy as np
        audit.update(epsilon_sum=np.zeros(4),epsilon_square_sum=np.zeros(4))
        with execution_scope(approved,audit):goal.launch('reference')
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if output().is_dir():
            try:finish(audit,completed,failure)
            except BaseException as error:
                if failure is None:raise
                print('Secondary reference noise audit error: '+repr(error),file=sys.stderr)


def commands():return {MODE:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',MODE]}


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence();cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=on.module('reference_noise_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]);inputs=HERE/'cpu_inputs';inputs.mkdir()
    for name,value in (('commands.json',commands()),('settings.json',parent.settings())):grid.write(inputs/name,value)
    grid.write(HERE/'cpu_verification.json',checks);paths|={HERE/'cpu_verification.json',*inputs.glob('*.json')}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--execute',choices=[MODE]);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.self_test:print(json.dumps(on.module('reference_noise_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif a.execute:launch()
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending execution admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,mode=MODE)))
