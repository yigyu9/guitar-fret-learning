"""CPU QA of completed own-schema prefix videos; immutable native inputs."""
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
    assert value['completed'] and value['returncode']==0
    assert [c['update'] for c in value['children']]==[250,300] and all(c['returncode']==0 for c in value['children'])


def main():
    launcher=json.loads((BASE/'01_launcher.json').read_text());completed(launcher)
    s=importlib.util.spec_from_file_location('prefix_video_actual_QA',BASE/'render.py')
    video=importlib.util.module_from_spec(s);sys.modules[s.name]=video;s.loader.exec_module(video)
    grid=video.grid;sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';video.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):
        p=Path(p).resolve();inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    selection,paths=video.evidence();assert selection['video_updates']==[250,300]
    seal=read(BASE/'preparation_seal.json');assert seal['independent_review']=='passed_no_findings' and len(seal['input_pins'])==1815
    pins(seal['input_pins']);review=read(BASE/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
    for p in paths:track(p)
    for p in (BASE/'01_launcher.json',Path(__file__),HERE/'PLAN.md'):track(p)
    commands=read(BASE/'cpu_inputs/commands.json')
    import numpy as np
    from PIL import Image,ImageDraw
    helper=video.producer.module('prefix_video_guard_QA',video.producer.HERE/'precheck_analysis/analyze.py');track(helper.__file__)
    cases={};media=[];images={};out.mkdir();env=os.environ.copy();env.pop('LD_LIBRARY_PATH',None)
    frames=[0,90,129,176]  # opening, A audible, B7 audible, final; same fixed frames for both models.
    for update,argv in zip(selection['video_updates'],commands['render']):
        child=read(BASE/('01_update_%06d_launcher.json'%update));assert child==launcher['children'][selection['video_updates'].index(update)] and child['argv']==argv
        folder=BASE/'runs'/('update_%06d'%update);prior=video.producer.output('evaluate',update=update)
        report=read(folder/'report.json');meta=read(folder/'capture_metadata.json');config=read(folder/'settings.json')
        assert all(report[k] for k in ('completed','native_pixels','policy_unchanged','checkpoint_unchanged','checkpoint_pins_validated','scene_closed','lifecycle_verified','wrapper_aliases_restored','cap_aliases_restored','loader_restored','prefix_task_verified','trace_finite','clock_contiguous'))
        assert report['failure'] is None and not report['cleanup_errors'] and report['encoding_exit_codes']=={'hand':0,'fullbody':0}
        assert report['training_updates']==0 and report['checkpoint_training_updates']==update and report['NN_constructors']==1 and report['fresh'] is False
        assert report['reference_N_injected'] is False and report['evaluator_fingerprint_callback_used'] is False and report['first_episode_only'] and report['recorded_environment']==0
        assert meta['selected_target_count']==report['selected_target_count']==3 and meta['source_indices']==[4,7,8] and meta['policy_schema']=='diagnostic.index_prefix_policy.v1'
        assert meta['frames']==report['frames']==177 and meta['video_fps']==30 and meta['capture_hz']==60 and meta['source_physics_hz']==240 and meta['actual_num_envs']==128
        assert meta['frame_mapping']=='frame n maps to control endpoint2*(n+1); no t0; odd final endpoint has no frame'
        np.testing.assert_allclose(meta['frame_times_s'],np.arange(1,178)/30,rtol=0,atol=1e-14)
        scene=report['gpu_scene'];assert scene['closed'] and scene['environment_count']==128 and scene['physics_steps']==1416 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert config==read(prior/'settings.json') and read(folder/'training_contract.json')==read(prior/'training_contract.json')
        effort=read(folder/'scene/native_effort_readback.json');assert effort==read(prior/'native_effort_readback.json') and effort['explicit_DOF105_readback_environments']==128 and effort['controller_caps_exact']
        before=read(folder/'inputs_before.json');pins(before);after=read(folder/'inputs_after.json')
        assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources'] and not report['changed_inputs'] and not report['unpinned_project_sources']
        checkpoint=track(video.producer.checkpoint(update));assert grid.sha(checkpoint)==report['checkpoint_sha256']==meta['checkpoint_sha256']
        evaluation=read(prior/'evaluation.json');assert grid.complete(evaluation['episodes'],128)
        e0=next(r for r in evaluation['episodes'] if r['env_id']==0);episode=read(folder/'episode_summary.json');raw_episode=read(folder/'episode_env0000.json')
        assert episode==meta['episode_summary']==report['episode_summary'] and episode['steps']==354 and len(episode['reward_components'])==9
        episode_diff={k:dict(video=episode.get(k),evaluation=e0.get(k)) for k in sorted(set(episode)|set(e0)) if episode.get(k)!=e0.get(k)}
        raw=dict(np.load(track(folder/'poses_env0000.npz')));old=dict(np.load(track(prior/'trace_env0_episode0.npz')))
        assert raw['q'].shape==(354,105) and all(np.isfinite(a).all() for a in raw.values()) and np.array_equal(raw['physics_step'],4*np.arange(1,355))
        assert np.array_equal(raw['control_tick'],np.arange(1,355)) and np.array_equal(raw['time_s'],np.arange(1,355)/60)
        pairs={k:k for k in old if k in raw};pairs['contact_force']='net_body_force_n';pairs['action']='executed_action'
        diff={}
        for k,j in pairs.items():
            a,b=raw[k],old[j];assert a.shape==b.shape
            diff[k]=dict(evaluation_field=j,shape=list(a.shape),exact=np.array_equal(a,b),max_abs=float(abs(a.astype(float)-b.astype(float)).max()))
        side=dict(np.load(track(folder/'current_goal_DIP60.npz')));previous=dict(np.load(track(prior/'current_goal_DIP60.npz')));assert set(side)==set(previous)
        side_diff={k:dict(exact=np.array_equal(side[k],previous[k]),max_abs=float(abs(side[k].astype(float)-previous[k].astype(float)).max())) for k in sorted(side)}
        scalar=helper.guard_audit(side,evaluation['episodes'],config['song']['short_learning']['view'])
        assert np.array_equal(raw['guard_current_goal'],side['current_goal'][:,0]) and np.array_equal(raw['target'][:,meta['joint_names'].index('LH:index3')],side['final_target_rad'][:,0])
        cases[str(update)]=dict(episode_env0_exact=episode==e0,episode_differences=episode_diff,reward9_video=episode['reward_components'],reward9_evaluation=e0['reward_components'],
            reward9_sum_residual=episode['reward']-sum(episode['reward_components'].values()),raw_fields=diff,video_only_fields=sorted(set(raw)-set(pairs)),
            scalar_fields=side_diff,scalar_audit=scalar,env0_raw_steps=354,raw_episode_source=str(folder/'episode_env0000.json'),
            strict_original_native_load_evidence='Successful frozen render source trainer.load(original checkpoint), completed report and model/checkpoint/updates checks; evaluator callback unused')
        for camera in ('hand','fullbody'):
            path=track(folder/(camera+'.mp4'))
            probe=json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(path)],capture_output=True,text=True,check=True,env=env).stdout)
            stream=probe['streams'][0];assert stream['codec_name']=='h264' and stream['width']==1280 and stream['height']==720 and stream['avg_frame_rate']=='30/1' and int(stream['nb_read_frames'])==177
            subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,check=True,env=env)
            for frame in frames:
                image=out/('%06d_%s_%03d.png'%(update,camera,frame))
                subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(path),'-vf','select=eq(n\\,%d)'%frame,'-vsync','0','-frames:v','1',str(image)],capture_output=True,check=True,env=env)
                images[update,camera,frame]=image
            media.append(dict(update=update,camera=camera,path=str(path),ffprobe=probe,decoded_frames=177,representative_frames=frames))
    def sheet(name,rows):
        canvas=Image.new('RGB',(1600,500),'white');draw=ImageDraw.Draw(canvas)
        for row,(label,update,camera) in enumerate(rows):
            for col,f in enumerate(frames):
                im=Image.open(images[update,camera,f]);im.thumbnail((400,225));canvas.paste(im,(400*col,250*row+25));draw.text((400*col+5,250*row+5),'%s frame%d'%(label,f),fill='black')
        canvas.save(out/(name+'.png'))
    for c in ('hand','fullbody'):sheet('comparison_'+c,[('best250',250,c),('latest300',300,c)])
    for u in (250,300):sheet('views_%06d'%u,[('hand%d'%u,u,'hand'),('fullbody%d'%u,u,'fullbody')])
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,video_updates=[250,300],cases=cases,
        media=media,decoded_frames=708,representative_PNGs=16,contact_sheets=4,evaluator_fingerprint_callback_used=False,
        scope='Actual env0 first episodes only; 60Hz endpoint resultant forces, not240Hz maxima/pair pressure. Tick reward9 not saved; episode components compared. Visual/independent review separate.'))
    links=['# 3음 prefix 정책 실제 영상 QA','','| 모델 | 손 | 전신 |','|---|---|---|']
    for u in (250,300):links.append('| %s | [손](%s) | [전신](%s) |'%('best250' if u==250 else 'latest300',BASE/('runs/update_%06d/hand.mp4'%u),BASE/('runs/update_%06d/fullbody.mp4'%u)))
    links+=['','두 모델 모두 원 all3/release0인 진단용 실패 모델이다. 새3음 schema/PrefixPolicy fresh=False, 원본 checkpoint strict load·128cap.25/90쌍·staged wrist/current-goal guard이며 N 주입은 없다. 영상은 env0 첫시도만이고 전체128 영상이 아니다.',
        '각 H264/1280×720/30fps/177프레임, 네 영상 총708프레임을 전부 CPU decode하고 16대표PNG/4sheet를 만들었다. frame n은 endpoint2(n+1), t0 frame은 없다. 0/90/129/176은 각각 시작/A음중/B7음중/마지막이다.',
        '원 고정평가 대비 env0 raw 모든 공통필드 exact/최대차와9항 episode보상·전128 sidecar는 verification.json에 그대로 기록했다. qd·tick별 보상은 원 평가에 저장되지 않아 동일성 검산을 주장하지 않는다. evaluator fingerprint callback은 사용하지 않았다. 몸체합력은 쌍별압력·motor torque·240Hz 최대가 아니다.',
        '색: 엄지 빨강, 검지 파랑, 중지 초록, 약지 주황, 소지 보라. 직접 시각검사와 넥/다른손가락 가림 한계는 VISUAL_QA.md, 통합독립검수는 review.json에 별도 기록한다. 자연스러움·해제·학습 성공·자유기타/J33 성공을 인증하지 않는다.','',
        '![손 비교](comparison_hand.png)','','![전신 비교](comparison_fullbody.png)']
    (out/'README.md').write_text('\n'.join(links)+'\n');print(json.dumps(dict(completed=True,decoded_frames=708,PNG=16,sheets=4,cases={u:dict(episode_exact=c['episode_env0_exact'],raw_nonexact={k:v['max_abs'] for k,v in c['raw_fields'].items() if not v['exact']}) for u,c in cases.items()})))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--self-check',action='store_true');a=p.parse_args()
    if a.self_check:
        good=dict(completed=True,returncode=0,children=[dict(update=u,returncode=0) for u in (250,300)]);completed(good)
        for bad in (dict(good,completed=False),dict(good,returncode=1),dict(good,children=good['children'][::-1]),dict(good,children=[])):
            try:completed(bad)
            except AssertionError:pass
            else:raise AssertionError('Incomplete video admitted')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print('CPU stdlib completion guard PASS; raw unread')
    elif a.root_completed:main()
    else:print('Wait for actual root completion; raw unread/native0')
