"""Decode existing native MP4s only; no rendering or physics."""
import json
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def main():
    launcher=json.loads((BASE/'01_launcher.json').read_text()); assert launcher['completed'] and launcher['returncode']==0
    out=HERE/'qa_frames'; out.mkdir()
    records=[]; cases=json.loads((BASE/'cpu_inputs/cases.json').read_text())
    for case in cases:
        name=case['condition']+'_'+case['finger']; folder=BASE/'runs'/name
        metadata=json.loads((folder/'capture_metadata.json').read_text()); times=metadata['frame_times_s']
        frames=dict(first=0,movement=29,audible=next(i for i,t in enumerate(times) if t>=3.05),last=len(times)-1)
        for camera in ('hand','fullbody'):
            video=folder/(camera+'.mp4')
            media=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries',
                'stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(video)],text=True))
            stream=media['streams'][0]; assert stream['codec_name']=='h264' and (stream['width'],stream['height'])==(1280,720) and stream['r_frame_rate']=='30/1'
            assert int(stream['nb_read_frames'])==metadata['frames']==(110 if case['finger']=='index' else 109)
            assert abs(float(media['format']['duration'])-len(times)/30)<.002
            for phase,index in frames.items():
                path=out/(name+'_'+camera+'_'+phase+'.png')
                subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(video),'-vf','select=eq(n\\,%d)'%index,'-frames:v','1',str(path)],check=True)
                records.append(dict(case=name,camera=camera,phase=phase,frame_index=index,local_time_s=times[index],control_endpoint=2*(index+1),path=str(path)))
            records.append(dict(case=name,camera=camera,video=str(video),probe=media))
    try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    except OSError: font=ImageFont.load_default()
    for camera in ('hand','fullbody'):
        sheet=Image.new('RGB',(2560,1560),'white'); draw=ImageDraw.Draw(sheet)
        for row,case in enumerate(cases):
            name=case['condition']+'_'+case['finger']
            for col,phase in enumerate(('first','movement','audible','last')):
                record=next(r for r in records if r.get('phase')==phase and r['case']==name and r['camera']==camera)
                with Image.open(record['path']) as im: sheet.paste(im.resize((640,360)),(col*640,row*390+30))
                draw.text((col*640+5,row*390+5),'%s %s f%d t%.4f'%(name,phase,record['frame_index'],record['local_time_s']),font=font,fill='black')
        sheet.save(out/('contactsheet_'+camera+'.png'))
    (HERE/'media_precheck.json').write_text(json.dumps(dict(completed=True,native_render_executed=False,records=records,
        scope='existing MP4 decode; first frame is endpoint2/local1/30s, not t0; visual QA pending'),indent=2)+'\n')
    print(json.dumps(dict(videos=8,frames=32,contact_sheets=[str(out/('contactsheet_'+c+'.png')) for c in ('hand','fullbody')])))

if __name__=='__main__': main()
