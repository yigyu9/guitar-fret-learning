"""학습 입력·JSON 저장·전이·에피소드 로그·체크포인트와 자원 감시를 함께 관리한다.

읽는 순서: 소스·해시와 Dragon4 JSON → 로그 기록·복구 → 요약·체크포인트 → 자원 감시.
모듈을 불러올 때는 네이티브·NumPy·Torch 실행 환경을 불러오지 않는다."""
import copy
import gzip
import hashlib
import math
import json
import os
import sys
from collections import Counter
from pathlib import Path
import tempfile
import time
import zlib
import threading
from datetime import datetime, timezone


# 학습 입력 식별과 JSON 저장: 실수 표현은 기존 Dragon4 형식을 유지한다.
def _float_token(value, allow_nan):
    value = float.__float__(value)
    if not math.isfinite(value):
        if not allow_nan:
            raise ValueError('Out of range float values are not JSON compliant')
        return 'NaN' if math.isnan(value) else 'Infinity' if value > 0 else '-Infinity'
    if value == 0:
        return '-0.0' if math.copysign(1., value) < 0 else '0.0'
    import numpy as np
    if abs(value) < 1e-4 or abs(value) >= 1e16:
        return np.format_float_scientific(value, unique=True, trim='-', exp_digits=2)
    token = np.format_float_positional(value, unique=True, trim='-')
    return token if '.' in token else token+'.0'


class _Dragon4Encoder(json.JSONEncoder):
    def iterencode(self, value, _one_shot=False):
        # C 인코더는 사용자 실수 포매터를 무시하고 dtoa를 다시 호출한다.
        encoder = (json.encoder.encode_basestring_ascii if self.ensure_ascii
                   else json.encoder.encode_basestring)
        return json.encoder._make_iterencode(
            {} if self.check_circular else None, self.default, encoder,
            self.indent, lambda item: _float_token(item, self.allow_nan),
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)(value, 0)


def dump(*args, **kwargs):
    """기본 Dragon4 인코더로 json.dump를 호출하되, 명시한 사용자 cls는 유지한다."""
    if kwargs.get('cls') is None:
        kwargs['cls'] = _Dragon4Encoder
    return json.dump(*args, **kwargs)


def dumps(*args, **kwargs):
    """기본 Dragon4 인코더로 json.dumps를 호출하되, 명시한 사용자 cls는 유지한다."""
    if kwargs.get('cls') is None:
        kwargs['cls'] = _Dragon4Encoder
    return json.dumps(*args, **kwargs)


def bridge_dependency(filename):
    if '/guitar_learning/native/' in filename:
        return False
    return any('/' + folder + '/' in filename for folder in ('guitar_learning', 'free_guitar_learning_v1', 'music_pipeline_v2', 'music_pipeline_v3'))


def project_source_paths(modules):
    """네임스페이스 패키지는 __file__=None이므로 소스 파일 목록에 넣지 않는다."""
    paths = set()
    for name, module in modules:
        filename = getattr(module, '__file__', None)
        if (name == 'guitar_learning' or name.startswith('guitar_learning.')) and isinstance(filename, str) and filename.endswith('.py'):
            paths.add(str(Path(filename).resolve()))
    return paths


def active_source_paths(folder):
    """보관 디렉토리와 디렉토리 링크 내부를 순회하지 않고 Python 입력 파일을 수집한다."""
    paths = set()
    for path in Path(folder).iterdir():
        if path.name == 'archive':
            continue
        if path.is_dir() and not path.is_symlink():
            paths.update(active_source_paths(path))
        elif path.suffix == '.py':
            paths.add(path)
    return paths


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def write(path, value, compressed=False):
    import numpy as np
    def encode(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)
    opener = gzip.open if compressed else open
    with opener(path, 'xt') as stream:
        dump(value, stream, allow_nan=False, default=encode)
        stream.write('\n')


