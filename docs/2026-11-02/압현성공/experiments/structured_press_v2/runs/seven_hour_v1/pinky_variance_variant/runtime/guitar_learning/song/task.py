"""악보 목표·전곡 일정·손목 안내를 같은 과제 단위로 구성한다.

읽는 순서:
1. ScoreTarget과 ScoreTask에서 음표 자료형·토큰·시간 기준을 확인한다.
2. MusicLedger에서 목표별 접촉 유지·타격·해제 기록을 읽는다.
3. SongTask와 make_task에서 전체 원 음표와 오디오 시계의 일정을 읽는다.
4. load_anchor_track과 WristGuide에서 준비 자세 기준의 손목 안내를 읽는다.

접촉 적격성은 호출자가 측정한다. 손목 안내는 부드러운 자세 기준이며
현 압력·소리 생성·음악 성공을 보장하지 않는다.
"""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import wave

from guitar_learning.score.canonical import load_music_task

# ── 음표 자료형과 과제 관측·이력 ──

EVENT_FIELDS = ('onset_delta_s', 'end_delta_s', 'press_delta_s', 'string_1based',
                'fret', 'finger', 'direction', 'current', 'preparing',
                'matched_50', 'matched_100', 'continuous_dwell_s',
                'held_s', 'hold_fraction', 'released', 'release_delta_s',
                'delta_x', 'delta_y', 'delta_z', 'velocity_x', 'velocity_y',
                'velocity_z', 'strict_deadline_delta_s', 'lenient_deadline_delta_s')
EVENT_DIM = len(EVENT_FIELDS)
STATE_FIELDS = ('remaining_s', 'strict_matches', 'lenient_matches', 'target_count',
                'held_total_s', 'released_count', 'nearest_strict_deadline_s',
                'elapsed_s')
STATE_DIM = len(STATE_FIELDS)


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be finite')
    return float(value)


@dataclass(frozen=True)
class ScoreTarget:
    target_id: str
    event_id: str
    string: int  # 시뮬레이터의 표준 현 번호: 0=높은 e현 ... 5=낮은 E현
    fret: int
    finger: int
    direction: int
    onset_s: float
    end_s: float
    press_s: float
    source_onset_s: float
    source_end_s: float


