"""Summarize saved feedback trials and verify preservation without simulation."""
import json
from pathlib import Path
from .palm_side_feedback import PHASE,SOURCE_PHASE,np
from .build_fixed_lower_asset import read,sha


def main():
    summaries=[];checks={}
    base=read(PHASE/'short/off/states.json')
    for mode in ('off','bias','tracking'):
        folder=PHASE/'short'/mode;report=read(folder/'report.json');tasks=np.array(read(folder/'tasks.json'))
        contact_rows=[(r['physics_step'],c) for r in read(folder/'contacts.json') for c in r['contacts']
            if {c['body0_name'],c['body1_name']}=={'human/LH:palm','guitar/guitar'}]
        states=read(folder/'states.json');controls=read(folder/'controls.json')
        updates=[c for c in controls if c['updated_before_step']]
        summaries.append({'mode':mode,'max_point_error_mm':float(np.linalg.norm(tasks[:,:3],axis=1).max()*1000),
            'end_point_error_mm':float(np.linalg.norm(tasks[-1,:3])*1000),
            'max_orientation_error_deg':float(np.linalg.norm(tasks[:,3:],axis=1).max()/.08*180/np.pi),
            'max_guitar_position_error_mm':report['max_position_error_m']*1000,
            'max_guitar_rotation_error_deg':report['max_rotation_error_deg'],
            'palm_contact_steps':sorted({step for step,c in contact_rows}),
            'positive_palm_contact_rows':sum(c['lambda']>0 for step,c in contact_rows),
            'guitar_all_body_states_exact_to_off':all(s['guitar_body_states']==b['guitar_body_states'] for s,b in zip(states,base)),
            'control_updates':len(updates),'blocked_counts_at_updates':[sum(c.get('integral_blocked',[])) for c in updates]})
        checks[mode+'_contracts']=all(report['checks'].values())
    native=read(PHASE/'native_tracking/report.json')
    checks['camera_contracts']=all(native['checks'].values())
    checks['camera_images_sha']=all(sha(p)==v['sha256'] for p,v in native['images'].items())
    checks['no_positive_palm_contact']=all(s['positive_palm_contact_rows']==0 for s in summaries)
    checks['guitar_all_body_states_exact']=all(s['guitar_all_body_states_exact_to_off'] for s in summaries)
    checks['pure_controller_checks']=all(read(PHASE/'controller_checks.json')['checks'].values())
    for kind in ('fk','response'):checks[kind+'_calibration_contracts']=all(read(PHASE/kind/'calibration.json')['checks'].values())
    old_inventory=read(SOURCE_PHASE/'artifact_inventory.json')
    checks['prior_phase_228_sha_preserved']=all(sha(p)==v['sha256'] for p,v in old_inventory.items())
    references=SOURCE_PHASE/'preservation_reference'
    checks['protected_original_87_stat']=all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v
        for p,v in read(references/'protected_original_stat.json').items())
    checks['aug19_49_sha']=all(sha(p)==v for p,v in read(references/'aug19_sha256.json').items())
    counts={'native_initializations':sum(read(PHASE/k/'calibration.json')['native_initializations'] for k in ('fk','response'))+4,
        'physics_steps':sum(read(PHASE/k/'calibration.json')['physics_steps'] for k in ('fk','response'))+sum(read(PHASE/'short'/m/'report.json')['physics_steps'] for m in ('off','bias','tracking'))+native['physics_steps']}
    checks['counts_32_init_110_steps']=counts=={'native_initializations':32,'physics_steps':110}
    output={'checks':checks,'summary':summaries,'counts':counts,'scope':'no support/stability success; after-the-fact evidence checks do not repair omitted production hashes',
        'producer_sha256':sha(__file__),'verification_native_initializations':0,'verification_physics_steps':0}
    (PHASE/'analysis.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps(output,indent=2))
    if not all(checks.values()):raise AssertionError(checks)


if __name__=='__main__':main()
