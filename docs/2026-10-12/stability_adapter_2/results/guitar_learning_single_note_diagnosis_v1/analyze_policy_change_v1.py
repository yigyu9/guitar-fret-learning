"""Compare frozen checkpoints on the same saved post-step observations, CPU only."""
import gzip
import hashlib
import json
from pathlib import Path
import torch
from guitar_learning.specialist_policy import SpecialistPolicy

PHASE = Path(__file__).resolve().parent
BASE = PHASE.parent/'guitar_learning_resource_long_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def construct(payload):
    a = payload['identity']['architecture']
    model = SpecialistPolicy(a['state_dim'], event_dim=a['event_dim'], size=a['size'],
        role=a['role'], frozen_partner=a['frozen_partner'], contract=a['contract'])
    model.load_state_dict(payload['model']); model.eval()
    return model


def main():
    torch.set_num_threads(1)
    manifest = json.loads((PHASE/'evidence_v1/manifest.json').read_text())
    result = dict(scope='offline fixed saved post-step observation probes; not native evaluation, trajectory prediction or music-success evidence', hands={})
    for role in ('left', 'right'):
        spec = manifest[role]
        initial_path, final_path = Path(spec['initial_checkpoint']), Path(spec['checkpoint'])
        assert digest(initial_path) == spec['initial_sha256']
        assert digest(final_path) == spec['checkpoint_sha256']
        initial = torch.load(initial_path, map_location='cpu', weights_only=False)
        final = torch.load(final_path, map_location='cpu', weights_only=False)
        assert initial['identity'] == final['identity']
        chosen = []
        folder = PHASE/'probe_evidence_v1'/role
        folder.mkdir(parents=True, exist_ok=True)
        for episode in (0, 5):
            paths = sorted((BASE/f'long_{role}_v1/worker_000'/('audit_episode_%06d'%episode)).glob('transition_*.json.gz'))
            for target in (0, 119, 239, 260, 299, 418):
                p = min(paths, key=lambda f: abs(int(f.name.split('_')[1].split('.')[0])-target))
                if p in chosen: continue
                chosen.append(p)
        rows, sources = [], []
        for source in chosen:
            data = source.read_bytes()
            dest = folder/(source.parent.name+'_'+source.name)
            dest.write_bytes(data)
            row = json.loads(gzip.decompress(data))
            rows.append(row)
            sources.append(dict(source=str(source), snapshot=str(dest), sha256=hashlib.sha256(data).hexdigest(),
                task_time_s=row['info']['task_time_s'], episode=source.parent.name))
        inputs = [torch.tensor([row['observation'][key] for row in rows], dtype=(torch.bool if 'mask' in key else torch.float32))
                  for key in ('state','events','mask','priority_events','priority_mask')]
        models = [construct(initial), construct(final)]
        with torch.no_grad():
            before, after = [m(*inputs) for m in models]
        sl = models[0].role_slices[role]
        means = [r['mean'][:, sl] for r in (before, after)]
        stds = [r['log_std'][:, sl].exp() for r in (before, after)]
        actions = [v.tanh() for v in means]
        kl = ((after['log_std'][:, sl]-before['log_std'][:, sl]) +
            (stds[0].square()+(means[0]-means[1]).square())/(2*stds[1].square())-.5).sum(-1)
        active_names = initial['identity']['architecture']['contract']['action']['names'][sl]
        parameters = {}
        for group, prefixes in dict(actor=('actor_encoders.'+role+'.','actor_heads.'+role+'.'),
                                    value=('value_encoder.','reward_critic.','cost_critic.')).items():
            keys = [k for k in initial['model'] if k.startswith(prefixes)]
            a = torch.cat([initial['model'][k].flatten() for k in keys]).double()
            b = torch.cat([final['model'][k].flatten() for k in keys]).double()
            parameters[group] = dict(elements=a.numel(), l2_initial=float(a.norm()), l2_delta=float((b-a).norm()),
                relative_l2_delta=float((b-a).norm()/a.norm()), max_abs_delta=float((b-a).abs().max()))
        effective = [std*(1-action.square()) for std,action in zip(stds,actions)]
        channels = [dict(name=name, mean_abs_action_before=float(actions[0][:,i].abs().mean()),
            mean_abs_action_after=float(actions[1][:,i].abs().mean()),
            max_abs_action_delta=float((actions[1][:,i]-actions[0][:,i]).abs().max()),
            saturated_probe_count_after=int((actions[1][:,i].abs()>=.98).sum()),
            mean_latent_std=float(stds[1][:,i].mean()),
            mean_local_action_std_approx=float(effective[1][:,i].mean())) for i,name in enumerate(active_names)]
        probes = [dict(**source, mean_abs_action_delta=float((actions[1][i]-actions[0][i]).abs().mean()),
            max_abs_action_delta=float((actions[1][i]-actions[0][i]).abs().max()),
            forward_gaussian_kl=float(kl[i]),
            saturated_channels_before=int((actions[0][i].abs()>=.98).sum()),
            saturated_channels_after=int((actions[1][i].abs()>=.98).sum()),
            saturated_channel_names_after=[name for j,name in enumerate(active_names) if abs(float(actions[1][i,j]))>=.98],
            initial_action=actions[0][i].tolist(), final_action=actions[1][i].tolist(),
            local_action_std_approx=effective[1][i].tolist()) for i,source in enumerate(sources)]
        result['hands'][role] = dict(initial_updates=initial['updates'],checkpoint_updates=final['updates'],
            accepted_updates_compared=final['updates']-initial['updates'], checkpoint=str(final_path),
            actor_lr=final['actor_optimizer']['param_groups'][0]['lr'], parameters=parameters,
            log_std_max_abs_change=float((final['model']['log_std'][sl]-initial['model']['log_std'][sl]).abs().max()),
            probe_count=len(rows), gaussian_kl_mean=float(kl.mean()),
            mean_abs_action_delta=float((actions[1]-actions[0]).abs().mean()),
            max_abs_action_delta=float((actions[1]-actions[0]).abs().max()),
            channels=channels,probes=probes,
            local_std_scope='first-order tanh derivative times latent std at probe mean; normalized action, not measured joint-angle variance')
    (PHASE/'policy_change_v1.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({h:{k:v for k,v in r.items() if k not in ('channels','probes')} for h,r in result['hands'].items()},indent=2))


if __name__ == '__main__': main()
