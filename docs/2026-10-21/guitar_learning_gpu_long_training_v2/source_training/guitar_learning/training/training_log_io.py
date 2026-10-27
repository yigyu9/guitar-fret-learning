"""Bounded gzip durability, explicit rollout accounting and final publication.

No native/Torch imports occur at module load. A logged row was accepted by the
gzip writer; a durable row belongs to a finished member followed by successful
fsync. Neither implies a PPO update committed it. Recovery yields only complete
CRC-verified gzip members, discarding an unfinished member (at most60 normal
control ticks). Legacy single-member streams remain readable.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import zlib


def _directory_sync(path):
    descriptor = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def _encode(value):
    import numpy as np
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    raise TypeError(type(value).__name__)


def _json_file(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, allow_nan=False, default=_encode)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    _directory_sync(Path(path).parent)


class TransitionJournal:
    """Append rows; infer transitions from reward[N], otherwise one per row.

    sampled counts rows delivered to write, including failed encodes. Native
    worker results lost before write must be accounted by the caller separately.
    commit/discard take incremental transition counts, never cumulative totals.
    metadata is optional pre-serialized JSON provenance, without implicit prune.
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
            self._file.flush(); os.fsync(self._file.fileno()); _directory_sync(self.path.parent)
            self._counts['sync_s'] += time.perf_counter()-start
        except BaseException:
            self._file.close(); self.closed = True
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
        if self.closed or self.failed: raise RuntimeError('journal is closed or failed')
        reward = row.get('reward') if isinstance(row, dict) else None
        batch = isinstance(reward, (list, tuple)) or getattr(reward, 'ndim', None) == 1
        transitions = len(reward) if batch else 1
        if transitions < 1: raise ValueError('nonempty transition row required')
        self._counts['sampled'] += transitions; self._counts['sampled_rows'] += 1
        start = time.perf_counter()
        try: data = (json.dumps(row, allow_nan=False, default=_encode)+'\n').encode('utf-8')
        finally: self._counts['encode_s'] += time.perf_counter()-start
        start = time.perf_counter()
        try:
            if self._member is None:
                self._member = gzip.GzipFile(filename='', fileobj=self._file, mode='wb', mtime=0)
            self._member.write(data)
        except BaseException:
            self.failed = True
            raise
        finally: self._counts['compress_write_s'] += time.perf_counter()-start
        self._counts['logged'] += transitions; self._counts['logged_rows'] += 1
        self._counts['encoded_bytes'] += len(data)
        self._pending_rows += 1; self._pending_transitions += transitions
        if self._pending_rows == 60: self.checkpoint()

    def checkpoint(self):
        if self.closed or self.failed: raise RuntimeError('journal is closed or failed')
        if not self._pending_rows: return self.stats
        try:
            start = time.perf_counter()
            try: self._member.close(); self._member = None
            finally: self._counts['compress_write_s'] += time.perf_counter()-start
            start = time.perf_counter()
            try: self._file.flush(); os.fsync(self._file.fileno())
            finally: self._counts['sync_s'] += time.perf_counter()-start
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
        if self.closed: return
        try:
            if not self.failed: self.checkpoint()
        finally:
            try:
                if self._member is not None:
                    self._member.close()
            finally:
                self._member = None
                self._file.close(); self.closed = True


class TransitionReadError(ValueError):
    pass


def iter_transitions(path, *, strict=True, diagnostics=None):
    """Read legacy/new gzip JSONL. Recovery requires an explicit diagnostic sink.

    Corrupt/truncated members are never silently skipped. strict raises, whereas
    recovery stops at the first bad member/JSON row and records the reason. A
    truncated single-member legacy log has no CRC-verified recoverable member.
    """
    if not strict and diagnostics is None: raise ValueError('recovery requires diagnostics')
    status = diagnostics if diagnostics is not None else {}
    status.update(complete=False, valid_prefix_rows=0, completed_members=0,
        valid_compressed_prefix_bytes=0, error=None, discarded_unverified_bytes=0)
    offset = 0; pending = b''
    with Path(path).open('rb') as stream:
        while True:
            if not pending: pending = stream.read(65536)
            if not pending:
                status['complete'] = True
                return
            start_offset = offset
            decoder = zlib.decompressobj(31)
            with tempfile.SpooledTemporaryFile(max_size=1024*1024) as member:
                try:
                    while not decoder.eof:
                        if not pending: pending = stream.read(65536)
                        if not pending: raise EOFError('unfinished gzip member')
                        chunk, pending = pending, b''
                        member.write(decoder.decompress(chunk))
                        consumed = len(chunk)-len(decoder.unused_data)
                        offset += consumed
                        pending = decoder.unused_data
                    member.seek(0)
                    for line in member:
                        if not line.strip(): continue
                        value = json.loads(line.decode('utf-8'))
                        status['valid_prefix_rows'] += 1
                        yield value
                except (EOFError, zlib.error, UnicodeError, ValueError) as error:
                    status.update(error=dict(type=type(error).__name__, message=str(error),
                        member_start_byte=start_offset),
                        discarded_unverified_bytes=0 if decoder.eof else member.tell())
                    if strict: raise TransitionReadError(str(status['error'])) from error
                    return
            status['completed_members'] += 1
            status['valid_compressed_prefix_bytes'] = offset


def _digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def publish_final_checkpoint(trainer, out, latest_checkpoint=None, metadata=None):
    """Reuse only an exact current PPO state; keep final.pt and old source bytes.

    Alias metadata lives in final_checkpoint.json because a hardlink must retain
    the original payload metadata. Both full-save and link are fsynced. Imports
    are lazy so native callers can import Isaac Gym first.
    """
    import random
    import numpy as np
    import torch
    out = Path(out); final = out/'final.pt'; manifest = out/'final_checkpoint.json'
    if final.exists() or manifest.exists(): raise FileExistsError('final publication already exists')
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter(); reused = False; differences = []
    latest = Path(latest_checkpoint) if latest_checkpoint is not None else None
    def same(a, b):
        if isinstance(a, torch.Tensor): return isinstance(b, torch.Tensor) and a.dtype==b.dtype and torch.equal(a.cpu(), b.cpu())
        if isinstance(a, np.ndarray): return isinstance(b, np.ndarray) and a.dtype==b.dtype and np.array_equal(a, b)
        if isinstance(a, dict): return isinstance(b, dict) and a.keys()==b.keys() and all(same(a[k], b[k]) for k in a)
        if isinstance(a, (list, tuple)): return type(a)==type(b) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        return a == b
    if latest is not None:
        if latest.resolve().parent != out.resolve(): raise ValueError('latest checkpoint must belong to this output directory')
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
    if reused: os.link(latest, final)
    else: trainer.save(final, metadata=metadata)
    save_or_link_s = time.perf_counter()-start
    start = time.perf_counter()
    with final.open('rb') as stream: os.fsync(stream.fileno())
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