@dataclass(frozen=True)
class ScoreTask:
    targets: tuple
    lookahead_s: float = 2.0
    capacity: int = 64
    provenance: object = None

    def __post_init__(self):
        if finite(self.lookahead_s, 'lookahead_s') <= 0:
            raise ValueError('lookahead_s must be positive')
        if isinstance(self.capacity, bool) or not isinstance(self.capacity, int) or self.capacity < 1:
            raise ValueError('capacity must be positive integer')
        if not self.targets or len({t.target_id for t in self.targets}) != len(self.targets):
            raise ValueError('targets must be nonempty with unique IDs')
        for t in self.targets:
            for name in ('onset_s', 'end_s', 'press_s', 'source_onset_s', 'source_end_s'):
                finite(getattr(t, name), name)
            if not 0 <= t.press_s <= t.onset_s <= t.end_s or t.source_end_s < t.source_onset_s:
                raise ValueError(f'invalid target timing: {t.target_id}')
            if (type(t.string) is not int or not 0 <= t.string < 6 or
                    type(t.fret) is not int or not 0 <= t.fret <= 22 or
                    type(t.finger) is not int or t.finger not in ((0,) if t.fret == 0 else (1, 2, 3, 4)) or
                    type(t.direction) is not int or t.direction not in (-1, 1)):
                raise ValueError(f'invalid target mapping: {t.target_id}')
        for i, t in enumerate(self.targets):
            for other in self.targets[i+1:]:
                if (t.string == other.string and (t.fret, t.finger) != (other.fret, other.finger)
                        and max(t.onset_s, other.onset_s) < min(t.end_s, other.end_s)):
                    raise ValueError('conflicting audible targets on one string')

    @classmethod
    def from_bundle(cls, bundle_root, *, stage='B', start_event_index=0,
                    phrase_events=8, tempo_scale=1.0, preroll_s=1.0,
                    lookahead_s=2.0, capacity=64):
        # 불변 변환기와 출처를 재사용한다. 여기서는 연속된 이벤트를 명시적으로
        # 선택하며 지원하지 않는 이벤트를 걸러내지 않고 오류로 처리한다.
        source = load_music_task(bundle_root, stage='B', tempo_scale=tempo_scale,
                                 preroll_s=preroll_s)
        if stage not in ('B', 'C', 'D', 'full'):
            raise ValueError('stage must be B, C, D, or full')
        count = {'B': 1, 'C': 2, 'D': phrase_events, 'full': len(source.timeline.events)}[stage]
        if type(count) is not int or count < 1 or type(start_event_index) is not int or start_event_index < 0:
            raise ValueError('invalid event selection')
        selected = source.timeline.events[start_event_index:start_event_index + count]
        if len(selected) != count:
            raise ValueError('selected interval exceeds timeline')
        unsupported = [e.event_id for e in selected if not e.supported]
        if unsupported:
            raise ValueError(f'unsupported selected event IDs: {unsupported}')
        if stage == 'B' and (len(selected[0].string_targets) != 1 or selected[0].string_targets[0].fret == 0):
            raise ValueError('B requires explicitly selected single fretted event')
        origin = min(t.press_start_s if t.press_start_s is not None else t.note_on_s for e in selected for t in e.string_targets)
        convert = lambda value: preroll_s + (value - origin) / tempo_scale
        targets = []
        for event in selected:
            for t in event.string_targets:
                onset = event.score_time_s + t.traversal_offset_s
                end = min(t.sustain_until_s, t.release_s if t.release_s is not None else t.sustain_until_s)
                targets.append(ScoreTarget(f'{event.event_id}/string-{t.string + 1}/note-{t.mapping_note_index}',
                    event.event_id, t.string, t.fret, t.finger or 0,
                    1 if event.strike.direction == 'down' else -1,
                    convert(onset), convert(end),
                    convert(t.press_start_s if t.press_start_s is not None else t.note_on_s), onset, end))
        metadata = source.content_document()
        metadata.pop('observation_dim')
        metadata.pop('lookahead')
        metadata.update(schema='music_pipeline.score.v2', stage=stage,
                        event_ids=[e.event_id for e in selected], source_origin_s=origin,
                        timing_mode='tempo_scaled' if tempo_scale != 1 else 'easy_training',
                        event_fields=EVENT_FIELDS, state_fields=STATE_FIELDS,
                        lookahead_s=lookahead_s, capacity=capacity,
                        temporal_composition='target-specific current and preparation owners; conflicting audible targets rejected',
                        geometry_frame='caller supplied guitar frame; delta meters and relative velocity meters/second',
                        priority_slots='current with earliest end; unmatched nearest nonexpired strict deadline within token window')
        return cls(tuple(targets), lookahead_s, capacity, metadata)

    @property
    def duration_s(self):
        return max(t.end_s for t in self.targets) + 0.1

    def tokens(self, now_s, geometry, ledger):
        """기하 오차는 목표에 대한 실제 기타 좌표계 위치차(m), 속도는 m/s다.
        
        두 벡터 모두 네이티브 호출 측에서 목표마다 측정해야 한다.
        """
        now = finite(now_s, 'now_s')
        ledger.require_task(self)
        selected = [t for t in self.targets if t.onset_s <= now + self.lookahead_s and
                    now <= t.end_s + .1]
        if len(selected) > self.capacity:
            raise ValueError(f'event token capacity overflow: {len(selected)} > {self.capacity}')
        features = []
        for t in selected:
            g = geometry[t.target_id]  # 측정값이 없으면 조건을 통과시키지 않는다.
            delta, velocity = tuple(g['delta']), tuple(g['velocity'])
            if len(delta) != 3 or len(velocity) != 3:
                raise ValueError('geometry delta/velocity must have three components')
            values = tuple(finite(v, 'geometry') for v in delta + velocity)
            p = ledger.progress[t.target_id]
            duration = t.end_s - t.onset_s
            features.append((t.onset_s-now, t.end_s-now, t.press_s-now,
                float(t.string+1), float(t.fret), float(t.finger), float(t.direction),
                float(t.onset_s <= now < t.end_s), float(t.press_s <= now < t.onset_s),
                float(t.target_id in ledger.matches[.05]), float(t.target_id in ledger.matches[.1]),
                p.dwell_s, p.held_s, p.held_s/duration if duration > 0 else 0.0,
                float(p.released), p.release_s-now if p.release_s is not None else 0.0,
                *values, t.onset_s+.05-now, t.onset_s+.1-now))
        return (tuple(features) + ((0.0,) * EVENT_DIM,) * (self.capacity-len(features)),
                (True,) * len(features) + (False,) * (self.capacity-len(features)),
                tuple(t.target_id for t in selected) + (None,) * (self.capacity-len(features)))

    def priority_tokens(self, features, mask, target_ids):
        """주의집중에 쓰는 전체 토큰 외에 두 개의 직접 입력 슬롯을 제공한다.
        
        동시에 진행 중인 목표는 모두 주의집중 입력에 남고, 가장 먼저 끝나는
        목표가 현재 목표의 직접 전달 슬롯을 차지한다. 마감도 같은 시간창을 쓴다.
        """
        rows = [(row, identity) for row, valid, identity in zip(features, mask, target_ids) if valid]
        current = [(row, identity) for row, identity in rows if row[EVENT_FIELDS.index('current')]]
        deadlines = [(row, identity) for row, identity in rows
                     if not row[EVENT_FIELDS.index('matched_50')] and row[EVENT_FIELDS.index('strict_deadline_delta_s')] >= 0]
        selections = [min(current, key=lambda x: (x[0][1], x[1])) if current else None,
                      min(deadlines, key=lambda x: (x[0][-2], x[1])) if deadlines else None]
        return (tuple(item[0] if item else (0.0,)*EVENT_DIM for item in selections),
                tuple(item is not None for item in selections),
                tuple(item[1] if item else None for item in selections))

    def state(self, now_s, ledger):
        now = finite(now_s, 'now_s')
        ledger.require_task(self)
        deadlines = [t.onset_s+.05-now for t in self.targets if t.target_id not in ledger.matches[.05] and t.onset_s+.05 >= now]
        return (max(0.0, self.duration_s-now), float(len(ledger.matches[.05])),
                float(len(ledger.matches[.1])), float(len(self.targets)),
                sum(p.held_s for p in ledger.progress.values()),
                float(sum(p.released for p in ledger.progress.values())),
                min(deadlines) if deadlines else 0.0, now)


