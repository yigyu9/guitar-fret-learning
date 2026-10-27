"""Extend the preserved upper-arm query summary to right wrist/palm/fingers."""
from pathlib import Path
import hashlib,json
P=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    inputs={str(Path(__file__)):sha(__file__)};summaries=[]
    for label in ('rounded3_left_away','rounded9_left_support','rounded9_left_away','rounded12_left_away'):
        path=P/'native_v2'/label/'contacts.json';inputs[str(path)]=sha(path);frames=json.loads(path.read_text());assert len(frames)==300;observed={}
        for frame in frames:
            seen=set()
            for c in frame['contacts']:
                a,b=c['body0_name'],c['body1_name'];human=b if a.startswith('guitar/') else a if b.startswith('guitar/') else ''
                name=human.rsplit('/',1)[-1]
                if name=='R_Wrist' or name.startswith('RH:'):seen.add(name)
            for n in seen:observed.setdefault(n,[]).append(frame['physics_step']/240)
        summaries.append({'label':label,'body_queries':{n:{'sample_count':len(t),'first_time_s':min(t),'last_time_s':max(t)} for n,t in sorted(observed.items())}})
    result={'passed':all(sha(p)==h for p,h in inputs.items()),'input_sha256':inputs,'summaries':summaries,'scope':'300 native queries before60Hz control; contact occurrence only, not calibrated force or successful support; all previously saved results remain unchanged'}
    with (P/'right_hand_contact_audit_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2));assert result['passed']
if __name__=='__main__':main()
