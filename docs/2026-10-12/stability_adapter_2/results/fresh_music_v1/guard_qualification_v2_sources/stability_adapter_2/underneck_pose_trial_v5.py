"""Fresh native initial pose and no-strap trial; joint targets only after t=0."""
from .environment import ROOT, gymapi, np, vector, quaternion
import argparse
import copy
import json
from pathlib import Path
from scipy.spatial.transform import Rotation as R
from .capture_isaac_gym_initial import CameraEnvironment
from .interactive_guitar_pose_static import NoPhysicsGym
from .gym_trial_recording import GymTrialRecording
from .run_joint_hold import native_state
from .native_contacts import body_names, read_contacts, plain
from .underneck_initial_search import read, save, sha, BASE, FACETS, calibrated_fk, pose
from .initial_overlap import build_probe, mujoco
from .face_referenced_geometry import face_geometry
from .palm_side_source_checks import intersection
from .build_fixed_lower_asset import LOWER_BODIES
from scipy.spatial import ConvexHull
from .audit_palm_side_target import closest_polygon
from scipy.optimize import least_squares
from .bounded_arm_hold import BoundedArmHold


class NoStrapGym:
    def __init__(self, gym, owner): self.gym, self.owner = gym, owner
    def __getattr__(self, name):
        if name.startswith('apply_') and ('force' in name or 'effort' in name):
            def forbidden(*args, **kwargs):
                self.owner.forbidden_calls.append(name)
                raise RuntimeError('no external force/effort submission: '+name)
            return forbidden
        if name.startswith('set_') and ('force' in name or 'effort' in name):
            def forbidden(*args, **kwargs):
                self.owner.forbidden_calls.append(name)
                raise RuntimeError('no external effort submission: '+name)
            return forbidden
        if name.startswith('set_') and 'state' in name:
            def submit(*args, **kwargs):
                if self.owner.started:
                    self.owner.forbidden_calls.append(name)
                    raise RuntimeError('no state overwrite after integration starts')
                return getattr(self.gym, name)(*args, **kwargs)
            return submit
        return getattr(self.gym, name)