# 전이 저널: 60행 gzip 묶음의 내구 저장과 PPO 반영 commit을 따로 센다.
def _directory_sync(path):
    descriptor = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _encode(value):
    import numpy as np
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def _json_file(path, value):
    with Path(path).open('x') as stream:
        dump(value, stream, allow_nan=False, default=_encode)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    _directory_sync(Path(path).parent)


class TransitionJournal:
    """행을 추가하며, reward[N]이면 N개 전이로, 그 외에는 행당 1개 전이로 센다.

    sampled는 인코딩 실패를 포함해 write에 전달된 행의 전이 수를 센다.
    write 전에 유실된 네이티브 작업 결과는 호출자가 별도로 집계해야 한다.
    commit/discard에는 누적 합계가 아닌 추가 전이 수를 전달한다.
    metadata는 미리 직렬화 가능한 선택적 JSON 출처 자료이며, 항목을 암묵적으로 제거하지 않는다.
    """
    def __init__(self, path, metadata=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.path.with_name(self.path.name+'.metadata.json')
        self._counts = dict(sampled=0, logged=0, durable=0, committed=0, discarded=0,
            sampled_rows=0, logged_rows=0, durable_rows=0, completed_members=0,
            encoded_bytes=0, encode_s=0., compress_write_s=0., sync_s=0.)
        self._pending_rows = self._pending_transitions = 0
        self._member = None
        self.closed = self.failed = False
        self._file = self.path.open('xb')
        try:
            if metadata is not None:
                _json_file(self.metadata_path, dict(schema='guitar_learning.transition_metadata.v1',
                    journal_schema='gzip_members60_crc_prefix_v1', metadata=metadata))
            start = time.perf_counter()
            self._file.flush()
            os.fsync(self._file.fileno())
            _directory_sync(self.path.parent)
            self._counts['sync_s'] += time.perf_counter()-start
        except BaseException:
            self._file.close()
            self.closed = True
            raise

    @property
    def stats(self):
        return dict(self._counts, pending_rows=self._pending_rows,
            pending_transitions=self._pending_transitions,
            unresolved_sampled=self._counts['sampled']-self._counts['committed']-self._counts['discarded'],
            logged_not_committed=self._counts['logged']-self._counts['committed'],
            compressed_bytes=self.path.stat().st_size if self.closed else self._file.tell(),
            closed=self.closed, failed=self.failed, member_control_ticks=60,
            timing_scope='encode_s: row JSON/UTF8; compress_write_s: gzip create/write/finish; sync_s: file flush/fsync and initial directory sync; excludes metadata sidecar work; compressed_bytes is produced file bytes, not measured device IO; completed_members are closed and synced')

    def write(self, row):
        if self.closed or self.failed:
            raise RuntimeError('journal is closed or failed')
        reward = row.get('reward') if isinstance(row, dict) else None
        batch = isinstance(reward, (list, tuple)) or getattr(reward, 'ndim', None) == 1
        transitions = len(reward) if batch else 1
        if transitions < 1:
            raise ValueError('nonempty transition row required')
        self._counts['sampled'] += transitions
        self._counts['sampled_rows'] += 1
        start = time.perf_counter()
        try:
            data = (dumps(row, allow_nan=False, default=_encode)+'\n').encode('utf-8')
        finally:
            self._counts['encode_s'] += time.perf_counter()-start
        start = time.perf_counter()
        try:
            if self._member is None:
                self._member = gzip.GzipFile(filename='', fileobj=self._file, mode='wb', mtime=0)
            self._member.write(data)
        except BaseException:
            self.failed = True
            raise
        finally:
            self._counts['compress_write_s'] += time.perf_counter()-start
        self._counts['logged'] += transitions
        self._counts['logged_rows'] += 1
        self._counts['encoded_bytes'] += len(data)
        self._pending_rows += 1
        self._pending_transitions += transitions
        if self._pending_rows == 60:
            self.checkpoint()

    def checkpoint(self):
        if self.closed or self.failed:
            raise RuntimeError('journal is closed or failed')
        if not self._pending_rows:
            return self.stats
        try:
            start = time.perf_counter()
            try:
                self._member.close()
                self._member = None
            finally:
                self._counts['compress_write_s'] += time.perf_counter()-start
            start = time.perf_counter()
            try:
                self._file.flush()
                os.fsync(self._file.fileno())
            finally:
                self._counts['sync_s'] += time.perf_counter()-start
            self._counts['durable'] += self._pending_transitions
            self._counts['durable_rows'] += self._pending_rows
            self._counts['completed_members'] += 1
            self._pending_rows = self._pending_transitions = 0
        except BaseException:
            self.failed = True
            raise
        return self.stats

    def commit(self, transitions):
        self._validate_count(transitions)
        if transitions > self._counts['logged']-self._counts['committed']:
            raise ValueError('cannot commit transitions absent from log')
        self.checkpoint()
        self._counts['committed'] += transitions

    def discard(self, transitions):
        self._validate_count(transitions)
        self._counts['discarded'] += transitions

    def _validate_count(self, count):
        if type(count) is not int or not 0 <= count <= self._counts['sampled']-self._counts['committed']-self._counts['discarded']:
            raise ValueError('incremental count exceeds unresolved sampled transitions')

    def close(self):
        if self.closed:
            return
        try:
            if not self.failed:
                self.checkpoint()
        finally:
            try:
                if self._member is not None:
                    self._member.close()
            finally:
                self._member = None
                self._file.close()
                self.closed = True


class TransitionReadError(ValueError):
    pass


def iter_transitions(path, *, strict=True, diagnostics=None):
    """기존·현재 gzip JSONL을 읽으며, 복구 모드는 명시적인 진단 기록 대상을 요구한다.

    손상되거나 잘린 gzip 구성원을 조용히 건너뛰지 않는다. strict 모드는 예외를 발생시키고,
    복구 모드는 첫 손상 구성원·JSON 행에서 멈춘 뒤 이유를 기록한다.
    구성원이 하나인 기존 로그가 잘렸다면 CRC 검증을 마친 복구 가능 구성원이 없다.
    """
    if not strict and diagnostics is None:
        raise ValueError('recovery requires diagnostics')
    status = diagnostics if diagnostics is not None else {}
    status.update(complete=False, valid_prefix_rows=0, completed_members=0,
        valid_compressed_prefix_bytes=0, error=None, discarded_unverified_bytes=0)
    offset = 0
    pending = b''
    with Path(path).open('rb') as stream:
        while True:
            if not pending:
                pending = stream.read(65536)
            if not pending:
                status['complete'] = True
                return
            start_offset = offset
            decoder = zlib.decompressobj(31)
            with tempfile.SpooledTemporaryFile(max_size=1024*1024) as member:
                try:
                    while not decoder.eof:
                        if not pending:
                            pending = stream.read(65536)
                        if not pending:
                            raise EOFError('unfinished gzip member')
                        chunk, pending = pending, b''
                        member.write(decoder.decompress(chunk))
                        consumed = len(chunk)-len(decoder.unused_data)
                        offset += consumed
                        pending = decoder.unused_data
                    member.seek(0)
                    for line in member:
                        if not line.strip():
                            continue
                        value = json.loads(line.decode('utf-8'))
                        status['valid_prefix_rows'] += 1
                        yield value
                except (EOFError, zlib.error, UnicodeError, ValueError) as error:
                    status.update(error=dict(type=type(error).__name__, message=str(error),
                        member_start_byte=start_offset),
                        discarded_unverified_bytes=0 if decoder.eof else member.tell())
                    if strict:
                        raise TransitionReadError(str(status['error'])) from error
                    return
            status['completed_members'] += 1
            status['valid_compressed_prefix_bytes'] = offset


# 파일 해시는 공용 스트리밍 구현으로 계산한다.
_digest = digest


def publish_final_checkpoint(trainer, out, latest_checkpoint=None, metadata=None):
    """현재 PPO 상태와 정확히 같은 저장본만 재사용하며, final.pt와 원본 바이트를 유지한다.

    하드 링크는 원본 저장 데이터의 메타데이터를 유지해야 하므로 별칭 메타데이터는
    final_checkpoint.json에 둔다. 전체 저장과 링크 모두 fsync로 동기화한다.
    네이티브 호출자가 Isaac Gym을 먼저 불러올 수 있도록 필요한 모듈은 사용 시점에 불러온다.
    """
    import random
    import numpy as np
    import torch
    out = Path(out)
    final = out/'final.pt'
    manifest = out/'final_checkpoint.json'
    if final.exists() or manifest.exists():
        raise FileExistsError('final publication already exists')
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    reused = False
    differences = []
    latest = Path(latest_checkpoint) if latest_checkpoint is not None else None
    def same(a, b):
        if isinstance(a, torch.Tensor):
            return isinstance(b, torch.Tensor) and a.dtype==b.dtype and torch.equal(a.cpu(), b.cpu())
        if isinstance(a, np.ndarray):
            return isinstance(b, np.ndarray) and a.dtype==b.dtype and np.array_equal(a, b)
        if isinstance(a, dict):
            return isinstance(b, dict) and a.keys()==b.keys() and all(same(a[k], b[k]) for k in a)
        if isinstance(a, (list, tuple)):
            return type(a)==type(b) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        return a == b
    if latest is not None:
        if latest.resolve().parent != out.resolve():
            raise ValueError('latest checkpoint must belong to this output directory')
        payload = torch.load(latest, map_location='cpu', weights_only=False)
        current = dict(identity=trainer._identity(), model=trainer.policy.state_dict(),
            actor_optimizer=trainer.actor_optimizer.state_dict(), value_optimizer=trainer.value_optimizer.state_dict(),
            cost_weight=trainer.cost_weight, updates=trainer.updates, torch_rng=torch.get_rng_state(),
            numpy_rng=np.random.get_state(), python_rng=random.getstate(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None)
        differences = [key for key,value in current.items() if key not in payload or not same(payload[key],value)]
        reused = not differences
    compare_s = time.perf_counter()-start
    start = time.perf_counter()
    if reused:
        os.link(latest, final)
    else:
        trainer.save(final, metadata=metadata)
    save_or_link_s = time.perf_counter()-start
    start = time.perf_counter()
    with final.open('rb') as stream:
        os.fsync(stream.fileno())
    _directory_sync(out)
    sync_s = time.perf_counter()-start
    result = dict(schema='guitar_learning.final_checkpoint.v1', path=str(final.resolve()),
        mode='hardlink_exact_PPO_state' if reused else 'full_save', updates=trainer.updates,
        source=str(latest.resolve()) if reused else None, sha256=_digest(final),
        metadata=metadata, original_payload_metadata_retained=reused,
        state_difference_keys=differences, compare_s=compare_s,
        save_or_link_s=save_or_link_s, checkpoint_sync_s=sync_s,
        scope='PPO model/optimizer/RNG only; fresh native episodes on strict resume')
    _json_file(manifest, result)
    return result


def contract(detail):
    return dict(schema='guitar_learning.training_log_format.v2', detail=detail,
        transition_hz=60, physics_summary_hz=240,
        episode_and_tick_indices='zero based, local to each worker/run',
        omitted_in_standard=['debug.action', 'resource', 'specialist.timing duplicate',
            'per-tick timing/skill config and strike preparation descriptions',
            'per-tick contact feature diagnostics'],
        retained_evidence='full terminal episode; first tick, classification change and physical failure raw samples',
        timing_reference='specialist.timing_ref refers to same info.timing; full config in training_contract.json',
        safety='safety240 reduces every native substep; stability remains last-substep endpoint',
        action='active-hand statistics, not evidence of physical pick grasp')


def classification_signature(info):
    q = info.get('musical_quality', {}).get('fretting_state', {})
    quality=info.get('musical_quality',{})
    role=quality.get('role',info.get('specialist',{}).get('role','joint'))
    fret=tuple(q.get(key) for key in ('status', 'wrong_assignment', 'wrong_finger', 'higher_fret'))
    strike=quality.get('strike',{})
    right=(len(strike.get('accepted_crossing_ids',[])),strike.get('unprepared_count'),strike.get('extra_count'),
        len(strike.get('blocked_event_ids',[])),strike.get('ready'),strike.get('recovered'),
        info.get('timing',{}).get('wrong_crossings'))
    return fret if role=='left' else right if role=='right' else fret+right


def format_info(info, action, *, detail='standard'):
    import numpy as np
    if detail not in ('standard', 'diagnostic'):
        raise ValueError('standard or diagnostic training log detail required')
    result = copy.deepcopy(info)
    role = result.get('musical_quality', {}).get('role', result.get('specialist', {}).get('role', 'joint'))
    active = np.asarray(action)[slice(0, 33) if role == 'left' else slice(33, 39) if role == 'right' else slice(None)]
    result['action_summary'] = dict(role=role, active_channels=int(active.size),
        active_nonzero=bool(np.any(np.abs(active) > 1e-8)),
        mean_abs=float(np.abs(active).mean()), max_abs=float(np.abs(active).max()),
        saturation_fraction=float(np.mean(np.abs(active) >= .99)))
    if detail == 'diagnostic':
        return result
    terminal=copy.deepcopy(result['episode']) if 'episode' in result else None
    result.pop('debug', None)
    specialist = result.get('specialist', {})
    if 'timing' in specialist:
        specialist.pop('timing')
        specialist['timing_ref'] = 'timing'
    specialist.get('skill', {}).pop('config', None)
    timing = result.get('timing', {})
    for key in ('config', 'scope', 'success_criterion'):
        timing.pop(key, None)
    quality = result.get('musical_quality', {})
    quality.get('strike', {}).pop('preparation', None)
    quality.get('fretting_state', {}).pop('feature_diagnostics', None)
    # 기존 요약에는 종료 시점의 품질 스냅샷이 필요하다. 전체 근거는 episode에 두며,
    # tick별 품질 수치도 계속 사용할 수 있다.
    if terminal is not None:
        result['episode']=terminal
        if 'musical_quality' in terminal:
            result['musical_quality'] = copy.deepcopy(terminal['musical_quality'])
    return result


def run_evidence(out):
    out = Path(out)
    summary_path = out/'training_summary.json'
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text())
        episodes=[]
        if summary.get('logging_detail','diagnostic')=='diagnostic':
            with (out/'episodes.jsonl').open() as stream:
                for line in stream:
                    record=json.loads(line)
                    if record['episode'] is not None:
                        episodes.append(record['episode'])
        return dict(episodes=episodes, logged_transitions=summary['accounting']['logged_transitions'],
            reward_terms=summary['reward_terms'], preparation=summary['preparation'],
            last_quality_by_worker=summary['last_quality_by_worker'],
            episode_stats=summary,episode_records=summary.get('episode_records'),
            accounting=summary['accounting'], open_episodes=summary.get('open_episodes', []),
            evidence_source='streaming_summary_and_episode_records')
    episodes, rewards, last, prep_rewards = [], Counter(), {}, Counter()
    total = prep_steps = nonzero = 0
    for row in iter_transitions(out/'transitions.jsonl.gz'):
        for worker, info in enumerate(row['infos']):
            total += 1
            rewards.update(info.get('reward_terms', {}))
            if 'episode' in info:
                episodes.append(info['episode'])
            if 'musical_quality' in info:
                last[str(worker)] = info['musical_quality']
            if info.get('task_time_s', float('inf')) <= 2.+1e-9:
                prep_steps += 1
                nonzero += info.get('action_summary', {}).get('active_nonzero',
                    any(abs(float(v)) > 1e-8 for v in info.get('debug', {}).get('action', [])))
                prep_rewards.update(info.get('reward_terms', {}))
    valid=[e for e in episodes if e.get('valid',True)]
    stats=dict(completed_episodes=len(valid),
        physical_failure_episodes=sum(e.get('reason')=='terminal_failure' for e in valid))
    for label,key in (('quality','musical_quality'),('specialist','specialist'),('timing','timing')):
        stats[label+'_successful_episodes']=sum(e.get(key,{}).get('stage_success',False) for e in valid)
        stats[label+'_evaluated_episodes']=sum('stage_success' in e.get(key,{}) for e in valid)
    stats['timing_only_successful_episodes']=sum(e.get('timing',{}).get('timing_only_stage_success',
        e.get('timing',{}).get('stage_success',False)) for e in valid)
    return dict(episodes=episodes, logged_transitions=total, reward_terms=dict(rewards),
        episode_stats=stats,episode_records=None,
        preparation=dict(total_logged_transitions=total, first2s_logged_transitions=prep_steps,
            first2s_nonzero_action_transitions=nonzero, first2s_reward_terms=dict(prep_rewards)),
        last_quality_by_worker=last, accounting=None, open_episodes=[],
        evidence_source='legacy_transition_scan')


def finalize_summary(out, producer, label):
    """요약 중 발생한 오류로 원래 학습 예외를 덮어쓰지 않는다."""
    original = sys.exc_info()[1]
    try:
        return producer(Path(out))
    except BaseException as error:
        if original is None:
            raise
        detail = dict(type=type(error).__name__, message=str(error),
            primary_exception=type(original).__name__)
        try:
            write(Path(out)/(label+'_summary_error.json'), detail)
        except BaseException:
            pass
        print('[%s] secondary summary error: %s' % (label, error), file=sys.stderr, flush=True)


# GPU 에피소드·학습 지표: 반복되는 고정 메타데이터는 별도 문서에 한 번 저장한다.
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
    # J의 구간/전곡 scope는 reset마다 달라질 수 있으므로 고정 메타데이터로 옮기지 않는다.
    scheduled_scope = episode.get('finger_skill', {}).get('schema') == 'guitar_learning.finger_skill.v3'

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
    stream.write(dumps(value, allow_nan=False)+'\n')
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
    """JSONL을 엄격하게 순차 읽으며, 잘린 마지막 부분을 유효한 행으로 조용히 세지 않는다."""
    with Path(path).open() as stream:
        for index, line in enumerate(stream, 1):
            if not line.endswith('\n'):
                raise ValueError('Incomplete JSONL line %s:%d' % (path, index))
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError('JSON object required at %s:%d' % (path, index))
            yield value


def iter_episode_rows(run):
    """간소화·기존 실행 기록에서 원래 update_index/episode 묶음을 반환한다."""
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
    """두 스키마를 모두 읽고, 요청 시 기존 completed_episodes 표현을 복원한다."""
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
    """기존 gzip CRC·유효 앞부분 검사를 유지하며, 에피소드 참조를 정본 기록으로 해석한다."""
    run = Path(run)
    episodes = iter(iter_episode_rows(run)) if expand_episodes else None
    for row in iter_transitions(run/'transitions.jsonl.gz', strict=strict, diagnostics=diagnostics):
        if row.get('schema') == TRANSITION_SCHEMA and expand_episodes:
            row = dict(row, episodes=_resolve(row['episode_refs'], episodes, row['update_index']))
        yield row
    # 실패한 실행에서도 저널 오류 전에 정본 에피소드 기록이 추가되어 있을 수 있다.
    # 해당 기록을 전이로 집계하거나 PPO에 반영이 확정되었다고 추정하지 않는다.


# 체크포인트 기록: 모델 저장 성공 뒤 크기·해시·저장 시점을 기록한다.
class CheckpointRecorder:
    """모든 저장 체크포인트를 측정하며, 모델을 복사하지 않고 명세 기록을 추가한다."""
    def __init__(self, run):
        self.run = Path(run)
        self.entries = []
        self.stream = (self.run/'checkpoint_manifest.jsonl').open('x')
        _directory_sync(self.run)

    def record(self, path, kind, optimizer_updates, save):
        path = Path(path)
        begin = time.perf_counter()
        result = save()
        # 실패 처리 보조 함수는 예외를 발생시키는 대신 오류 기록을 반환한다.
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


# 실행 감시와 실패 복구: 저장 가능한 유효 상태인지 호출자가 명시한다.
class LowMemoryError(RuntimeError):
    pass


def available_memory_bytes():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])*1024
    raise RuntimeError('MemAvailable not reported')


