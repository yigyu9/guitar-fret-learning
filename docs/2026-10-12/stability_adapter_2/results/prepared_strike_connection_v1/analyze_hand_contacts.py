"""Saved contact evidence counts for the policy interval, not contact forces."""
from pathlib import Path
import hashlib
import json

P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=P/'contact_analysis';out.mkdir(exist_ok=False)
    path=P/'native/data/controls.json'
    before={str(p):sha(p) for p in (Path(__file__).resolve(),path)}
    (out/'inputs_before.json').write_text(json.dumps(before,indent=2)+'\n')
    rows=[r for r in json.loads(path.read_text()) if r['actor_used']]
    current=maximum=0
    for r in rows:
        both=all(r['readiness']['conditions'][k] for k in ('left_palm_under_neck_contact','left_finger_neck_contact'))
        current=current+1 if both else 0;maximum=max(maximum,current)
    result={'policy_samples':len(rows),'handoff_right_contact_rows':rows[0]['readiness']['right_contact_rows'],
        'policy_samples_with_any_right_guitar_contact':sum(r['readiness']['right_contact_rows']>0 for r in rows),
        'right_guitar_contact_rows_total':sum(r['readiness']['right_contact_rows'] for r in rows),
        'left_palm_and_finger_joint_samples':sum(all(r['readiness']['conditions'][k] for k in ('left_palm_under_neck_contact','left_finger_neck_contact')) for r in rows),
        'longest_left_joint_contact_streak_controls':maximum,
        'note':'Right contact includes all raw lambda values; LH support evidence uses positive raw lambda in the readiness helper. Joint contact samples do not certify force or complete-interval stable support.'}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    changed=[p for p,h in before.items() if sha(Path(p))!=h]
    (out/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n')
    assert not changed

if __name__=='__main__':main()
