"""Source audit against the scene's actual asset paths, plus finite body profile."""
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from .initial_pose_noise_v1 import read
from .upper_arm_static_geometry_v1 import ROOT

def half_width(manifest,guitar_y):
    t=( -.4+manifest['new_body_length_m']/2-guitar_y)/manifest['new_body_length_m'];profile=np.asarray(manifest['half_width_profile_t_m'])
    if not 0<=t<=1:raise ValueError('support target outside finite body length')
    return float(np.interp(t,profile[:,0],profile[:,1]))

def source_scene(state,bodies,asset):
    import xml.etree.ElementTree as ET
    cfg=read(ROOT/'stability_adapter_2/config.json');cfg['humanoid_asset']=str(ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml');cfg['guitar_asset']=str(asset)
    guitar_names=[b.get('name') for b in ET.parse(asset).getroot().findall('./worldbody//body')];names=[bodies,guitar_names]
    assert len(guitar_names)==len(state['guitar_body_states'])
    return SimpleNamespace(config=cfg,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:names[actor]),bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])

def source_audit(scene,parents):
    from .initial_overlap import build_probe
    from .palm_side_source_checks import source_checks,intersection
    probe=build_probe(scene);meshes,overlap,cross=source_checks(probe)
    def distance(a,b):
        chain=[]
        while a in parents:chain.append(a);a=parents[a]
        chain.append(a);steps=0
        while b not in chain and b in parents:steps+=1;b=parents[b]
        return steps+chain.index(b) if b in chain else 99
    human=[s for s in probe[2] if s['actor']=='human'];selfcross=[]
    changed=lambda n:n in ('Torso','Spine','Chest','Neck','Head') or n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:'))
    for i,a in enumerate(human):
        for b in human[i+1:]:
            if not(changed(a['body']) or changed(b['body'])) or distance(a['body'],b['body'])<=2:continue
            radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if radius>1e-7:selfcross.append({'a':a['body'],'b':b['body'],'common_radius_m':radius})
    return {'source_clear':not(overlap or cross or selfcross),'human_guitar_overlap':overlap,'crosshands':cross,'nonadjacent_human_overlap':selfcross,'actual_guitar_asset':str(scene.config['guitar_asset']),'scope':'source convex geometry at saved native/source poses, not cooked clearance certification'}
