"""CPU-only actual four-run contact-source/noise audit; no checkpoint deserialization."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
V7 = HERE.parent/'index_reward_value_warmup_v7'
CASES = ('det','private7','private17','private27')
AXES = ('LH:index1_x','LH:index1_z','LH:index2','LH:index3')


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path);value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value;spec.loader.exec_module(value);return value

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def require(ok,message):
    if not ok: raise ValueError(message)


def inputs(core):
    pins = dict(core.gate())  # stdlib gate before any numerical import.
    pins[str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
    for case in CASES:
        execution = HERE/('execution_'+case+'.json')
        info = read(execution)
        require(info['case'] == case and info['returncode'] == 0,'Execution failed')
        pins[str(execution)] = sha(execution)
        log = HERE/('execution_'+case+'.log');pins[str(log)] = sha(log)
        folder = HERE/'runs'/case
        report = read(folder/'observer_report.json')
        require(report['completed'] and not report['failure'] and not report['changed_inputs'],'Observer failed')
        require(report['case'] == case and report['private_policy_noise_seed'] == core.CASES[case] and report['physical_reset_seed'] == 7,'Case/seed mismatch')
        require(report['fit_steps'] == report['value_warmup_steps'] == report['PPO_updates'] == 0,'Unexpected new fitting/update')
        require(report['act_calls'] == report['act_attempts'] == report['step_calls'] == report['step_attempts'],'Partial observer calls')
        require(report['global_RNG_scope_restored'] and report['factory_and_step_restored'] and report['policy_sample_shape'] == [128,4],'Observer invariants failed')
        require(read(folder/'inputs_before.json') == report['input_pins'],'Observer input map mismatch')
        for mapping in (report['input_pins'],report['output_sha256']):
            for p,h in mapping.items():
                require(sha(p) == h,'Observer input/output SHA changed: '+p)
                require(p not in pins or pins[p] == h,'Conflicting input SHA');pins[p] = h
        for p in folder.rglob('*'):
            if p.is_file(): pins[str(p)] = sha(p)
    require(all(sha(p) == h for p,h in pins.items()),'Initial input mismatch')
    return pins


def raw_sources(core,folder,evaluation,report):
    import numpy as np
    raw = read(folder/'raw_ledgers.json')
    require(raw['complete'] and raw['assigned_quotas'] == [1]*128 and raw['selected_note_opportunities'] == 384,'Raw ledger incomplete')
    episodes = raw['episodes']
    require(len(episodes) == 128 and sorted(e['env_id'] for e in episodes) == list(range(128)),'Raw128 unique environments required')
    episodes = sorted(episodes,key=lambda e:e['env_id'])
    compact = sorted(evaluation['episodes'],key=lambda e:e['env_id'])
    notes = report['source_notes']
    require([(n['source_index'],n['string_1based'],n['fret']) for n in notes] == [(4,3,4),(7,2,5),(8,2,5)],'Original target cells changed')
    require(all(n['audible_duration_s'] == n['end_s']-n['onset_s'] and n['audible_duration_s'] > 0 for n in notes),'Original audible durations required')
    all_times = [];all_min = [];all_max = []
    wrong_errors = [];support_errors = []
    for raw_ep,ep in zip(episodes,compact):
        require(raw_ep['env_id'] == ep['env_id'] and raw_ep['steps'] == ep['steps'],'Raw/compact identity mismatch')
        ledger = core.validate_raw_ledger(raw_ep)
        source = ledger['wrong_press_sources']
        require(source['contract'] == read(folder/'evaluation/training_contract.json')['diagnostics']['wrong_press'],'Raw contract changed')
        require(raw_ep['selected_source_indices'] == [4,7,8] and sum(ledger['focus_mask']) == 3,'Selected scope mismatch')
        for note,short in zip(notes,ep['notes']):
            index = note['source_index'];duration = note['audible_duration_s']
            require(source['target_strings_1based'][index] == note['string_1based'],'Source target string mismatch')
            require(ledger['target_ids'][index] == short['target_id'],'Source target ID mismatch')
            values = ledger['values']
            wrong_errors.append(abs(values['wrong'][index]/duration-short['audible_wrong_fraction']))
            support_errors.append(abs(values['wrong_supported_time'][index]+values['wrong_ambiguous_time'][index]-values['wrong'][index]))
        all_times.append(source['values']['wrong_source_time'])
        all_min.append(source['values']['wrong_source_fret_min']);all_max.append(source['values']['wrong_source_fret_max'])
    times = np.asarray(all_times,dtype=np.float64)
    minima,maxima = np.asarray(all_min),np.asarray(all_max)
    require(np.isfinite(times).all() and (times >= 0).all(),'Invalid source times')
    require(max(wrong_errors) < 1e-12 and max(support_errors) < 1e-12,'Raw wrong/support and compact wrong disagree')
    summaries = []
    for note in notes:
        index,duration = note['source_index'],note['audible_duration_s']
        require(bool((times[:,index] <= duration+1e-10).all()),'Individual body/cause time exceeds audible duration')
        sources = []
        for body,name in enumerate(core.BODIES):
            for cause,label in enumerate(core.CAUSES):
                values = times[:,index,body,cause];active = values > 0
                sources.append(dict(body=name,cause=label,mean_time_fraction=float((values/duration).mean()),
                    nonzero_env_count=int(active.sum()),source_fret_min=int(minima[active,index,body].min()) if active.any() else None,
                    source_fret_max=int(maxima[active,index,body].max()) if active.any() else None,
                    fret_range_scope='Target/body range unions all contributing causes; not an independent cause-specific range'))
        summaries.append(dict(**note,sources=sources))
    return dict(notes=summaries,raw_wrong_fraction_max_abs_error=max(wrong_errors),supported_plus_ambiguous_max_abs_error=max(support_errors),
        denominator='All128 assigned first attempts, including failures; each source time divided by original target audible duration. Sources/causes overlap and must not be summed as a wrong penalty.'),episodes


def actor_summary(folder,raw_episodes):
    import numpy as np
    with np.load(folder/'actor_selected4.npz',allow_pickle=False) as z: data = {k:z[k].copy() for k in z.files}
    count = len(data['env_id'])
    require(all(data[k].shape == (count,4) and np.isfinite(data[k]).all() for k in ('mean','log_std','latent','action')),'Invalid selected4 samples')
    require(np.array_equal(data['env_id'][:128],np.arange(128)) and (data['control_tick'][:128] == 0).all(),'First original128 sample batch required')
    require((data['action'] <= 1).all() and (data['action'] >= -1).all(),'Invalid normalized goals')
    tanh_error = float(np.max(np.abs(np.tanh(data['latent'])-data['action'])))
    require(tanh_error < 2e-7,'Latent/action transform mismatch')
    for ep in raw_episodes:
        selected = data['env_id'] == ep['env_id'];steps = ep['steps']
        require(selected.sum() == steps and np.array_equal(data['control_tick'][selected],np.arange(steps)),'First-attempt actor rows/steps mismatch')
        require(np.array_equal(data['start_clock'][selected],4*np.arange(steps)),'Actual clock discontinuity')
    np.testing.assert_allclose(data['end_source_time_s']-data['start_source_time_s'],1/60,rtol=0,atol=2e-14)
    noise = data['latent']-data['mean'];std = np.exp(data['log_std'])
    result = dict(rows=count,axes=AXES,units='Raw Gaussian latent / log_std; action is tanh normalized absolute goal, not degrees',
        latent_noise_RMS4=np.sqrt((noise.astype(np.float64)**2).mean(0)).tolist(),
        Gaussian_std_mean4=std.astype(np.float64).mean(0).tolist(),
        noise_over_std_RMS4=np.sqrt(((noise/std).astype(np.float64)**2).mean(0)).tolist(),
        latent_to_action_max_abs_error=tanh_error,first128_mean=data['mean'][:128].tolist(),first128_log_std=data['log_std'][:128].tolist())
    return result


def plots(result,out):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # Every cell is a source fraction averaged over original128; never sum overlapping rows.
    active = []
    for body in result['body_names']:
        for cause in result['cause_order']:
            if any(s['mean_time_fraction'] > 0 for case in CASES for note in result['cases'][case]['sources']['notes'] for s in note['sources'] if s['body'] == body and s['cause'] == cause):active.append((body,cause))
    fig,axes = plt.subplots(1,3,figsize=(14,max(4,len(active)*.55)))
    for column,source_index in enumerate((4,7,8)):
        matrix = []
        for body,cause in active:
            matrix.append([next(s['mean_time_fraction'] for note in result['cases'][case]['sources']['notes'] if note['source_index'] == source_index for s in note['sources'] if s['body'] == body and s['cause'] == cause) for case in CASES])
        data = np.asarray(matrix) if matrix else np.zeros((1,4))
        ax = axes[column];im = ax.imshow(data,vmin=0,vmax=1,cmap='magma',aspect='auto')
        ax.set_xticks(range(4));ax.set_xticklabels(CASES,rotation=25)
        ax.set_yticks(range(len(active)) if active else [0]);ax.set_yticklabels([b.replace('human/LH:','')+' / '+c for b,c in active] if active else ['no nonzero source'],fontsize=8)
        note = result['cases']['det']['sources']['notes'][column]
        ax.set_title('Source%d: string%d / fret%d'%(source_index,note['string_1based'],note['fret']))
        for i in range(len(matrix)):
            for j in range(4):ax.text(j,i,'%.3f'%data[i,j],ha='center',va='center',color='white',fontsize=8)
    fig.colorbar(im,ax=axes.ravel().tolist(),label='Mean source time / original audible duration; overlapping sources',shrink=.7)
    fig.subplots_adjust(left=.15,right=.88,wspace=.65,bottom=.15,top=.87)
    fig.savefig(out/'wrong_sources.png',dpi=160);plt.close(fig)
    fig,axes = plt.subplots(2,4,figsize=(16,7),sharex=True)
    for case in CASES:
        folder = HERE/'runs'/case/'evaluation'
        metadata = read(folder/'trace_metadata.json')
        columns = [metadata['joint_names'].index(n) for n in AXES]
        with np.load(folder/'learning_control_env0.npz',allow_pickle=False) as z:
            time = z['source_time_s'];goal = np.rad2deg(z['decoded_goal_rad']);q = np.rad2deg(z['q'][:,columns])
        for i,name in enumerate(AXES):
            axes[0,i].plot(time,goal[:,i],label=case,lw=1);axes[1,i].plot(time,q[:,i],label=case,lw=1)
    for row in range(2):
        for i,name in enumerate(AXES):
            ax = axes[row,i]
            for note,color in zip(result['cases']['det']['sources']['notes'],('grey','steelblue','orange')):
                ax.axvspan(note['onset_s'],note['end_s'],color=color,alpha=.1)
            ax.set_xlim(5.2,8.35);ax.grid(alpha=.2);ax.set_title(name.replace('LH:',''));ax.legend(fontsize=7)
            ax.set_ylabel('Decoded goal (deg)' if row == 0 else 'Actual q (deg)');ax.set_xlabel('Actual score clock (s)')
    fig.suptitle('Env0 first attempt: A to B7/B8; Gaussian latent statistics use separate normalized units')
    fig.tight_layout();fig.savefig(out/'env0_goal_actual.png',dpi=160);plt.close(fig)


def prose(result,out):
    lines = ['# 最終V7: 정책 잡음과 실제 오압현 출처','',
        'V7 마지막300 저장본을 고정하고 원128 첫시도·384음을 네 번 관찰했다. 물리/reset seed는7이며 정책 잡음만 private7/17/27로 분리했다. fit/PPO/optimizer 갱신은0이다. 평균행동과private7은 기존 V7의 전체128 원장·9보상 및 env0 모든 nonforce trace가 동일하다.','',
        '|조건|all3|A 해제 포함 joint|A 해제|실패|원 stage_ready|','|---|---:|---:|---:|---:|---|']
    for case in CASES:
        e = result['cases'][case]['evaluation']
        lines.append('|%s|%d|%d|%d|%d|%s|'%(case,e['all3'],e['joint'],e['A_released'],e['failures'],e['acceptance']['stage_ready']))
    lines += ['', '기준 수행 재현 통과와 원 음악 수용기준 통과는 구분한다. stage_ready가 거짓이어도 이 관찰에서 실패 시도를 제외하지 않는다.','',
        '|조건/음(원소스ID)|달성|clean|wrong|missing|','|---|---:|---:|---:|---:|']
    for case in CASES:
        for note in result['cases'][case]['evaluation']['per_note']:
            lines.append('|%s/%d|%d|%.6f|%.6f|%.6f|'%(case,note['source_index'],note['achieved'],note['clean_mean'],note['wrong_mean'],note['missing_mean']))
    lines += ['', '원소스4(A)는 3번현4프렛, 원소스7/8(B)은 2번현5프렛이다. 7/8은 프렛 번호가 아니다. 각 출처 시간은 해당 음의 실제 발음 길이로 나누고 전체128환경에 평균했다. 원인·몸체는 동시에 활성일 수 있어 합산 감점이나 독립 비중으로 해석하지 않는다.','',
        '![오압현 출처](wrong_sources.png)','', '|조건/음|몸체/원인|시간비율 평균|활성환경/128|출처 프렛 범위*|','|---|---|---:|---:|---|']
    for case in CASES:
        for note in result['cases'][case]['sources']['notes']:
            for s in note['sources']:
                if s['nonzero_env_count']:
                    lines.append('|%s/%d|%s/%s|%.6f|%d|%s..%s|'%(case,note['source_index'],s['body'].replace('human/LH:',''),s['cause'],s['mean_time_fraction'],s['nonzero_env_count'],s['source_fret_min'],s['source_fret_max']))
    lines += ['', '*프렛 min/max는 목표·몸체별 모든 기여 원인의 합집합 범위이며 원인별 독립 범위가 아니다. wrong_string은 목표현이 아닌 표본을 뜻하지만 저장된 이 원장만으로 정확히 어느 다른 현인지까지 정하지 않는다. 실제 접촉쌍·줄 압력·음향의 증명도 아니다.','',
        '|조건|Gaussian latent 잡음 RMS 4축|Gaussian std 평균 4축|잡음/std RMS 4축|','|---|---|---|---|']
    for case in CASES:
        a = result['cases'][case]['actor']
        f = lambda key:'/'.join('%.5f'%x for x in a[key])
        lines.append('|%s|%s|%s|%s|'%(case,f('latent_noise_RMS4'),f('Gaussian_std_mean4'),f('noise_over_std_RMS4')))
    lines += ['', '첫128행의 mean/log_std는 네 조건에서 정확히 같다. 위 수치는 tanh 이전 Gaussian latent 단위이며 관절 도수가 아니다. 아래 곡선은 선택4축의 실제 디코딩 목표와 native 관절각을 도수로 바꾼 env0의 관찰이다.','',
        '![env0 목표와 실제 관절](env0_goal_actual.png)','',
        '세 private 잡음 수행에서 나타난 점수·출처 차이는 표본 변화에 따른 궤적 관찰이다. 첫 행동 이후에는 상태와 평균행동도 피드백으로 달라지므로 후반 mean 차이를 순간 잡음만의 인과효과로 설명하지 않는다. 같은 초기 물리 seed의 정책잡음3개이지 새 학습seed3개나 일반화 검증이 아니다.','',
        '9보상 평균, 원 수용기준, 모든 몸체·원인별 시간비율과 활성환경 수는 analysis.json에 보존했다. 고정기타·검지4축·원3음·seed7 범위를 넘는 다른 손가락/학습seed·자유기타J33·원67음 목표는 미완료다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def run(out):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '','Explicit CPU-only environment required')
    core = module('noise_contact_frozen_core',HERE/'experiment.py')
    pins = inputs(core)
    require(not any(n in sys.modules for n in ('numpy','torch','isaacgym')),'Numerical import before gate')
    out = Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    write(out/'inputs_before.json',pins)
    failure = None
    try:
        import numpy as np
        helper = module('noise_contact_v7_analysis_helper',V7/'analysis/analyze.py').helper().h
        result = dict(cases={},body_names=core.BODIES,cause_order=core.CAUSES)
        for case in CASES:
            folder = HERE/'runs'/case;observer = read(folder/'observer_report.json')
            evaluated = helper.evaluation(helper.V5,(300,case != 'det',folder/'evaluation',V7/'runs/ppo/final.pt'))
            raw_eval = read(folder/'evaluation/evaluation.json')
            report = read(folder/'evaluation/learning_report.json')
            require(report['schema'] == 'diagnostic.reward_value_warmup.v7' and report['checkpoint_updates'] == 300,'Wrong source evaluation')
            after = read(folder/'evaluation/inputs_after.json')
            require(after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'],'Evaluation input audit failed')
            sources,raw = raw_sources(core,folder,raw_eval,observer)
            actor = actor_summary(folder,raw)
            result['cases'][case] = dict(evaluation=evaluated,sources=sources,actor=actor,
                private_noise_seed=core.CASES[case],physical_reset_seed=7,observer_invariance=observer['invariance'])
        first = result['cases']['det']['actor']
        for case in CASES:
            actor = result['cases'][case]['actor']
            np.testing.assert_array_equal(actor['first128_mean'],first['first128_mean'])
            np.testing.assert_array_equal(actor['first128_log_std'],first['first128_log_std'])
        require(all(x == 0 for x in first['latent_noise_RMS4']),'Mean policy sampled noise')
        result['first128_Gaussian_mean_and_log_std_exact_all_cases'] = True
        result['limitations'] = ['Source/cause times overlap; no summed penalty attribution','Post-first-step means/states diverge through feedback; not an instantaneous-noise causal estimate','Fixed guitar/index4/source3notes/reset seed7 only']
        write(out/'analysis.json',result);plots(result,out);prose(result,out)
        require(not any(n in sys.modules for n in ('torch','isaacgym')),'Forbidden model/native import')
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error));raise
    finally:
        try:
            changed = [p for p,h in pins.items() if not Path(p).is_file() or sha(p) != h]
            write(out/'verification.json',dict(completed=failure is None and not changed,failure=failure,changed_inputs=changed,input_sha256_before=pins,
                input_sha256_after={p:sha(p) for p in pins},cases=CASES,new_GPU_runs=0,new_native_runs=0,checkpoint_loads=0,NN_forwards=0,training_steps=0,
                output_sha256={str(p):sha(p) for p in out.iterdir() if p.name in ('analysis.json','RESULTS.md','wrong_sources.png','env0_goal_actual.png')}))
            if failure is None and changed: raise RuntimeError('Analysis input changed')
        except BaseException as error:
            if failure is None: raise
            print('Secondary noise analysis verification error: '+repr(error),file=sys.stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True);args = parser.parse_args();run(args.out)
