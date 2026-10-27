"""Correct diagnostic clock in new configs and select positive-gap candidates."""
import argparse
from pathlib import Path
from .initial_pose_noise_v1 import read,save,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--search',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=read(a.search);a.out.mkdir(parents=True,exist_ok=False)
    inputs={str(a.search):sha(a.search)};selected=[]
    labels=['reference']
    for lean in (0.,3.,5.):
        eligible=[r for r in d['rows'] if r['accepted_for_native'] and r['support_requested'] and r['requested_lean_deg']==lean and 0<=r['support_top_plane_signed_gap_m']<=.002]
        if eligible:labels.append(min(eligible,key=lambda r:r['support_top_plane_signed_gap_m'])['label'])
    for label in labels:
        old=a.search.parent/label/'config.json';cfg=read(old);inputs[str(old)]=sha(old);inputs[cfg['initial_candidate']]=sha(cfg['initial_candidate'])
        cfg['prep_seconds']=2;cfg['diagnostic_seconds']=5;path=a.out/(label+'.json');save(path,cfg)
        row=next(r for r in d['rows'] if r['label']==label);selected.append({'label':label,'config_path':str(path),'actual_predicted_gap_m':row['support_top_plane_signed_gap_m'],'requested_lean_deg':row['requested_lean_deg'],'source_row':row})
    save(a.out/'selected.json',{'input_sha256':inputs,'selected':selected,'selection':'source_clear, smallest nonnegative predicted top-plane gap within2mm for each lean; not proof of native contact','clock':'prep2 diagnostic5; constant q_ref target all5seconds, no music','supersedes_clock_only':True})
    if any(sha(path)!=h for path,h in inputs.items()):raise AssertionError('source changed')
    print({'selected':labels},flush=True)
if __name__=='__main__':main()
