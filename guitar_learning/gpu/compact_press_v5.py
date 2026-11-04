"""압현 V5의 상태·목표, 준비 보상, 동시 유지와 해제 평가를 한곳에 정의한다.

공용 FingerSkillEnvironment의 물리·관절 제어·접촉·종료 계산을 사용한다.
이전 계약 이름은 저장된 진단 필드의 의미를 유지하는 메타데이터다.
"""
import copy
import math

import torch

from guitar_learning.gpu.control import apply, conjugate, multiply, origin_velocity, relative_point
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment, WRIST_FIELDS, remaining_negative_budget
from guitar_learning.gpu.finger_reward import B_PREPARATION_ANGLES_DEGREES
from guitar_learning.gpu.press_coordination import audible_sections, validate_assignments

OBSERVATION_SCHEMA = 'guitar_learning.compact_press_observation.v5'
GOAL_COLUMNS = (3, 4, 5, 2, 0, 1, 16, 17, 18, 19, 20, 21, 22, 23, 9, 10)
GOAL_FIELDS = ('string_1based', 'fret', 'finger', 'press_delta_s', 'onset_delta_s',
               'end_delta_s', 'surface_error_x', 'surface_error_y', 'surface_error_z',
               'surface_relative_velocity_x', 'surface_relative_velocity_y',
               'surface_relative_velocity_z', 'pad_normal_cos', 'pad_signed_height',
               'surface_candidate_now', 'surface_wrong_now')
GOAL_SCALES = (6., 14., 4., 2., 2., 2., .03, .03, .03, .5, .5, .5, 1., .03, 1., 1.)
ADDED_STATE_FIELDS = ('contact_loss_s.support_any', 'contact_loss_s.left_foot',
    'contact_loss_s.right_foot', 'episode.remaining_s', 'episode.remaining_negative_note_budget',
    'coordination.target_count', 'coordination.all_clean', 'coordination.clean_streak_s',
    'coordination.remaining_s')
ADDED_GOAL_FIELDS = ('contact_streak_s', 'contact_progress', 'left_achieved',
    'best_clean_streak_s', 'missing_s', 'performance_paid', 'performance_settled',
    'required_clean_s', 'note_duration_s', 'selected_note_weight')
ADDED_GOAL_SCALES = (2., 1., 1., 2., 2., 1., 1., 2., 2., 1.)
IMPROVEMENT_PROFILES = ('corrected', 'preparation', 'full_hold', 'combined')
PROFILES = IMPROVEMENT_PROFILES


def actual_reward_posture(posture):
    """관측용 원문은 보존하고 실제 지급 gate를 읽는 진단 사전을 만든다."""
    gate = posture.get('standby_reward_gate', posture['gate'])
    return dict(posture, gate=gate, idle_weight=gate)


def geometric_posture_flags(angles, valid):
    """실제 기하 굽힘각(rad)의 진단 전용 문턱. 관절 명령이나 안전 조건이 아니다."""
    finite = valid.all(-1) & torch.isfinite(angles).all(-1)
    mcp, pip, dip = (angles*180/math.pi).unbind(-1)
    flags = torch.stack((mcp < -20, (mcp > 60) & (pip < 45) & (dip < 30), dip-pip > 50), -1)
    return flags & finite[..., None]


def standby_posture_quality(angles, valid, narrow=True):
    """B 실제 기하 자세의 품질. 비교·진단에서도 동일한 순수 계산을 재사용한다."""
    finite = valid.all(-1) & torch.isfinite(angles).all(-1)
    safe = torch.where(torch.isfinite(angles), angles, 0.)
    reference = angles.new_tensor(B_PREPARATION_ANGLES_DEGREES)*math.pi/180.
    band = angles.new_tensor([30., 10., 10.] if narrow else [30., 15., 15.])*math.pi/180.
    outside = torch.relu((safe-reference).abs()-band)
    quality = (1+outside.square().sum(-1)/math.radians(15. if narrow else 30.)**2).reciprocal()
    return dict(quality=torch.where(finite, quality, 0.), band_inside=finite & (outside == 0).all(-1))


