"""CPU-only audit of completed B native policy videos; preserve every input."""
import hashlib,json,os,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with p.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink();out.mkdir()
    inputs={Path(__file__),HERE/'PLAN.md',BASE/'03_native_video_launcher.json',BASE/'03_native_video_started.json'}
    reviewed=BASE/'analysis/results_v1/review.json';review=read(reviewed)
    assert review['verdict']=='PASS' and not review['findings']
    assert all(sha(p)==h for p,h in review['reviewed_sha256'].items())
    selection=read(reviewed.parent/'comparison.json')['selection'];updates=selection['video_updates']
    assert updates==sorted({selection['best_update'],selection['latest_update']}) and selection['latest_update']==300
    inputs.update((reviewed,reviewed.parent/'comparison.json'))
    verified={};results=[];images=[]
    launch=read(BASE/'03_native_video_launcher.json')
    assert launch['completed'] and launch['returncode']==0 and [r['update'] for r in launch['children']]==updates and all(r['returncode']==0 for r in launch['children'])
    env=os.environ.copy();env.pop('LD_LIBRARY_PATH',None)
    for update in updates:
        folder=BASE/('native_video_%06d'%update);report=read(folder/'report.json');meta=read(folder/'capture_metadata.json');diag=read(folder/'diagnostic_report.json');after=read(folder/'inputs_after.json')
        assert report['completed'] and report['native_pixels'] and report['policy_unchanged'] and report['checkpoint_unchanged'] and report['scene_closed'] and not report['cleanup_errors'] and report['recorded_environment']==0 and report['first_episode_only']
        assert report['training_updates']==0 and meta['checkpoint_training_updates']==update and report['gpu_scene']['environment_count']==128
        assert diag['completed'] and diag['closed'] and diag['scene_valid'] and diag['aliases_restored'] and diag['loader_restored'] and not diag['failure'] and not diag['cleanup_errors']
        assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        for p,h in after['input_pins'].items(): assert sha(p)==h;verified[p]=h
        for p in folder.rglob('*'):
            if p.is_file(): inputs.add(p)
        checkpoint=Path(report['checkpoint']);assert sha(checkpoint)==report['checkpoint_sha256'];inputs.add(checkpoint)
        raw=np.load(folder/'poses_env0000.npz');original_path=BASE/('evaluation_%06d'%update)/'trace_env0_episode0.npz';original=np.load(original_path);inputs.add(original_path)
        assert len(raw['q'])==221 and all(np.isfinite(raw[k]).all() for k in raw.files)
        assert np.array_equal(raw['physics_step'],4*np.arange(1,222)) and meta['frames']==110
        pairs={k:k for k in ('q','target','body_state','candidate','wrong','wrist_pose_error_world','wrist_requested_arm_rad')}
        pairs.update(requested_action='policy_action',executed_action='executed_action',contact_force='net_body_force_n')
        comparison={}
        for key,old in pairs.items():
            a,b=raw[key],original[old];assert a.shape==b.shape
            comparison[key]=dict(exact=np.array_equal(a,b),max_abs_diff=float(np.max(np.abs(a.astype(float)-b.astype(float)))))
        view=read(folder/'settings.json')['song']['short_learning']['view'];middle=(view['local_onset_s']+view['local_end_s'])/2
        audible_frame=int(np.argmin(np.abs(np.array(meta['frame_times_s'])-middle)))
        for camera in ('hand','fullbody'):
            video=folder/(camera+'.mp4')
            value=json.loads(subprocess.run(['/usr/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(video)],capture_output=True,text=True,check=True,env=env).stdout)
            stream=value['streams'][0];assert stream['codec_name']=='h264' and stream['width']==1280 and stream['height']==720 and stream['avg_frame_rate']=='30/1' and int(stream['nb_read_frames'])==110
            subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True,capture_output=True,env=env)
            frames=sorted({0,36,audible_frame,109});paths=[]
            for frame in frames:
                png=out/('%06d_%s_%03d.png'%(update,camera,frame))
                subprocess.run(['/usr/bin/ffmpeg','-v','error','-i',str(video),'-vf','select=eq(n\\,%d)'%frame,'-vsync','0','-frames:v','1',str(png)],check=True,capture_output=True,env=env)
                paths.append(png);images.append((update,camera,frame,png))
            results.append(dict(update=update,camera=camera,ffprobe=value,frames=frames,audible_frame=audible_frame,trace_comparison=comparison,episode=read(folder/'episode_summary.json')))
    for camera in ('hand','fullbody'):
        rows=[x for x in images if x[1]==camera];sheet=Image.new('RGB',(4*400,len(updates)*250),'white');draw=ImageDraw.Draw(sheet)
        for i,(u,_,f,p) in enumerate(rows):
            im=Image.open(p);im.thumbnail((400,225));x=(i%4)*400;y=(i//4)*250
            sheet.paste(im,(x,y+25));draw.text((x+5,y+5),'update %d / frame %d'%(u,f),fill='black')
        sheet.save(out/('contactsheet_'+camera+'.png'))
    write(out/'verification.json',dict(completed=True,CPU_only=True,policy_updates_during_video=0,scope='Native env0 first attempt in128env scene; not whole128 force or sound certification',input_sha256={str(p):sha(p) for p in sorted(inputs)},verified_input_sha256=verified,videos=results))
    lines=['# 검지 실제 영상 확인','','독립 검수된 B 고정평가의 사전 순위에 따라 선택한 모델과 최종300회 모델이다. 영상은 동일128장면의env0첫시도다. 전체128 성과는 비교 분석 원장을 따른다.','','| 모델 | 손 | 전신 |','|---|---|---|']
    for u in updates: lines.append('| %d | [손](%s) | [전신](%s) |'%(u,BASE/('native_video_%06d/hand.mp4'%u),BASE/('native_video_%06d/fullbody.mp4'%u)))
    lines.extend(['','선정된영상h264/1280×720/30fps/110프레임·전체디코딩을확인했다. 원renderer의모델불변/strictload/105native/90쌍/입력·장면종료검사를재확인했고프레임은control endpoint2*(n+1)에해당한다. 비교수치와원장/SHA는verification.json에있다. 몸체합력은접촉쌍압력이나240Hz최대가아니며음성인증은없다.','','![손 비교](contactsheet_hand.png)','','![전신 비교](contactsheet_fullbody.png)','','자세·구도는추출이미지를직접보고독립검수한뒤확정한다.'])
    (out/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(completed=True,videos=len(results),decoded_frames=220*len(updates),extracted_frames=len(images))))
if __name__=='__main__': main()