def process_memory(pid):
    """현재 RSS/PSS와 실행 중 최대 RSS를 서로 다른 필드에 바이트 단위로 기록한다."""
    result=dict(pid=pid,rss_current_bytes=None,pss_current_bytes=None,rss_peak_bytes=None)
    try:
        for line in Path('/proc/%s/status'%pid).read_text().splitlines():
            key=line.split(':',1)[0]
            if key in ('VmRSS','VmHWM'):
                result['rss_current_bytes' if key=='VmRSS' else 'rss_peak_bytes']=int(line.split()[1])*1024
        try:
            for line in Path('/proc/%s/smaps_rollup'%pid).read_text().splitlines():
                if line.startswith('Pss:'):
                    result['pss_current_bytes']=int(line.split()[1])*1024
                    break
        except (OSError,ValueError):
            pass
    except (OSError,ValueError):
        pass
    return result


def stopped_reason(error):
    if isinstance(error,LowMemoryError):
        return 'memory_guard'
    if isinstance(error,KeyboardInterrupt):
        return 'interrupted'
    if isinstance(error,TimeoutError):
        return 'worker_timeout'
    if 'worker' in str(error).lower() and any(word in str(error).lower() for word in ('failure','failed','exited','died')):
        return 'worker_failed'
    return 'error'


