"""CPU-only integrity/raw-field QA of four already rendered native scenes."""
import csv
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('video_observer',BASE/'render.py')
observer=importlib.util.module_from_spec(spec); spec.loader.exec_module(observer)
parent,repro,cap=observer.parent,observer.repro,observer.cap


def difference(a,b):
    assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    delta=a.astype(np.float64)-b.astype(np.float64)
    return dict(shape=list(a.shape),dtype_new=str(a.dtype),dtype_original=str(b.dtype),value_exact=bool(np.array_equal(a,b)),
        bit_exact=bool(a.dtype==b.dtype and np.array_equal(a.tobytes(),b.tobytes())),different_values=int(np.count_nonzero(a!=b)),
        max_abs=float(np.abs(delta).max()) if delta.size else 0.,rms=float(np.sqrt(np.mean(delta**2))) if delta.size else 0.,
        scope='descriptive exact/residual comparison; no new music acceptance or physical tolerance')


def main():
    out=HERE/'results_v1'; cap.reject_existing(out)
    hashes,verified={},{}
    def remember(path):
        hashes[str(path)]=parent.sha(path); return parent.read(path)
    def pins(values):
        for p,h in values.items(): assert parent.sha(p)==h,p; verified[p]=h
    seal=remember(BASE/'preparation_seal.json'); assert seal['independent_review']=='passed_no_findings' and len(seal['input_pins'])==836
    pins(seal['input_pins'])
    cases=remember(BASE/'cpu_inputs/cases.json'); launcher=remember(BASE/'01_launcher.json')
    assert launcher['completed'] and launcher['returncode']==0 and len(launcher['children'])==4
    media=remember(HERE/'media_precheck.json'); visual=remember(HERE/'visual_qa.json')
    assert media['completed'] and visual['inspected'] and visual['upright'] and visual['fullbody_head_and_feet_visible'] and visual['hand_joint_flexion_visible']
    for path in (HERE/'qa_frames').glob('*.png'): hashes[str(path)]=parent.sha(path)
    rows=[]; compared={}; clocks={}; native_checks={}
    for case,job in zip(cases,launcher['children']):
        name=case['condition']+'_'+case['finger']; finger=case['finger']; selected=repro.SELECTED[finger]
        folder=BASE/'runs'/name
        original=(repro.HERE if case['condition']=='baseline20' else cap.HERE)/'runs'/finger
        assert job['finger']==name and job['argv']==case['argv'] and job['returncode']==0
        child=remember(BASE/('01_'+name+'_launcher.json')); assert child['returncode']==0
        report=remember(folder/'report.json'); render=remember(folder/'render_report.json'); scene=remember(folder/'gpu_scene_final.json')
        assert report['completed'] and report['closed'] and report['scene_valid'] and report['failure'] is None and report['close_failure'] is None
        assert not report['changed_inputs'] and not report['unpinned_project_sources']
        assert render['completed'] and render['failure'] is None and not render['cleanup_errors'] and not render['changed_inputs']
        assert all(render[k] for k in ('source_pins_unchanged','trace_finite','physics_clock_contiguous','observer_aliases_restored','visual_colors_restored','original_run_completed','scene_closed','no_NN_checkpoint'))
        assert render['policy_performance'] is False and render['encoding_exit_codes']==dict(hand=0,fullbody=0)
        before=remember(folder/'inputs_before.json'); after=remember(folder/'inputs_after.json'); pins(before)
        assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources']
        assert set(seal['input_pins'])<=set(before) and str(BASE/'preparation_seal.json') in before
        assert scene['closed'] and scene['num_envs']==scene['environment_count']==4 and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['diagnostic_guitar_mode']=='fixed'
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==4
        assert scene['physics_steps']==report['resources']['physics_steps']==4*report['resources']['control_ticks']
        assert scene['hand_collision']==remember(original/'gpu_scene_final.json')['hand_collision']
        config=remember(folder/'settings.json'); assert config==remember(original/'settings.json')==parent.settings(finger,4)
        assert report['resources']['control_ticks']<=config['song']['short_learning']['view']['duration_ticks'] and not list(folder.glob('*.pt'))
        contract=remember(folder/'training_contract.json'); assert contract==remember(original/'training_contract.json')
        native_checks[name]=dict(environment_count=4,collision_pairs=90,source_constructor_PD105_checked=True,
            baseline_PD105_scope='Pinned gpu/scene.py constructor lines232-246 checks full native property array on every env; baseline raw PD105 array not separately saved')
        if case['condition']=='cap025':
            readback=remember(folder/'native_effort_readback.json'); assert readback==remember(original/'native_effort_readback.json')
            assert readback['expected_readback_exact'] and readback['cap_Nm']==.25 and len(readback['native_indices'])==16
            for field,values in readback['actual_native_PD105'].items():
                old=readback['original_profile_native_PD105'][field]; assert len(values)==len(old)==105
                changed=[i for i,(a,b) in enumerate(zip(values,old)) if a!=b]
                assert changed==readback['changed_native_field_indices'][field]==(readback['native_indices'] if field=='effort' else [])
            native_checks[name]['saved_PD105_exact_to_original']=True
        evaluation=remember(folder/'evaluation.json'); old_eval=remember(original/'evaluation.json')
        assert evaluation['assigned_quotas']==[1]*4 and parent.complete(evaluation['episodes'],4) and evaluation['policy_performance'] is False
        acceptance=repro.acceptance(evaluation['episodes']); assert acceptance==evaluation['acceptance']
        statistics=remember(folder/'statistics.json'); old_stats=remember(original/'statistics.json')
        compared[name]=dict(acceptance=acceptance,original_acceptance=old_eval['acceptance'],acceptance_exact=acceptance==old_eval['acceptance'],
            entire_evaluation_exact=evaluation==old_eval,all_statistics_exact=statistics==old_stats,raw={})
        for e,old_e,s in zip(evaluation['episodes'],old_eval['episodes'],statistics['rows']):
            assert e['env_id']==old_e['env_id']==s['env_id'] and e['grid_index']==selected and e['attempt_id']==s['attempt_id']
            assert e['selected_target_count']==1 and e['target_id']==config['song']['short_learning']['teacher']['source_target_id']
            rows.append(dict(case=name,env_id=e['env_id'],attempt_id=e['attempt_id'],achieved=e['achieved'],original_achieved=old_e['achieved'],
                clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],missing=e['missing_fraction'],reason=e['reason'],
                physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],
                note_exact=e['note']==old_e['note'],all_episode_exact=e==old_e,audible_body123_mean_N=json.dumps(s['phases']['audible']['mean'][12:15])))
        meta=remember(folder/'capture_metadata.json'); trace_meta=remember(folder/'trace_metadata.json')
        assert meta['environment']==0 and meta['first_attempt'] and meta['no_NN_checkpoint'] and meta['policy_performance'] is False
        assert meta['joint_names']==trace_meta['joint_names'] and len(meta['joint_names'])==105 and meta['wrist_control']==config['song']['short_learning']['wrist_control']
        assert meta['width']==1280 and meta['height']==720 and meta['video_fps']==30 and meta['capture_hz']==60 and meta['physics_hz']==240
        paths=dict(observer=folder/'poses_env0000.npz',same_collector=folder/trace_meta['file'],original=original/trace_meta['file'])
        traces={}
        for key,path in paths.items(): hashes[str(path)]=parent.sha(path); traces[key]=np.load(path)
        movie=traces['observer']; count=len(movie['time_s'])
        assert count==meta['control_endpoints']==evaluation['episodes'][0]['steps']==(221 if finger=='index' else 218)
        assert np.array_equal(movie['control_tick'],np.arange(1,count+1)) and np.array_equal(movie['physics_step'],4*np.arange(1,count+1))
        times=np.arange(2,count+1,2)/60.; assert np.array_equal(times,meta['frame_times_s']) and len(times)==meta['frames']==count//2
        clocks[name]=dict(control_endpoints=count,physics_endpoints_last=int(movie['physics_step'][-1]),frames=len(times),
            first_frame_local_s=float(times[0]),last_frame_local_s=float(times[-1]),unfilmed_odd_last_endpoint=bool(count%2))
        for kind in ('same_collector','original'):
            source=traces[kind]; fields={}
            for key in movie.files:
                other='net_body_force_n' if key=='contact_force' else key
                if other in source.files: fields[key]=difference(movie[key],source[other])
            if 'selected_native_qd' in source.files:
                names=remember(original/'trace_metadata.json')['selected_native_qd_names']
                ids=[meta['joint_names'].index(n) for n in names]; fields['qd_selected_native']=difference(movie['qd'][:,ids],source['selected_native_qd'])
            compared[name]['raw'][kind]=dict(fields=fields,observer_only_fields=[k for k in movie.files if k not in source.files and k!='contact_force'],
                scope='Full qd baseline original unrecorded; selected qd comparisons only where saved; mixed body_state units preserved, max/rms descriptive only')
            for key in ('q','target','body_state','contact_force','candidate','wrong','scripted_action','executed_action','surface_distance_m','surface_height_m'):
                assert fields[key]['value_exact'],(name,kind,key)
            assert fields['time_s']['max_abs']<=1e-12  # Same rational clock expressed /60 versus /240; not a music tolerance.
        for camera in ('hand','fullbody'):
            entry=next(r for r in media['records'] if r.get('video')==str(folder/(camera+'.mp4')))
            hashes[entry['video']]=parent.sha(entry['video']); assert render['video_files'][camera]['bytes']==Path(entry['video']).stat().st_size
    assert len(rows)==16 and sum(c['control_endpoints'] for c in clocks.values())==878 and 'isaacgym' not in sys.modules
    for path in (Path(__file__).resolve(),HERE/'PLAN.md',HERE/'extract_frames.py'):
        hashes[str(path)]=parent.sha(path)
    out.mkdir()
    parent.write(out/'comparison.json',dict(cases=compared,clocks=clocks,native_checks=native_checks,scope='16 musical first attempts; only four env0 movies; existing115/114, not new112 or learned policy'))
    parent.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,native_executed=False,input_sha256=hashes,verified_input_sha256=verified,
        preparation_pins=836,actual_input_paths_verified=len(verified),scenes_closed=4,MP4=8,representative_PNG=32,contact_sheets=2,env0_endpoints=878,first_attempts=16,
        overall_launcher_wall_s=launcher['wall_s'],visual_QA=visual,
        time_expression_comparison_bound_s=1e-12,time_scope='same rational clock numerical representation; no fretting/physical tolerance change',
        codec_scope='ffprobe8MP4 h264/1280x720/30fps; index110/middle109 frames; all8encoders exit0'))
    with (out/'attempts.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    text=['# 기존115/114 scripted 비교 영상 QA','',
        '**네 실제 scene·8MP4의 촬영/종료/원자료 대조를 통과했다. 음악 결과는 기준20Nm 검지3/4·중지4/4, 진단0.25Nm 검지0/4·중지4/4다. 전체16첫시도 원장은 원실행과 같으며 영상은 그중 각env0 첫시도만이다.**','',
        '| 조건 | 전체4 달성 | mean clean/wrong | env0 달성 | 손 영상 | 전신 영상 |','|---|---:|---:|---|---|---|']
    for case in cases:
        name=case['condition']+'_'+case['finger']; a=compared[name]['acceptance']; e=next(r for r in rows if r['case']==name and r['env_id']==0)
        text.append('| %s | %d/4 | %.2f%%/%.2f%% | %s | [hand](%s) | [fullbody](%s) |'%(name,a['achieved'],100*a['mean_clean'],100*a['mean_wrong'],e['achieved'],BASE/'runs'/name/'hand.mp4',BASE/'runs'/name/'fullbody.mp4'))
    text+=['','손 색상은 엄지 red, 검지 blue, 중지 green, 약지 orange, 소지 purple이다. 시각 식별용이며 접촉쌍·힘 색상이 아니다.','', '각4환경의첫시도·실패를포함하며네개촬영의16시도를878개env0끝점과구분한다. 이전원장과전체음악상태/입력·통계대조는comparison.json과attempts.csv에남겼다. 모든물리/손목실패는0이다. 기존index115/middle114고정목표이며새grid112성공영상·정책학습/체크포인트·4seed·4환경전체영상으로부르지않는다.','',
        '![손 비교](%s)'%(HERE/'qa_frames/contactsheet_hand.png'),'','![전신 비교](%s)'%(HERE/'qa_frames/contactsheet_fullbody.png'),'',
        '행은기준index/middle→capindex/middle,열은첫프레임/이동1초/음중3.066667초/마지막이다. view_image로32대표프레임contactsheet와4조건음중손원본·전신원본을직접확인했다. upright·전신머리/양발여백·손마디굴곡방향은보인다. 넥이손일부를가리므로모든관절/실제접촉·압력·자연성을시각인증하지않는다.','',
        '1280×720·30fps·h264각index110/middle109프레임이다. frame n은실제60Hz endpoint2(n+1)에대응하며첫화면local1/30초로t0프레임은없다. index의마지막221번째끝점은raw에만있고110번째프레임은endpoint220이다. middle마지막109번째프레임은endpoint218이다.','',
        '관찰raw와같은촬영collector/원실행의q·target·body_state·force·candidate/wrong·scripted/executed action·nearest거리/높이는네조건모두값이정확히같았다. 시간표현(/60 vs /240)의차이를별도기록하고음악/물리허용오차로사용하지않았다. 나머지원시필드의dtype/exact/maxabs/RMS와미저장필드는comparison.json에전부보존한다. 기존CPUnearest argmin/높이재생한계를해결했다는뜻은아니다.','',
        '836준비핀과모든실제전후입력·설정/계약·네scene닫힘·8encoder종료0·physics240/control60시계를확인했다. cap의저장native105전필드readback은원cap자료와exact이며16effort외차이0/충돌90쌍이다. 기준native105는pin된원constructor의각환경전필드readback검사근거이며별도baseline배열을새로저장한것처럼다루지않는다.','',
        '이자료는기존scripted/fixed기타비교다. cap일괄채택·인간힘한계·현별압력/접촉쌍·음향·자연스러운자세·장기학습·해제/전환/전곡성과를인증하지않는다. 새GPU/native실행없이기존native영상만디코딩했다.']
    (out/'README.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True,pins=len(verified),MP4=8,frames=32,first_attempts=16,env0_endpoints=878)))

if __name__=='__main__': main()
