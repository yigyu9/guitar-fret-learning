"""Fixed, named actor/critic inputs from the current moving-guitar scene."""
import numpy as np
from guitar_learning.core.geometry_v1 import frame, body_point_motion, relative_point_motion
from guitar_learning.music_task import EVENT_FIELDS, STATE_FIELDS

PROXIES = ('L_Wrist','R_Wrist','RH:pick','LH:thumb3','LH:index3','LH:middle3','LH:ring3','LH:pinky3')
EVENT_SCALES = np.array([2,2,2,6,22,4,1,1,1,1,1,1,1,1,1,2,.25,.25,.25,1,1,1,2,2], dtype=float)


class ObservationBuilder:
    def __init__(self, names, human_names, guitar_names, human_com, guitar_com, reference105, task):
        self.names, self.human_names, self.guitar_names = tuple(names), tuple(human_names), tuple(guitar_names)
        self.human_com, self.guitar_com = human_com, guitar_com
        self.reference = np.asarray(reference105,dtype=float).copy()
        if len(self.names) != 105 or self.reference.shape != (105,):
            raise ValueError('exact native105 observation order required')
        self.task = task
        fields, scales = [], []
        def add(prefix, components, scale):
            fields.extend(prefix+'.'+s for s in components)
            scales.extend(np.broadcast_to(scale,(len(components),)).tolist())
        for block, scale in (('q_offset',1.),('q_velocity',10.),('target_error',1.)):
            add(block,self.names,scale)
        from guitar_learning.core.control import ACTIVE_NAMES
        add('previous_action',ACTIVE_NAMES,1.)
        add('guitar_in_pelvis',tuple('p_'+x for x in 'xyz'),.5)
        add('guitar_in_pelvis',tuple('r'+str(i) for i in range(6)),1.)
        add('guitar_in_pelvis',tuple('v_'+x for x in 'xyz'),1.)
        add('guitar_in_pelvis',tuple('omega_'+x for x in 'xyz'),10.)
        for proxy in PROXIES:
            add(proxy+'_in_guitar',tuple('p_'+x for x in 'xyz'),.5)
            add(proxy+'_in_guitar',tuple('v_'+x for x in 'xyz'),1.)
        add('contact',('chest','right_upper_arm','right_thigh','thumb','index','middle','ring','pinky','left_foot','right_foot'),1.)
        add('guitar_reset_delta',tuple('p_'+x for x in 'xyz'),.02)
        add('guitar_reset_delta',tuple('rot_'+x for x in 'xyz'),.2)
        add('feet_reset_delta',tuple(side+'_'+x for side in ('L','R') for x in 'xyz'),.02)
        add('music',STATE_FIELDS,(max(task.duration_s,1),max(len(task.targets),1),max(len(task.targets),1),max(len(task.targets),1),max(task.duration_s*len(task.targets),1),max(len(task.targets),1),2,max(task.duration_s,1)))
        add('strike_detector',tuple(f'{field}_string{n}' for field in ('armed','side','cooldown_steps') for n in range(1,7)),1.)
        add('contact_loss_s',('all_support','left_foot','right_foot'),.25)
        self.fields, self.scales = fields, np.array(scales,dtype=float)
        self.spec = dict(dimension=len(fields), fields=fields, scales=self.scales.tolist(),
                         clip_abs=10., normalization='fixed_divide_by_scales_no_running_updates',
                         event_dim=24, event_fields=list(EVENT_FIELDS), event_scales=EVENT_SCALES.tolist(),
                         capacity=task.capacity, priority_slots=2,
                         proxy_scope='body origins; not finger pads', joint_order=list(self.names))

    def build(self, sample, measured, safety, target105, previous_action):
        native = sample['native']
        humans = dict(zip(self.human_names,native['human_body_states']))
        guitars = dict(zip(self.guitar_names,native['guitar_body_states']))
        guitar, pelvis = guitars['guitar'], humans['Pelvis']
        gp, gv = body_point_motion(guitar,np.zeros(3),self.guitar_com['guitar'])
        rp, rv = relative_point_motion(gp,gv,pelvis,self.human_com['Pelvis'])
        _, gr = frame(guitar)
        _, pr = frame(pelvis)
        relative_rotation = (pr.inv()*gr).as_matrix()[:,:2].T.ravel()
        omega = pr.inv().apply(np.array([guitar['vel']['angular'][x]-pelvis['vel']['angular'][x] for x in 'xyz']))
        positions = np.array([r['pos'] for r in native['human_dof_states']],dtype=float)
        velocity = np.array([r['vel'] for r in native['human_dof_states']],dtype=float)
        proxies = []
        for name in PROXIES:
            p,v = body_point_motion(humans[name],np.zeros(3),self.human_com[name])
            p,v = relative_point_motion(p,v,guitar,self.guitar_com['guitar'])
            proxies.extend((*p,*v))
        raw = np.r_[positions-self.reference,velocity,np.asarray(target105)-positions,previous_action,
                    rp,relative_rotation,rv,omega,proxies,safety['flags'],safety['guitar_delta_m'],
                    safety['guitar_rotation_vector_rad'],safety['foot_delta_m'].ravel(),
                    measured['observation']['state'],measured['detector_state'],safety['loss_s']]
        if raw.shape != self.scales.shape or not np.isfinite(raw).all():
            raise ValueError('nonfinite or misdimensioned state observation')
        music = measured['observation']
        def events(key,mask_key):
            a = np.array(music[key],dtype=float)
            mask = np.asarray(music[mask_key],dtype=bool)
            if a.shape != mask.shape+(24,) or not np.isfinite(a[mask]).all():
                raise ValueError('invalid measured event observation')
            return np.where(mask[:,None],np.clip(a/EVENT_SCALES,-10,10),0).astype(np.float32),mask.copy()
        e,m = events('tokens','mask')
        p,pm = events('priority_tokens','priority_mask')
        return dict(state=np.clip(raw/self.scales,-10,10).astype(np.float32),events=e,mask=m,
                    priority_events=p,priority_mask=pm)
