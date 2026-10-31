"""Stage A v3: measured Jacobian consistency faults end an episode safely.

Native imports are deferred. The process must import Isaac Gym before Torch.
"""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
POSE_CONFIG = ROOT/'stability_adapter_2/current_pose_test_v1/config.json'
GEOMETRY = ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
MASS_REFERENCE = ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/native_properties.json'
INITIAL_REFERENCE = ROOT/'docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/initial_values.json'
DEFAULT_CONFIG = {'prep_seconds': 2., 'active_seconds': 3., 'goal_radius_m': .003,
                  'support_range_rad': .035, 'fret_range_rad': .08,
                  'strike_range_rad': .08, 'finger_range_rad': .04,
                  'proximal_feedback': True}


class JacobianConsistencyError(RuntimeError):
    """No effort is submitted for the controller call that detects this fault."""
    def __init__(self,message,diagnostic):
        super().__init__(message)
        self.diagnostic = diagnostic


def finite_native_state(value):
    if isinstance(value,dict): return all(finite_native_state(v) for v in value.values())
    if isinstance(value,(list,tuple)): return all(finite_native_state(v) for v in value)
    return bool(np.isfinite(value)) if isinstance(value,(int,float,np.number)) else True


def action_groups(names):
    """Semantic scalar DOF order; suffixes are not world rotation axes."""
    support = [i for i,n in enumerate(names) if n.startswith(('Torso_', 'Spine_', 'Chest_', 'R_Thorax_', 'R_Shoulder_'))]
    fret = [i for i,n in enumerate(names) if n.startswith(('L_Thorax_', 'L_Shoulder_', 'L_Elbow_', 'L_Wrist_', 'LH:'))]
    strike = [i for i,n in enumerate(names) if n.startswith(('R_Elbow_', 'R_Wrist_'))]
    if [len(support), len(fret), len(strike)] != [15,33,6]:
        raise ValueError('required support15/fret33/strike6 grouping unavailable')
    return [np.array(g, dtype=int) for g in (support,fret,strike)]


