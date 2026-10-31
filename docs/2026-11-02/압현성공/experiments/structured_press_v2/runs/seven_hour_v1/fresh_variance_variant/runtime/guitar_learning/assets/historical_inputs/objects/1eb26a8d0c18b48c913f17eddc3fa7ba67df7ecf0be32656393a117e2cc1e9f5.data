"""Static native Gym scenes with coordinate-correct explanatory range overlays."""
import argparse
import itertools
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as R
from PIL import Image, ImageDraw, ImageFont

from .validate_team_pose_envelope import BODY_CENTER_G, ROOT, RESULTS, read, save, sha
from .strap_trial_recording import project

FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
CASES = ('current_control', 'reported_reference', 'reported_center')
LABELS = ('현재 수평 배치', '팀원 보고 기준 재구성', '팀원 중앙 후보 재구성')
BITS = np.array(list(itertools.product((0, 1), repeat=3)))
EDGES = [(i,j) for i in range(8) for j in range(i+1,8) if np.sum(BITS[i]!=BITS[j])==1]


def corners(low, high): return np.asarray(low)+BITS*(np.asarray(high)-low)


def rotation_membership(case, rotation):
    if case != 'reported_center':
        angles = [67.5,90.,157.5] if case == 'current_control' else [90.,68.,180.]
        error = float((rotation*R.from_euler('xyz',angles,degrees=True).inv()).magnitude())
        assert error < 1e-5
        return {'inside': True, 'witness_xyz_deg': angles, 'rotation_error_rad': error}
    angles = rotation.as_euler('xyz',degrees=True)
    alternatives = [angles,angles+[180.,180.-2*angles[1],180.]]
    inside=False
    for v in alternatives:
        for shifts in itertools.product((-360.,0.,360.),repeat=3):
            a=v+shifts
            inside |= bool(np.all(a >= [45,50,135]) and np.all(a <= [90,100,180]))
    assert not inside and abs(np.cos(np.radians(angles[1]))) > .1
    return {'inside': False, 'two_equivalent_xyz_deg': [v.tolist() for v in alternatives], 'non_singular': True}


