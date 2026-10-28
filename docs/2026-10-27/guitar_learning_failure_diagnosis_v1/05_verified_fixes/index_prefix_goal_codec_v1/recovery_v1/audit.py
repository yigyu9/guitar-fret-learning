"""CPU proof of a complete saved fit plus one isolated finally-report NameError."""
import ast
import builtins
from pathlib import Path
import symtable
import tempfile


def unresolved(path):
    text=Path(path).read_text();ast.parse(text,feature_version=(3,8));top=symtable.symtable(text,str(path),'exec')
    defined={s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}|set(dir(builtins))|{'__file__','__name__','__doc__'}
    missing=set()
    def visit(table):
        for symbol in table.get_symbols():
            if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in defined:missing.add(symbol.get_name())
        for child in table.get_children():visit(child)
    visit(top);return sorted(missing)


def saved_state(payload,trainer,initial,impl):
    import torch
    assert payload['identity']==trainer._identity()
    assert payload['updates']==0 and payload['cost_weight']==1 and not payload['actor_optimizer']['state'] and not payload['value_optimizer']['state']
    assert len(payload['model'])==73 and set(payload['model'])==set(initial) and all(torch.isfinite(v).all() for v in payload['model'].values())
    trainer.policy.load_state_dict(payload['model'],strict=True)
    invariant=impl.invariants(initial,trainer.policy)
    assert invariant['frozen_state_tensors']==54 and len(invariant['changed_names'])==19
    return invariant


def run(probe):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in __import__('sys').modules
    source=probe.source;codec=source.support();folder=source.output('fit');config=probe.grid.read(folder/'settings.json');pins=probe.grid.read(folder/'inputs_before.json')
    assert config==source.parent.settings() and all(probe.grid.sha(p)==h for p,h in pins.items())
    files={str(p.resolve()):probe.grid.sha(p) for p in folder.iterdir()}
    parent=probe.grid.read(source.HERE/'02_launcher.json');log=(source.HERE/'02_fit.log').read_text();probe.single_defect(parent,log,[p.name for p in folder.iterdir()])
    files.update({str(source.HERE/n):probe.grid.sha(source.HERE/n) for n in ('02_launcher.json','02_fit.log','preparation_seal.json','codec.py','probe.py')})
    errors=probe.grid.read(folder/'offline_errors.json');assert len(errors['losses'])==1000 and np.isfinite(errors['losses']).all() and min(errors['losses'])>=0
    data,buckets,labels,contract,label_evidence=codec.dataset(source);assert errors['label_evidence']==label_evidence
    assert [sum(data['env_id'][b]<3) for b in buckets]==[len(b) for b in buckets]
    torch.manual_seed(7);policy=codec.policy_type(source)(contract=contract,size='large',fresh=True)
    initial={n:v.detach().clone() for n,v in policy.state_dict().items()};fresh=torch.load(source.parent.checkpoint(0),map_location='cpu',weights_only=False)
    assert len(initial)==73 and all(torch.equal(v,fresh['model'][n]) for n,v in initial.items())
    payload=torch.load(probe.CHECKPOINT,map_location='cpu',weights_only=False);assert probe.grid.sha(probe.CHECKPOINT)==probe.MODEL_SHA
    m=payload['metadata'];assert m['schema']==source.SCHEMA and m['settings']==config and m['input_pins']==pins and m['actual_initialization']==source.descriptor()
    assert m['policy_output_adapter']==codec.ADAPTER and m['collection_sha256']==source.source.DATA_SHA and m['original_initial_sha256']==probe.grid.sha(source.parent.checkpoint(0))
    trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']));invariant=saved_state(payload,trainer,initial,source.source.source.support())
    assert invariant==probe.grid.read(folder/'parameter_invariants.json')
    try:trainer.load(probe.CHECKPOINT)
    except ValueError as error:assert str(error)=='CUDA RNG topology mismatch'
    else:raise AssertionError('Original CUDA RNG checkpoint unexpectedly restored on CPU')
    # One /tmp projection of CUDA RNG only; never rewrite original bytes/metadata/identity.
    with tempfile.TemporaryDirectory() as temp:
        projection=dict(payload,cuda_rng=None);path=Path(temp)/'CPU_projection.pt';torch.save(projection,path);trainer.load(path)
        assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        assert all(torch.equal(v,policy.state_dict()[n]) for n,v in payload['model'].items())
    assert probe.grid.sha(probe.CHECKPOINT)==probe.MODEL_SHA
    code=(source.HERE/'codec.py').read_text();assert unresolved(source.HERE/'codec.py')==['sys']
    # Source ordering + actual parameter file establish that strict reload and checks ran before finally failed.
    ordered=[code.index(s) for s in ("loaded.load(out/'initial.pt')","checks=dict(original_fresh73_exact", "runner.write(out/'parameter_invariants.json',invariant);completed=all(checks.values())","missing=sorted(runner.project_source_paths(list(sys.modules.items()))")]
    assert ordered==sorted(ordered) and "import sys" not in code
    inputs={str(source.source.COLLECT/'training_contract.json'):probe.grid.sha(source.source.COLLECT/'training_contract.json')}
    return dict(schema=probe.SCHEMA,accepted_for_evaluate_only=True,original_parent_completed=False,original_returncode=1,only_known_error="NameError sys in codec.py:221 post-fit finally audit",
        unchanged_original_missing_reports=['inputs_after.json','goal_codec_report.json'],checkpoint_sha256=probe.MODEL_SHA,original_checkpoint_schema=source.SCHEMA,PPO_updates=0,supervised_steps=1000,
        model_tensors=73,fresh73_exact=True,model_finite=True,frozen54_exact=True,changed19_declared_only=True,critics_std_other_exact=True,cost2zero=True,PPO_empty0=True,new_goal_identity_exact=True,
        original_input_pins_count=len(pins),original_input_pins_current=True,losses_count=1000,losses_finite=True,original_labels_exact=label_evidence,
        original_native_post_save_strict_reload_evidence='Source ordered strict reload/checks, actual parameter_invariants, then sole finally NameError. Not a normal completed fit/report.',
        CPU_original_CUDA_topology_rejected=True,CPU_projection_scope='Only /tmp copy cuda_rng=None; original full identity/model/metadata/optimizers retained; not actual CUDA restore',
        original_checkpoint_metadata_unchanged=True,all_original_fit_checks_reconstructed_true=True,hidden_false_invariants_cost_or_PPO_rejected=True,raw_sha256=files,input_sha256=inputs,
        scope='Explicit salvage of original saved model after one known post-fit reporting error only; original exit1/missing reports retained; no refit/recapture/physical-success inheritance')
