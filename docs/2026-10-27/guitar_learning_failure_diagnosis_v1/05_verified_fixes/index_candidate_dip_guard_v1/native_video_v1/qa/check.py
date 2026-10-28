"""CPU-only completed native guard video QA; never render or modify inputs."""
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
    assert value['completed'] and value['returncode']==0 and len(value['children'])==1
    assert value['children'][0]['condition']=='guard' and value['children'][0]['returncode']==0


def main():
    launcher_path=BASE/'01_launcher.json';launcher=json.loads(launcher_path.read_text());completed(launcher)
    spec=importlib.util.spec_from_file_location('guard_native_video_QA',BASE/'render.py')
    video=importlib.util.module_from_spec(spec);sys.modules[spec.name]=video;spec.loader.exec_module(video)
    grid=video.grid;sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';video.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):p=Path(p).resolve();inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    seal,paths=video.gate();assert len(seal['input_pins'])==1515;pins(seal['input_pins'])
    for p in paths:track(p)
    for p in (launcher_path,Path(__file__),HERE/'PLAN.md'):track(p)
    child=read(BASE/'01_guard_launcher.json');assert child==launcher['children'][0] and child['argv']==read(BASE/'cpu_inputs/command.json')
    import numpy as np
    from PIL import Image,ImageDraw
    guard=video.guard;folder=BASE/'runs/guard';evalfolder=guard.HERE/'runs'/guard.MODES[1]
    report=read(folder/'report.json');meta=read(folder/'capture_metadata.json');diag=read(folder/'diagnostic_report.json');own=read(folder/'guard_video_report.json')
    assert report['completed'] and report['policy_unchanged'] and report['checkpoint_unchanged'] and report['checkpoint_pins_validated']
    assert report['scene_closed'] and report['lifecycle_verified'] and report['native_pixels'] and report['recorded_environment']==0 and report['first_episode_only']
    assert report['training_updates']==0 and not report['cleanup_errors'] and report['encoding_exit_codes']=={'hand':0,'fullbody':0}
    assert meta['checkpoint_training_updates']==300 and meta['environment']==0 and meta['video_fps']==30 and meta['capture_hz']==60 and meta['source_physics_hz']==240
    assert meta['frames']==report['frames']==110 and meta['frame_mapping']=='frame n maps to control endpoint2*(n+1); no t0 frame; odd final endpoint has no frame'
    assert all(diag[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and diag['failure'] is None and not diag['cleanup_errors']
    assert own['completed'] and own['failure'] is None and not own['cleanup_errors'] and all(own['checks'].values()) and own['completed_first_attempts']==128
    override=read(folder/'execution_override.json');assert override['enabled'] and override['mode']==guard.MODES[1] and override['fresh'] is False and override['evaluator_fingerprint_callback_used'] is False
    scene=report['gpu_scene'];assert scene['environment_count']==128 and scene['closed'] and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
    assert diag['physics_steps']==scene['physics_steps']==884
    assert read(folder/'training_contract.json')==read(evalfolder/'training_contract.json') and read(folder/'settings.json')==read(evalfolder/'settings.json')
    assert read(folder/'scene/native_effort_readback.json')==read(evalfolder/'native_effort_readback.json')
    before=read(folder/'inputs_before.json');pins(before)
    for name in ('inputs_after.json','diagnostic_inputs_after.json'):
        after=read(folder/name);assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources']
    checkpoint=track(video.B.checkpoint(300));assert grid.sha(checkpoint)==report['checkpoint_sha256']==meta['checkpoint_sha256']
    episode=read(folder/'episode_summary.json');evaluation=read(evalfolder/'evaluation.json');e0=next(e for e in evaluation['episodes'] if e['env_id']==0)
    episode_differences=[dict(field=k,video=episode.get(k),evaluation=e0.get(k)) for k in sorted(set(episode)|set(e0)) if episode.get(k)!=e0.get(k)]
    raw=dict(np.load(track(folder/'poses_env0000.npz')));old=dict(np.load(track(evalfolder/'trace_env0_episode0.npz')))
    assert len(raw['q'])==221 and all(np.isfinite(v).all() for v in raw.values()) and np.array_equal(raw['physics_step'],4*np.arange(1,222))
    pairs={k:k for k in ('q','target','body_state','candidate','wrong','surface_distance_m','surface_height_m','wrist_pose_error_world','wrist_requested_delta_rad','wrist_requested_arm_rad','wrist_goal_G_m','wrist_goal_G_xyzw','source_time_s')}
    pairs.update(requested_action='policy_action',executed_action='executed_action',checkpoint_policy_action='policy_action',contact_force='net_body_force_n')
    differences={}
    for k,v in pairs.items():
        a,b=raw[k],old[v];assert a.shape==b.shape
        differences[k]=dict(original_field=v,shape=list(a.shape),exact=np.array_equal(a,b),max_abs=float(abs(a.astype(float)-b.astype(float)).max()))
    side=dict(np.load(track(folder/'dip_control60.npz')));prior=dict(np.load(track(evalfolder/'dip_control60.npz')))
    side_diff={}
    for k in sorted(set(side)|set(prior)):
        assert k in side and k in prior and side[k].shape==prior[k].shape
        side_diff[k]=dict(exact=np.array_equal(side[k],prior[k]),max_abs=float(abs(side[k].astype(float)-prior[k].astype(float)).max()))
    helper=video.B.module('guard_video_scalar_audit',guard.HERE/'analysis/analyze.py');track(helper.__file__)
    scalar_audit=helper.sidecar_audit(side,evaluation['episodes'],True)
    assert np.array_equal(raw['target'][:,meta['joint_names'].index('LH:index3')],side['final_target_rad'][:,0])
    assert np.allclose(np.asarray(meta['frame_times_s']),np.arange(1,111)/30,rtol=0,atol=1e-14)
    # Decode existing media only. The old B300 videos/PNGs are provenance-labelled reuse.
    out.mkdir();env=os.environ.copy();env.pop('LD_LIBRARY_PATH',None)
    view=read(folder/'settings.json')['song']['short_learning']['view'];middle=(view['local_onset_s']+view['local_end_s'])/2
    audible=int(np.argmin(abs(np.asarray(meta['frame_times_s'])-middle)));frames=sorted({0,36,audible,109});assert len(frames)==4
    videos=[];new_images={}
    for camera in ('hand','fullbody'):
        path=track(folder/(camera+'.mp4'))
        result=json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(path)],capture_output=True,text=True,check=True,env=env).stdout)
        s=result['streams'][0];assert s['codec_name']=='h264' and s['width']==1280 and s['height']==720 and s['avg_frame_rate']=='30/1' and int(s['nb_read_frames'])==110
        subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,check=True,env=env)
        for f in frames:
            png=out/('guard_%s_%03d.png'%(camera,f))
            subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(path),'-vf','select=eq(n\\,%d)'%f,'-vsync','0','-frames:v','1',str(png)],capture_output=True,check=True,env=env)
            new_images[camera,f]=png
        videos.append(dict(camera=camera,source=str(path),ffprobe=result,extracted_frames=frames))
        sheet=Image.new('RGB',(1600,500),'white');draw=ImageDraw.Draw(sheet)
        for row,label in enumerate(('original B300 (reused)','DIP guard (new)')):
            for col,f in enumerate(frames):
                path=track(video.OLD_QA/('000300_%s_%03d.png'%(camera,f))) if row==0 else new_images[camera,f]
                im=Image.open(path);im.thumbnail((400,225));sheet.paste(im,(col*400,row*250+25));draw.text((col*400+5,row*250+5),'%s frame %d'%(label,f),fill='black')
        sheet.save(out/('contactsheet_'+camera+'.png'))
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        new_videos=videos,decoded_frames=220,extracted_PNGs=8,scalar_audit=scalar_audit,scalar_vs_guard_evaluation=side_diff,env0_vs_guard_evaluation=differences,
        episode_env0_exact_guard_evaluation=episode==e0,episode_env0_differences=episode_differences,evaluator_fingerprint_callback_used=False,renderer_model_checkpoint_updates300_native_closed=True,
        reused_original_video_sources=[str(guard.BPATH/'native_video_000300'/(c+'.mp4')) for c in ('hand','fullbody')],
        visual_scope='Direct view_image/independent review still required; actual native env0first in128 scene, not all128video/naturalness/pressure/release certification'))
    lines=['# 검지 DIP guard 실제 영상','','| 조건 | 손 | 전신 |','|---|---|---|',
        '| 기존 B300 (재사용) | [손](%s) | [전신](%s) |'%(guard.BPATH/'native_video_000300/hand.mp4',guard.BPATH/'native_video_000300/fullbody.mp4'),
        '| DIP guard (신규) | [손](%s) | [전신](%s) |'%(folder/'hand.mp4',folder/'fullbody.mp4'),'',
        '두 새 MP4는 원 native renderer의 env0 첫시도다. 동일 B300 strict/fresh=False·128cap.25/90쌍/guard 실행이며 checkpoint/모델/updates300/입력/scene·encoder 종료를 확인했다. 평가용 fingerprint callback은 호출되지 않았고 원 renderer 자체의 strict 검증을 사용했다.',
        '신규 H264/1280×720/30fps/110프레임씩 총220프레임 전체디코딩, 8대표PNG를 추출했다. frame n은 control endpoint2(n+1)이고 t0와 홀수 마지막endpoint221에는 frame이 없다. 위 비교sheet의 첫행은 기존 B300 PNG를 출처와 SHA를 확인해 재사용했고 기존 영상을 다시 렌더하지 않았다.',
        'env0 원 guard 평가와 q/target/body/gate/action/wrist/몸체합력의 exact 여부와 최대차, 전128 scalar sidecar 및 first-attempt 검산은 verification.json에 보존했다. 음악성과의 전체분모는 기존 독립검수된256 평가원장을 따르고 새 영상 자체는 env0 요약이다.',
        '몸체합력은 쌍별 압력·motor torque·240Hz 최대하중이 아니다. 영상의 큰 굽힘 감소를 자연스러움/해제 성공·새 학습성과·기본제어 채택으로 확대하지 않는다. 직접 시각검사와 독립검수 결과는 VISUAL_QA.md/review에 별도로 기록한다.','',
        '![손 비교](contactsheet_hand.png)','','![전신 비교](contactsheet_fullbody.png)']
    (out/'README.md').write_text('\n'.join(lines)+'\n');print(json.dumps(dict(completed=True,new_videos=2,decoded_frames=220,PNG=8,audible_frame=audible)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:
        good=dict(completed=True,returncode=0,children=[dict(condition='guard',returncode=0)]);completed(good)
        for bad in (dict(good,completed=False),dict(good,children=[]),dict(good,returncode=1)):
            try:completed(bad)
            except AssertionError:pass
            else:raise AssertionError('Incomplete video admitted')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print('stdlib completion guard PASS; actual raw unread')
    elif a.root_completed:main()
    else:print('Prepared only; wait for root actual video exit. No native/raw read.')
