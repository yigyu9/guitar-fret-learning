"""Record finite independent static trials sequentially, preserving failures."""
import argparse,os,subprocess,sys
from pathlib import Path
from .initial_pose_noise_v1 import read,save,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--selected',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);d=read(a.selected);records=[]
    for e in d['selected']:
        label=e['label'];target=a.out/label;log=a.out/(label+'.log');timed_out=False
        with log.open('x') as stream:
            process=subprocess.Popen([sys.executable,'-u','-m','stability_adapter_2.run_upper_arm_static_v1','--config',e['config_path'],'--out',str(target)],env=os.environ.copy(),stdout=stream,stderr=subprocess.STDOUT)
            print('starting',label,process.pid,flush=True)
            try:code=process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                timed_out=True;process.terminate()
                try:code=process.wait(timeout=15)
                except subprocess.TimeoutExpired:process.kill();code=process.wait(timeout=5)
        record={'label':label,'returncode':code,'timed_out':timed_out,'config_path':e['config_path'],'config_sha256':sha(e['config_path']),'output':str(target),'log':str(log)};records.append(record);save(a.out/(label+'_exit.json'),record)
        print('finished',label,code,flush=True)
    save(a.out/'batch_report.json',{'all_completed':all(r['returncode']==0 for r in records),'records':records,'music_policy_checkpoint_calls':0,'selected_sha256':sha(a.selected)})
if __name__=='__main__':main()
