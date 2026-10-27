"""Compact GPU records with one canonical, streaming episode source.

Only serialization changes: PPO receives the original completed episodes. Fixed
metadata is checked on every episode rather than silently accepting run drift.
Readers reject incomplete JSON lines and unresolved references; legacy records
remain readable without rewriting them.
"""
import copy
import json
import os
from pathlib import Path
import time

from guitar_learning.training import json_io
from guitar_learning.training.recording import digest
from guitar_learning.training.training_log_io import _directory_sync, iter_transitions

EPISODE_SCHEMA = 'guitar_learning.gpu_episode_record.v2'
METRICS_SCHEMA = 'guitar_learning.gpu_learning_metrics.v2'
TRANSITION_SCHEMA = 'guitar_learning.gpu_transition.v2'
METADATA_SCHEMA = 'guitar_learning.gpu_episode_metadata.v1'
_FIXED_KEYS = frozenset(('schema', 'scope', 'contract', 'contact_measurement',
    'target_ids', 'required_clean_s', 'body_names', 'target_strings_1based', 'joint_names'))


def _split_episode(episode):
    compact = copy.deepcopy(episode)
    quality = compact.get('musical_quality', {})
    duplicate_song = 'song' in quality
    if duplicate_song:
        if quality['song'] != compact.get('song'):
            raise ValueError('musical_quality.song differs from canonical song')
        del quality['song']
    fixed = []
    scheduled_scope = episode.get('finger_skill', {}).get('schema') == 'guitar_learning.finger_skill.v2'

    def visit(value, path):
        for key in list(value):
            dynamic_scope = scheduled_scope and key == 'scope' and path in (
                ['finger_skill'], ['finger_skill_eval'])
            if key in _FIXED_KEYS and not dynamic_scope:
                fixed.append(dict(path=path+[key], value=value.pop(key)))
            elif isinstance(value[key], dict):
                visit(value[key], path+[key])
    visit(compact, [])
    return compact, dict(schema=METADATA_SCHEMA, fields=fixed,
        restore_musical_quality_song=duplicate_song)


def _restore_episode(episode, metadata):
    if metadata.get('schema') != METADATA_SCHEMA:
        raise ValueError('Unknown GPU episode metadata schema')
    result = copy.deepcopy(episode)
    for field in metadata['fields']:
        target = result
        for key in field['path'][:-1]:
            target = target[key]
        key = field['path'][-1]
        if key in target:
            raise ValueError('Episode shadows fixed metadata: '+'.'.join(field['path']))
        target[key] = copy.deepcopy(field['value'])
    if metadata['restore_musical_quality_song']:
        result['musical_quality']['song'] = copy.deepcopy(result['song'])
    return result


def _write_line(stream, value):
    stream.write(json_io.dumps(value, allow_nan=False)+'\n')
    stream.flush()


class EpisodeWriter:
    def __init__(self, run):
        self.run = Path(run)
        self.stream = (self.run/'episodes.jsonl').open('x')
        self.metadata = None
        self.count = 0
        self.dirty = False

    def append(self, episode, update_index, tick_in_update):
        compact, metadata = _split_episode(episode)
        if self.metadata is None:
            path = self.run/'episode_metadata.json'
            with path.open('x') as stream:
                _write_line(stream, metadata)
                os.fsync(stream.fileno())
            _directory_sync(path.parent)
            self.metadata = metadata
        elif metadata != self.metadata:
            raise ValueError('Fixed GPU episode metadata changed during run')
        episode_id = self.count
        _write_line(self.stream, dict(schema=EPISODE_SCHEMA, episode_id=episode_id,
            update_index=update_index, tick_in_update=tick_in_update, episode=compact))
        self.count += 1
        self.dirty = True
        return dict(episode_id=episode_id, env_id=episode['env_id'],
            reason=episode['reason'], steps=episode['steps'])

    def sync(self):
        if self.dirty:
            self.stream.flush()
            os.fsync(self.stream.fileno())
            self.dirty = False

    def close(self):
        try:
            self.sync()
        finally:
            self.stream.close()


def episode_summary(episodes):
    count = len(episodes)
    summary = dict(count=count,
        timeline_complete=sum(e['reason'] == 'timeline_complete' for e in episodes),
        physical_failure=sum(e.get('termination', {}).get('physical_failure',
                             e['reason'] == 'terminal_failure') for e in episodes),
        stage_success=sum(bool(e['song']['stage_success']) for e in episodes),
        mean_reward=sum(e['reward'] for e in episodes)/count if count else None,
        mean_cost=sum(e['cost'] for e in episodes)/count if count else None,
        mean_left_success_count=sum(e['song']['left_success_count'] for e in episodes)/count if count else None,
        mean_right_success_count=sum(e['song']['right_success_count'] for e in episodes)/count if count else None)
    if any('termination' in episode for episode in episodes):
        summary['wrist_failure'] = sum(e['termination']['wrist_failure'] for e in episodes if 'termination' in e)
    return summary


