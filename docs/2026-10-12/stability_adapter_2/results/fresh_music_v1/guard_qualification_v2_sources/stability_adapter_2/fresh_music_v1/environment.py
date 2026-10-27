"""Fresh music targets on the preserved v5 CPU physical shell.

Fret readiness is a marker/contact candidate, never verified string force.
Pick releases are finite-segment kinematic events; strings do not collide.
"""
import hashlib
from pathlib import Path
import numpy as np

from ..fresh_learning_v1 import environment_v5 as shell
from ..deadline_rotation_v3 import RotationEnvelope as SourceRotationEnvelope
from .events import load_music_task, OBSERVATION_DIM

FINGERS = ('index', 'middle', 'ring', 'pinky')
PREP_SECONDS = 2.


class RotationEnvelope(SourceRotationEnvelope):
    """Normalize the double-cover representative before the preserved solver."""
    def distance(self,quaternion_xyzw):
        q = np.asarray(quaternion_xyzw,dtype=float).copy()
        if q.shape!=(4,) or not np.isfinite(q).all() or np.linalg.norm(q)==0:
            raise ValueError('finite nonzero quaternion required')
        q /= np.linalg.norm(q)
        for value in q[[3,0,1,2]]:
            if value!=0:
                if value<0: q *= -1
                break
        return super().distance(q)