def save_failure_checkpoint(trainer,out,metadata,eligible=True,ineligible_reason='resume_not_validated'):
    """기존 체크포인트를 덮어쓰거나 원래 예외를 감추지 않는다."""
    if trainer is None:
        return dict(path=None,error=None,reason='trainer_not_created')
    if not eligible:
        return dict(path=None,error=None,reason=ineligible_reason)
    path=Path(out)/'failure_last_valid.pt'
    try:
        trainer.save(path,metadata=metadata)
        return dict(path=str(path),error=None,reason='current_valid_PPO_optimizer_state')
    except BaseException as error:
        return dict(path=None,error=dict(type=type(error).__name__,message=str(error)),attempted_path=str(path))


class Monitor:
    def __init__(self,out,min_available_memory_gib=4.,heartbeat_seconds=10.,resource_interval_seconds=5.,
                 memory_probe=available_memory_bytes,process_probe=process_memory,console=None):
        self.out=Path(out)
        self.threshold=int(min_available_memory_gib*1024**3)
        self.heartbeat_seconds=heartbeat_seconds
        self.resource_interval_seconds=resource_interval_seconds
        self.memory_probe,self.process_probe=memory_probe,process_probe
        self.console=console if console is not None else sys.stdout
        self.lock=threading.RLock()
        self.stop_event=threading.Event()
        self.thread=None
        self.started=time.monotonic()
        self.last_sample=-float('inf')
        self.last_heartbeat=-float('inf')
        self.context=dict(phase='initializing',operation=None,pending_workers=[],worker_status=[],update_index=None,ticks=0,horizon=None)
        self.minimum_available=None
        self.low_memory=None
        self.probe_error=None
        self.status={}
        self.streams={name:(self.out/(name+'.jsonl')).open('x') for name in ('resources','events')}

    def _write(self,name,value):
        self.streams[name].write(dumps(value,allow_nan=False)+'\n')
        self.streams[name].flush()

    def _base(self):
        return dict(wall_time_utc=datetime.now(timezone.utc).isoformat(),elapsed_s=time.monotonic()-self.started,
                    parent_pid=os.getpid(),**self.context)

    def _status(self,value):
        temporary=self.out/'status.json.tmp'
        with temporary.open('w') as stream:
            dump(value,stream,indent=2,allow_nan=False)
            stream.write('\n')
        os.replace(str(temporary),str(self.out/'status.json'))
        self.status=value

    def event(self,kind,**fields):
        with self.lock:
            self._write('events',dict(self._base(),event=kind,**fields))

    def set_phase(self,phase,**fields):
        with self.lock:
            self.context.update(phase=phase,operation=None,pending_workers=[],**fields)
            self.event('phase')
            self.sample(force=True)
        self.check()

    def sample(self,force=False):
        with self.lock:
            now=time.monotonic()
            due=force or now-self.last_sample>=self.resource_interval_seconds
            if due:
                try:
                    available=self.memory_probe()
                    self.minimum_available=available if self.minimum_available is None else min(self.minimum_available,available)
                    workers=[dict(row,memory=self.process_probe(row['pid'])) for row in self.context['worker_status'] if row.get('pid')]
                    sample=dict(self._base(),available_memory_bytes=available,min_available_memory_bytes=self.minimum_available,
                                memory_floor_bytes=self.threshold,parent_memory=self.process_probe(os.getpid()),workers=workers)
                    if available<self.threshold and self.low_memory is None:
                        self.low_memory=dict(available_memory_bytes=available,memory_floor_bytes=self.threshold)
                        self._write('events',dict(self._base(),event='low_memory',**self.low_memory))
                    sample['low_memory']=self.low_memory
                    self._write('resources',sample)
                    self._status(sample)
                    self.last_sample=now
                except Exception as error:
                    self.probe_error=dict(type=type(error).__name__,message=str(error))
                    # 감시 실패로 보호 검사를 조용히 비활성화해서는 안 된다.
            if force or now-self.last_heartbeat>=self.heartbeat_seconds:
                available=self.status.get('available_memory_bytes')
                memory='unknown' if available is None else '%.2f GiB'%(available/1024**3)
                message='[training] phase=%s update=%s tick=%s/%s free=%s waiting=%s'%(
                    self.context['phase'],self.context['update_index'],self.context['ticks'],self.context['horizon'],
                    memory,self.context['pending_workers'])
                print(message,file=self.console,flush=True)
                self.last_heartbeat=now

    def check(self):
        if self.probe_error is not None:
            raise RuntimeError('resource monitor failed: '+str(self.probe_error))
        if self.low_memory is not None:
            raise LowMemoryError('MemAvailable %.3f GiB below %.3f GiB guard'%(
                self.low_memory['available_memory_bytes']/1024**3,self.threshold/1024**3))

    def wait(self,context):
        with self.lock:
            self.context.update({key:context[key] for key in ('operation','pending_workers','worker_status') if key in context})
            self.sample()
        self.check()

    def progress(self,context):
        with self.lock:
            self.context.update({key:context[key] for key in ('ticks','horizon') if key in context})
            self.sample()
        self.check()

    def start(self):
        self.sample(force=True)
        self.check()
        def run():
            interval=min(self.heartbeat_seconds,self.resource_interval_seconds,.5)
            while not self.stop_event.wait(interval):
                self.sample()
        self.thread=threading.Thread(target=run,name='training-resource-monitor',daemon=True)
        self.thread.start()

    def close(self,stopped):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2.)
        with self.lock:
            self.context.update(phase='stopped',stopped=stopped,pending_workers=[])
            self.sample(force=True)
            self.event('stopped',reason=stopped)
            for stream in self.streams.values():
                stream.close()
