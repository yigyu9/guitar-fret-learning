"""검수된 곡 번들을 단음·스트럼 타현 이벤트로 읽는다.

왼손 압현·음고·음향 성공은 판단하지 않는다. 원본의 왼손 미지원 사유는
보존하며, 오른손에서 뜻이 모호한 주법과 재타격 묶음은 거부한다.
"""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import wave

from guitar_learning.score import canonical


SCHEMA = 'guitar_learning.strike_task.v1'
WINDOW_S = .05
# 오른손의 계획된 교차를 정의하는 데 왼손 압현 성공은 요구하지 않는다.
LEFT_ONLY_REASONS = frozenset((
    'unsupported_barre', 'missing_or_invalid_fretted_finger',
    'open_string_has_fretted_finger', 'missing_fret_event_link',
    'fret_event_finger_mismatch', 'fret_event_barre_mismatch'))


@dataclass(frozen=True)
class StrikeEvent:
    event_id: str
    gesture: str
    direction: int
    onset_s: float
    traversal_strings: tuple
    audible_strings: tuple
    protected_strings: tuple
    traversal_offsets_s: tuple
    sweep_duration_s: float
    source_note_on_s: tuple
    source_note_off_s: tuple
    mapping_note_indices: tuple
    unsupported_reasons: tuple

    @property
    def crossing_times_s(self):
        return tuple(self.onset_s + offset for offset in self.traversal_offsets_s)

    @property
    def start_s(self):
        return self.crossing_times_s[0] - WINDOW_S

    @property
    def deadline_s(self):
        return self.crossing_times_s[-1] + WINDOW_S


@dataclass(frozen=True)
class StrikeTask:
    events: tuple
    duration_s: float
    provenance: dict


def _finite(value, name, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < 0 or positive and value == 0):
        raise ValueError(name + ' must be finite and ' + ('positive' if positive else 'nonnegative'))
    return float(value)


def _fingerprint(path):
    payload = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))


def load_strike_task(bundle, *, pre_roll_s=3., tail_s=.5):
    """원 시계와 이벤트 경계를 보존한다. 임의 목표 사전은 받지 않는다."""
    if not isinstance(bundle, (str, Path)):
        raise ValueError('a verified song bundle path is required')
    pre_roll = _finite(pre_roll_s, 'pre_roll_s')
    tail = _finite(tail_s, 'tail_s', positive=True)
    root = Path(bundle).resolve()
    timeline = canonical.compile_song_bundle_events(root, fail_on_unsupported=False)
    canonical.validate_timeline(timeline)
    manifest_path = root/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    files = {}
    # 표준 변환기의 필수 입력 검증에 더해, 선언된 나머지 입력도 검증한다.
    for name, record in manifest['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('manifest file escapes bundle: ' + name)
        path = (root/relative).resolve()
        path.relative_to(root)
        actual = _fingerprint(path)
        if (not isinstance(record, dict) or actual['sha256'] != record.get('sha256') or
                type(record.get('bytes')) is not int or actual['bytes'] != record['bytes']):
            raise ValueError('bundle SHA/size mismatch: ' + name)
        files[str(path)] = actual
    audio_path = root/'source/audio.wav'
    if 'source/audio.wav' not in manifest['files']:
        raise ValueError('audio manifest fingerprint required')
    with wave.open(str(audio_path), 'rb') as audio:
        frames, sample_rate = audio.getnframes(), audio.getframerate()
    audio_duration = frames/sample_rate
    ticks = math.ceil((pre_roll + audio_duration + tail)*60)
    duration = ticks/60.
    events = []
    for original in timeline.events:
        strike = original.strike
        if strike.gesture not in ('single_pick', 'strum'):
            raise ValueError('unsupported right strike gesture: ' + original.event_id + '/' + strike.gesture)
        if ((strike.gesture == 'single_pick' and
             (len(strike.traversal_strings) != 1 or len(original.string_targets) != 1)) or
                (strike.gesture == 'strum' and len(strike.audible_strings) < 2) or
                len(original.string_targets) != len(strike.audible_strings)):
            raise ValueError('strike gesture/target cardinality mismatch: ' + original.event_id)
        rejected = set(original.unsupported_reasons) - LEFT_ONLY_REASONS
        if rejected:
            raise ValueError('unsupported right strike semantics: ' + original.event_id + '/' + ','.join(sorted(rejected)))
        event = StrikeEvent(original.event_id, strike.gesture,
            1 if strike.direction == 'down' else -1, original.score_time_s + pre_roll,
            strike.traversal_strings, strike.audible_strings, strike.protected_strings,
            strike.traversal_offsets_s, strike.sweep_duration_s,
            tuple(target.note_on_s for target in original.string_targets),
            tuple(target.note_off_s for target in original.string_targets),
            tuple(target.mapping_note_index for target in original.string_targets),
            original.unsupported_reasons)
        if (any(value > audio_duration for value in event.source_note_on_s) or
                event.crossing_times_s[-1] > pre_roll + audio_duration):
            raise ValueError('strike source onsets or traversal extend beyond audio: ' + event.event_id)
        if events and event.crossing_times_s[0] <= events[-1].crossing_times_s[-1]:
            raise ValueError('separate strike traversal intervals overlap: ' + event.event_id)
        if event.deadline_s > duration:
            raise ValueError('episode does not include last strike deadline: ' + event.event_id)
        events.append(event)
    if not events:
        raise ValueError('nonempty strike task required')
    indices = [index for event in events for index in event.mapping_note_indices]
    if sorted(indices) != list(range(len(indices))):
        raise ValueError('complete unique source-note coverage required')
    for path in (manifest_path, Path(__file__).resolve(), Path(canonical.__file__).resolve(),
                 Path(canonical.__file__).resolve().with_name('strike_goal_compiler.py')):
        files[str(path)] = _fingerprint(path)
    provenance = dict(schema=SCHEMA, bundle=str(root), song_id=timeline.song_id,
        canonical_content_sha256=timeline.content_sha256,
        files=[files[path] for path in sorted(files)],
        source_event_ids=[dict(event_id=event.event_id, source_event_ids=list(event.source_event_ids))
                          for event in timeline.events],
        source_origin_s=0., pre_roll_s=pre_roll, tail_s=tail,
        audio_duration_s=audio_duration, audio_frames=frames, audio_sample_rate=sample_rate,
        control_hz=60, control_ticks=ticks, event_count=len(events), source_note_count=len(indices),
        string_convention='runtime0=high-e,5=low-E; mapping0=low-E,5=high-e',
        timing='source center + policy pre-roll; crossing=center+traversal offset; no origin shift or tempo change',
        acceptance_window_s=WINDOW_S,
        event_order='sequential event approval; acceptance windows may overlap; separate traversal intervals must be strictly ordered',
        left_only_reasons_preserved=sorted(LEFT_ONLY_REASONS),
        scope='right pick geometry only; left-hand unsupported reasons retained; no left pressure, pitch or acoustic success claim')
    return StrikeTask(tuple(events), duration, provenance)