def reward_configuration():
    """V5가 고정 사용하는 보상 정의를 기존 저장 계약과 같은 사전으로 반환한다."""
    profile = 'combined'
    enabled = dict(timing=True, posture=True, reach=True, alignment=True)
    return dict(schema='guitar_learning.compact_press_reward.v4', profile=profile,
        enabled=enabled,
        authority=dict(source='reward.compact_press_v4',
            selection='enabled flags select v4 changes; disabled components retain v3 formulas',
            inherited_role='inherited_v3_reference_only',
            overrides={
                'reward.surface_learning': ['timing', 'reach', 'alignment', 'invalid'],
                'reward.natural_preparation': ['timing', 'reach', 'alignment'],
                'reward.finger_posture': ['posture', 'timing'],
                'reward.finger_recovery': ['posture', 'timing'],
                'reward.simplified': ['timing', 'posture', 'reach', 'alignment'],
                'diagnostics.natural_preparation': ['diagnostics']}),
        fixed=dict(observation='compact_press_observation.v3', goal_dim=26,
            control='original position LH21 native range and4rad/s; no injected targets',
            first_contact_budget=.25, clean_hold_budget=1., achievement_budget=.25,
            wrong_budget=.15, performance_budget=.10, standby_rate_per_s=.02,
            thumb='unchanged', coordination='unchanged v3',
            gamma='unchanged configured surface_approach_gamma, default0.99',
            terminal_potential=0., positive_failure_tick='suppressed by existing completed control boundary'),
        timing=dict(enabled=enabled['timing'],
            gate='original score gate; first selected global earliest-press group protected from reset through own end',
            unchanged='original release grace, gap lead, fade, early goal exposure and2s lookahead',
            tracking='potential multiplied by1-final standby reward gate'),
        posture=dict(enabled=enabled['posture'], half_band_degrees=[30., 10., 10.],
            outside_scale_degrees=15., quality='1/(1+sum((outside/scale)^2))',
            budget='0.02/s mean4; maximum0.005/s per finger; no active posture cost'),
        reach=dict(enabled=enabled['reach'], quality='0.5*exp(-d/0.08)+0.5*exp(-d/0.03)',
            per_unweighted_target_potential_max=1., budget='bounded potential, not cumulative reward budget'),
        alignment=dict(enabled=enabled['alignment'],
            spacing='nearest adjacent physical string at selected fret-cell center y, projected in press plane perpendicular to target string',
            tolerance='min(0.003,spacing/4)', hover_height_m=[.004, .008],
            lateral_quality='1/(1+(relu(lateral-tolerance)/tolerance)^2)',
            near='clamp(1-lerp(hover_distance,surface_distance,descent_blend)/0.03,0,1)',
            factor='1-0.5*near*(1-lateral_quality)',
            unchanged='along-cell excess, normal factor and quintic descent blend; no hard gate'),
        invalid='nonfinite or invalid geometry has zero positive potential; never NaN multiplied by masked zero; baseline matches finite v3 inputs, invalid-zero is an intentional exception',
        diagnostics=dict(schema='guitar_learning.compact_press_diagnostics.v4',
            gate='actual standby_reward_gate; legacy score and original E4 gates separately recorded',
            sample_hz=240, reset='selected episode rows only; H32 boundary preserves statistics',
            alignment='hover-ready: valid target, height4..8mm, cell-along excess<=1e-6m, lateral<=profile tolerance, normal cosine>=0.1',
            angles='actual parent-child geometric flexion, degrees; not native MCP x/z coordinates',
            flags=dict(mcp_hyperextension='MCP<-20deg',
                mcp_dominance='MCP>60deg and PIP<45deg and DIP<30deg',
                dip_dominance='DIP-PIP>50deg'),
            phases='all, actual standby gate-weighted, pressing score interval, preparing exposed goal; may overlap',
            payment='legacy parent weighted_standby_reward uses actual failure-suppressed payout; opportunity is not paid reward'))


def improvement_configuration(profile):
    """실행 설정·저장 검증에 쓰는 독립된 JSON 가능 v5 계약을 반환한다."""
    if profile not in IMPROVEMENT_PROFILES:
        raise ValueError('지원하지 않는 압현 v5 improvement profile: '+str(profile))
    preparation = profile in ('preparation', 'combined')
    full_hold = profile in ('full_hold', 'combined')
    return dict(schema='guitar_learning.compact_press_reward.v5', profile=profile,
        base_reward_profile='combined',
        authority=dict(source='reward.compact_press_v5',
            inherited='reward.compact_press_v4 and inherited v3 descriptions are reference where overridden; other v4 combined components unchanged',
            overrides=['standby context observation', 'remaining note budget scale',
                'goal velocity meaning', 'target fret validation', 'preparation tracking factor',
                'required continuous hold', 'completion evaluation']),
        observation=dict(schema=OBSERVATION_SCHEMA, state_dim=464, pelvis_state_dim=473,
            goal_dim=26, slots=8,
            added_order=['actual_standby_gate4', 'next_press_delta_s4', 'next_press_valid4'],
            next_press='minimum strictly future press>score_time among actual recovery_mask, including unselected boundary notes',
            invalid_next_press='delta0 and valid0; active or first-protected state is represented by actual gate',
            next_press_scale='fixed max(full task duration_s,1) seconds; normalized clip[-10,10]',
            budget_scale='fixed0.25*full task target count, positive; not selected-view count; clip[-10,10]',
            velocity='negative physical chosen pad-point relative velocity in moving guitar frame; not exact derivative of nearest-point error',
            fret_range=[1, 14]),
        preparation=dict(enabled=preparation,
            factor='1-0.90*actual_standby_gate' if preparation else '1-actual_standby_gate',
            potential='same bounded v4 combined quality and gamma difference; no extra reward or control override'),
        full_hold=dict(enabled=full_hold, left_fraction=1. if full_hold else .4,
            required='full audible note duration D' if full_hold else 'min(D,max(0.05,0.4*D))',
            application='existing achievement latch/bonus and performance deficit settlement; budgets unchanged'),
        completion=dict(schema='guitar_learning.press_completion.v5',
            hold='existing v3 full-note and simultaneous strict holds preserved',
            release='original release_required; separate raw contact_loaded_target True-to-False latch in inclusive[end,end+0.1s]; legacy clean-candidate release ledger preserved',
            release_scope='loss of target pad geometry/facing/load candidate; not contact-pair separation, pressure or physical complete detachment; wrong-only changes do not count',
            exception='continuous same string/fret/finger next onset at current end does not require intermediate release, using original full-score release_required',
            statuses=['not_required', 'released', 'pending', 'missed', 'aborted'],
            success='safe complete selected timeline AND strict full hold AND every required release; no pending/aborted success'))


