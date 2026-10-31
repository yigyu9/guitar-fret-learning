"""Read-only fixed-state CPU inference at fit/update50; not native evaluation."""
import os
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
import hashlib,json,sys
from pathlib import Path
import numpy as np
import torch
OUT=Path(__file__).resolve().parent;V4=OUT.parents[1];REPO=V4.parents[4]
sys.path[:0]=[str(V4),str(REPO)]
import runtime as rt
import learn
from guitar_learning.training.ppo import DecisionPPOTrainer,PPOConfig
from guitar_learning.training.finger_skill_runner import _validate_pins
CAP=V4/'capture/runs/reference'
if not (CAP/'observations4.npz').exists():
 choices=list((V4/'capture/runs').glob('*/observations4.npz'));assert len(choices)==1;CAP=choices[0].parent
paths={'fit0':V4/'runs/fit/fit.pt','PPO50':V4/'runs/ppo_attempt02/evaluation_000050.pt'}
files=list(paths.values())+[CAP/'observations4.npz',CAP/'training_contract.json',V4/'runs/fit/settings.json',V4/'runtime.py',V4/'learn.py',REPO/'guitar_learning/training/ppo.py',REPO/'guitar_learning/training/policy.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(n,d):(OUT/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
pinsets=[torch.load(p,map_location='cpu',weights_only=False)['metadata']['input_pins'] for p in paths.values()]
assert all(pinsets[1].get(p)==h for p,h in pinsets[0].items())
assert set(pinsets[1])-set(pinsets[0])=={str(paths['fit0'])}
allpins=dict(pinsets[0]);allpins.update(pinsets[1])
files=list(dict.fromkeys(files+[Path(p) for p in allpins]))
before={str(p):sha(p) for p in files}
assert all(before[p]==h for p,h in allpins.items())
settings=read(V4/'runs/fit/settings.json');data,buckets,phases,contract=learn.dataset(CAP,settings);torch.set_num_threads(1);inputs={k:torch.as_tensor(data[k],device='cpu') for k in learn.runner.FIELDS}
ctrl=contract['action']['target_contract'];active=[ctrl['joint_names'].index(n) for n in ctrl['action_order']];ref=torch.tensor(ctrl['reference105_rad'])[active][17:21];low=torch.tensor(ctrl['action_lower_rad'])[17:21];high=torch.tensor(ctrl['action_upper_rad'])[17:21]
result={'scope':'fixed captured1416 teacher states only; no new native/GPU/training; do not rank actual performance or choose best policy by these outputs','capture':str(CAP),'phase_boundaries_local_s':[2,3.1703,3.2703,3.712,3.832],'loader_scope':'trainer.load cannot restore CUDA RNG on CPU; exact trainer identity, V4 metadata/settings/adapter/fresh/pins and finite model validated; new local CPU policy.load_state_dict(strict=True); optimizer/RNG not restored; original checkpoint never changed','pin_relationship':'PPO50 metadata retains all fit0 pins exactly and adds only original fit.pt checkpoint pin','models':{},'deltas':{}}
models={};preds={};values={};latent={}
for name,path in paths.items():
 payload=torch.load(path,map_location='cpu',weights_only=False);meta=payload['metadata'];assert meta['schema']==rt.SCHEMA and meta['settings']==settings and meta['policy_output_adapter']==rt.ADAPTER and meta['fresh_only'] and meta['fit_steps']==1000;_validate_pins(meta)
 policy=rt.GoalPolicy(contract=contract,size=settings['size']).to('cpu');trainer=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']));assert payload['identity']==trainer._identity();assert all(torch.isfinite(v).all() for v in payload['model'].values());policy.load_state_dict(payload['model'],strict=True);policy.eval()
 state_before={n:v.clone() for n,v in policy.state_dict().items()}
 with torch.no_grad():output=policy(*(inputs[k] for k in learn.runner.FIELDS));raw=output['mean'][:,17:21].tanh();decoded=rt.shared.decode(raw,ref,low,high)
 assert all(torch.equal(state_before[n],v) for n,v in policy.state_dict().items());assert all(v.device.type=='cpu' for v in policy.state_dict().values());assert not torch.cuda.is_initialized()
 models[name]=payload['model'];preds[name]=(raw.numpy(),decoded.numpy());latent[name]=output['mean'][:,17:21].numpy();values[name]={k:output[k].numpy() for k in ['reward_value','cost_value']}
 r={'updates':payload['updates'],'checkpoint_sha256':before[str(path)],'selected_log_std4':output['log_std'][0,17:21].tolist(),'selected_std4_dimensionless_latent':output['log_std'][0,17:21].exp().tolist(),'six_phases':[]}
 for phase in range(6):
  k=phases==phase;delta=raw.numpy()[k]-data['raw_goal_normalized'][k];r['six_phases'].append({'phase':phase,'rows':int(k.sum()),'selected_normalized_mean4':raw.numpy()[k].mean(0).tolist(),'latent_mean4':output['mean'][k,17:21].mean(0).tolist(),'decoded_goal_mean_deg4':np.rad2deg(decoded.numpy()[k]).mean(0).tolist(),'normalized_teacher_error_RMS4':np.sqrt((delta**2).mean(0)).tolist(),**{v:{'mean':float(values[name][v][k].mean()),'min':float(values[name][v][k].min()),'max':float(values[name][v][k].max())} for v in values[name]}})
 result['models'][name]=r
for phase in range(6):
 k=phases==phase;raw=preds['PPO50'][0][k]-preds['fit0'][0][k];deg=np.rad2deg(preds['PPO50'][1][k]-preds['fit0'][1][k]);result['deltas'][str(phase)]={'rows':int(k.sum()),'normalized_mean_bias4':raw.mean(0).tolist(),'normalized_mean_RMS4':np.sqrt((raw**2).mean(0)).tolist(),'decoded_goal_bias_deg4':deg.mean(0).tolist(),'decoded_goal_RMS_deg4':np.sqrt((deg**2).mean(0)).tolist(),'decoded_goal_max_abs_deg4':abs(deg).max(0).tolist()}
result['parameter_changes']={}
for prefix in ['finger_encoder.','finger_heads.index.','finger_log_std','value_encoder.','reward_critic.','cost_critic.','support_encoder.','support_head.','support_log_std','finger_heads.middle.','finger_heads.ring.','finger_heads.pinky.']:
 keys=[n for n in models['fit0'] if n.startswith(prefix)];ds=[(models['PPO50'][n]-models['fit0'][n]).reshape(-1) for n in keys];d=torch.cat(ds) if ds else torch.zeros(0);result['parameter_changes'][prefix]={'tensors':len(keys),'elements':d.numel(),'changed_elements':int((d!=0).sum()),'RMS':float(d.square().mean().sqrt()) if d.numel() else None,'max_abs':float(d.abs().max()) if d.numel() else None}
dump('analysis.json',result)
after={str(p):sha(p) for p in files};checks={'inputs_unchanged':before==after,'same_capture1416':len(data['state'])==1416,'checkpoint_updates0_and50':result['models']['fit0']['updates']==0 and result['models']['PPO50']['updates']==50,'strict_identity_and_state_validated':True,'inference_did_not_mutate_model':True,'CPU_only_no_CUDA_initialized':not torch.cuda.is_initialized()}
dump('verification.json',{'all_checks_passed':all(checks.values()),'checks':checks,'input_sha256_before':before,'input_sha256_after':after,'new_GPU_runs':0,'new_native_runs':0,'training_steps':0});assert all(checks.values())
print(json.dumps({'std':{n:v['selected_std4_dimensionless_latent'] for n,v in result['models'].items()},'delta':result['deltas'],'params':result['parameter_changes']},indent=2))

lines=['# PPO50 고정상태 CPU 정책변화: 중간관찰','','이검사는fit0과attempt02의update50checkpoint를동일한캡처teacher상태1416개에적용한CPU추론이다. 실제물리실행·음악성공률·최적checkpoint선정근거가아니다. 진행중학습폴더전체를봉인하거나PPO300완료로기록하지않는다.','','## 정확한모델검증과한계','','현재V4 GoalPolicy557을독립CPU인스턴스로생성했다. V4 schema/settings/adapter/fresh metadata,모든sourcepins(PPOmetadata는fit원핀동일+원fit.pt핀1개추가),전체architecture·contract·PPO config를포함한traineridentity가정확히일치하고finite model임을검증한뒤load_state_dict(strict=True)로읽었다. 원trainer.load는CUDA RNG topology를확인하므로CUDA_VISIBLE_DEVICES=빈값인CPU에서GPUcheckpoint전체resume를거부한다. loader/원checkpoint/RNG항목을고치거나제거하지않았고optimizer/RNG를복원하지않았다. 따라서full checkpoint가재개되었다고주장하지않는다. 모델추론전후state_dict동일,CUDA초기화0을확인했다.','','## 6phase의선택4축평균변화','','bucket은입력time+1/60기준[2,3.1703,3.2703,3.712,3.832]초로6분할한다. phase3는V2 N유지와early closing을함께포함한다. 축순서는index1_x/index1_z/PIP/DIP다. 아래는PPO50−fit0의decoded목표bias와RMS(도)이며latent std의각도환산이아니다.','','| phase/행 | bias deg4 | RMS deg4 |','|---|---|---|']
for phase,d in result['deltas'].items():lines.append('| '+phase+'/'+str(d['rows'])+' | '+ '/'.join(f'{v:+.6f}' for v in d['decoded_goal_bias_deg4'])+' | '+'/'.join(f'{v:.6f}' for v in d['decoded_goal_RMS_deg4'])+' |')
lines+=['','선택normalized평균·latent평균·decoded평균과teacher목표오차는analysis.json에보존했다. 같은teacher상태에서의변화이며훈련정책자체상태분포나native접촉변화를뜻하지않는다.','','| 모델 | logstd4 | std4(무차원latent) |','|---|---|---|']
for name,r in result['models'].items():lines.append('| '+name+' | '+'/'.join(f'{v:.9f}' for v in r['selected_log_std4'])+' | '+'/'.join(f'{v:.9f}' for v in r['selected_std4_dimensionless_latent'])+' |')
lines+=['','## 실제파라미터와가치출력의변화','','| parameter group | 변경elements / 전체 | RMS delta | max abs delta |','|---|---:|---:|---:|']
for name,r in result['parameter_changes'].items():lines.append(f"| {name} | {r['changed_elements']} / {r['elements']} | {r['RMS']:.9g} | {r['max_abs']:.9g} |")
lines+=['','finger_log_std16개중4개만달라졌다. support와다른손가락head의불변은그들의입력shared encoder까지모두불변이라는뜻은아니다. finger_encoder는변했고active출력은index4축뿐이다.','','| 모델/phase | reward value mean | cost value mean |','|---|---:|---:|']
for name,r in result['models'].items():
 for phase in r['six_phases']:lines.append(f"| {name}/{phase['phase']} | {phase['reward_value']['mean']:.9f} | {phase['cost_value']['mean']:.9f} |")
lines+=['','value출력분포는고정상태에서의학습변화를보여줄뿐실제실현return/cost나압현품질을증명하지않는다. 음의cost value도그대로기록했으며실제음의안전비용으로해석하지않는다. 검수된실제성과판정은root의PPO300종료확인과고정128평가후별도stage_PPO_v1에서해야한다. attempt01의49update/200704전이중단은추가소모로별도기록하고attempt02학습이나최종성과에합산하지않는다.','','## 무결성','',f"verification.json: 고정checkpoint2개·capture2개·현행실행소스·metadata모든pin을포함한입력{len(files)}파일전후SHA256동일,자체{len(checks)}검사통과. 새native/GPU/학습은0이다. 현재학습의mutable metrics나전체runs폴더를입력으로삼지않았다."]
(OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
