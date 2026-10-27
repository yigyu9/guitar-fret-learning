"""Publish float-free runtime evidence without replacing an earlier failure."""
import json
import sys

from .serialization import SCHEMA


def publish(observer, path, *, completed, mode, out, primary=None, worker_audits=None):
    report = dict(observer.summary(), schema='guitar_learning.runtime_json_audit.v1',
        backend=SCHEMA, completed=completed, mode=mode, out=str(out.resolve()),
        worker_audit_sha256=worker_audits or {},
        failure=dict(type=type(primary).__name__, message=str(primary)) if primary else None)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2)+'\n')
    except BaseException as secondary:
        if primary is None:
            raise
        primary.runtime_audit_error = secondary
        print('[runtime audit] secondary failure: '+str(secondary), file=sys.stderr, flush=True)