class CompactPressV5Environment(FingerSkillEnvironment):
    """464/473 상태·26필드 목표8개와33축 정책의 공용 GPU 압현 환경이다."""
    include_pelvis = False
    natural_preparation = dict(schema='guitar_learning.natural_preparation.v3', condition='E4')
    reward_profile = 'combined'
    improvement_profile = 'corrected'

    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        configuration = improvement_configuration(self.improvement_profile)
        if self.reward_profile != 'combined':
            raise ValueError('압현 v5는 v4 combined 보상을 기준으로 고정한다')
        fraction = song.get('left_fraction')
        if isinstance(fraction, bool) or fraction != configuration['full_hold']['left_fraction']:
            raise ValueError('압현 v5 프로필과 명시적 song.left_fraction이 일치해야 한다')
        self.v5_configuration = configuration
        configuration = reward_configuration()
        if song.get('finger_recovery', {}).get('standby_rate_per_s', .02) != .02:
            raise ValueError('압현 V5는0.02/s 대기 예산으로 고정한다')
        self.v4_configuration = configuration
        super().__init__(metadata, bundle=bundle, song=song, skill=skill, device=device, hand=hand)
        legacy = copy.deepcopy(self.contract['observation'])
        if legacy['dimension'] != 557 or legacy['event_dim'] != 24:
            raise ValueError('compact press requires the explicit557-state/24-event parent contract')
        self._legacy_fields = tuple(legacy['fields'])
        # 부모 _events는24필드로 계산하므로 기존 scale은 그 경로에 그대로 둔다.
        self.compact_event_scales = self._tensor(GOAL_SCALES)
        self._goal_columns = self._tensor(GOAL_COLUMNS, torch.long)
        fields, scales, blocks = [], [], {}

        def add(name, names, factors):
            start = len(fields)
            fields.extend(names)
            scales.extend(factors)
            blocks[name] = [start, len(fields)]

        def legacy_block(name, first, last):
            add(name, self._legacy_fields[first:last], legacy['scales'][first:last])

        legacy_block('joint_state', 0, 315)
        legacy_block('previous_left_action', 315, 348)
        legacy_block('guitar_in_pelvis', 354, 369)
        add('left_wrist_in_guitar', ['left_wrist_in_guitar.'+item for item in
            [*('p_'+a for a in 'xyz'), *('r'+str(i) for i in range(6)),
             *('v_'+a for a in 'xyz'), *('omega_'+a for a in 'xyz')]],
            [.5]*3+[1.]*6+[1.]*3+[10.]*3)
        legacy_block('contacts', 417, 427)
        legacy_block('reset_delta', 427, 439)
        add('finger_performance', ['finger_performance.'+finger+'.'+item
            for finger in ('index', 'middle', 'ring', 'pinky')
            for item in ('valid_clean', 'clean_streak_s')], [1., 2.]*4)
        add('wrist_guide', ['wrist_guide.'+item for item in
            ['valid', *('center_'+a for a in 'xyz'), *('half_width_'+a for a in 'xyz')]],
            [1.]+[.5]*3+[.1]*3)
        legacy_block('thumb_in_neck', 544, 552)
        add('finger_flexion', ['finger_flexion.'+finger+'.'+joint
            for finger in ('index', 'middle', 'ring', 'pinky') for joint in ('MCP', 'PIP', 'DIP')]
            +['finger_flexion.'+finger+'.valid' for finger in ('index', 'middle', 'ring', 'pinky')],
            [1.]*16)
        add('wrist_termination', list(WRIST_FIELDS), [1., 1.5, 3., .1])
        if self.include_pelvis:
            add('pelvis', ['pelvis.'+item+'_'+axis for item in
                ('gravity', 'origin_velocity', 'angular_velocity') for axis in 'xyz'],
                [1.]*6+[10.]*3)
        observation = copy.deepcopy(legacy)
        observation.update(dimension=len(fields), fields=fields, scales=scales,
            capacity=0, event_dim=26, event_fields=list(GOAL_FIELDS)+list(ADDED_GOAL_FIELDS),
            event_scales=list(GOAL_SCALES)+list(ADDED_GOAL_SCALES),
            priority_slots=8,
            compact_press=dict(schema=OBSERVATION_SCHEMA, include_pelvis=self.include_pelvis,
                blocks=blocks, legacy_state_dimension=legacy['dimension'],
                priority_order='index tracking,next; middle tracking,next; ring tracking,next; pinky tracking,next',
                goals='16 fields; normalized string/6,fret/14,finger/4; invalid slots all zero',
                wrist='left wrist origin in moving guitar coordinates; rotation first two matrix columns',
                flexion='actual geometric angle/(pi/2); invalid finger angles zero; validity4',
                performance='audible clean candidate and uninterrupted audible clean seconds; interleaved per finger',
                guide_valid='finite ordered source wrist track exists, including idle time; not target-valid flag',
                pelvis='optional local unit gravity, body-origin linear velocity and angular velocity',
                general_events='empty; only eight finger tracking/next slots'))
        # 새 입력에서는 과거 전곡 수행 요약이나 sin/cos가 있다고 오해하지 않도록
        # 해당 관측 설명만 제거한다. 보상·종료 계약은 수정하지 않는다.
        for key in ('first_contact', 'finger_posture', 'surface_geometry', 'proxy_scope'):
            observation.pop(key, None)
        self.contract['observation'] = observation
        validate_assignments(self.task.targets)
        observation = self.contract['observation']
        start = observation['dimension']
        added_scales = [.25]*3+[self.task.duration_s, 1., 4., 1., 2., 2.]
        observation['fields'] += list(ADDED_STATE_FIELDS)
        observation['scales'] += added_scales
        observation['dimension'] += 9
        compact = observation['compact_press']
        compact.update(
            goals='26 fields; original16 plus10 note-progress fields; invalid slots all zero',
            goal_progress='original16 plus contact_streak, contact_progress, legacy left latch, best_clean_streak, missing, performance_paid/settled, required, duration, selected weight; invalid slots zero',
            coordination='audible constant-target sections with >=2 selected targets; no-target/single all four fields zero',
            remaining_budget='same remaining_negative_budget as terminal failure cost, before base/time cost',
            strict_success='selected full audible note streaks and each constant-target overlap section full streak; legacy40% achievements retained separately')
        compact['blocks']['v3_state'] = [start, start+9]
        # 공용 부모의24필드, 표면16필드, 추가 진행10필드의 척도를 구분한다.
        self.progress_goal_scales = self._tensor(ADDED_GOAL_SCALES)
        coordination = dict(schema='guitar_learning.press_coordination.v3', individual_hold_fraction=.5,
            overlap='exact240Hz interval intersection with audible constant selected-target sets',
            hold='single unchanged; overlap0.5*sum(w_i/D_i*clean_i)+0.5*sum(w_i/D_i)*all_clean',
            budget='all-clean receives the original total hold budget; no added positive bonus',
            clean='both measured endpoints candidate and not wrong; strict section streak also requires safe endpoints',
            strict='each selected best_clean_streak>=full note duration and each overlap-section best>=section duration; tolerance1e-9 only',
            scope='source surface geometry and resultant body load, not calibrated pressure or acoustic success')
        self.contract['reward']['press_coordination'] = copy.deepcopy(coordination)
        self.contract['reward']['surface_learning']['hold'] = coordination['hold']
        self.contract['reward']['surface_learning']['observation'] = (
            str(observation['dimension'])+'state/26event/8priority; positive pad geometry unchanged; wrong_press_sources.v3; observable v3 budget and coordination state')
        self.contract['diagnostics']['press_coordination'] = copy.deepcopy(coordination)

        self.contract['reward']['compact_press_v4'] = copy.deepcopy(configuration)
        self.contract['diagnostics']['compact_press_v4'] = copy.deepcopy(configuration['diagnostics'])
        # 기존 저장본의 설명 키와 진단 schema는 유지한다. 아래 표시는
        # 관측·보상 계산에 사용하지 않으며 실제 수식의 기준을 명시한다.
        for path in configuration['authority']['overrides']:
            section, name = path.split('.')
            self.contract[section][name].update(
                v4_description_role=configuration['authority']['inherited_role'],
                v4_authoritative_contract=configuration['authority']['source'])
        configuration = self.v5_configuration
        if not self.M or bool(((self.fret < 1) | (self.fret > 14)).any()):
            raise ValueError('압현 v5 목표는1~14프렛의 비어 있지 않은 악보여야 한다')
        observation = self.contract['observation']
        start = observation['dimension']
        fingers = ('index', 'middle', 'ring', 'pinky')
        observation['fields'] += ['preparation_context.'+finger+'.'+item
            for item in ('actual_standby_gate', 'next_press_delta_s', 'next_press_valid') for finger in fingers]
        self.next_press_scale_s = max(float(self.task.duration_s), 1.)
        observation['scales'] += [1.]*4+[self.next_press_scale_s]*4+[1.]*4
        observation['dimension'] += 12
        budget_index = observation['fields'].index('episode.remaining_negative_note_budget')
        observation['scales'][budget_index] = .25*self.M
        observation['event_fields'][9:12] = ['negative_pad_relative_velocity_'+axis for axis in 'xyz']
        observation['compact_press'].update(schema=OBSERVATION_SCHEMA,
            goal_velocity=configuration['observation']['velocity'],
            strict_success='selected full audible note and overlap-section holds; configured achievement threshold: '+
                configuration['full_hold']['required']+'; release is evaluated separately under press_completion',
            goal_progress=observation['compact_press']['goal_progress'].replace(
                'legacy left latch', 'configured-threshold left latch'),
            preparation_context=copy.deepcopy(configuration['observation']))
        observation['compact_press']['blocks']['v5_preparation_context'] = [start, start+12]
        self.contract['compact_press'] = dict(schema=OBSERVATION_SCHEMA, include_pelvis=self.include_pelvis)
        self.scales = self._tensor(observation['scales'])
        self.contract['reward']['schema'] = configuration['schema']
        self.contract['reward']['compact_press_v5'] = copy.deepcopy(configuration)
        self.contract['reward']['v5_authority'] = copy.deepcopy(configuration['authority'])
        self.contract['diagnostics']['press_completion_v5'] = copy.deepcopy(configuration['completion'])

    @staticmethod
    def _rotation6(quaternion):
        """회전행렬의 첫 두 열을 xyz 순서로 연결한다."""
        axes = quaternion.new_tensor([[1., 0., 0.], [0., 1., 0.]])
        return apply(quaternion[:, None], axes[None]).flatten(1)

    def _compact_state(self, state):
        """부모가 계산한 비정규화552 상태에서 필요한 항목만 조립한다."""
        guitar = self.guitar_body
        wrist = self.body[:, self.proxy_indices[0]]
        p, v = relative_point(wrist[:, :3], origin_velocity(wrist, self.com[self.proxy_indices[0]]),
                              guitar, self.com[self.guitar_index])
        orientation = multiply(conjugate(guitar[:, 3:7]), wrist[:, 3:7])
        omega = apply(conjugate(guitar[:, 3:7]), wrist[:, 10:13]-guitar[:, 10:13])
        now = self._score_time()
        selection = self._finger_targets(now)
        indices = selection['indices'][..., 0].clamp_min(0)
        rows = torch.arange(self.N, device=self.device)[:, None]
        audible = (self.onset[indices] <= now[:, None]) & (now[:, None] < self.end[indices])
        clean = selection['valid'][..., 0] & audible & self.candidate[rows, indices] & ~self.wrong[rows, indices]
        streak = torch.where(clean, self.note['clean_streak'][rows, indices], 0.)
        performance = torch.stack((clean, streak), -1).flatten(1)
        lower, upper = self.guide['lower_G_m'], self.guide['upper_G_m']
        guide_valid = torch.isfinite(lower).all(-1) & torch.isfinite(upper).all(-1) & (lower <= upper).all(-1)
        guide = torch.cat((guide_valid[:, None], (lower+upper)/2, (upper-lower)/2), -1)
        guide = torch.where(guide_valid[:, None], guide, 0.)
        # 부모의 실제 마디 회전으로 산출한 sin/cos를 같은 각도 하나로 바꾼다.
        trig = state[:, 512:536].reshape(self.N, 4, 3, 2)
        valid = state[:, 536:540]
        angle = torch.atan2(trig[..., 0], trig[..., 1])/(math.pi/2)
        angle = torch.where(valid[..., None].bool(), angle, 0.)
        timers = torch.stack((self.wrist_active.double(), self.wrist_elapsed,
            (3.-self._local_time()).clamp_min(0), self.wrist_severe_elapsed), -1)
        parts = [state[:, :315], state[:, 315:348], state[:, 354:369],
                 torch.cat((p, self._rotation6(orientation), v, omega), -1),
                 state[:, 417:427], state[:, 427:439], performance, guide,
                 state[:, 544:552], angle.flatten(1), valid, timers]
        if self.include_pelvis:
            pelvis = self.body[:, self.pelvis_index]
            inverse = conjugate(pelvis[:, 3:7])
            gravity = apply(inverse, pelvis.new_tensor([0., 0., -1.]))
            velocity = apply(inverse, origin_velocity(pelvis, self.com[self.pelvis_index]))
            angular = apply(inverse, pelvis[:, 10:13])
            parts.extend((gravity, velocity, angular))
        return torch.cat([item.float() for item in parts], -1)

    def _surface_events(self):
        """기존 목표 선택·기하를 재사용하고 새16필드의 정규화만 적용한다."""
        _, _, priority, valid = super()._events()
        raw = priority*self.event_scales
        goals = (raw.index_select(-1, self._goal_columns)/self.compact_event_scales).clamp(-10, 10)
        goals = torch.where(valid[..., None], goals, 0.)
        return (goals.new_zeros(self.N, 0, 16),
                torch.zeros(self.N, 0, dtype=torch.bool, device=self.device), goals, valid)

    def _allocate(self, count):
        super()._allocate(count)
        size = max(1, len(audible_sections(self.task.targets, [True]*self.M)))
        self.coordination_groups = [[] for _ in range(count)]
        self.coordination_mask = torch.zeros(count, size, self.M, dtype=torch.bool, device=self.device)
        self.coordination_rates = torch.zeros(count, size, self.M, device=self.device)
        self.coordination_valid = torch.zeros(count, size, dtype=torch.bool, device=self.device)
        self.coordination_start = torch.zeros(count, size, dtype=torch.float64, device=self.device)
        self.coordination_end = self.coordination_start.clone()
        self.coordination_values = {name: self.coordination_start.clone()
                                    for name in ('observed', 'clean', 'streak', 'best')}
        self.v4_stats = {name: torch.zeros(count, 4, dtype=torch.float64, device=self.device)
            for name in ('observed_s', 'legacy_score_gate_s', 'legacy_e4_gate_s', 'actual_gate_s',
                         'legacy_e4_blocked_s', 'final_blocked_s', 'eligible_s', 'quality_integral',
                         'raw_standby_reward', 'valid_geometry_s', 'target_exposed_s',
                         'aligned_s', 'distance_integral_m_s', 'lateral_tolerance_integral_m_s',
                         'height_integral_m_s', 'lateral_integral_m_s', 'along_excess_integral_m_s',
                         'normal_cos_integral_s',
                         'preparing_s', 'audible_s', 'candidate_s')}
        self.v4_shape = torch.zeros(count, 4, 4, 3, dtype=torch.float64, device=self.device)
        self.v4_phase = torch.zeros(count, 4, 4, dtype=torch.float64, device=self.device)
        self.v5_released = torch.zeros(count, self.M, dtype=torch.bool, device=self.device)
        self.v5_release_s = torch.zeros(count, self.M, dtype=torch.float64, device=self.device)

    def _reset_scope(self, indices):
        super()._reset_scope(indices)
        for value in (self.coordination_mask, self.coordination_rates, self.coordination_valid,
                      self.coordination_start, self.coordination_end, *self.coordination_values.values()):
            value[indices] = 0
        for index in indices.cpu().tolist():
            sections = audible_sections(self.task.targets, self.focus_mask[index].cpu().tolist())
            self.coordination_groups[index] = sections
            for slot, section in enumerate(sections):
                self.coordination_valid[index, slot] = True
                self.coordination_start[index, slot] = section['start_s']
                self.coordination_end[index, slot] = section['end_s']
                targets = list(section['target_indices'])
                self.coordination_mask[index, slot, targets] = True
                self.coordination_rates[index, slot, targets] = (
                    self.finger_weights[index, targets]/(self.end-self.onset)[targets]).float()
        for value in (*self.v4_stats.values(), self.v4_shape, self.v4_phase):
            value[indices] = 0
        self.v5_released[indices] = False
        self.v5_release_s[indices] = 0.

    def _coordination_safe(self):
        failed = self.invalid | self.failure.any(-1) | self.wrist_failure | self.wrist_severe_failure | self.control_invalid
        if self._substeps is not None:
            failed |= self.tick_failure.any(-1)
        return ~failed

    def substep(self, snapshot):
        loaded_before = self.contact_loaded_target.clone()
        before = self._score_time().clone()
        before_clean = self.candidate & ~self.wrong
        before_safe = self._coordination_safe()
        super().substep(snapshot)
        now = self._score_time()
        clean = before_clean & self.candidate & ~self.wrong
        all_clean = (~self.coordination_mask | clean[:, None]).all(-1)
        dt = (torch.minimum(now[:, None], self.coordination_end)-
              torch.maximum(before[:, None], self.coordination_start)).clamp_min(0)*self.coordination_valid
        # 부모의 원시계수2·최종계수0.5는 유지한다. 일부만 clean이면 절반을
        # 차감하고, 전원 clean이면 원래 예산을 그대로 지급한다.
        individual = torch.bmm(self.coordination_rates, clean.float()[..., None]).squeeze(-1)
        self.terms['song_clean_hold'] -= (dt*individual*~all_clean).sum(-1).float()
        together = all_clean & before_safe[:, None] & self._coordination_safe()[:, None]
        values = self.coordination_values
        values['observed'] += dt
        values['clean'] += dt*together
        values['streak'] = torch.where(dt > 0,
            torch.where(together, values['streak']+dt, 0.), values['streak'])
        values['best'] = torch.maximum(values['best'], values['streak'])
        now = self._score_time()[:, None]
        # clean후보는 오압현만 생겨도 사라진다. 실제 분리가 아니라 원래 패드의
        # 기하·법선·하중 후보 소실을 별도로 보아 wrong-only 해제를 배제한다.
        lost = loaded_before & ~self.contact_loaded_target & self.focus_mask & ~self.v5_released
        lost &= (now >= self.end) & (now <= self.end+.1)
        self.v5_released |= lost
        self.v5_release_s = torch.where(lost, now, self.v5_release_s)

    def _coordination_state(self):
        now = self._score_time()[:, None]
        current = self.coordination_valid & (self.coordination_start <= now) & (now < self.coordination_end)
        selected = current.to(torch.long).argmax(-1)
        rows = torch.arange(self.N, device=self.device)
        mask = self.coordination_mask[rows, selected]
        all_clean = (~mask | (self.candidate & ~self.wrong)).all(-1) & self._coordination_safe()
        values = torch.stack((mask.sum(-1), all_clean,
            self.coordination_values['streak'][rows, selected],
            self.coordination_end[rows, selected]-now[:, 0]), -1)
        return torch.where(current.any(-1)[:, None], values, 0.)

    def _observation_state(self, state):
        original = self._compact_state(state)
        remaining = (self._episode_duration()-self._local_time()).clamp_min(0)
        budget = remaining_negative_budget(self._score_time(), self.onset, self.end,
            self.finger_weights, self.focus_mask, self.note['performance_paid'], self.note['performance_settled'])
        progress = torch.cat((original, self.loss, remaining[:, None].float(), budget[:, None].float(),
                          self._coordination_state().float()), -1)
        return torch.cat((progress, self._preparation_context()), -1)

    def _events(self):
        _, _, original, valid = self._surface_events()
        selected = self._finger_targets(self._score_time())['indices'].flatten(1).clamp_min(0)
        raw = torch.stack((self.note['contact_streak'], self.note['contact_progress'], self.note['left'],
            self.note['best_clean_streak'], self.note['missing'], self.note['performance_paid'],
            self.note['performance_settled'], self.required.expand(self.N, -1),
            (self.end-self.onset).expand(self.N, -1), self.finger_weights), -1)
        extra = raw.gather(1, selected[..., None].expand(-1, -1, 10))/self.progress_goal_scales
        extra = torch.where(valid[..., None], extra.clamp(-10, 10), 0.).float()
        goals = torch.cat((original, extra), -1)
        return goals.new_zeros(self.N, 0, 26), valid[:, :0], goals, valid

    def _finger_preparation(self, now):
        posture = super()._finger_preparation(now)
        legacy = posture['gate']
        old_e4 = posture.get('standby_reward_gate', legacy)
        gate = old_e4
        first = self.press.expand(self.N, -1).masked_fill(~self.focus_mask, torch.inf).amin(-1)
        first_notes = self.focus_mask & (self.press[None] == first[:, None])
        protected = ((first_notes & (now[:, None] <= self.end))[:, None] &
                     self.preparation_assignment[None]).any(-1)
        gate = torch.where(protected, 0., legacy)
        posture.update(standby_posture_quality(posture['angles'], posture['valid']))
        quality = posture['quality']
        good = torch.isfinite(quality) & torch.isfinite(gate) & posture['valid'].all(-1)
        quality = torch.where(good, quality, 0.)
        gate = torch.where(torch.isfinite(gate), gate, 0.)
        posture.update(legacy_score_gate=legacy, legacy_e4_gate=old_e4,
            standby_reward_gate=gate, quality=quality)
        posture['per_finger_rate'] = .02*gate*quality/4
        posture['rate'] = posture['per_finger_rate'].sum(-1)
        posture['tracking_weight'] = 1-gate
        return posture

    def _lateral_tolerance(self, selected):
        """선택 프렛의 y에서 이웃한 실제 현 사이의 접선 간격을 구한다."""
        string = self.string[selected]
        line = self.ends-self.starts
        y = self.goals.gather(1, selected[..., None].expand(-1, -1, 3))[..., 1]
        fraction = (y[..., None]-self.starts[:, None, :, 1])/line[:, None, :, 1]
        points = self.starts[:, None]+fraction[..., None]*line[:, None]
        own = points.gather(2, string[..., None, None].expand(-1, -1, 1, 3)).squeeze(2)
        direction = line.gather(1, string[..., None].expand(-1, -1, 3))
        normal = self.press_plane[:3]
        normal = normal/torch.linalg.vector_norm(normal).clamp_min(1e-12)
        direction = direction-(direction*normal).sum(-1, keepdim=True)*normal
        direction = direction/torch.linalg.vector_norm(direction, dim=-1, keepdim=True).clamp_min(1e-12)
        delta = points-own[:, :, None]
        delta = delta-(delta*normal).sum(-1, keepdim=True)*normal
        lateral = delta-(delta*direction[:, :, None]).sum(-1, keepdim=True)*direction[:, :, None]
        neighbor = (torch.arange(6, device=self.device)[None, None]-string[..., None]).abs() == 1
        spacing = torch.linalg.vector_norm(lateral, dim=-1).masked_fill(~neighbor, torch.inf).amin(-1)
        return (spacing/4).clamp_max(.003)

    def _natural_state(self, now):
        state = super()._natural_state(now)
        tolerance = self._lateral_tolerance(state['selected'])
        height_error = torch.relu(.004-state['height'])+torch.relu(state['height']-.008)
        distance = torch.sqrt(state['along'].square()+torch.relu(state['lateral']-tolerance).square()+height_error.square())
        finite = torch.isfinite(tolerance) & (tolerance > 1e-8)
        state.update(distance=distance, lateral_tolerance=tolerance,
            valid=state['valid'] & finite,
            ready=state['valid'] & finite & (state['height'] >= .004) & (state['height'] <= .008) &
                (state['lateral'] <= tolerance) & (state['along'].abs() <= 1e-6) & (state['alignment'] >= .1))
        return state

    def _diagnose_posture(self, posture, pressing, now):
        # 관측용 score gate를 바꾸지 않고, 진단에만 실제 지급 gate를 전달한다.
        actual = posture['standby_reward_gate']
        measured = actual_reward_posture(posture)
        super()._diagnose_posture(measured, pressing, now)
        values = self.v4_stats
        dt = 1/240.
        legacy, old_e4 = posture['legacy_score_gate'], posture['legacy_e4_gate']
        values['observed_s'] += dt
        for key, value in (('legacy_score_gate_s', legacy), ('legacy_e4_gate_s', old_e4),
            ('actual_gate_s', actual), ('legacy_e4_blocked_s', (legacy-old_e4).clamp_min(0)),
            ('final_blocked_s', (legacy-actual).clamp_min(0)), ('eligible_s', actual > 0),
            ('quality_integral', actual*posture['quality']), ('raw_standby_reward', posture['per_finger_rate'])):
            values[key] += value.double()*dt
        state = self._natural_state(now)
        valid = state['valid']
        for key in ('distance', 'lateral', 'height', 'along', 'alignment'):
            valid = valid & torch.isfinite(state[key])
        selected = state['selected']
        tolerance = state.get('lateral_tolerance', torch.full_like(state['distance'], .003))
        for key, value in (('valid_geometry_s', valid), ('target_exposed_s', state['valid']),
            ('aligned_s', valid & state['ready']),
            ('distance_integral_m_s', torch.where(valid, state['distance'], 0.)),
            ('lateral_tolerance_integral_m_s', torch.where(valid, tolerance, 0.)),
            ('height_integral_m_s', torch.where(valid, state['height'], 0.)),
            ('lateral_integral_m_s', torch.where(valid, state['lateral'], 0.)),
            ('along_excess_integral_m_s', torch.where(valid, state['along'].abs(), 0.)),
            ('normal_cos_integral_s', torch.where(valid, state['alignment'], 0.)),
            ('preparing_s', state['valid'] & (now[:, None] < self.press[selected])),
            ('audible_s', state['valid'] & (self.onset[selected] <= now[:, None]) & (now[:, None] < self.end[selected])),
            ('candidate_s', state['valid'] & self.candidate.gather(1, selected))):
            values[key] += value.double()*dt
        angle = posture['angles']*180/math.pi
        finite = posture['valid'].all(-1) & torch.isfinite(angle).all(-1)
        flags = geometric_posture_flags(posture['angles'], posture['valid'])
        preparing = state['valid'] & (now[:, None] < self.press[selected])
        phases = torch.stack((torch.ones_like(actual), actual, pressing, preparing), -1)
        phases = torch.where(finite[..., None], phases, 0.).double()
        self.v4_phase += phases*dt
        self.v4_shape += phases[..., None]*flags[:, :, None].double()*dt

    def _preparation_context(self):
        now = self._score_time()
        gate = self._finger_preparation(now)['standby_reward_gate']
        owned = self.preparation_assignment[None] & self.recovery_mask[:, None]
        future = owned & (self.press[None, None] > now[:, None, None])
        next_press = self.press.expand(self.N, 4, self.M).masked_fill(~future, torch.inf).amin(-1)
        valid = torch.isfinite(next_press)
        delta = torch.where(valid, next_press-now[:, None], 0.)
        return torch.cat((gate.double(), delta, valid.double()), -1).float()

    def _surface_potential(self):
        state = self._natural_state(self._score_time())
        selected = state['selected']
        surface = self.surface_distance.gather(1, selected)
        hover, normal, blend = state['distance'], state['alignment'], state['blend']
        valid = state['valid'] & torch.isfinite(surface) & torch.isfinite(hover)
        valid &= torch.isfinite(normal) & torch.isfinite(blend) & (surface >= 0) & (hover >= 0)
        surface, hover, normal = [torch.where(valid, value, 0.) for value in (surface, hover, normal)]
        blend = torch.where(valid, blend, 0.).to(surface.dtype)

        def quality(distance):
            return (.5*torch.exp(-distance/.08)+.5*torch.exp(-distance/.03))*(
                1-.2*(1-distance/.02).clamp(0, 1)*(1-normal))

        value = torch.lerp(quality(hover), quality(surface), blend)
        tolerance, lateral = state['lateral_tolerance'], state['lateral']
        finite = torch.isfinite(tolerance) & (tolerance > 1e-8) & torch.isfinite(lateral)
        tolerance = torch.where(finite, tolerance, 1.)
        lateral = torch.where(finite, lateral, 0.)
        lateral_quality = (1+(torch.relu(lateral-tolerance)/tolerance).square()).reciprocal()
        distance = torch.lerp(hover, surface, blend)
        value *= 1-.5*(1-distance/.03).clamp(0, 1)*(1-lateral_quality)
        gate = self._finger_preparation(self._score_time())['standby_reward_gate']
        coefficient = .90 if self.v5_configuration['preparation']['enabled'] else 1.
        value *= 1-coefficient*gate
        weight = self._selected_finger_weights(selected)
        valid &= finite & torch.isfinite(weight)
        return (torch.where(valid, weight, 0.)*torch.where(valid, value, 0.)).sum(-1).to(self.surface_distance.dtype)

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        song = result['song']
        song['legacy_stage_success'] = song['stage_success']
        song['legacy_provisional_success'] = song['provisional_success']
        selected = self.focus_mask[index]
        note_ok = self.note['best_clean_streak'][index]+1e-9 >= self.end-self.onset
        notes_succeeded = bool(selected.any() and note_ok[selected].all())
        groups = []
        for slot, section in enumerate(self.coordination_groups[index]):
            length = section['end_s']-section['start_s']
            values = {name: float(value[index, slot]) for name, value in self.coordination_values.items()}
            groups.append(dict(target_ids=[self.task.targets[target].target_id for target in section['target_indices']],
                start_s=section['start_s'], end_s=section['end_s'], duration_s=length,
                observed_s=values['observed'], clean_s=values['clean'],
                clean_fraction=min(1., values['clean']/length), longest_clean_s=values['best'],
                strict_success=values['observed']+1e-9 >= length and values['best']+1e-9 >= length))
        groups_ok = all(section['strict_success'] for section in groups)
        safe = not bool(self.invalid[index]) and not failed
        full = bool(result['left_curriculum']['full_safe'])
        strict = full and notes_succeeded and groups_ok
        provisional = safe and notes_succeeded and groups_ok
        song.update(stage_success=strict, provisional_success=provisional,
            strict_note_success_count=int((note_ok & selected).sum()),
            strict_group_success_count=sum(section['strict_success'] for section in groups),
            strict_group_count=len(groups))
        duration = sum(section['duration_s'] for section in groups)
        clean = sum(section['clean_s'] for section in groups)
        notes = [dict(target_id=target.target_id, onset_s=target.onset_s, end_s=target.end_s,
            duration_s=target.end_s-target.onset_s,
            best_clean_streak_s=float(self.note['best_clean_streak'][index, number]),
            strict_success=bool(note_ok[number]))
            for number, target in enumerate(self.task.targets) if bool(selected[number])]
        result['press_coordination'] = dict(schema='guitar_learning.press_coordination.v3',
            success=strict, strict_notes_success=notes_succeeded, strict_groups_success=groups_ok,
            overlap_duration_s=duration, simultaneous_clean_s=clean,
            simultaneous_clean_fraction=clean/duration if duration else 0.,
            longest_simultaneous_clean_s=max([section['longest_clean_s'] for section in groups]+[0.]),
            notes=notes, groups=groups, full_safe=full,
            scope='selected complete audible notes and constant-target overlap sections; source pad geometry and resultant load only; no acoustic success')
        result['musical_quality'].update(stage_success=strict, provisional_success=provisional,
                                         song=copy.deepcopy(song))

        stats = {name: value[index].cpu().tolist() for name, value in self.v4_stats.items()}
        valid = self.v4_stats['valid_geometry_s'][index]
        distance = self.v4_stats['distance_integral_m_s'][index]
        stats['mean_hover_distance_m'] = torch.where(valid > 0, distance/valid.clamp_min(1e-12), 0.).cpu().tolist()
        for output, source in (('mean_height_m', 'height_integral_m_s'),
            ('mean_lateral_m', 'lateral_integral_m_s'), ('mean_along_excess_m', 'along_excess_integral_m_s'),
            ('mean_normal_cos', 'normal_cos_integral_s')):
            value = self.v4_stats[source][index]
            stats[output] = torch.where(valid > 0, value/valid.clamp_min(1e-12), 0.).cpu().tolist()
        result['compact_press_v4'] = dict(schema='guitar_learning.compact_press_diagnostics.v4',
            profile=self.reward_profile, fingers=['index', 'middle', 'ring', 'pinky'],
            values=stats, phase_names=['all', 'standby_gate_weighted', 'pressing', 'preparing'],
            phase_valid_s=self.v4_phase[index].cpu().tolist(),
            shape_names=['mcp_hyperextension', 'mcp_dominance', 'dip_dominance'],
            shape_seconds=self.v4_shape[index].cpu().tolist(),
            actual_paid_standby=result['left_episode_diagnostics']['standby']['weighted_standby_reward'],
            scope='240Hz completed endpoints; opportunities are not received payout; geometric diagnostics only')

        now = float(self._score_time()[index])
        safe = not failed and not bool(self.invalid[index]) and bool(self._coordination_safe()[index])
        timeline = float(self._local_time()[index])+1e-9 >= float(self._episode_duration()[index])
        full = safe and timeline
        # 종료된 한 행만 일괄 복사하여 목표마다 GPU 동기화를 반복하지 않는다.
        selected = self.focus_mask[index].cpu().tolist()
        required_values = self.release_required.cpu().tolist()
        released_values = self.v5_released[index].cpu().tolist()
        release_times = self.v5_release_s[index].cpu().tolist()
        legacy_released = self.note['released'][index].cpu().tolist()
        notes = []
        for number, target in enumerate(self.task.targets):
            if not selected[number]:
                continue
            required, released = required_values[number], released_values[number]
            timestamp = release_times[number]
            valid_release = released and target.end_s-1e-12 <= timestamp <= target.end_s+.1+1e-12
            if not required:
                status = 'not_required'
            elif valid_release:
                status = 'released'
            elif not safe:
                status = 'aborted'
            elif now+1e-12 < target.end_s+.1:
                status = 'pending'
            else:
                status = 'missed'
            notes.append(dict(target_id=target.target_id, release_required=required,
                release_status=status, release_s=timestamp if released else None,
                legacy_clean_release=legacy_released[number],
                release_deadline_s=target.end_s+.1))
        release_satisfied = bool(notes) and all(note['release_status'] in ('released', 'not_required') for note in notes)
        hold = result['press_coordination']
        hold_satisfied = hold['strict_notes_success'] and hold['strict_groups_success']
        result['press_completion'] = dict(schema='guitar_learning.press_completion.v5',
            safe=safe, timeline_complete=timeline, hold_satisfied=bool(hold_satisfied),
            full_hold_success=bool(full and hold_satisfied), release_satisfied=release_satisfied,
            release_success=bool(full and release_satisfied),
            completion_success=bool(full and hold_satisfied and release_satisfied), notes=notes,
            counts={status: sum(note['release_status'] == status for note in notes)
                    for status in self.v5_configuration['completion']['statuses']})
        return result