class UnderneckEnvironment(CameraEnvironment):
    def __init__(self, candidate, static=False):
        self.candidate, self.started, self.forbidden_calls = candidate, False, []
        self.follow=False;self.hold_enabled=False;self.controls=[]
        base=read(BASE);settings=copy.deepcopy(base['input_trial']['initial_settings'])
        settings['joint_angles_rad'].update({n:float(q) for n,q in zip(candidate['joint_names'],candidate['joint_angles_rad'])
            if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:'))})
        acquire=gymapi.acquire_gym
        gymapi.acquire_gym=lambda: NoStrapGym(NoPhysicsGym(acquire()) if static else acquire(),self)
        try: super().__init__(settings,[0.,0.,0.])
        finally: gymapi.acquire_gym=acquire
        try:
            props=self.gym.get_actor_dof_properties(self.env,self.human)
            props['stiffness'][self.torso_indices]*=2
            props['damping'][self.torso_indices]*=np.sqrt(2)
            if not self.gym.set_actor_dof_properties(self.env,self.human,props):raise RuntimeError('PD submission failed')
            self.target=self.initial_q.copy();self._submit_targets()
        except BaseException:
            self.close()
            raise

    def _create_scene(self):
        self.goal_position=np.array(self.candidate['position_W_m'],dtype=float)
        x,y,z,w=self.candidate['quaternion_xyzw']
        self.pose['params']['guitar_quat_wxyz_computed']=[w,x,y,z]
        super()._create_scene()
        center=self.goal_position+R.from_quat([x,y,z,w]).apply([0,.064,0])
        for view in ('hands','hands_collision'):
            self.gym.set_camera_location(self.cameras[view],self.env,gymapi.Vec3(*(center+[.05,.42,.12])),gymapi.Vec3(*center))
        props=gymapi.CameraProperties();props.width,props.height=1280,720
        camera=self.gym.create_camera_sensor(self.env,props)
        if camera<0:raise RuntimeError('rear hand camera failed')
        self.gym.set_camera_location(camera,self.env,gymapi.Vec3(*(center+[-.15,-.35,.12])),gymapi.Vec3(*center))
        self.cameras['rear_hand']=camera

    def configure_follow(self):
        state=native_state(self);gp,gr=pose(state['guitar_body_states'][0])
        wrist=state['human_body_states'][self.human_bodies.index('L_Wrist')];wp,wr=pose(wrist)
        self.relative_wrist_position=gr.inv().apply(wp-gp);self.relative_wrist_rotation=gr.inv()*wr
        self.reference_chest=pose(state['human_body_states'][self.human_bodies.index('Chest')])
        self.fk,_=calibrated_fk(self.names,self.human_bodies,state,self.initial_q)
        self.follow_indices=np.array([i for i,n in enumerate(self.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))])
        self.follow_low=np.maximum(self.lower[self.follow_indices],self.initial_q[self.follow_indices]-.3)
        self.follow_high=np.minimum(self.upper[self.follow_indices],self.initial_q[self.follow_indices]+.3)
        self.follow=True

    def update_follow(self):
        state=native_state(self);gp,gr=pose(state['guitar_body_states'][0])
        cp,cr=pose(state['human_body_states'][self.human_bodies.index('Chest')]);rp,rr=self.reference_chest
        delta=cr*rr.inv()
        safe_gp=np.clip(gp,[-.5,-.15,.66],[-.15,.15,max(.66,self.reference_chest[0][2])])
        desired_p=safe_gp+gr.apply(self.relative_wrist_position);desired_r=gr*self.relative_wrist_rotation
        actual_q=np.array([s['pos'] for s in state['human_dof_states']]);indices=self.follow_indices
        previous=self.target[indices].astype(float)
        def residual(v):
            q=actual_q.copy();q[indices]=v;p,r=self.fk(q)['L_Wrist']
            predicted_p=cp+delta.apply(p-rp);predicted_r=delta*r
            return np.r_[1000*(predicted_p-desired_p),30*(desired_r.inv()*predicted_r).as_rotvec(),.2*(v-previous)]
        fit=least_squares(residual,np.clip(previous,self.follow_low+1e-8,self.follow_high-1e-8),bounds=(self.follow_low,self.follow_high),max_nfev=12)
        proposed=np.clip(fit.x,previous-.8/60,previous+.8/60)
        proposed=np.clip(proposed,self.follow_low,self.follow_high)
        if not np.isfinite(proposed).all():raise FloatingPointError('nonfinite follow target')
        before=native_state(self)
        self.target=self.initial_q.copy();self.target[indices]=proposed.astype(np.float32);self._submit_targets()
        if native_state(self)!=before:raise AssertionError('PD command changed state')
        wp,wr=pose(state['human_body_states'][self.human_bodies.index('L_Wrist')])
        self.controls.append({'before_physics_step':self.steps+1,'time_s':self.steps/240,'observed_G_position_W_m':gp.tolist(),
            'goal_G_position_for_hand_only_W_m':safe_gp.tolist(),'desired_wrist_position_W_m':desired_p.tolist(),
            'wrist_position_error_m':float(np.linalg.norm(wp-desired_p)),'wrist_rotation_error_rad':float((desired_r.inv()*wr).magnitude()),
            'fit_success':bool(fit.success),'fit_cost':float(fit.cost),'final_arm_targets_rad':self.target[indices].astype(float).tolist(),
            'max_target_delta_from_initial_rad':float(np.max(abs(self.target[indices]-self.initial_q[indices]))),
            'max_target_step_rad':float(np.max(abs(self.target[indices]-previous))),
            'position_boundary_goal_active':bool(np.linalg.norm(gp-safe_gp)>1e-10)})

    def configure_hold(self):
        self.follow_indices=np.array([i for i,n in enumerate(self.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
        idx=self.follow_indices
        self.hold_controller=BoundedArmHold(self.initial_q[idx],self.lower[idx],self.upper[idx])
        self.hold_enabled=True

    def update_hold(self):
        before=native_state(self);actual=np.array([s['pos'] for s in before['human_dof_states']])
        idx=self.follow_indices;previous=self.target[idx].astype(float)
        proposed,record=self.hold_controller.update(actual[idx],1/60)
        self.target=self.initial_q.copy();self.target[idx]=proposed.astype(np.float32);self._submit_targets()
        if native_state(self)!=before:raise AssertionError('PD command changed state')
        record.update(before_physics_step=self.steps+1,time_s=self.steps/240,
            final_arm_targets_rad=self.target[idx].astype(float).tolist(),
            max_target_delta_from_initial_rad=float(max(abs(self.target[idx]-self.initial_q[idx]))),
            max_target_step_rad=float(max(abs(self.target[idx]-previous))))
        self.controls.append(record)

    def step_physics(self):
        if self.steps%4==0:
            if self.hold_enabled:self.update_hold()
            elif self.follow:self.update_follow()
        self.started=True;self.tension=0.
        self.gym.simulate(self.sim);self.gym.fetch_results(self.sim,True);self.steps+=1


def initial_audit(env,candidate):
    state=native_state(env);poses=candidate['predicted_human_poses']
    errors={}
    for n,s in zip(env.human_bodies,state['human_body_states']):
        p,r=pose(s);expected=poses[n]
        errors[n]={'position_m':float(np.linalg.norm(p-expected['p'])),
                   'rotation_rad':float((r*R.from_quat(expected['q']).inv()).magnitude())}
    probe=build_probe(env);model,data,shapes=probe
    meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes}
    human=[s for s in shapes if s['actor']=='human'];guitar=[s for s in shapes if s['actor']=='guitar']
    overlaps=[];self_cross=[]
    for a in human:
        for b in guitar:
            rad=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if rad>1e-7:overlaps.append({'human':a['body'],'guitar':b['body'],'common_radius_m':rad})
    _,parents=calibrated_fk(env.names,env.human_bodies,state,env.initial_q)
    def distance(a,b):
        chain=[];c=a
        while c in parents:chain.append(c);c=parents[c]
        chain.append(c);steps=0;c=b
        while c not in chain and c in parents:steps+=1;c=parents[c]
        return steps+chain.index(c) if c in chain else 99
    for i,a in enumerate(human):
        for b in human[i+1:]:
            changed=lambda n:n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:'))
            if not (changed(a['body']) or changed(b['body'])) or distance(a['body'],b['body'])<=2:continue
            rad=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if rad>1e-7:self_cross.append({'a':a['body'],'b':b['body'],'common_radius_m':rad})
    right=[]
    for a in human:
        if not a['body'].startswith('RH:') and a['body']!='R_Wrist':continue
        for b in guitar:
            av,bv=meshes[a['geom_id']].vertices,meshes[b['geom_id']].vertices
            ae,be=ConvexHull(av).equations,ConvexHull(bv).equations
            # Unit separating-plane gap is a conservative Euclidean lower bound.
            gap=max(np.min(av@be[:,:3].T+be[:,3],axis=0).max(),np.min(bv@ae[:,:3].T+ae[:,3],axis=0).max())
            right.append(float(gap))
    station=candidate['station_G_m'];ylo,yhi=station-.05,station+.05
    widths=[.027908-.01631590413943356*(y+.241803) for y in (ylo,yhi)]
    gp,gr=pose(state['guitar_body_states'][0])
    frontz=.01123002571264832
    polygons={
        'palm':[[widths[0],ylo,-.008],[widths[0],ylo,.0093],[widths[1],yhi,.0093],[widths[1],yhi,-.008]],
        'thumb':[[-widths[0],ylo,-.008],[widths[0],ylo,-.008],[widths[1],yhi,-.008],[-widths[1],yhi,-.008]],
        'front':[[-widths[0],ylo,frontz],[widths[0],ylo,frontz],[widths[1],yhi,frontz],[-widths[1],yhi,frontz]]}
    surface_gaps={}
    for digit in ('palm','thumb','index','middle','ring','pinky'):
        face='palm' if digit=='palm' else 'thumb' if digit=='thumb' else 'front'
        members=[s for s in human if s['body']=='LH:palm' if digit=='palm'] if digit=='palm' else [s for s in human if s['body'] in ['LH:'+digit+str(i) for i in (1,2,3)]]
        gaps={s['body']:closest_polygon(meshes[s['geom_id']],gp+gr.apply(polygons[face])) for s in members}
        selected=min(gaps,key=lambda n:gaps[n]['distance_m'])
        surface_gaps[digit]={'face':face,'nearest_body':selected,'minimum_distance_m':gaps[selected]['distance_m'],'member_distances':gaps}
    checks={'81_dofs_66_main_no_lower':len(env.names)==81 and len(env.main_indices)==66 and len(env.leg_indices)==0,
            'names_match':env.names==candidate['joint_names'],
            'initial_angles_match':bool(np.max(np.abs(env.initial_q-candidate['joint_angles_rad']))<2e-7),
            'FK_position_match':max(e['position_m'] for e in errors.values())<1e-5,
            'FK_rotation_match':max(e['rotation_rad'] for e in errors.values())<1e-3,
            'guitar_position_match':bool(np.linalg.norm(vector(env.bodies(env.guitar)[0]['pose']['p'])-candidate['position_W_m'])<1e-6),
            'guitar_rotation_match':float((R.from_quat(quaternion(env.bodies(env.guitar)[0]['pose']['r']))*R.from_quat(candidate['quaternion_xyzw']).inv()).magnitude())<1e-5,
            'zero_physics_steps':env.steps==0,'no_external_force_calls':not env.forbidden_calls}
    q=np.array([s['pos'] for s in state['human_dof_states']])
    palm=state['human_body_states'][env.human_bodies.index('LH:palm')]
    normal=pose(palm)[1].apply(read(FACETS)['facets']['LH:palm']['normal_local'])
    chest=state['human_body_states'][env.human_bodies.index('Chest')]['pose']['p']['z']
    checks.update(native_joint_limits=bool(((q>=env.lower)&(q<=env.upper)).all()),palm_up=bool(normal[2]>=0),
        initial_position_in_user_box=bool(-.5<=gp[0]<=-.15 and -.15<=gp[1]<=.15 and .65<=gp[2]<=chest),
        initial_neck_horizontal_and_front=bool(abs(gr.apply([0,1,0])[2])<1e-5 and np.linalg.norm(gr.apply([0,0,1])-[0,1,0])<1e-5))
    return {'checks':checks,'max_FK_position_error_m':max(e['position_m'] for e in errors.values()),
            'max_FK_rotation_error_rad':max(e['rotation_rad'] for e in errors.values()),'body_errors':errors,
            'source_intersections':overlaps,'source_nonadjacent_human_intersections':self_cross,
            'right_hand_conservative_source_gap_m':min(right),'surface_gaps':surface_gaps,'target_polygons_G_m':polygons,
            'source_clear':not overlaps and not self_cross and min(right)>.005,
            'scope':'source proxy overlap/query at actual native poses; not PhysX cooked clearance certification'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--dynamic',action='store_true');modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--follow',action='store_true');modes.add_argument('--hold',action='store_true');args=parser.parse_args()
    if (args.follow or args.hold) and not args.dynamic:parser.error('controller requires --dynamic')
    args.out=args.out.resolve();args.out.mkdir(parents=True,exist_ok=False)
    candidate=read(args.candidate);base=read(BASE)
    from .trial_settings import source_hashes
    import sys
    files=[Path(m.__file__) for n,m in sys.modules.items() if n.startswith('stability_adapter_2') and getattr(m,'__file__',None)]
    files += [Path(__file__).resolve(),args.candidate,BASE,FACETS,ROOT/'stability_adapter_2/UNDERNECK_INITIAL_BUILD.md',ROOT/'stability_adapter_2/UNDERNECK_FOLLOWER_PLAN.md',ROOT/'stability_adapter_2/UNDERNECK_ARM_HOLD_PLAN.md',ROOT/'stability_adapter_2/UNDERNECK_GUARD_HARDENING.md',ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml']
    hashes=source_hashes();hashes.update({str(p.resolve()):sha(p) for p in files})
    save(args.out/'attempt.json',{'input_sha256':hashes,'requested_physics_steps':1200 if args.dynamic else 0,'strap_force_enabled':False,'strap_visible':False})
    env=None;recorder=None;failure=None;videos={};samples=[];contact_samples=[];counts={};audit=None
    try:
        env=UnderneckEnvironment(candidate,static=not args.dynamic)
        if args.follow:env.configure_follow()
        if args.hold:env.configure_hold()
        audit=initial_audit(env,candidate);save(args.out/'initial_audit.json',audit)
        state0=native_state(env);props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        save(args.out/'initial_values.json',{'candidate_path':str(args.candidate.resolve()),'joint_names':env.names,'human_body_names':env.human_bodies,'guitar_body_names':env.guitar_bodies,
            'actual_initial_angles_rad':env.initial_q.astype(float).tolist(),'initial_PD_targets_rad':env.target.astype(float).tolist(),
            'native_initial_state':state0,'PD_properties':plain(props),'self_collision_policy':env.self_collision_policy,
            'strap_force_enabled':False,'strap_visible':False,'guitar_goal_position_W_m':env.goal_position.tolist(),'guitar_goal_quaternion_xyzw':env.goal_quaternion.tolist()})
        recorder=GymTrialRecording(env,args.out/'images');recorder.capture()
        env.gym.write_camera_image_to_file(env.sim,env.env,env.cameras['hands_collision'],gymapi.IMAGE_COLOR,str(args.out/'hands_collision.png'))
        env.gym.write_camera_image_to_file(env.sim,env.env,env.cameras['rear_hand'],gymapi.IMAGE_COLOR,str(args.out/'rear_hand.png'))
        if not all(audit['checks'].values()):raise AssertionError('fresh native pose differs: '+str(audit['checks']))
        if args.dynamic and not audit['source_clear']:raise AssertionError('initial source intersections/noncontact failure; no physics extension')
        contact_names=body_names(env.gym,env.env)
        lower=[env.human_bodies.index(n) for n in LOWER_BODIES]
        checks={'root_lower_unchanged':True,'held_other_targets':True,'target_bounds':True,'renders_readonly':True}
        gp0,gr0=pose(state0['guitar_body_states'][0])
        def sample():
            state=native_state(env);gp,gr=pose(state['guitar_body_states'][0])
            samples.append({'physics_step':env.steps,'time_s':env.steps/240,'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),
                'position_change_m':float(np.linalg.norm(gp-gp0)),'rotation_change_deg':float(np.degrees((gr*gr0.inv()).magnitude())),
                'human_angles_rad':[s['pos'] for s in state['human_dof_states']],'guitar_velocity':state['guitar_body_states'][0]['vel']})
            return state
        sample()
        for step in range(1200 if args.dynamic else 0):
            env.step_physics();contacts=read_contacts(env.gym,env.env,contact_names)
            pairs=set()
            for c in contacts:
                a,b=c['body0_name'],c['body1_name']
                if a.startswith('guitar/') or b.startswith('guitar/'):
                    pair=' | '.join(sorted((a,b)));pairs.add(pair)
            for pair in pairs:counts[pair]=counts.get(pair,0)+1
            if env.steps%8==0:
                current=sample();contact_samples.append({'physics_step':env.steps,'contacts':contacts})
                checks['root_lower_unchanged'] &= all(current['human_body_states'][i]==state0['human_body_states'][i] for i in lower+[0])
                other=np.setdiff1d(np.arange(len(env.names)),env.follow_indices) if (env.follow or env.hold_enabled) else np.arange(len(env.names))
                checks['held_other_targets'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
                checks['target_bounds'] &= bool(((env.target>=env.lower)&(env.target<=env.upper)).all() and np.max(abs(env.target-env.initial_q))<=.300001)
                recorder.capture()
            if env.steps%240==0:print('simulation seconds',env.steps/240,flush=True)
        checks['no_forbidden_force_or_state_write']=not env.forbidden_calls
        checks['PD_unchanged']=bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human)))
        checks['renders_readonly']=all(f['render_preserves_states'] for f in recorder.frames)
        if not all(checks.values()):raise AssertionError(checks)
    except BaseException as e:failure={'type':type(e).__name__,'message':str(e)};checks=locals().get('checks',{})
    finally:
        if env is not None:env.close()
        if recorder is not None and args.dynamic and len(recorder.frames)>1:
            try:videos=recorder.encode()
            except Exception as e:failure={'type':type(e).__name__,'message':str(e)}
        checks['inputs_unchanged']=all(sha(p)==h for p,h in hashes.items())
        save(args.out/'trace.json',samples);save(args.out/'contacts.json',{'sampling_interval_steps':8,'samples':contact_samples,'contact_step_counts_all_1200_steps':counts})
        save(args.out/'controls.json',env.controls if env else [])
        completed=failure is None and all(checks.values()) and env is not None and env.steps==(1200 if args.dynamic else 0)
        save(args.out/'report.json',{'completed':completed,'failure':failure,'checks':checks,'physics_steps':env.steps if env else 0,'native_initializations':int(env is not None),
            'frame_count':len(recorder.frames) if recorder else 0,'videos':videos,'strap_force_enabled':False,'strap_visible':False,'stability_success':False,
            'max_position_change_m':max((s['position_change_m'] for s in samples),default=None),'max_rotation_change_deg':max((s['rotation_change_deg'] for s in samples),default=None),
            'source_clear':audit['source_clear'] if audit else None,'follow_enabled':args.follow,'hold_enabled':args.hold,'input_sha256':hashes,'scope':'no-strap physics; optional bounded arm24 PI or current-G wrist tracking; no guitar state overwrite, no music or contact-force controller'})
    if not completed:raise RuntimeError(failure or checks)
    print(json.dumps({'completed':completed,'source_clear':audit['source_clear'],'physics_steps':env.steps}),flush=True)


if __name__=='__main__':main()
