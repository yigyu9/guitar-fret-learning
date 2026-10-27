"""Reuse the frozen wrist trial with a complete fresh-native source self screen."""
import xml.etree.ElementTree as ET
from pathlib import Path
import json

from . import near_contact_initial_audit as admission
from . import run_small_wrist_recorded_diagnostic as runner
from .run_joint_hold import native_state
from .initial_overlap import build_probe
from .palm_side_source_checks import source_checks, intersection

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/initial_collision/shape_properties.json'
original_audit=admission.audit_initial

def expanded_audit(env,search,row):
    before=native_state(env);result=original_audit(env,search,row)
    properties=env.gym.get_actor_rigid_shape_properties(env.env,env.human)
    spans=env.gym.get_actor_rigid_body_shape_indices(env.env,env.human)
    filters={name:[int(properties[k].filter) for k in range(span.start,span.start+span.count)] for name,span in zip(env.human_bodies,spans)}
    expected=json.loads(POLICY.read_text())['mask_audit']['native_filters']
    result['checks']['fresh_native_filters_equal_reference']=all(filters[n]==expected[n] for n in env.human_bodies)
    probe=build_probe(env);meshes,hg,cross=source_checks(probe)
    xml=ET.parse(ROOT/env.config['humanoid_asset']).getroot()
    parents={c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a,b):
        chain=[];current=a
        while current in parents:chain.append(current);current=parents[current]
        chain.append(current);steps=0;current=b
        while current not in chain and current in parents:steps+=1;current=parents[current]
        return steps+chain.index(current) if current in chain else 99
    humans=[s for s in probe[2] if s['actor']=='human'];overlaps=[];count=0
    for i,a in enumerate(humans):
        for b in humans[i+1:]:
            if distance(a['body'],b['body'])<=2:continue
            sameleft=all(s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow') for s in (a,b))
            allowed=all(x&y==0 for x in filters[a['body']] for y in filters[b['body']])
            if not (sameleft or allowed):continue
            count+=1;radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if radius>1e-7:overlaps.append(dict(a=a['body'],b=b['body'],common_radius_m=radius))
    result['complete_source_self_screen']=dict(pair_count=count,intersections=overlaps,native_filters=filters,scope='fresh native poses and native readback filters; source LP radius, not cooked penetration')
    result['checks'].update(complete_source_self_clear=not overlaps,repeat_source_human_guitar_clear=not hg,repeat_source_cross_hands_clear=not cross,
                            complete_audit_zero_steps_and_readonly=env.steps==0 and native_state(env)==before)
    return result

def main():
    admission.audit_initial=expanded_audit
    try:runner.main()
    finally:admission.audit_initial=original_audit

if __name__=='__main__':main()
