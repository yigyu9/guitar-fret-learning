"""기타 좌표계 기하 계산과 CPU·GPU 공통 관측 필드 구성을 제공한다.

읽는 순서: 좌표 변환·점 운동 → geometry_snapshot → 프렛 목표·타격 구간 → 관측 구성.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.song.task import EVENT_FIELDS, STATE_FIELDS


def frame(body_state):
    pose = body_state['pose']
    p = np.array([pose['p'][axis] for axis in 'xyz'], dtype=float)
    q = np.array([pose['r'][axis] for axis in 'xyzw'], dtype=float)
    if not np.isfinite(np.r_[p, q]).all() or np.linalg.norm(q) == 0:
        raise ValueError('finite pose and nonzero quaternion required')
    return p, Rotation.from_quat(q)


def world_to_guitar(points_W, guitar_state):
    p, rotation = frame(guitar_state)
    return rotation.inv().apply(np.asarray(points_W, dtype=float) - p)


def guitar_to_world(points_G, guitar_state):
    p, rotation = frame(guitar_state)
    return p + rotation.apply(np.asarray(points_G, dtype=float))


def body_point_motion(body_state, local_point, com_local):
    """몸체 원점의 자세, 네이티브 질량중심 선속도, 월드 각속도를 사용한다."""
    p, rotation = frame(body_state)
    point = np.asarray(local_point, dtype=float)
    com = np.asarray(com_local, dtype=float)
    if point.shape != (3,) or com.shape != (3,) or not np.isfinite(np.r_[point, com]).all():
        raise ValueError('finite body-local point and COM vectors required')
    linear = np.array([body_state['vel']['linear'][a] for a in 'xyz'])
    angular = np.array([body_state['vel']['angular'][a] for a in 'xyz'])
    return p + rotation.apply(point), linear + np.cross(angular, rotation.apply(point - com))


def relative_point_motion(point_W, velocity_W, guitar_state, guitar_com_local):
    """기타 회전까지 포함해 R_GW (point_W - origin_W)를 미분한다."""
    origin, origin_velocity = body_point_motion(guitar_state, np.zeros(3), guitar_com_local)
    _, rotation = frame(guitar_state)
    omega = np.array([guitar_state['vel']['angular'][a] for a in 'xyz'])
    point = np.asarray(point_W, dtype=float)
    return (rotation.inv().apply(point - origin),
            rotation.inv().apply(np.asarray(velocity_W) - origin_velocity - np.cross(omega, point - origin)))


def geometry_snapshot(state, human_names, guitar_names):
    """리셋 당시 목표가 아닌 현재 물리 표본의 마커 원점을 읽는다.
    
    손가락 말단 몸체 원점은 보정된 패드가 아닌 대리점으로 구분한다.
    이 함수는 실제 접촉·압력·음악 성공을 판정하지 않는다.
    """
    if len(set(human_names)) != len(human_names) or len(set(guitar_names)) != len(guitar_names):
        raise ValueError('unique body names required')
    if len(human_names) != len(state['human_body_states']) or len(guitar_names) != len(state['guitar_body_states']):
        raise ValueError('body names and states must align')
    humans = dict(zip(human_names, state['human_body_states']))
    guitars = dict(zip(guitar_names, state['guitar_body_states']))
    guitar = guitars['guitar']
    local = {name: world_to_guitar(frame(body)[0], guitar) for name, body in guitars.items()}
    tips = {finger: world_to_guitar(frame(humans['LH:' + finger + '3'])[0], guitar)
            for finger in ('thumb', 'index', 'middle', 'ring', 'pinky')}
    pick = world_to_guitar(frame(humans['RH:pick'])[0], guitar)
    return dict(schema='free_guitar_geometry_v1', physics_step=int(state['physics_step']),
                frame='current guitar root body origin; +x string6 to string1, +y bridge to nut',
                string_numbers=list(range(1, 7)),
                starts_G_m=np.array([local['G:string%d' % n] for n in range(1, 7)]),
                ends_G_m=np.array([local['G:string%d_end' % n] for n in range(1, 7)]),
                fret_markers_G_m=np.array([local['G:nut']] + [local['G:fret%d' % n] for n in range(1, 23)]),
                pick_G_m=pick, finger_distal_origins_G_m=tips,
                measurement_scope='saved/live body origins; distal proxies, no pad or pressure measurement')


def fret_target(snapshot, string_number, musical_fret):
    """측정한 현의 프렛 구간 중점을 구하며 개방현에는 압현 목표를 두지 않는다."""
    if type(string_number) is not int or not 1 <= string_number <= 6:
        raise ValueError('physical string number must be 1..6')
    if type(musical_fret) is not int or not 0 <= musical_fret <= 22:
        raise ValueError('musical fret must be 0..22; legacy sentinels need an adapter')
    if musical_fret == 0:
        return None
    markers = snapshot['fret_markers_G_m']
    y = (markers[musical_fret - 1, 1] + markers[musical_fret, 1]) / 2
    start, end = snapshot['starts_G_m'][string_number - 1], snapshot['ends_G_m'][string_number - 1]
    if abs(end[1] - start[1]) < 1e-12:
        raise ValueError('string must span the measured fret direction')
    fraction = (y - start[1]) / (end[1] - start[1])
    if not 0 <= fraction <= 1:
        raise ValueError('fret interval outside measured finite string')
    return start + fraction * (end - start)


def relative_sweep_inputs(previous, current, physics_hz=240.):
    """각 표본의 좌표계를 사용해 기존 국소 통과 검출기의 입력을 만든다.
    
    두 끝점을 직선으로 잇는 상대 이동은 한 물리 구간의 근사다.
    여섯 줄을 가진 강체 기타의 로컬 끝점은 그대로 유지해야 한다.
    """
    elapsed = current['physics_step'] - previous['physics_step']
    if elapsed != 1 or not np.isfinite(physics_hz) or physics_hz <= 0:
        raise ValueError('consecutive physics samples and positive frequency required')
    for key in ('starts_G_m', 'ends_G_m'):
        if not np.allclose(previous[key], current[key], atol=1e-5, rtol=0):
            raise ValueError('local string geometry changed; rigid-guitar sweep is invalid')
    return dict(previous_tip_g=previous['pick_G_m'].copy(), current_tip_g=current['pick_G_m'].copy(),
                string_start_g=current['starts_G_m'].copy(), string_end_g=current['ends_G_m'].copy(),
                dt=1. / physics_hz)


# GPU·CPU 전곡 환경이 공유하는 관측 필드다.
LEFT_FIELDS = ('delta_x', 'delta_y', 'delta_z', 'rotation_x', 'rotation_y',
               'rotation_z', 'focus_contact_fraction', 'focus_contact_achieved',
               'contact_achieved_fraction', 'progress',
               'contact_weight', 'timing_weight')
LEFT_SCALES = (.05, .05, .05, .6, .6, .6, 1., 1., 1., 2., 1., 1.)

HISTORY_FIELDS = (
    'elapsed_fraction', 'remaining_fraction', 'target_count', 'expired_fraction',
    'left_achieved_fraction', 'right_matched_fraction', 'coupled_fraction',
    'left_missed_fraction', 'right_missed_fraction', 'mean_clean_fraction',
    'wrong_crossings', 'repeat_crossings', 'duplicate_crossings', 'safety_invalidated',
    'strict50_fraction', 'strict100_fraction',
    'focus_present', 'focus_current', 'focus_preparing', 'focus_string', 'focus_fret',
    'focus_finger', 'focus_direction', 'focus_onset_delta_s', 'focus_end_delta_s',
    'focus_candidate', 'focus_wrong', 'focus_clean_fraction', 'focus_left_achieved',
    'focus_right_matched', 'focus_coupled', 'focus_required_fraction')
HISTORY_SCALES = tuple(100. if name in ('target_count', 'wrong_crossings', 'repeat_crossings',
    'duplicate_crossings') else 6. if name == 'focus_string' else 22. if name == 'focus_fret'
    else 4. if name == 'focus_finger' else 2. if name.endswith('_delta_s') else 1.
    for name in HISTORY_FIELDS)


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
