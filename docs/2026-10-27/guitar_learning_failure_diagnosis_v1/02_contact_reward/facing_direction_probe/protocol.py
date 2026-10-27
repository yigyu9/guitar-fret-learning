"""Small pure diagnostic trajectory/summary helpers; no scene or policy."""
import math


def schedule(time_s, condition, *, torch):
    """Next-control-endpoint requests; no omitted preparation physics."""
    fraction = (time_s/2.).clamp(0, 1)
    clearance = .015*(1-(time_s-2.).clamp(0, .8)/.8)
    clearance = torch.where(condition == 0, torch.zeros_like(clearance), clearance)
    return fraction, clearance


def goals(control, teacher, reference, plane, string_vector):
    """Seal numerical16-row goals using only original stored bounds/coordinates."""
    import numpy as np
    from scipy.spatial.transform import Rotation
    names=control['action_order']
    # Stable named order, independent of reference JSON object ordering.
    selected=list(range(21,25))
    q=np.array([reference['selected_targets_rad'][names[i]] for i in selected])
    finger=np.tile(q,(8,1))
    finger[2,[0,2,3]]=np.array(control['action_lower_rad'])[np.array(selected)[[0,2,3]]]
    finger[3,3]=control['action_upper_rad'][selected[3]]
    n=np.asarray(plane[:3],float);n/=np.linalg.norm(n)
    u=np.asarray(string_vector,float);u-=n*(u@n);u/=np.linalg.norm(u)
    v=np.cross(n,u);v/=np.linalg.norm(v)
    base=Rotation.from_quat(teacher['wrist_quaternion_G_xyzw'])
    wrist=np.tile(base.as_quat(),(8,1))
    for row,axis,sign in ((4,u,1),(5,u,-1),(6,v,1),(7,v,-1)):
        wrist[row]=(Rotation.from_rotvec(sign*math.pi/2*axis)*base).as_quat()
    return dict(selected_action_indices=selected, selected_action_names=[names[i] for i in selected],
        finger_goals_rad=finger.tolist(), wrist_goals_G_xyzw=wrist.tolist(),
        wrist_position_G_m=teacher['wrist_position_G_m'], plane_normal_G=n.tolist(),
        string_axis_G=u.tolist(), cross_axis_G=v.tolist(), action_lower_rad=control['action_lower_rad'],
        action_upper_rad=control['action_upper_rad'], assignments=[dict(env_id=i,condition=i%8,repetition=i//8) for i in range(16)])


def manifest(numerical, view):
    return dict(schema='facing_direction_probe.v1', conditions=8,repetitions=2,num_envs=16,
        assignment='env_id%8; repetition env_id//8; all first attempts including failures',
        trajectories=['original reference','reference + clearance','x/PIP/DIP lower + clearance',
            'DIP upper + clearance','u +90deg + clearance','u -90deg + clearance',
            'v +90deg + clearance','v -90deg + clearance'],
        numerical=numerical,view=view, ramp_s=2.,clearance_m=.015,approach_end_s=2.8,
        physics_hz=240,control_hz=60,substeps=4,
        negative='first attempt before native physical/wrist failure; assigned resultant>=0.01N; any original position sample; no SAME valid position sample faces cosine>=0.1',
        stable='at least13 consecutive eligible endpoints; span=(last-first)/240>=.05s; gaps/ineligible/reset break span',
        direction_reporting_threshold_rad=math.radians(10),
        direction_reporting_scope='diagnostic orientation error after2.8s only; no native predicate/termination relaxation',
        saved_num_envs=128,batch_override='16 for diagnostic only; exact original architecture/control/config strict load retained',
        scope='new finite trajectory conditions around original row8; not same-task policy evaluation or training performance',
        gpu_handoff='root internal scheduler handoff only; user authorization already given; no additional user approval question',
        updates=0,state_overwrites='prepared reset only at episode boundary',
        limitations='net body resultant does not identify pairs, real string pressure, dorsal skin contact or whole-body force extrema')


def summarize(arrays, episodes, protocol):
    """Report native gates; failed/after-first-attempt samples never qualify."""
    import numpy as np
    count=protocol['num_envs']; rows=[]
    force=np.linalg.norm(arrays['distal_force_n'],axis=-1)
    for i in range(count):
        live=arrays['first_attempt'][:,i] & ~arrays['failed'][:,i]
        position=arrays['position_mask'][:,i].any(-1)
        facing=arrays['facing_mask'][:,i].any(-1)
        geometric=live & position & ~facing
        loaded=geometric & (force[:,i]>=.01)
        indices=np.flatnonzero(loaded); runs=[]
        if len(indices):
            split=np.flatnonzero((np.diff(indices)!=1)|(np.diff(arrays['clock'][indices,i])!=1))+1
            runs=np.split(indices,split)
        best=max(runs,key=len) if runs else []
        span=int(arrays['clock'][best[-1],i]-arrays['clock'][best[0],i]) if len(best) else 0
        post=live & (arrays['local_time_s'][:,i]>=2.8)
        first=int(indices[0]) if len(indices) else None
        episode=episodes.get(i)
        safe_episode=bool(episode and not episode['termination']['physical_failure'] and not episode['termination']['wrist_failure'])
        rows.append(dict(env_id=i,condition=i%8,repetition=i//8,assigned_denominator=2,
            episode_reason=episode['reason'] if episode else 'missing',
            orientation_error_min_after2p8_rad=float(arrays['orientation_error_rad'][post,i].min()) if post.any() else None,
            orientation_within10deg_after2p8=bool(np.any(post & (arrays['orientation_error_rad'][:,i]<=protocol['direction_reporting_threshold_rad']))),
            position_samples=int((live&position).sum()), facing_samples=int((live&facing).sum()),
            negative_geometry_unloaded_samples=int((geometric&(force[:,i]<.01)).sum()),
            loaded_negative_samples=len(indices),loaded_negative_before_failure=bool(len(indices)),
            safe_episode=safe_episode,loaded_negative_witness=bool(len(indices)),
            safe_episode_witness=bool(len(indices)) and safe_episode,
            stable_before_failure=span>=12,stable50ms=span>=12,
            safe_episode_stable50ms=span>=12 and safe_episode,
            max_contiguous_samples=len(best),max_contiguous_span_s=span/240.,
            first_witness=dict(clock=int(arrays['clock'][first,i]),resultant_n=float(force[first,i]),
                position_sample_indices=np.flatnonzero(arrays['position_mask'][first,i]).tolist(),
                position_sample_cosines=arrays['normal_cos'][first,i][arrays['position_mask'][first,i]].tolist()) if first is not None else None,
            cause=('loaded_negative_observed' if len(indices) else 'negative_geometry_unloaded' if geometric.any()
                else 'position_not_observed' if not np.any(live&position) else 'same_sample_facing_remained'),
            first_failure_clock=int(arrays['clock'][np.flatnonzero(arrays['first_attempt'][:,i]&arrays['failed'][:,i])[0],i])
                if np.any(arrays['first_attempt'][:,i]&arrays['failed'][:,i]) else None))
    return rows