@dataclass
class TargetProgress:
    held_s: float = 0.0
    dwell_s: float = 0.0
    released: bool = False
    release_s: object = None
    ever_valid: bool = False
    contact_lost_count: int = 0


class MusicLedger:
    def __init__(self, task):
        self.task = task
        self.progress = {t.target_id: TargetProgress() for t in task.targets}
        self.matches = {.05: {}, .1: {}}
        self.crossing_ids = set()
        self.interval_end_s = None
        self.previous_valid = set()

    def require_task(self, task):
        if task is not self.task:
            raise ValueError('ledger belongs to another task')

    def update_interval(self, start_s, end_s, valid_target_ids):
        """측정한 적격 상태를 오디오 범위로 자른 [start,end] 구간에 적분한다.
        
        호출 측은 물리 시간 간격으로 표본을 수집하고 전체 구간을 검증한다.
        짧게 소리 나는 음에도 최소 100ms 유지 조건을 추가하지 않는다.
        """
        start, end = finite(start_s, 'start_s'), finite(end_s, 'end_s')
        valid = set(valid_target_ids)
        if not valid <= self.progress.keys() or start < 0 or end < start or (self.interval_end_s is not None and start < self.interval_end_s):
            raise ValueError('invalid/overlapping measurement interval or target ID')
        for t in self.task.targets:
            p = self.progress[t.target_id]
            amount = max(0.0, min(end, t.end_s)-max(start, t.onset_s)) if t.target_id in valid else 0.0
            # 접촉 경과 시간은 준비 구간도 포함하며 발음 중 유지 시간만 잘라 계산한다.
            if t.target_id in valid:
                contiguous = self.interval_end_s == start
                p.dwell_s = p.dwell_s + end-start if contiguous else end-start
            else:
                p.dwell_s = 0.0
            p.held_s += amount
            if t.target_id in valid:
                p.ever_valid = True
            if t.target_id in self.previous_valid and t.target_id not in valid:
                p.contact_lost_count += 1
        self.interval_end_s = end
        self.previous_valid = valid

    def crossing(self, crossing_id, at_s, string, direction, valid_target_ids):
        """외부에서 검증한 타격 한 번을 50ms·100ms 원장에 각각 대응시킨다.
        
        valid_target_ids는 타격 전후의 기하·접촉 검사에서 와야 한다.
        어느 원장에서도 한 후보로 목표 두 개를 소비할 수 없다.
        """
        at = finite(at_s, 'at_s')
        valid = set(valid_target_ids)
        if (at < 0 or type(string) is not int or not 0 <= string < 6 or
                type(direction) is not int or direction not in (-1, 1)):
            raise ValueError('invalid crossing time/string/direction')
        if crossing_id in self.crossing_ids or not valid <= self.progress.keys():
            raise ValueError('duplicate crossing or unknown eligible target')
        self.crossing_ids.add(crossing_id)
        matched = {}
        for tolerance in (.05, .1):
            candidates = [t for t in self.task.targets if t.target_id in valid and t.string == string and t.direction == direction and t.target_id not in self.matches[tolerance] and abs(at-t.onset_s) <= tolerance + 1e-12]
            if candidates:
                target = min(candidates, key=lambda t: (abs(at-t.onset_s), t.onset_s, t.target_id))
                self.matches[tolerance][target.target_id] = crossing_id
                matched[tolerance] = target.target_id
        return matched

    def release(self, target_id, at_s):
        at = finite(at_s, 'at_s')
        if at < 0:
            raise ValueError('release time must be nonnegative')
        t = next(t for t in self.task.targets if t.target_id == target_id)
        p = self.progress[target_id]
        if at < t.end_s or not p.ever_valid:
            raise ValueError('final release requires prior valid contact and target end')
        if p.released:
            raise ValueError('target release already recorded')
        p.released, p.release_s = True, at