def annotate(raw, destination, boxes, body_center, origin, neck, view, proj, depth, title, inside, elevation):
    im=Image.open(raw).convert('RGB');w,h=im.size;draw=ImageDraw.Draw(im)
    stats={'visible_segments':0,'hidden_segments':0}
    def line(a,b,color,width):
        pixels,_,_=project(np.array([a,b]),view,proj,w,h)
        count=min(4096,max(2,int(np.linalg.norm(pixels[1]-pixels[0])*2)+1))
        points=a+(b-a)*np.linspace(0,1,count)[:,None]
        px,z,valid=project(points,view,proj,w,h)
        for i in range(count-1):
            if not (valid[i] and valid[i+1]):continue
            xy=px[i:i+2].astype(int);visible=bool(np.all(z[i:i+2]>=depth[xy[:,1],xy[:,0]]-.002))
            if visible:draw.line([tuple(px[i]),tuple(px[i+1])],fill=color,width=width);stats['visible_segments']+=1
            elif i//12%2==0:draw.line([tuple(px[i]),tuple(px[i+1])],fill=tuple(int(c*.55) for c in color),width=2);stats['hidden_segments']+=1
    for box,color in zip(boxes,((75,190,255),(255,210,45))):
        for i,j in EDGES:line(box[i],box[j],color,4)
    line(origin,body_center,(190,190,190),2)
    line(origin,origin+neck*.20,(75,255,130),5)
    for point,color,label in ((body_center,(255,100,200),'바디 중심'),(origin,(230,230,230),'기타 원점')):
        px,_,valid=project(np.array([point]),view,proj,w,h)
        if valid[0]:
            x,y=px[0];draw.ellipse((x-6,y-6,x+6,y+6),fill=color,outline='black',width=1)
            draw.text((x+10,y+7),label,font=ImageFont.truetype(str(FONT),20),fill=color,stroke_width=2,stroke_fill='black')
    canvas=Image.new('RGB',(w,h+155),'#131a24');canvas.paste(im,(0,0));d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype(str(FONT),22)
    d.text((16,h+8),f'{title} | 넥 고도 {elevation:.1f}° | 사용자 회전범위 {"안" if inside else "밖"}',font=font,fill='white')
    d.text((16,h+42),'파랑: 사용자 위치범위 → 이 회전에서의 바디 중심 범위',font=font,fill=(75,190,255))
    d.text((16,h+74),'노랑: 팀원 바디 중심 후보  |  분홍: 실제 중심  |  초록: 실제 넥 방향',font=font,fill=(255,210,45))
    d.text((16,h+110),'t=0 · 물리 OFF · 가려진 선은 점선 · 범위/점/화살표는 설명 표시이며 접촉 형상 아님',font=ImageFont.truetype(str(FONT),19),fill='#d0d5df')
    canvas.save(destination);return stats


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    from .underneck_pose_trial_v5 import UnderneckEnvironment
    from .underneck_initial_search import BASE
    from .build_fixed_lower_asset import MANIFEST, REFERENCE
    from .run_joint_hold import native_state
    from .native_contacts import plain
    from .environment import gymapi
    from .trial_settings import source_hashes
    reference=RESULTS/'team_pose_envelope_validation_v1/native'/args.case
    attempt=read(reference/'attempt.json');candidate=attempt['candidate']
    paths=list((ROOT/'stability_adapter_2').glob('*.py'))+[BASE,MANIFEST,REFERENCE/'report.json',REFERENCE/'states.json',FONT,
        reference/'attempt.json',reference/'initial_values.json',
        ROOT/'stability_adapter_2/ENVELOPE_NATIVE_COMPARISON_PLAN.md',ROOT/'stability_adapter_2/run_envelope_native.sh']
    hashes=source_hashes();hashes.update({str(p.resolve()):sha(p) for p in paths})
    save(out/'attempt.json',{'input_sha256':hashes,'case':args.case,'requested_physics_steps':0,'renderer':'Isaac Gym native camera + projected range guides'})
    env=None
    try:
        env=UnderneckEnvironment(candidate,static=True);initial=native_state(env)
        pose=initial['guitar_body_states'][0]['pose'];gp=np.array([pose['p'][k] for k in 'xyz']);gr=R.from_quat([pose['r'][k] for k in 'xyzw'])
        pel=initial['human_body_states'][env.human_bodies.index('Pelvis')]['pose'];pp=np.array([pel['p'][k] for k in 'xyz']);pr=R.from_quat([pel['r'][k] for k in 'xyzw'])
        basis=pr.apply([[-1,0,0],[0,-1,0],[0,0,1]])
        chest=initial['human_body_states'][env.human_bodies.index('Chest')]['pose']['p']['z']
        root_box=corners([-.5,-.15,.65],[-.15,.15,chest])
        body_offset=gr.apply(BODY_CENTER_G);user_body_box=root_box+body_offset
        team_box=pp+corners([.17,.245,.08],[.23,.345,.10]) @ basis
        center=gp+body_offset;membership=rotation_membership(args.case,gr)
        expected=read(reference/'initial_values.json')['actual_initial_state']
        checks={'native_human_dofs_exact':initial['human_dof_states']==expected['human_dof_states'],
            'native_body_poses_exact':all(a['pose']==b['pose'] for a,b in zip(initial['human_body_states'],expected['human_body_states'])),
            'native_guitar_pose_exact':initial['guitar_body_states'][0]['pose']==expected['guitar_body_states'][0]['pose'],
            'box_conversion_inverse':bool(np.allclose(user_body_box-body_offset,root_box,rtol=0,atol=1e-15)),
            'team_box_inverse':bool(np.allclose((team_box-pp) @ basis.T,corners([.17,.245,.08],[.23,.345,.10]),rtol=0,atol=1e-15))}
        save(out/'geometry.json',{'initial_state':initial,'case':args.case,'body_center_local_m':BODY_CENTER_G.tolist(),
            'user_root_box_W_m':root_box.tolist(),'user_body_box_W_m_fixed_rotation':user_body_box.tolist(),
            'team_body_box_W_m':team_box.tolist(),'actual_body_center_W_m':center.tolist(),'actual_guitar_origin_W_m':gp.tolist(),
            'neck_direction_W':gr.apply([0,1,0]).tolist(),'rotation_membership':membership,
            'native_human_dof_properties':plain(env.gym.get_actor_dof_properties(env.env,env.human)),
            'scope':'Two position boxes in world body-center coordinates; blue depends on this fixed rotation; not full rotation/safe-volume certification'})
        if not all(checks.values()):raise AssertionError(checks)
        views={}
        for name,position in [('front',(.25,1.8,1.0)),('side',(1.5,.03,1.0))]:
            props=gymapi.CameraProperties();props.width,props.height=1280,720
            camera=env.gym.create_camera_sensor(env.env,props)
            if camera<0:raise RuntimeError('camera creation failed')
            env.gym.set_camera_location(camera,env.env,gymapi.Vec3(*position),gymapi.Vec3(0,0,.74))
            env.gym.step_graphics(env.sim);env.gym.render_all_camera_sensors(env.sim)
            raw=out/(name+'_raw.png');env.gym.write_camera_image_to_file(env.sim,env.env,camera,gymapi.IMAGE_COLOR,str(raw))
            view=np.asarray(env.gym.get_camera_view_matrix(env.sim,env.env,camera));proj=np.asarray(env.gym.get_camera_proj_matrix(env.sim,env.env,camera))
            depth=np.asarray(env.gym.get_camera_image(env.sim,env.env,camera,gymapi.IMAGE_DEPTH)).reshape(720,1280);np.save(out/(name+'_depth.npy'),depth)
            elevation=float(np.degrees(np.arcsin(np.clip(gr.apply([0,1,0])[2],-1,1))))
            stats=annotate(raw,out/(name+'.png'),[user_body_box,team_box],center,gp,gr.apply([0,1,0]),view,proj,depth,LABELS[CASES.index(args.case)],membership['inside'],elevation)
            views[name]={'view_matrix':view.tolist(),'projection_matrix':proj.tolist(),'camera_position_W_m':list(position),'target_W_m':[0,0,.74],'overlay_stats':stats,'raw_sha256':sha(raw),'output_sha256':sha(out/(name+'.png'))}
        checks.update(rendering_preserves_native_state=native_state(env)==initial,zero_physics_steps=env.steps==0,
            no_forbidden_force_or_write=not env.forbidden_calls,inputs_unchanged=all(sha(p)==h for p,h in hashes.items()))
        save(out/'report.json',{'checks':checks,'native_initializations':1,'physics_steps':env.steps,'learning_updates':0,'strap_enabled':False,'case':args.case,'cameras':views,'input_sha256':hashes})
        if not all(checks.values()):raise AssertionError(checks)
        print(args.case,'PASS; native t0; two raw and two annotated PNGs',flush=True)
    finally:
        if env is not None:env.close()


if __name__=='__main__':main()