def collect_inputs():
    """CPU-only conservative source and physical asset closure for pre-run sealing."""
    from ..environment_contract_v1 import EnvironmentContract
    contract = EnvironmentContract(POSE_CONFIG)
    geometry = json.loads(GEOMETRY.read_text())
    paths = {Path(p) for p in contract.inputs}
    paths |= set((ROOT/'stability_adapter_2').glob('*.py'))
    paths |= set(Path(__file__).parent.glob('*.py'))
    paths |= set((ROOT/'tab2body').rglob('*.py'))
    paths |= {GEOMETRY, MASS_REFERENCE, INITIAL_REFERENCE, ROOT/'stability_adapter_2/config.json'}
    paths |= {Path(p) for p in geometry['input_sha256']}
    paths |= {Path(m['path']) for m in geometry['meshes']}
    # Follow every declared mesh, including unused declarations.
    import xml.etree.ElementTree as ET
    for asset in (ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml', Path(geometry['asset'])):
        xml = ET.parse(asset).getroot()
        compiler = xml.find('compiler')
        meshdir = (asset.parent/(compiler.get('meshdir','') if compiler is not None else '')).resolve()
        paths.add(asset)
        paths |= {(meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh')}
    native_config = json.loads((ROOT/'stability_adapter_2/config.json').read_text())
    paths |= {ROOT/native_config[k] for k in ('pose_source','gain_source')}
    fixed_manifest = ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.json'
    fixed = json.loads(fixed_manifest.read_text())
    paths.add(fixed_manifest)
    paths |= {Path(p) for p in fixed['input_sha256']}
    reference = ROOT/'docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125'
    paths |= {reference/'report.json',reference/'states.json'}
    # The reused support factory's import chain hashes these documents/searches.
    paths |= {ROOT/('stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V%d.md'%v) for v in (1,2,3,5,6,7,8,10)}
    search = ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
    paths |= {search/('search_v%d/search.json'%v) for v in (2,4,5)}
    return {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def action_targets(action,reference,indices,lower,upper):
    action = np.asarray(action,dtype=float)
    if action.shape!=(54,) or not np.isfinite(action).all() or np.any(abs(action)>1):
        raise ValueError('finite bounded action54 required')
    requested = reference.copy()
    anchor = reference[indices]
    requested[indices] = anchor+np.where(action>=0,upper-anchor,anchor-lower)*action
    return requested


def _build_scene(recording, horizon, prep_seconds):
    import isaacgym  # Must precede gymtorch/Torch.
    from .. import right_block_body_effort_v5 as support
    from .. import dual_music_scene_v1 as dual
    from .. import dual_shoulder_effort_v1 as shoulder
    from .. import capture_isaac_gym_initial as cameras
    from ..self_collision_environment import SelfCollisionEnvironment
    from ..environment_contract_v1 import EnvironmentContract
    from ..environment import gymapi
    from ..deadline_graphics_v1 import graphics_wrapper
    geometry = json.loads(GEOMETRY.read_text())
    mass_reference = json.loads(MASS_REFERENCE.read_text())['applied']

    def camera_free(owner):
        candidate = owner.contract.candidate
        owner.goal_position = np.array(candidate['position_W_m'])
        x,y,z,w = candidate['quaternion_xyzw']
        owner.pose['params']['guitar_quat_wxyz_computed'] = [w,x,y,z]
        SelfCollisionEnvironment._create_scene(owner)
        owner.cameras = {}
        owner.initial_q = owner.contract.q_ref.astype(np.float32)
        props = owner.gym.get_actor_dof_properties(owner.env,owner.human)
        props['stiffness'][owner.torso_indices] *= owner.contract.config['body_kp_scale']
        props['damping'][owner.torso_indices] *= owner.contract.config['body_kd_scale']
        if not owner.gym.set_actor_dof_properties(owner.env,owner.human,props):
            raise RuntimeError('construction POSITION properties rejected')

    class MassGym:
        def __init__(self, gym, owner): self.gym,self.owner = gym,owner
        def __getattr__(self,name): return getattr(self.gym,name)
        def create_actor(self,*args,**kwargs):
            actor = self.gym.create_actor(*args,**kwargs)
            if args[3] != 'guitar': return actor
            env = args[0]
            names = list(self.gym.get_actor_rigid_body_names(env,actor))
            if names != [v['name'] for v in mass_reference]: raise RuntimeError('guitar mass body order')
            props = self.gym.get_actor_rigid_body_properties(env,actor)
            for value,target in zip(props,mass_reference):
                ratio = target['mass_kg']/value.mass
                value.mass = target['mass_kg']
                for i in 'xyz':
                    for j in 'xyz': setattr(getattr(value.inertia,i),j,float(getattr(getattr(value.inertia,i),j))*ratio)
            # Match the established OM wrapper: the older reference prescribes
            # masses only. COM comes from OM geometry; its inertia scales with
            # imported-to-requested mass rather than copying older geometry.
            requested = [{'name':name,'mass_kg':float(value.mass),
                'COM_body_m':[value.com.x,value.com.y,value.com.z],
                'inertia_COM_kg_m2':[[float(getattr(getattr(value.inertia,i),j)) for j in 'xyz'] for i in 'xyz']}
                for name,value in zip(names,props)]
            self.owner.property_submission_allowed = True
            try:
                if self.gym.set_actor_rigid_body_properties(env,actor,props,False) is False: raise RuntimeError('guitar mass rejected')
            finally: self.owner.property_submission_allowed = False
            actual = self.gym.get_actor_rigid_body_properties(env,actor)
            applied = []
            for value,target in zip(actual,requested):
                inertia = [[getattr(getattr(value.inertia,i),j) for j in 'xyz'] for i in 'xyz']
                com = [value.com.x,value.com.y,value.com.z]
                if abs(value.mass-target['mass_kg'])>1e-6 or not np.allclose(com,target['COM_body_m'],rtol=1e-6,atol=1e-7) or not np.allclose(inertia,target['inertia_COM_kg_m2'],rtol=1e-5,atol=1e-9): raise RuntimeError('guitar mass readback')
                applied.append({'name':target['name'],'mass_kg':float(value.mass),'COM_body_m':com,'inertia_COM_kg_m2':inertia})
                if value.mass<=0 or not np.isfinite(inertia).all() or np.linalg.eigvalsh(inertia).min()<=0: raise RuntimeError('invalid guitar inertia')
            self.owner.mass_properties = {'requested':requested,'applied':applied,'mass_reference':str(MASS_REFERENCE),'readback_verified':True,
                'rule':'OM imported COM unchanged; OM imported inertia linearly scaled by requested/imported mass'}
            return actor

    Parent = support.factory(recording,False)
    class Scene(Parent):
        def _create_scene(self):
            self.config['guitar_asset'] = geometry['asset']
            self.config['strap']['buttons_G_m'] = geometry['strap_buttons_G_m']
            self.property_submission_allowed = False
            self.property_setter_calls = self.property_setter_rejections = 0
            old = self.gym
            old.gym = support.ArmEffortGuard(old.gym.gym,self)
            self.gym = MassGym(old,self)
            try: support.create_effort(self)
            finally: self.gym = old

    contract = EnvironmentContract(POSE_CONFIG)
    contract.config['diagnostic_seconds'] = horizon
    contract.config['prep_seconds'] = prep_seconds
    wrapper = graphics_wrapper(cameras.GraphicsGym,recording)
    original = shoulder.create_original
    with patch.object(dual,'EnvironmentContract',lambda:contract), patch.object(cameras,'GraphicsGym',wrapper), patch.object(shoulder,'create_original',original if recording else camera_free):
        scene = Scene(horizon)
    scene.position_command_rows = []
    return scene


class ScalarEffortController:
    """One target-consuming PD+gravity command for human33; bounded support tasks."""
    def __init__(self,scene,proximal_feedback):
        from isaacgym import gymtorch
        from ..initial_pose_noise_v1 import pose
        from ..run_joint_hold import native_state
        self.scene = scene
        self.tensor = gymtorch.wrap_tensor(scene.gym.acquire_jacobian_tensor(scene.sim,'human'))
        if tuple(self.tensor.shape) != (1,len(scene.human_bodies)-1,6,81): raise RuntimeError('Jacobian ABI')
        props = scene.gym.get_actor_rigid_body_properties(scene.env,scene.human)
        self.mass = np.array([v.mass for v in props])
        self.com = np.array([[v.com.x,v.com.y,v.com.z] for v in props])
        self.indices = np.array([i for i,n in enumerate(scene.names) if n.startswith(('Torso_','Spine_','Chest_','L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_','R_Thorax_','R_Shoulder_','R_Elbow_','R_Wrist_'))])
        self.kp,self.kd = np.zeros(81),np.zeros(81)
        for i in self.indices:
            name = scene.names[i]
            self.kp[i],self.kd[i] = (150,1) if name.startswith(('Torso_','Spine_','Chest_')) else {'Thorax':(30,1),'Shoulder':(60,3),'Elbow':(60,3),'Wrist':(20,1)}[name.split('_')[1]]
        self.references = []
        initial = native_state(scene)
        gp,gr = pose(initial['guitar_body_states'][0])
        if proximal_feedback:
            candidate = scene.contract.candidate['right_block_cradle']
            for name,witness in [('R_Thorax',candidate['capsule_body']['R_Thorax']),('R_Shoulder',candidate['proximal_upper_arm30_witness'])]:
                settings = scene.contract.config['proximal_point_parameters'][name]
                body = scene.human_bodies.index(name)
                p,r = pose(initial['human_body_states'][body])
                surface = np.array(witness['guitar_surface_G_m'])
                normal = np.array(witness['capsule_axis_G_m'])-surface
                normal /= np.linalg.norm(normal)
                point = gp+gr.apply(surface+normal*witness['gap_m'])
                owned = [i for i,n in enumerate(scene.names) if n.startswith('R_Thorax_') or (name=='R_Shoulder' and n.startswith('R_Shoulder_'))]
                self.references.append((body,r.inv().apply(point-p),surface+normal*(witness['gap_m']-settings['depth_m']),settings['cap_N'],owned))
        self.last = {}

    def __call__(self):
        from ..run_joint_hold import native_state
        from ..initial_pose_noise_v1 import pose
        from ..dual_shoulder_effort_v1 import skew
        from ..strap import point_kinematics
        s = self.scene
        state = native_state(s)
        q = np.array([v['pos'] for v in state['human_dof_states']])
        qdot = np.array([v['vel'] for v in state['human_dof_states']])
        if not np.isfinite(np.r_[q,qdot]).all() or abs(qdot).max()>50: raise RuntimeError('unsafe native joint state')
        s.gym.refresh_jacobian_tensors(s.sim)
        jac = self.tensor.detach().cpu().numpy()[0].astype(float)
        if not np.isfinite(jac).all(): raise RuntimeError('nonfinite Jacobian')
        # Isaac fixed-root Jacobians are at COM. Validate this using native velocities.
        vec = lambda body,key:np.array([body['vel'][key][k] for k in 'xyz'])
        errors = {mode:0. for mode in ('COM','origin')}
        body_errors = {mode:[] for mode in errors}
        for i in range(1,len(s.human_bodies)):
            body = state['human_body_states'][i]
            _,r = pose(body)
            for mode in errors:
                j = jac[i-1,:3] if mode=='COM' else jac[i-1,:3]-skew(r.apply(self.com[i]))@jac[i-1,3:]
                error = float(np.linalg.norm(j@qdot-vec(body,'linear')))
                body_errors[mode].append({'body':s.human_bodies[i],'error_m_s':error,
                    'jacobian_qdot_W_m_s':(j@qdot).tolist(),'native_COM_velocity_W_m_s':vec(body,'linear').tolist()})
                errors[mode] = max(errors[mode],error)
        mode = min(errors,key=errors.get)
        if errors[mode]>.01:
            diagnostic = {'kind':'COM_Jacobian_velocity_consistency','physics_step':s.steps,
                'threshold_m_s':.01,'selected_mode':mode,'mode_max_errors_m_s':errors,
                'body_errors':body_errors,'native_state':state,'target81_rad':s.target.tolist(),
                'faulting_controller_effort_submitted':False}
            self.last_diagnostic = diagnostic
            raise JacobianConsistencyError('COM Jacobian native velocity mismatch',diagnostic)
        gravity = np.zeros(81)
        for i in range(1,len(s.human_bodies)):
            _,r = pose(state['human_body_states'][i])
            j = jac[i-1,:3] if mode=='COM' else jac[i-1,:3]-skew(r.apply(self.com[i]))@jac[i-1,3:]
            gravity += 9.81*self.mass[i]*j[2]
        task = np.zeros(81)
        guitar = state['guitar_body_states'][0]
        gp,gr = pose(guitar)
        for i,local,goal,cap,owned in self.references:
            body = state['human_body_states'][i]
            p,r = pose(body)
            point,velocity = point_kinematics(p,r.as_quat(),vec(body,'linear'),vec(body,'angular'),local,self.com[i])
            desired,dvelocity = point_kinematics(gp,gr.as_quat(),vec(guitar,'linear'),vec(guitar,'angular'),goal,s.com[s.guitar_bodies[0]])
            j = jac[i-1,:3]-skew(r.apply(local-(self.com[i] if mode=='COM' else 0)))@jac[i-1,3:]
            point_error = float(np.linalg.norm(j@qdot-velocity))
            if point_error>.01:
                diagnostic = {'kind':'support_point_Jacobian_velocity_consistency','physics_step':s.steps,
                    'body':s.human_bodies[i],'threshold_m_s':.01,'error_m_s':point_error,
                    'selected_mode':mode,'mode_max_errors_m_s':errors,'body_errors':body_errors,
                    'jacobian_qdot_W_m_s':(j@qdot).tolist(),'native_point_velocity_W_m_s':velocity.tolist(),
                    'native_state':state,'target81_rad':s.target.tolist(),'faulting_controller_effort_submitted':False}
                self.last_diagnostic = diagnostic
                raise JacobianConsistencyError('support point Jacobian mismatch',diagnostic)
            force = 2000*(desired-point)+30*(dvelocity-velocity)
            force *= min(1.,cap/max(float(np.linalg.norm(force)),1e-12))
            task[owned] += (j.T@force)[owned]
        request = gravity+self.kp*(s.target-q)-self.kd*qdot+task
        efforts = np.zeros(81,dtype=np.float32)
        efforts[self.indices] = np.clip(request[self.indices],-s.pd_properties['effort'][self.indices],s.pd_properties['effort'][self.indices])
        if not np.isfinite(efforts).all(): raise RuntimeError('nonfinite effort')
        self.last = {'physics_step':s.steps,'target81_rad':s.target.tolist(),'submitted_effort81_Nm':efforts.tolist(),'jacobian_mode':mode,'velocity_error_m_s':errors[mode]}
        return efforts


class FreshGuitarEnvironment:
    observation_dim = obs_dim = 558
    action_dim = 54

    def __init__(self,recording=False,seed=0,config=None):
        self.config = dict(DEFAULT_CONFIG)
        if config: self.config.update(config)
        if set(self.config)!=set(DEFAULT_CONFIG): raise ValueError('unknown environment config')
        for key,value in self.config.items():
            if key!='proximal_feedback' and (not np.isfinite(value) or value<=0): raise ValueError('invalid environment setting: '+key)
        self.recording,self.seed = bool(recording),int(seed)
        self.scene = None
        self.metadata = {}
        self.abi = {'version':'fresh_guitar_stage_a_v3','observation_dim':558,'action_dim':54,'config':dict(self.config),
            'Jacobian_fault_policy':{'threshold_m_s':.01,'terminated':True,'reward':-1.,'cost':1.,'no_faulting_effort_submission':True}}
        self.observation_slices = {}

    def reset(self,seed=None):
        self.close()
        if seed is not None: self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.horizon = self.config['prep_seconds']+self.config['active_seconds']
        self.scene = _build_scene(self.recording,self.horizon,self.config['prep_seconds'])
        s = self.scene
        from ..run_joint_hold import native_state
        from ..initial_pose_noise_v1 import pose
        from ..build_fixed_lower_asset import LOWER_BODIES
        from ..native_contacts import body_names
        self.initial = native_state(s)
        if self.initial != json.loads(INITIAL_REFERENCE.read_text())['native_initial_state']:
            raise RuntimeError('current three-face native initial state differs from reference')
        self.fixed = [s.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
        self.initial_gp,self.initial_gr = pose(self.initial['guitar_body_states'][0])
        self.groups = action_groups(s.names)
        self.indices = np.concatenate(self.groups)
        self.kept = np.setdiff1d(np.arange(81),self.indices)
        self.action_metadata = {key:{'indices':g.tolist(),'names':[s.names[i] for i in g]} for key,g in zip(('support15','fret33','strike6'),self.groups)}
        widths = np.r_[np.full(15,self.config['support_range_rad']),np.full(33,self.config['fret_range_rad']),np.full(6,self.config['strike_range_rad'])]
        widths[[k for k,i in enumerate(self.indices) if s.names[i].startswith('LH:')]] = self.config['finger_range_rad']
        self.action_lower = np.maximum(s.contract.lower[self.indices],s.contract.q_ref[self.indices]-widths)
        self.action_upper = np.minimum(s.contract.upper[self.indices],s.contract.q_ref[self.indices]+widths)
        self.abi.update(action_groups=self.action_metadata,action_lower_rad=self.action_lower.tolist(),action_upper_rad=self.action_upper.tolist(),remaining27_indices=self.kept.tolist())
        self.controller = ScalarEffortController(s,self.config['proximal_feedback'])
        s.right_effort_controller = self.controller
        self.contacts_map = body_names(s.gym,s.env)
        self.base_palms = self._palms()
        directions = self.rng.normal(size=(2,3))
        directions /= np.linalg.norm(directions,axis=1,keepdims=True)
        self.goal_delta = directions*self.config['goal_radius_m']
        self.finished = False
        self.metadata = {'stage':'A_small_hand_motion','music_success_claim':False,'pretrained_policy_loaded':False,
            'config':dict(self.config),'action_groups':self.action_metadata,'action_lower_rad':self.action_lower.tolist(),
            'action_upper_rad':self.action_upper.tolist(),'remaining27_indices':self.kept.tolist(),
            'control_hz':60,'physics_hz':240,'CPU_PhysX':True,'root_lower_fixed':True,'self_collision':True,
            'strap_enabled':False,'guitar_free':True,'controller':'human33 scalar target PD+gravity; POSITION48',
            'proximal_feedback':self.config['proximal_feedback'],'proximal_scope':'human right Thorax3/Shoulder3 only; caps10N/20N; no guitar forces',
            'initial_exact_current_three_face_reference':True,'initial_reference':str(INITIAL_REFERENCE),
            'Jacobian_fault_policy':dict(self.abi['Jacobian_fault_policy']),
            'goal_seed':self.seed,'goal_delta_G_m':self.goal_delta.tolist(),'graphics':s.gym.graphics_creations}
        return self._observe()

    def _palms(self):
        s = self.scene
        guitar = s.origin_motion(s.bodies(s.guitar)[0],s.guitar_bodies[0])
        human = s.bodies(s.human)
        return np.array([guitar[1].T@(s.origin_motion(human[s.human_bodies.index(n)],n)[0]-guitar[0]) for n in ('LH:palm','RH:palm')])

    def _goal(self):
        ramp = np.clip((self.scene.steps/240-self.config['prep_seconds'])/.5,0,1)
        return self.base_palms+ramp*self.goal_delta

    def _observe(self):
        from ..native_contacts import read_contacts
        s = self.scene
        physical = s.observe()
        manifest = s.observation_manifest
        contacts = read_contacts(s.gym,s.env,self.contacts_map)
        groups = [lambda n:n.startswith(('human/L_','human/LH:')),lambda n:n.startswith(('human/R_','human/RH:')),
                  lambda n:n in ('human/Torso','human/Spine','human/Chest'),lambda n:n=='human/Head']
        counts = np.zeros(4)
        for c in contacts:
            pair = (c['body0_name'],c['body1_name'])
            if any(n.startswith('guitar/') for n in pair):
                for i,predicate in enumerate(groups): counts[i] += any(predicate(n) for n in pair)
        self.contact_counts = counts
        self.observation_slices = {m['name']:[m['offset'],m['offset']+m['length']] for m in manifest}
        self.observation_slices.update(contact_counts=[548,552],goal_palms_G=[552,558])
        observation = np.r_[physical,np.minimum(counts,100)/100,self._goal().reshape(-1)/.25].astype(np.float32)
        if observation.shape!=(558,) or not np.isfinite(observation).all(): raise RuntimeError('invalid fresh observation')
        return observation

    def step(self,action):
        if self.scene is None or self.finished: raise RuntimeError('reset before stepping')
        s = self.scene
        before = s.target.copy()
        requested = action_targets(action,s.contract.q_ref,self.indices,self.action_lower,self.action_upper)
        a = np.asarray(action,dtype=float)
        native_action = np.clip((requested-s.contract.mid)/s.contract.half,-1,1)
        start_physics_step = s.steps
        start_effort_calls = s.right_effort_calls
        consistency_fault = None
        try:
            _,info = s.step(native_action)
        except JacobianConsistencyError as error:
            consistency_fault = error.diagnostic
            info = {'clock':s.contract.clock(s.steps),'requested_rad':requested.tolist(),'final_rad':s.target.tolist()}
        from ..run_joint_hold import native_state
        from ..initial_pose_noise_v1 import pose
        state = native_state(s)
        if not finite_native_state(state): raise RuntimeError('nonfinite post-step native body state')
        qv = np.array([[v['pos'],v['vel']] for v in state['human_dof_states']])
        if not np.isfinite(qv).all() or abs(qv[:,1]).max()>50: raise RuntimeError('unsafe post-step native state')
        if not all(state['human_body_states'][i]==self.initial['human_body_states'][i] for i in self.fixed): raise RuntimeError('fixed lower moved')
        if s.forbidden_calls: raise RuntimeError('forbidden native API')
        if not np.array_equal(s.target[self.kept].astype(float),s.contract.q_ref[self.kept]): raise RuntimeError('remaining27 target ownership')
        observation = self._observe()
        gp,gr = pose(state['guitar_body_states'][0])
        displacement = float(np.linalg.norm(gp-self.initial_gp))
        rotation = float((self.initial_gr.inv()*gr).magnitude())
        error = float(np.mean(np.sum((self._palms()-self._goal())**2,axis=1)))
        active = s.steps/240>self.config['prep_seconds']
        rate = float(np.mean(((s.target-before)[self.indices]*60)**2))
        reward = (float(np.exp(-error/.01**2)) if active else 0.)/60-.001*rate/60
        cost = (max(0.,displacement/.03-1)+max(0.,rotation/np.deg2rad(10)-1))/60
        terminated = bool(consistency_fault is not None or displacement>.20 or rotation>np.deg2rad(35))
        truncated = bool(not terminated and s.steps>=round(self.horizon*240))
        if consistency_fault is not None:
            reward,cost = -1.,1.
        self.finished = terminated or truncated
        info.update({'goal_error_squared_m2':error,'guitar_displacement_m':displacement,'guitar_rotation_rad':rotation,
                     'contact_counts':self.contact_counts.tolist(),'requested_action54':a.tolist(),'requested_target81_rad':requested.tolist(),
                     'submitted_target81_rad':s.target.tolist(),'target_changed_count':int(np.count_nonzero(s.target!=before)),
                     'effort_control':self.controller.last,'termination_reason':'Jacobian_consistency_safety' if consistency_fault is not None else 'guitar_safety' if terminated else 'time_limit' if truncated else None,
                     'Jacobian_consistency_fault':consistency_fault,'transition_physics_steps':s.steps-start_physics_step,
                     'transition_elapsed_s':(s.steps-start_physics_step)/240,
                     'transition_effort_submissions':s.right_effort_calls-start_effort_calls,
                     'music_success':False})
        return observation,float(reward),float(cost),terminated,truncated,info

    def close(self):
        if self.scene is not None:
            self.scene.close()
            self.scene = None
