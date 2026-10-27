"""CPU-only real-song task input; raw audio never enters policy observations."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'fresh_music.events.v1'
LOOKAHEAD = 4
# Current 6 strings x (fret/22, finger/4, pressing, sounding, release delta),
# followed by 4 slots x (valid, onset delta, direction, 6 x
# (audible, traversed, fret/22, finger/4, crossing delta, sustain delta)).
OBSERVATION_DIM = 30 + LOOKAHEAD * 39


def _compiler():
    # Importing full.__init__ would load frozen policies/Torch. Execute the exact
    # reviewed compiler source instead, preserving its stdlib-only boundary.
    name = '_fresh_music_canonical_events_v1'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / 'tab2body/full/events.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[name]
            raise
    return sys.modules[name]


def _finite(value, name, minimum=0.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f'{name} must be finite and >= {minimum}')
    return float(value)


def validate_timeline(timeline):
    """Check canonical roundtrip plus stricter fresh-policy target semantics."""
    _compiler().CanonicalEventTimeline.from_document(timeline.to_document())
    for event in timeline.events:
        for target in event.string_targets:
            if target.source_string != 5 - target.string:
                raise ValueError('source/simulator string conversion mismatch')
            if not target.supported or not event.supported:
                continue
            crossing = event.score_time_s + target.traversal_offset_s
            if target.sustain_until_s < crossing:
                raise ValueError('sustain ends before string crossing')
            if target.fret:
                if target.finger not in (1, 2, 3, 4):
                    raise ValueError('fretted note needs finger 1..4')
                if target.press_start_s is None or target.release_s is None:
                    raise ValueError('fretted note needs press and release')
                if not target.press_start_s <= crossing <= target.release_s:
                    raise ValueError('press/release does not cover string crossing')
            elif target.finger not in (None, 0):
                raise ValueError('open string has fretted finger')


@dataclass(frozen=True)
class MusicTask:
    timeline: object
    events: tuple
    stage: str
    tempo_scale: float
    preroll_s: float
    source_origin_s: float
    provenance: tuple

    def __post_init__(self):
        # Distinct audible frets/fingers on one string cannot be represented
        # by this contract. Shared source preparation windows may overlap;
        # they never displace a note that is already sounding.
        targets = [(e, t) for e in self.events for t in e.string_targets]
        for index, (event, target) in enumerate(targets):
            start = event.score_time_s + target.traversal_offset_s
            end = min(target.sustain_until_s, target.release_s if target.release_s is not None else target.sustain_until_s)
            for other_event, other in targets[index + 1:]:
                other_start = other_event.score_time_s + other.traversal_offset_s
                other_end = min(other.sustain_until_s, other.release_s if other.release_s is not None else other.sustain_until_s)
                if (target.string == other.string
                        and (target.fret, target.finger) != (other.fret, other.finger)
                        and max(start, other_start) < min(end, other_end)):
                    raise ValueError(f'conflicting audible targets on string {target.string}: {event.event_id}, {other_event.event_id}')

    @property
    def timing_mode(self):
        return 'tempo_scaled' if self.tempo_scale != 1.0 else 'easy_training'

    def task_time(self, source_time_s):
        return self.preroll_s + (source_time_s - self.source_origin_s) / self.tempo_scale

    @property
    def duration_s(self):
        return max(self.task_time(t.sustain_until_s) for e in self.events for t in e.string_targets) + 0.5

    def content_document(self):
        return dict(schema=SCHEMA, song_id=self.timeline.song_id,
                    timeline_sha256=self.timeline.content_sha256,
                    event_ids=[e.event_id for e in self.events], stage=self.stage,
                    unsupported_event_ids=[e.event_id for e in self.timeline.events if not e.supported],
                    hold_mode='selected_note_sustain_capped_at_source_release',
                    temporal_composition='sounding_targets_first_else_earliest_preparation; conflicting_audible_targets_rejected',
                    timing_mode=self.timing_mode, tempo_scale=self.tempo_scale,
                    preroll_s=self.preroll_s, source_origin_s=self.source_origin_s,
                    string_numbering='1=high-e,6=low-E; simulator_index=number-1',
                    observation_dim=OBSERVATION_DIM, lookahead=LOOKAHEAD,
                    provenance=list(self.provenance))

    def active_targets(self, score_time_s):
        """Return string -> (event, target, task_release_s, sounding).

        Current audible targets take priority over overlapping preparations.
        Without a sounding target the earliest upcoming preparation wins.
        """
        now = _finite(score_time_s, 'score_time_s')
        candidates = [[] for _ in range(6)]
        for event in self.events:
            for t in event.string_targets:
                onset = self.task_time(event.score_time_s + t.traversal_offset_s)
                press = self.task_time(t.press_start_s if t.press_start_s is not None else t.note_on_s)
                release = self.task_time(min(t.sustain_until_s, t.release_s if t.release_s is not None else t.sustain_until_s))
                if press <= now < release:
                    candidates[t.string].append((onset, release, event, t))
        active = {}
        for string, entries in enumerate(candidates):
            if not entries:
                continue
            sounding = [entry for entry in entries if entry[0] <= now]
            if sounding:
                onset, release, event, target = max(sounding, key=lambda entry: entry[1])
            else:
                onset, release, event, target = min(entries, key=lambda entry: entry[0])
            active[string] = (event, target, release, bool(sounding))
        return active

    def encode(self, score_time_s):
        now = _finite(score_time_s, 'score_time_s')
        rows = [[0.0] * 5 for _ in range(6)]
        for string, (_, target, release, sounding) in self.active_targets(now).items():
            rows[string] = [target.fret / 22.0, (target.finger or 0) / 4.0,
                            float(target.fret > 0), float(sounding), release - now]
        result = [v for row in rows for v in row]
        upcoming = [e for e in self.events if self.task_time(e.traversal_end_time_s) >= now][:LOOKAHEAD]
        for event in upcoming:
            result.extend([1.0, self.task_time(event.score_time_s) - now, 1.0 if event.strike.direction == 'down' else -1.0])
            targets = {t.string: t for t in event.string_targets}
            offsets = dict(zip(event.strike.traversal_strings, event.strike.traversal_offsets_s))
            for string in range(6):
                t = targets.get(string)
                result.extend([float(t is not None), float(string in offsets),
                               t.fret / 22.0 if t else 0.0, (t.finger or 0) / 4.0 if t else 0.0,
                               self.task_time(event.score_time_s + offsets[string]) - now if string in offsets else 0.0,
                               self.task_time(t.sustain_until_s) - now if t else 0.0])
        result.extend([0.0] * (OBSERVATION_DIM - len(result)))
        return tuple(result)


def load_music_task(bundle_root, *, stage='B', tempo_scale=1.0, preroll_s=1.0, phrase_events=8):
    if stage not in ('B', 'C', 'D'):
        raise ValueError('music stage must be B, C, or D')
    scale = _finite(tempo_scale, 'tempo_scale', 0.000001)
    preroll = _finite(preroll_s, 'preroll_s')
    if isinstance(phrase_events, bool) or not isinstance(phrase_events, int) or phrase_events < 1:
        raise ValueError('phrase_events must be positive integer')
    root = Path(bundle_root).resolve()
    timeline = _compiler().compile_song_bundle_events(root, fail_on_unsupported=False)
    validate_timeline(timeline)
    count = {'B': 1, 'C': 2, 'D': phrase_events}[stage]
    events = None
    for index in range(len(timeline.events) - count + 1):
        candidate = timeline.events[index:index + count]
        if all(e.supported and (stage != 'B' or len(e.string_targets) == 1 and e.string_targets[0].fret > 0) for e in candidate):
            events = candidate
            break
    if events is None:
        raise ValueError(f'no supported consecutive {count}-event curriculum segment')
    files = {root / f.relative_path for f in timeline.source_files}
    files.update((root / 'manifest.json', ROOT / 'tab2body/full/events.py', ROOT / 'tab2body/env/strike_goal_compiler.py', Path(__file__).resolve()))
    # Audio is provenance only, never read by encode().
    files.update(p for p in (root / 'source').rglob('*') if p.is_file())
    provenance = tuple(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size) for p in sorted(files))
    origin = min(t.press_start_s if t.press_start_s is not None else t.note_on_s for e in events for t in e.string_targets)
    return MusicTask(timeline, tuple(events), stage, scale, preroll, origin, provenance)