def iter_json_lines(path):
    """Strict streaming JSONL; a torn tail is never silently counted as valid."""
    with Path(path).open() as stream:
        for index, line in enumerate(stream, 1):
            if not line.endswith('\n'):
                raise ValueError('Incomplete JSONL line %s:%d' % (path, index))
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError('JSON object required at %s:%d' % (path, index))
            yield value


def iter_episode_rows(run):
    """Yield original update_index/episode wrappers from compact or legacy runs."""
    run = Path(run)
    metadata = None
    expected = 0
    for row in iter_json_lines(run/'episodes.jsonl'):
        if row.get('schema') == EPISODE_SCHEMA:
            if row['episode_id'] != expected:
                raise ValueError('Nonsequential canonical episode ID')
            if metadata is None:
                metadata = json.loads((run/'episode_metadata.json').read_text())
            episode = _restore_episode(row['episode'], metadata)
            yield dict(row, episode=episode)
            expected += 1
        elif 'schema' in row and row['schema'].startswith('guitar_learning.gpu_episode_record.'):
            raise ValueError('Unsupported GPU episode record schema')
        else:
            yield row


def _resolve(refs, episodes, update_index):
    result = []
    for ref in refs:
        row = next(episodes, None)
        if row is None or row.get('episode_id') != ref['episode_id'] or row['update_index'] != update_index:
            raise ValueError('Missing or mismatched canonical episode reference')
        episode = row['episode']
        for key in ('env_id', 'reason', 'steps'):
            if key in ref and ref[key] != episode[key]:
                raise ValueError('Episode reference summary mismatch: '+key)
        result.append(episode)
    return result


def iter_learning_metrics(run, *, expand_episodes=True):
    """Read both schemas; optionally restore old completed_episodes on demand."""
    run = Path(run)
    episodes = iter(iter_episode_rows(run)) if expand_episodes else None
    compact = (run/'episode_metadata.json').is_file()
    for row in iter_json_lines(run/'learning_metrics.jsonl'):
        if row.get('schema') == METRICS_SCHEMA and expand_episodes:
            compact = True
            row = dict(row, completed_episodes=_resolve(
                [dict(episode_id=i) for i in row['completed_episode_ids']], episodes, row['update_index']))
        yield row
    if expand_episodes and compact and next(episodes, None) is not None:
        raise ValueError('Canonical episodes absent from committed metrics; run may be incomplete')


def iter_gpu_transitions(run, *, strict=True, diagnostics=None, expand_episodes=True):
    """Keep original gzip CRC/prefix checks and resolve canonical episode refs."""
    run = Path(run)
    episodes = iter(iter_episode_rows(run)) if expand_episodes else None
    for row in iter_transitions(run/'transitions.jsonl.gz', strict=strict, diagnostics=diagnostics):
        if row.get('schema') == TRANSITION_SCHEMA and expand_episodes:
            row = dict(row, episodes=_resolve(row['episode_refs'], episodes, row['update_index']))
        yield row
    # A failed run can have canonical records appended before a journal failure.
    # Such records are not claimed as transitions or inferred to be PPO committed.


class CheckpointRecorder:
    """Measure every saved checkpoint; append a manifest without model copies."""
    def __init__(self, run):
        self.run = Path(run)
        self.entries = []
        self.stream = (self.run/'checkpoint_manifest.jsonl').open('x')
        _directory_sync(self.run)

    def record(self, path, kind, optimizer_updates, save):
        path = Path(path)
        begin = time.perf_counter()
        result = save()
        # Failure helper returns an error record instead of raising.
        if not path.is_file():
            return result
        with path.open('rb') as stream:
            os.fsync(stream.fileno())
        _directory_sync(path.parent)
        save_s = time.perf_counter()-begin
        entry = dict(path=path.name, kind=kind, optimizer_updates=optimizer_updates,
            bytes=path.stat().st_size, save_s=save_s, sha256=digest(path))
        _write_line(self.stream, entry)
        os.fsync(self.stream.fileno())
        self.entries.append(entry)
        return result

    @property
    def stats(self):
        return dict(count=len(self.entries), bytes=sum(e['bytes'] for e in self.entries),
            save_s=sum(e['save_s'] for e in self.entries), manifest='checkpoint_manifest.jsonl',
            scope='all successful initial/periodic/final/recovery saves, including checkpoint fsync; save_s excludes manifest hashing/write')

    def close(self):
        self.stream.close()