def collect_inputs(bundle_root):
    inputs = shell.collect_inputs()
    task = load_music_task(bundle_root)
    inputs.update({r['path']: r['sha256'] for r in task.provenance})
    for path in Path(__file__).parent.glob('*.py'):
        inputs[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    contract = shell.ROOT/'stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md'
    inputs[str(contract)] = hashlib.sha256(contract.read_bytes()).hexdigest()
    return inputs


def world_to_guitar(points, position, rotation):
    return (np.asarray(points)-position) @ np.asarray(rotation)


def fret_target(start, end, fret_y, previous_y):
    """Center of the playable wire interval, on the actual finite string."""
    y = (fret_y+previous_y)/2
    u = (y-start[1])/(end[1]-start[1])
    return start+u*(end-start)


def swept_crossings(previous, current, starts, ends, dt=1/240):
    """NumPy equivalent of strike_detector.swept_point_string_segments gates."""
    delta = current-previous
    cross = lambda a,b:a[0]*b[1]-a[1]*b[0]
    rows = []
    for string,(start,end) in enumerate(zip(starts,ends)):
        segment = end-start
        denominator = cross(delta[:2],segment[:2])
        if abs(denominator)<=1e-9: continue
        t = cross((start-previous)[:2],segment[:2])/denominator
        u = cross((start-previous)[:2],delta[:2])/denominator
        if not (0<t<=1 and 0<=u<=1): continue
        point = previous+t*delta
        tangent = segment[:2]/np.linalg.norm(segment[:2])
        normal = np.array([-tangent[1],tangent[0]])
        if normal[0]<0: normal *= -1
        speed = float(delta[:2]@normal/dt)
        depth = float((start+u*segment)[2]-point[2])
        # Same allowed strike corridor as the source detector.
        if abs(speed)>=.05 and depth>=.001 and -.385<=point[1]<=-.255:
            rows.append(dict(string=string, fraction=float(t), direction=1 if speed>0 else -1,
                             depth_m=depth, across_speed_m_s=speed))
    return rows


def press_candidate(tip, target, assigned_contact, held_seconds):
    error = np.asarray(tip)-target
    geometric = bool(np.linalg.norm(error[:2])<=.01 and -.006<=error[2]<=.01)
    return geometric, bool(geometric and assigned_contact and held_seconds>=.1-1e-12)


def crossing_press_valid(crossing,target):
    if target.fret==0: return True
    bracket = crossing.get('press_bracket',{}).get(str(target.string),{})
    owner = [target.fret,target.finger]
    return bool(bracket.get('owner_before')==owner and bracket.get('owner_after')==owner
                and bracket.get('valid_before') and bracket.get('valid_after')
                and bracket.get('continuous_dwell_before_s',0)>=.1-1e-12)


class MusicGuitarEnvironment(shell.FreshGuitarEnvironment):
    observation_dim = obs_dim = 548+4+OBSERVATION_DIM+6
    action_dim = 54

    def __init__(self,bundle_root=None,*,bundle=None,stage='B',tempo_scale=1.,preroll_s=1.,
                 phrase_events=8,event_limit=None,recording=False,seed=0,config=None):
        if bundle_root is None: bundle_root = bundle
        if bundle_root is None: raise ValueError('song bundle directory required')
        if event_limit is not None: phrase_events = event_limit
        self.task = load_music_task(bundle_root,stage=stage,tempo_scale=tempo_scale,
                                   preroll_s=preroll_s,phrase_events=phrase_events)
        settings = dict(shell.DEFAULT_CONFIG)
        settings.update(active_seconds=self.task.duration_s,support_range_rad=np.deg2rad(5),
                        fret_range_rad=.65,strike_range_rad=.65,finger_range_rad=.9)
        if config: settings.update(config)
        if settings['prep_seconds']!=PREP_SECONDS: raise ValueError('music preparation is exactly two seconds')
        if settings['active_seconds']!=self.task.duration_s: raise ValueError('music horizon belongs to task timeline')
        super().__init__(recording=recording,seed=seed,config=settings)
        self.horizon = PREP_SECONDS+self.task.duration_s
        self.rotation_envelope = RotationEnvelope()
        self._clear_music()
        self.abi = dict(version='fresh_music_native_v1',observation_dim=self.obs_dim,action_dim=54,
                        physical_shell='fresh_learning_v1.environment_v5',task=self.task.content_document(),
                        config=dict(self.config),clock='score=max(0,physics_seconds-2)',
                        press_scope='assigned distal-marker and native-contact candidate; force unverified',
                        strike_scope='kinematic finite string crossing, not physical string vibration',
                        crossing_gate='240Hz same assigned distal owner+geometry/native-contact before/after bracket; prior continuous dwell >=.1s; not exact subframe force verification',
                        crossing_timing=dict(training_half_window_s=.1,strict_report_half_window_s=.05),
                        candidate_thresholds=dict(tip_xy_m=.01,tip_z_min_m=-.006,tip_z_max_m=.01,
                                                  contact_hold_s=.1,release_distance_m=.015,timing_window_s=.1,
                                                  required_hold_fraction=.8,anticipatory_approach_s=.25),
                        target_ranges='torso5deg; right proximal .35rad; left arm .65rad; LH .9rad; right distal .65rad')

    def _clear_music(self):
        self.readiness = np.zeros(6)
        self.hold_seconds = np.zeros(6)
        self.crossings = []
        self.matched = set()
        self.strict_matched = set()
        self.missed = set()
        self.ledger = []
        self.last_metrics = {}
        self._hold_owner = [None]*6
        self.press_history = {}
        self._physics_hold = np.zeros(6)

    def reset(self,seed=None):
        self._clear_music()
        super().reset(seed=seed)
        s = self.scene
        # v5 ranges deliberately tiny; music needs explicit reachable target authority.
        for k,i in enumerate(self.indices):
            if s.names[i].startswith(('R_Thorax_','R_Shoulder_')):
                self.action_lower[k] = max(s.contract.lower[i],s.contract.q_ref[i]-.35)
                self.action_upper[k] = min(s.contract.upper[i],s.contract.q_ref[i]+.35)
        self.abi.update(action_groups=self.action_metadata,action_lower_rad=self.action_lower.tolist(),
                        action_upper_rad=self.action_upper.tolist(),remaining27_indices=self.kept.tolist())
        self.metadata.update(stage=self.task.stage,task=self.task.content_document(),music_success_claim=False,
                             joint_names=list(s.names),finger_measurement='distal finger3 body origin proxy; not calibrated fingertip/pad',
                             target_ranges_justification='Stage A milliradian practice bounds cannot reach frets/strings; native joint limits and rate caps remain')
        self._previous_pick = self._geometry()['pick']
        self._previous_physics = s.steps
        self._previous_press = self._press_bracket(self._geometry(),0.,self.contacts)
        previous = s.after_physics
        def observe(owner):
            if previous is not None: previous(owner)
            geometry = self._geometry()
            from ..native_contacts import read_contacts
            contacts = read_contacts(owner.gym,owner.env,self.contacts_map)
            current_press = self._press_bracket(geometry,max(0.,owner.steps/240-PREP_SECONDS),contacts)
            bracket = {}
            for string in range(6):
                before,after = self._previous_press[string],current_press[string]
                bracket[str(string)] = dict(owner_before=before['owner'],owner_after=after['owner'],
                    valid_before=before['valid'],valid_after=after['valid'],
                    continuous_dwell_before_s=float(self._physics_hold[string]),
                    physics_step_before=self._previous_physics,physics_step_after=owner.steps)
            for row in swept_crossings(self._previous_pick,geometry['pick'],geometry['starts'],geometry['ends']):
                row['score_time_s'] = (self._previous_physics+row['fraction'])/240-PREP_SECONDS
                row['press_bracket'] = bracket
                self.crossings.append(row)
            for string in range(6):
                before,after = self._previous_press[string],current_press[string]
                self._physics_hold[string] = self._physics_hold[string]+1/240 if (
                    before['valid'] and after['valid'] and before['owner']==after['owner']) else 0.
            self._previous_press = current_press
            self._previous_pick = geometry['pick'].copy()
            self._previous_physics = owner.steps
        s.after_physics = observe
        return self._observe()

    def _selected_targets(self,score):
        active = self.task.active_targets(score)
        preparing = {}
        occupied = {value[1].finger for value in active.values() if value[1].fret>0}
        for event in self.task.events:
            for target in event.string_targets:
                if not target.fret or target.string in active or target.string in preparing: continue
                if 0<self.task.task_time(target.press_start_s)-score<=.25 and target.finger not in occupied:
                    preparing[target.string] = (event,target)
                    occupied.add(target.finger)
        return active,preparing

    def _press_bracket(self,geometry,score,contacts):
        active,preparing = self._selected_targets(score)
        selected = dict(preparing)
        selected.update(active)
        rows = [dict(owner=None,valid=False) for _ in range(6)]
        for string,value in selected.items():
            target = value[1]
            if not target.fret: continue
            finger = FINGERS[target.finger-1]
            point = fret_target(geometry['starts'][string],geometry['ends'][string],
                geometry['local']['G:fret%d'%target.fret][1],
                geometry['local']['G:nut' if target.fret==1 else 'G:fret%d'%(target.fret-1)][1])
            contact = any(any(n=='human/LH:'+finger+'3' for n in (c['body0_name'],c['body1_name']))
                and any(n.startswith('guitar/') and 'pluck_range' not in n for n in (c['body0_name'],c['body1_name'])) for c in contacts)
            geometric,_ = press_candidate(geometry['tips']['LH:'+finger+'3'],point,contact,0)
            rows[string] = dict(owner=[target.fret,target.finger],valid=bool(geometric and contact))
        return rows

    def _geometry(self):
        s = self.scene
        guitar = s.bodies(s.guitar)
        gp,gr,_,_ = s.origin_motion(guitar[0],s.guitar_bodies[0])
        local = {name:world_to_guitar(s.origin_motion(row,name)[0],gp,gr)
                 for name,row in zip(s.guitar_bodies,guitar)}
        human = s.bodies(s.human)
        points = {name:world_to_guitar(s.origin_motion(human[s.human_bodies.index(name)],name)[0],gp,gr)
                  for name in ('RH:pick',)+tuple('LH:'+f+'3' for f in FINGERS)}
        return dict(starts=np.array([local['G:string%d'%n] for n in range(1,7)]),
                    ends=np.array([local['G:string%d_end'%n] for n in range(1,7)]),
                    local=local,tips=points,pick=points['RH:pick'])

    def _observe(self):
        from ..native_contacts import read_contacts
        s = self.scene
        physical = s.observe()
        contacts = read_contacts(s.gym,s.env,self.contacts_map)
        self.contacts = contacts
        counts = np.zeros(4)
        for c in contacts:
            pair = (c['body0_name'],c['body1_name'])
            if not any(n.startswith('guitar/') for n in pair): continue
            for k,prefixes in enumerate((('human/L_','human/LH:'),('human/R_','human/RH:'),
                                         ('human/Torso','human/Spine','human/Chest'),('human/Head',))):
                counts[k] += any(n.startswith(prefixes) for n in pair)
        self.contact_counts = counts
        score = max(0.,s.steps/240-PREP_SECONDS)
        observation = np.r_[physical,np.minimum(counts,100)/100,self.task.encode(score),self.readiness].astype(np.float32)
        self.observation_slices = {m['name']:[m['offset'],m['offset']+m['length']] for m in s.observation_manifest}
        self.observation_slices.update(contact_counts=[548,552],music_targets=[552,738],readiness=[738,744])
        if observation.shape!=(self.obs_dim,) or not np.isfinite(observation).all(): raise RuntimeError('music observation ABI')
        return observation

    def _measure_music(self,score):
        geometry = self._geometry()
        self.readiness[:] = 0
        approach,release,rows = [],[],[]
        owners = [None]*6
        active_targets,preparation_targets = self._selected_targets(score)
        for event in self.task.events:
            for t in event.string_targets:
                if not t.fret: continue
                start = self.task.task_time(t.press_start_s)
                end = self.task.task_time(min(t.sustain_until_s,t.release_s))
                audible_start = self.task.task_time(event.score_time_s+t.traversal_offset_s)
                target = fret_target(geometry['starts'][t.string],geometry['ends'][t.string],
                                     geometry['local']['G:fret%d'%t.fret][1],
                                     geometry['local']['G:nut' if t.fret==1 else 'G:fret%d'%(t.fret-1)][1])
                finger = FINGERS[t.finger-1]
                tip = geometry['tips']['LH:'+finger+'3']
                contacted = any(any(n=='human/LH:'+finger+'3' for n in (c['body0_name'],c['body1_name']))
                                 and any(n.startswith('guitar/') and 'pluck_range' not in n for n in (c['body0_name'],c['body1_name'])) for c in self.contacts)
                geometric,_ = press_candidate(tip,target,contacted,0)
                selected = active_targets.get(t.string)
                active = bool(selected is not None and selected[0].event_id==event.event_id)
                preparing = bool(t.string in preparation_targets and preparation_targets[t.string][0].event_id==event.event_id)
                history_key = (str(event.event_id),t.string)
                history = self.press_history.setdefault(history_key,dict(required_seconds=end-audible_start,
                    audible_start_s=audible_start,audible_end_s=end,source_press_start_task_s=start,
                    assigned_contact_geometric_seconds=0.,ready_dwell_seconds=0.,released_after_hold=False))
                if active or preparing:
                    owner = (t.fret,t.finger)
                    owners[t.string] = owner
                    if self._hold_owner[t.string]!=owner: self.hold_seconds[t.string] = 0
                    self.hold_seconds[t.string] = self.hold_seconds[t.string]+1/60 if geometric and contacted else 0
                    _,ready = press_candidate(tip,target,contacted,self.hold_seconds[t.string])
                    self.readiness[t.string] = ready
                    approach.append(float(np.exp(-np.sum((tip-target)**2)/.025**2)))
                elif score>=end and t.string not in active_targets and not any(
                        current[1].finger==t.finger and current[1].fret>0 for current in active_targets.values()):
                    released = bool(np.linalg.norm(tip-target)>.015 and not contacted)
                    release.append(float(released))
                    if released and history['assigned_contact_geometric_seconds']>=.1-1e-12:
                        history['released_after_hold'] = True
                rows.append(dict(event_id=str(event.event_id),string=t.string,fret=t.fret,finger=t.finger,
                                 required=active,target_G_m=target.tolist(),tip_G_m=tip.tolist(),
                                 audible_hold_required=audible_start<=score<end,
                                 anticipatory_approach=preparing,
                                 distance_m=float(np.linalg.norm(tip-target)),assigned_native_contact=contacted,
                                 geometric_candidate=geometric,ready_candidate=bool(self.readiness[t.string]),
                                 force_verified_press=False))
        for string,owner in enumerate(owners):
            if owner is None: self.hold_seconds[string] = 0
        self._hold_owner = owners
        for row in rows:
            owned = owners[row['string']]==(row['fret'],row['finger'])
            row['ready_candidate'] = bool(owned and self.readiness[row['string']])
            if row['audible_hold_required'] and owned:
                history = self.press_history[(row['event_id'],row['string'])]
                history['assigned_contact_geometric_seconds'] += float(row['geometric_candidate'] and row['assigned_native_contact'])/60
                history['ready_dwell_seconds'] += float(row['ready_candidate'])/60
        accepted,wrong = 0,0
        processed = []
        for crossing in self.crossings:
            matches = []
            record = dict(crossing,accepted=False,event_id=None,fret=None,finger=None,
                          expected_time_s=None,signed_timing_error_s=None,proxy_ready=False,
                          reason='no_unmatched_target_in_training_window_or_wrong_direction')
            if self.task.stage!='B':
                for event in self.task.events:
                    for t in event.string_targets:
                        key = (str(event.event_id),t.string)
                        onset = self.task.task_time(event.score_time_s+t.traversal_offset_s)
                        if key not in self.matched and t.string==crossing['string'] and abs(crossing['score_time_s']-onset)<=.1 and crossing['direction']==(1 if event.strike.direction=='down' else -1):
                            matches.append((abs(crossing['score_time_s']-onset),key,t))
            if matches:
                _,key,target = min(matches,key=lambda r:r[0])
                event = next(e for e in self.task.events if str(e.event_id)==key[0])
                expected = self.task.task_time(event.score_time_s+target.traversal_offset_s)
                ready = crossing_press_valid(crossing,target)
                record.update(event_id=key[0],fret=target.fret,finger=target.finger,
                              expected_time_s=expected,signed_timing_error_s=crossing['score_time_s']-expected,
                              proxy_ready=ready)
                if ready:
                    self.matched.add(key); accepted += 1
                    if abs(record['signed_timing_error_s'])<=.05+1e-12: self.strict_matched.add(key)
                    record.update(accepted=True,reason='matched_kinematic_crossing_with_press_candidate' if target.fret else 'matched_open_string_kinematic_crossing')
                else:
                    wrong += 1
                    record['reason'] = 'assigned_press_owner_bracket_or_continuous_dwell_invalid'
            elif crossing['score_time_s']>=0 and self.task.stage!='B': wrong += 1
            self.ledger.append(record)
            processed.append(record)
        self.crossings.clear()
        for event in self.task.events:
            for t in event.string_targets:
                key = (str(event.event_id),t.string)
                if self.task.stage!='B' and score>self.task.task_time(event.score_time_s+t.traversal_offset_s)+.1 and key not in self.matched:
                    self.missed.add(key)
        press_rows = [dict(event_id=key[0],string=key[1],**value) for key,value in self.press_history.items()]
        press_complete = bool(press_rows and all(r['ready_dwell_seconds']>0 and r['assigned_contact_geometric_seconds']>=max(.1,.8*r['required_seconds'])
                                                and r['released_after_hold'] for r in press_rows))
        return dict(fret_rows=rows,press_hold_release=press_rows,press_hold_release_candidate_complete=press_complete,
                    approach_quality=float(np.mean(approach)) if approach else 0.,
                    release_quality=float(np.mean(release)) if release else 0.,accepted_crossings=accepted,
                    wrong_crossings=wrong,matched_string_targets=len(self.matched),missed_string_targets=len(self.missed),
                    processed_crossings=processed,strict_50ms_matched_string_targets=len(self.strict_matched),
                    total_string_targets=sum(len(e.string_targets) for e in self.task.events),
                    completed_canonical_events=sum(all((str(e.event_id),t.string) in self.matched for t in e.string_targets) for e in self.task.events),
                    force_verified_press=False,physical_string_sound_verified=False)

    def step(self,action):
        if self.scene is None or self.finished: raise RuntimeError('reset before stepping')
        s = self.scene
        before = s.target.copy()
        requested = shell.action_targets(action,s.contract.q_ref,self.indices,self.action_lower,self.action_upper)
        filtered = shell.smooth_target(requested,before,self.config['target_smoothing_alpha'])
        native_action = np.clip((filtered-s.contract.mid)/s.contract.half,-1,1)
        _,info = s.step(native_action)
        from ..run_joint_hold import native_state
        from ..initial_pose_noise_v1 import pose
        state = native_state(s)
        qv = np.array([[r['pos'],r['vel']] for r in state['human_dof_states']])
        if not np.isfinite(qv).all() or abs(qv[:,1]).max()>50: raise RuntimeError('unsafe post-step native state')
        if not all(state['human_body_states'][i]==self.initial['human_body_states'][i] for i in self.fixed): raise RuntimeError('fixed lower moved')
        if s.forbidden_calls: raise RuntimeError('forbidden native API')
        if not np.array_equal(s.target[self.kept].astype(float),s.contract.q_ref[self.kept]): raise RuntimeError('remaining27 target ownership')
        self._observe()
        score = max(0.,s.steps/240-PREP_SECONDS)
        metrics = self._measure_music(score)
        gp,gr = pose(state['guitar_body_states'][0])
        outside = np.maximum(np.maximum(np.array([-.50,-.15,.65])-gp,gp-np.array([-.15,.15,s.z_chest])),0)
        rotation = self.rotation_envelope.distance(gr.as_quat())
        cost = (float(np.linalg.norm(outside))/.1+rotation['upper_rad'])/60
        active = s.steps/240>=PREP_SECONDS
        rate = float(np.mean(((s.target-before)[self.indices]*60)**2))
        reward = ((metrics['approach_quality']+.5*float(self.readiness.mean())+.2*metrics['release_quality'])/60
                  +metrics['accepted_crossings']-.25*metrics['wrong_crossings']) if active else 0.
        reward -= .001*rate/60
        truncated = s.steps>=round(self.horizon*240)
        self.finished = bool(truncated)
        self.last_metrics = metrics
        info.update(metrics,music_success=False,score_time_s=score,contact_counts=self.contact_counts.tolist(),
                    native_motion=dict(q81_rad=qv[:,0].tolist(),qdot81_rad_s=qv[:,1].tolist(),
                                       guitar_root_body_state=state['guitar_body_states'][0]),
                    requested_action54=np.asarray(action).tolist(),requested_target81_rad=requested.tolist(),
                    submitted_target81_rad=s.target.tolist(),filtered_requested_target81_rad=filtered.tolist(),
                    effort_control=self.controller.last,position_outside_m=outside.tolist(),rotation_envelope=rotation,
                    rotation_cost_scope='feasible upper distance bound; exact nearest distance uncertified',
                    termination_reason='timeline_complete' if truncated else None)
        return self._observe(),float(reward),float(cost),False,bool(truncated),info
