"""CPU-only QA of one predeclared goal initialization native replay."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent


def completed(value):
    assert value['completed'] is True and value['returncode']==0
    assert value['argv'][-1]=='--execute' and value['wall_s']>0


def main():
    completed(json.loads((BASE/'01_launcher.json').read_text()))
    spec=importlib.util.spec_from_file_location('goal_video_QA_source',BASE/'render.py')
    video=importlib.util.module_from_spec(spec);sys.modules[spec.name]=video;spec.loader.exec_module(video)
    grid=video.grid;sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';video.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):
        p=Path(p).resolve();inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():
            verified[p]=grid.sha(p);assert verified[p]==h,p
    paths=video.evidence();seal=read(BASE/'preparation_seal.json')
    assert seal['independent_review']=='passed_no_findings' and len(seal['input_pins'])==2109
    pins(seal['input_pins']);review=read(BASE/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
    for p in paths|{Path(__file__),HERE/'PLAN.md',BASE/'01_launcher.json'}:track(p)
    commands=read(BASE/'cpu_inputs/commands.json');assert commands['render']==[read(BASE/'01_launcher.json')['argv']]
    import numpy as np
    from PIL import Image,ImageDraw
    helper=video.parent.module('warmstart_QA_guard_helper',video.parent.HERE/'precheck_analysis/analyze.py');track(helper.__file__)
    folder=video.OUT;prior=video.recovery.output('evaluate')
    report=read(folder/'report.json');meta=read(folder/'capture_metadata.json');audit=read(folder/'goal_video_report.json');config=read(folder/'settings.json')
    assert all(report[k] for k in ('completed','native_pixels','policy_unchanged','checkpoint_unchanged','checkpoint_pins_validated','scene_closed','lifecycle_verified','wrapper_aliases_restored','cap_aliases_restored','loader_restored','prefix_task_verified','trace_finite','clock_contiguous'))
    assert report['failure'] is None and not report['cleanup_errors'] and report['encoding_exit_codes']=={'hand':0,'fullbody':0}
    assert audit['completed'] and audit['failure'] is None and all(audit['checks'].values()) and audit['reference_calls']==0
    for value in (report,meta,audit):
        assert value['checkpoint_sha256']==grid.sha(track(video.CHECKPOINT))==video.SHA
        assert value['PPO_updates']==0 and value['supervised_steps']==1000
        assert value['evaluator_fingerprint_callback_used'] is False
    for value in (report,meta):
        assert value['schema']==video.VIDEO_SCHEMA and value['actual_initialization']==video.source.descriptor()
        assert value['checkpoint_metadata_schema']==video.source.SCHEMA and value['policy_output_adapter']==video.source.support().ADAPTER
        assert value['training_updates']==value['checkpoint_training_updates']==0 and value['fresh'] is False and value['reference_N_injected'] is False
    assert report['NN_constructors']==1 and report['first_episode_only'] and report['recorded_environment']==0
    assert meta['selected_target_count']==report['selected_target_count']==3 and meta['source_indices']==[4,7,8] and meta['policy_schema']=='diagnostic.index_prefix_goal_policy.v1'
    assert meta['frames']==report['frames']==177 and meta['video_fps']==30 and meta['capture_hz']==60 and meta['source_physics_hz']==240 and meta['actual_num_envs']==128
    assert meta['frame_mapping']=='frame n maps to control endpoint2*(n+1); no t0; odd final endpoint has no frame'
    np.testing.assert_allclose(meta['frame_times_s'],np.arange(1,178)/30,rtol=0,atol=1e-14)
    scene=report['gpu_scene'];assert scene['closed'] and scene['environment_count']==128 and scene['physics_steps']==1416 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
    assert config==read(prior/'settings.json') and read(folder/'training_contract.json')==read(prior/'training_contract.json')
    effort=read(folder/'scene/native_effort_readback.json');assert effort==read(prior/'native_effort_readback.json') and effort['explicit_DOF105_readback_environments']==128 and effort['controller_caps_exact']
    before=read(folder/'inputs_before.json');pins(before);after=read(folder/'inputs_after.json')
    assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources'] and not report['changed_inputs'] and not report['unpinned_project_sources']
    evaluation=read(prior/'evaluation.json');assert grid.complete(evaluation['episodes'],128)
    e0=next(r for r in evaluation['episodes'] if r['env_id']==0);episode=read(folder/'episode_summary.json');track(folder/'episode_env0000.json')
    assert episode==meta['episode_summary']==report['episode_summary'] and episode['steps']==354 and len(episode['reward_components'])==9
    episode_diff={k:dict(video=episode.get(k),evaluation=e0.get(k)) for k in sorted(set(episode)|set(e0)) if episode.get(k)!=e0.get(k)}
    raw=dict(np.load(track(folder/'poses_env0000.npz')));old=dict(np.load(track(prior/'trace_env0_episode0.npz')))
    assert raw['q'].shape==(354,105) and all(np.isfinite(a).all() for a in raw.values())
    assert np.array_equal(raw['physics_step'],4*np.arange(1,355)) and np.array_equal(raw['control_tick'],np.arange(1,355)) and np.array_equal(raw['time_s'],np.arange(1,355)/60)
    def compare(a,b):
        result=dict(shape_video=list(a.shape),shape_evaluation=list(b.shape),exact=np.array_equal(a,b))
        result['max_abs']=float(abs(a.astype(float)-b.astype(float)).max()) if a.shape==b.shape else None
        return result
    pairs={k:k for k in old if k in raw};pairs['contact_force']='net_body_force_n';pairs['action']='executed_action'
    diff={k:dict(compare(raw[k],old[j]),evaluation_field=j) for k,j in sorted(pairs.items())}
    side=dict(np.load(track(folder/'current_goal_DIP60.npz')));previous=dict(np.load(track(prior/'current_goal_DIP60.npz')));assert set(side)==set(previous)
    side_diff={k:compare(side[k],previous[k]) for k in sorted(side)}
    scalar=helper.guard_audit(side,evaluation['episodes'],config['song']['short_learning']['view'])
    assert np.array_equal(raw['guard_current_goal'],side['current_goal'][:,0]) and np.array_equal(raw['target'][:,meta['joint_names'].index('LH:index3')],side['final_target_rad'][:,0])
    typed_diff={}
    for name in ('observations4.npz','goal_codec_env0.npz'):
        now=dict(np.load(track(folder/name),allow_pickle=False));was=dict(np.load(track(prior/name),allow_pickle=False));assert set(now)==set(was)
        typed_diff[name]={k:compare(now[k],was[k]) for k in sorted(now)}
    assert audit['conversion_calls']==354 and audit['reference_calls']==0 and audit['evaluator_fingerprint_callback_used'] is False
    out.mkdir();media=[];images={};env=os.environ.copy();env.pop('LD_LIBRARY_PATH',None);frames=[0,90,129,176]
    for camera in ('hand','fullbody'):
        path=track(folder/(camera+'.mp4'))
        probe=json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(path)],capture_output=True,text=True,check=True,env=env).stdout)
        stream=probe['streams'][0];assert stream['codec_name']=='h264' and stream['width']==1280 and stream['height']==720 and stream['avg_frame_rate']=='30/1' and int(stream['nb_read_frames'])==177
        subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,check=True,env=env)
        for frame in frames:
            image=out/('goal_%s_%03d.png'%(camera,frame))
            subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(path),'-vf','select=eq(n\\,%d)'%frame,'-vsync','0','-frames:v','1',str(image)],capture_output=True,check=True,env=env);images['goal',camera,frame]=image
        media.append(dict(camera=camera,path=str(path),ffprobe=probe,decoded_frames=177,representative_frames=frames))
    oldqa=video.parent.HERE/'native_video_v1/qa/results_v1';oldreview=read(oldqa/'review.json');assert oldreview['verdict']=='PASS' and not oldreview['findings'];pins(oldreview['reviewed_sha256'])
    for camera in ('hand','fullbody'):
        canvas=Image.new('RGB',(1600,750),'white');draw=ImageDraw.Draw(canvas)
        for row,label in enumerate(('old250','old300','goal')):
            for col,frame in enumerate(frames):
                image=images[label,camera,frame] if label=='goal' else track(oldqa/('%06d_%s_%03d.png'%(int(label[3:]),camera,frame)))
                im=Image.open(image);im.thumbnail((400,225));canvas.paste(im,(400*col,250*row+25));draw.text((400*col+5,250*row+5),'%s%s frame%d'%(label,' reused' if label!='goal' else ' NEW',frame),fill='black')
        canvas.save(out/('comparison_'+camera+'.png'))
    verification=dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,media=media,decoded_frames=354,representative_PNGs=8,contact_sheets=2,
        checkpoint_sha256=video.SHA,PPO_updates=0,supervised_steps=1000,episode_env0_exact=episode==e0,episode_differences=episode_diff,reward9_video=episode['reward_components'],reward9_evaluation=e0['reward_components'],reward9_sum_residual=episode['reward']-sum(episode['reward_components'].values()),
        raw_fields=diff,video_only_fields=sorted(set(raw)-set(pairs)),scalar_fields=side_diff,scalar_audit=scalar,typed_goal_fields=typed_diff,conversion_calls=audit['conversion_calls'],original_128_episodes=len(evaluation['episodes']),
        evaluator_fingerprint_callback_used=False,strict_original_native_load_evidence='Frozen original renderer trainer.load(original checkpoint), completed report/model unchanged/checkpoint updates0/scene checks; CPU QA does not rerun CUDA restoration.',
        scope='New env0 first attempt only, not all128 video. Common endpoint raw and all128 scalar compared; missing qd/tick reward9 in original not claimed. Forces are60Hz resultants, not240Hz maxima/pair pressure. Old250/300 PNGs reused without rerender.')
    grid.write(out/'verification.json',verification)
    text=['# Goal 초기화 모델 실제 영상 QA','','[손 영상](%s) · [전신 영상](%s)'%(folder/'hand.mp4',folder/'fullbody.mp4'),'',
        '사전지정 env0 첫시도 1회이며 성공 환경을 고르지 않았다. 원128평가는 A126/B7·B8각128/all3 126, A release73/128: musicTrue/releaseFalse/stage_readyFalse다. 영상env0의 실제 음악·해제 결과는 verification.json의 원장 비교에 보존한다.',
        '원70e40d 모델·1000 supervised step/PPO0/실제 GoalPolicy와 두 layered contract를 native 원본 full strict load했다. 고정기타/F4/finite staged wrist/current-goal DIP guard/128cap.25/90쌍, 첫tick NN·fresh=False·reference/N0·goal→physical변환1회다. RL-only·자유기타J33·자연스러움/압력의 증거가 아니다.',
        '두 H264/1280×720/30fps/177frame 전체354frame CPU decode, 대표8PNG/비교2sheet. frame n=control endpoint2(n+1), t0없음. 고정0/90/129/176=시작/A음중/B7음중/마지막. old250/300 행은 기존 PNG를 재사용했고 재촬영하지 않았다.',
        '원128평가 env0원장9항·공통raw·전128 scalar와 typedgoal 차이는 verification.json에 그대로 보존했다. physical action과 normalized goal/decoded goal을 구분한다. qd/tick별9항은 원trace에 없어 동일성을 주장하지 않는다. evaluator fingerprint callback은 renderer에서 쓰지 않았다.',
        '색: 엄지 빨강/검지 파랑/중지 초록/약지 주황/소지 보라. 직접 시각검사와 가림 한계는 VISUAL_QA.md, 독립검수는 review.json에 기록한다. 원fit exit1/누락보고서2개와 별도회복수용 이력은 유지했다.','',
        '영상 env0는 A/B7/B8 모두 달성, clean1/0.9892873976946475/1·wrong0·fail0이지만 A releaseFalse/release_s0이다. 원128평가 동일 env0 원장9항 전체 exact다.',
        '354끝점 공통raw 차이는 합력 최대3.814697265625e-6N와 시간8.881784197001252e-16s이며 나머지 공통필드는 exact다. 전128 guard21필드와 precontrol4환경 typedgoal/요청·관측 및 env0typedgoal은 exact, rawgoal→physical변환은354회·NN reference0이다.',
        '![손 비교](comparison_hand.png)','','![전신 비교](comparison_fullbody.png)']
    (out/'README.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True,decoded_frames=354,episode_exact=episode==e0,raw_nonexact={k:v['max_abs'] for k,v in diff.items() if not v['exact']},scalar_nonexact=[k for k,v in side_diff.items() if not v['exact']])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--self-check',action='store_true');a=p.parse_args()
    if a.self_check:
        good=dict(completed=True,returncode=0,argv=['render.py','--execute'],wall_s=1);completed(good)
        for key,value in (('completed',False),('returncode',1),('argv',[]),('wall_s',0)):
            try:completed(dict(good,**{key:value}))
            except (AssertionError,IndexError):pass
            else:raise AssertionError('Incomplete launcher admitted')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print('stdlib completion guard PASS; raw unread')
    elif a.root_completed:main()
    else:print('Root completion required; raw unread/native0')