# ── 원 음표 전체의 전곡 일정 ──

@dataclass(frozen=True)
class SongTask(ScoreTask):
    episode_duration_s: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        duration = finite(self.episode_duration_s, 'episode_duration_s')
        if duration <= max(target.end_s for target in self.targets):
            raise ValueError('song duration must include all targets and the final tail')

    @property
    def duration_s(self):
        return self.episode_duration_s


def make_task(bundle, pre_roll_s=3., tail_s=.5):
    """모든 음표와 원 시계, 기존 해제 시각으로 제한된 유지 구간을 보존한다.
    
    검수된 계획이 같은 현의 재타격 두 개를 지원하지 않는 단일 이벤트로
    합친 경우에만 해당 동작을 원 음표의 시작 시각들로 펼친다. 각각은 묶음의
    타격 방향을 이어받으며 두 번째 방향을 새로 추론하지 않는다.
    """
    pre_roll = finite(pre_roll_s, 'pre_roll_s')
    tail = finite(tail_s, 'tail_s')
    if pre_roll < 0 or tail <= 0:
        raise ValueError('nonnegative pre-roll and positive tail required')
    root = Path(bundle).resolve()
    source = load_music_task(root, stage='B', tempo_scale=1., preroll_s=pre_roll)
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    audio_path = root / 'source/audio.wav'
    audio_bytes = audio_path.read_bytes()
    audio_sha = hashlib.sha256(audio_bytes).hexdigest()
    audio_entry = manifest['files']['source/audio.wav']
    if audio_entry['sha256'] != audio_sha or audio_entry['bytes'] != len(audio_bytes):
        raise ValueError('audio manifest fingerprint mismatch')
    with wave.open(str(audio_path), 'rb') as audio:
        frames, sample_rate = audio.getnframes(), audio.getframerate()
    audio_duration = frames / sample_rate
    control_ticks = math.ceil((pre_roll + audio_duration + tail) * 60)
    duration = control_ticks / 60.
    notes = json.loads((root / 'mapping/fingering.json').read_text())['notes']
    targets, schedule, expanded = [], [], []
    for event in source.timeline.events:
        split = not event.supported
        if split:
            if (event.unsupported_reasons != ('unsupported_alternate_restrike',)
                    or event.strike.gesture != 'alternate_restrike'
                    or len(event.string_targets) != 2
                    or len({t.string for t in event.string_targets}) != 1
                    or any(not t.supported for t in event.string_targets)):
                raise ValueError('unsupported full-song event: ' + event.event_id)
            expanded.append(event.event_id)
        for target in event.string_targets:
            onset = target.note_on_s if split else event.score_time_s + target.traversal_offset_s
            end = min(target.sustain_until_s,
                      target.release_s if target.release_s is not None else target.sustain_until_s)
            press = target.press_start_s if target.press_start_s is not None else target.note_on_s
            identity = f'{event.event_id}/string-{target.string + 1}/note-{target.mapping_note_index}'
            direction = 1 if event.strike.direction == 'down' else -1
            targets.append(ScoreTarget(identity, event.event_id, target.string, target.fret,
                                       target.finger or 0, direction, onset + pre_roll,
                                       end + pre_roll, press + pre_roll, onset, end))
            schedule.append(dict(target_id=identity, event_id=event.event_id,
                                 mapping_note_index=target.mapping_note_index,
                                 source_event_id=target.source_event_id,
                                 source_string=target.source_string,
                                 string=target.string, fret=target.fret, finger=target.finger or 0,
                                 direction=direction, source_onset_s=onset,
                                 source_note_on_s=target.note_on_s,
                                 source_note_off_s=target.note_off_s,
                                 source_end_s=end, source_press_s=press,
                                 source_release_s=target.release_s,
                                 onset_s=onset + pre_roll, end_s=end + pre_roll,
                                 press_s=press + pre_roll, expanded_restrike=split))
    indices = [row['mapping_note_index'] for row in schedule]
    if len(indices) != len(notes) or sorted(indices) != list(range(len(notes))):
        raise ValueError('full-song source-note coverage is incomplete or duplicated')
    if max(target.source_end_s for target in targets) > audio_duration:
        raise ValueError('song targets extend beyond the source audio')
    metadata = source.content_document()
    metadata.pop('observation_dim')
    metadata.pop('lookahead')
    files = {item['path']: dict(item) for item in source.provenance}
    for path in (Path(__file__).resolve(),):
        payload = path.read_bytes()
        files[str(path)] = dict(path=str(path), sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
    metadata.update(schema='guitar_learning.song_score.v1', stage='full',
                    event_ids=[event.event_id for event in source.timeline.events],
                    source_origin_s=0., timing_mode='source_audio_clock',
                    preroll_s=pre_roll, tempo_scale=1.,
                    event_fields=list(EVENT_FIELDS), state_fields=list(STATE_FIELDS),
                    lookahead_s=4., capacity=64,
                    provenance=[files[path] for path in sorted(files)],
                    temporal_composition='all source notes; release-capped audible intervals; conflicting same-string targets rejected',
                    geometry_frame='caller supplied guitar frame; delta meters and relative velocity meters/second',
                    priority_slots='current with earliest end; unmatched nearest nonexpired strict deadline within token window',
                    song=dict(source_manifest=manifest,
                              manifest_path=str(manifest_path),
                              manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                              audio_path=str(audio_path), audio_sha256=audio_sha,
                              audio_frames=frames, audio_sample_rate=sample_rate,
                              audio_duration_s=audio_duration,
                              pre_roll_s=pre_roll, tail_s=tail,
                              control_hz=60, control_ticks=control_ticks,
                              policy_duration_s=duration,
                              source_event_count=len(source.timeline.events),
                              source_note_count=len(notes), source_mapping_indices=indices,
                              coverage=dict(complete=True, unique=True, omitted_indices=[], duplicated_indices=[]),
                              expanded_event_ids=expanded,
                              derivation='supported onset=canonical score+traversal; alternate_restrike split at source note_on; each split inherits aggregate direction; end=min(sustain,release); no source-origin shift; +policy pre-roll; horizon=ceil((audio+pre-roll+tail)*60)/60',
                              direction_scope='aggregate plan direction inherited independently by each split note; second direction is not inferred',
                              schedule=schedule))
    return SongTask(tuple(targets), lookahead_s=4., provenance=metadata, episode_duration_s=duration)


# ── 준비 자세를 기준으로 한 손목 안내 ──

WRIST_GUIDE_SCHEMA = 'guitar_learning.song_wrist_guide.v1'
POSITION_RADIUS_M = .04
ORIENTATION_RADIUS_RAD = .6


def load_anchor_track(bundle):
    """목록 해시로 검증한 60Hz 기준점 궤적을 읽고 손목 오프셋은 사용하지 않는다."""
    root = Path(bundle).resolve()
    relative = 'training/hand_position_targets.json'
    payload = (root / relative).read_bytes()
    manifest = json.loads((root / 'manifest.json').read_text())
    entry = manifest.get('files', {}).get(relative)
    if (not isinstance(entry, dict) or entry.get('bytes') != len(payload) or
            entry.get('sha256') != hashlib.sha256(payload).hexdigest()):
        raise ValueError('hand anchor manifest fingerprint mismatch')
    document = json.loads(payload)
    if (document.get('schema') != 'tab2body.hand_position_targets.v1' or
            document.get('coordinate_frame') != 'guitar local'):
        raise ValueError('guitar-local hand anchor schema required')
    frames = document.get('frames')
    if not isinstance(frames, list) or not frames:
        raise ValueError('nonempty hand anchor frames required')
    anchors = []
    for index, row in enumerate(frames):
        if not isinstance(row, dict) or type(row.get('frame')) is not int or row['frame'] != index:
            raise ValueError('sequential integer hand anchor frames required')
        timestamp, anchor = row.get('t'), row.get('anchor_fret')
        if (type(timestamp) not in (int, float) or not math.isfinite(timestamp) or
                abs(timestamp - index / 60.) > 5e-5):
            raise ValueError('hand anchor time must match its 60Hz frame')
        if (type(anchor) not in (int, float) or not math.isfinite(anchor) or
                not 1 <= anchor <= 22):
            raise ValueError('finite hand anchor fret in1..22 required')
        anchors.append(float(anchor))
    return dict(times_s=[index / 60. for index in range(len(frames))],
                anchors=anchors, ignored_fields=['wrist_pos_guitar', 'allowed_radius_m', 'offsets_m'])


class WristGuide:
    def __init__(self, bundle, sample, human_names, guitar_names, pre_roll_s=3.):
        if type(pre_roll_s) not in (int, float) or not math.isfinite(pre_roll_s) or pre_roll_s < 0:
            raise ValueError('finite nonnegative wrist guide pre-roll required')
        self.track = load_anchor_track(bundle)
        self.human_names, self.guitar_names = tuple(human_names), tuple(guitar_names)
        self.pre_roll_s = float(pre_roll_s)
        self.reference_wrist, self.reference_rotation, self.reference_frets = self._sample(sample)

    def _sample(self, sample):
        # 기하 모듈은 이 과제의 자료형을 사용하므로 측정 시점에 불러온다.
        import numpy as np
        from guitar_learning.core.geometry import frame

        native, geometry = sample['native'], sample['geometry']
        step = native['physics_step']
        if (isinstance(step, bool) or not isinstance(step, (int, np.integer)) or step < 0 or
                geometry['physics_step'] != step):
            raise ValueError('matching native/geometry physics steps required')
        if (len(set(self.human_names)) != len(self.human_names) or
                len(set(self.guitar_names)) != len(self.guitar_names) or
                len(native['human_body_states']) != len(self.human_names) or
                len(native['guitar_body_states']) != len(self.guitar_names)):
            raise ValueError('unique aligned wrist guide body names required')
        wrist = native['human_body_states'][self.human_names.index('L_Wrist')]
        guitar = native['guitar_body_states'][self.guitar_names.index('guitar')]
        wp, wr = frame(wrist)
        gp, gr = frame(guitar)
        frets = np.asarray(geometry['fret_markers_G_m'], dtype=float)
        if frets.shape != (23, 3) or not np.isfinite(frets).all():
            raise ValueError('finite live nut and22 fret markers required')
        return gr.inv().apply(wp - gp), gr.inv() * wr, frets.copy()

    def metadata(self):
        return dict(schema=WRIST_GUIDE_SCHEMA, reference_anchor_fret=5,
                    position_radius_m=POSITION_RADIUS_M,
                    orientation_radius_rad=ORIENTATION_RADIUS_RAD,
                    position_full_score_radius_m=.02,
                    reference='actual reset wrist in guitar frame; fret5 clean contact candidate',
                    target='reset wrist x/z and live anchor-to-fret5 y displacement',
                    orientation='weak actual reset relative wrist posture prior',
                    ignored_legacy_wrist_offsets=True,
                    scope='soft posture shaping; not reachability, pressure or musical success')

    def measure(self, sample, now_s):
        import numpy as np

        if not np.isfinite(now_s) or now_s < 0:
            raise ValueError('finite nonnegative wrist guide time required')
        wrist, rotation, frets = self._sample(sample)
        if not np.allclose(frets, self.reference_frets, atol=1e-5, rtol=0):
            raise ValueError('local fret geometry changed during wrist guidance')
        anchor = float(np.interp(float(now_s) - self.pre_roll_s,
                                 self.track['times_s'], self.track['anchors']))
        fret_y = float(np.interp(anchor, np.arange(1, 23), frets[1:, 1]))
        target = self.reference_wrist + np.array([0., fret_y - frets[5, 1], 0.])
        delta = target - wrist
        rotation_error = (self.reference_rotation.inv() * rotation).as_rotvec()
        distance, angle = float(np.linalg.norm(delta)), float(np.linalg.norm(rotation_error))
        return dict(schema=WRIST_GUIDE_SCHEMA, anchor_fret=anchor, target_G_m=target.tolist(),
                    wrist_G_m=wrist.tolist(), delta_G_m=delta.tolist(),
                    rotation_error_rad=rotation_error.tolist(), distance_m=distance,
                    angle_rad=angle,
                    position_score=math.exp(-(max(0., distance - .02) / POSITION_RADIUS_M) ** 2),
                    orientation_score=math.exp(-(angle / ORIENTATION_RADIUS_RAD) ** 2),
                    ready=bool(distance <= POSITION_RADIUS_M and angle <= ORIENTATION_RADIUS_RAD))
