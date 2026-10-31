"""Install the same checked JSON path inside each fresh spawn worker."""
from pathlib import Path

_base_factory = None


def _audit(spec, observer, *, completed=False, primary=None):
    from .audit import publish
    folder = Path(spec['out'])
    publish(observer, folder/'runtime_json_audit.json', completed=completed,
        mode='worker', out=folder, primary=primary)


def native_environment(spec, worker_id):
    import isaacgym
    import sys
    from .activation import activated
    from .observer import Observer
    from ..transition_refinement.worker import native_environment as source_factory
    factory = _base_factory or source_factory
    observer = Observer()
    session = activated(observer)
    entered = False
    try:
        session.__enter__()
        entered = True
        env = factory(spec, worker_id)
    except BaseException:
        if entered:
            session.__exit__(*sys.exc_info())
        _audit(spec, observer, primary=sys.exc_info()[1])
        raise
    original_close = env.close
    closed = False

    def close():
        nonlocal closed
        if closed:
            return
        closed = True
        try:
            return original_close()
        finally:
            session.__exit__(*sys.exc_info())
            # Only integers, strings and booleans; the original encoder is safe
            # for this report even if the guard rejected anomalous FP masks.
            primary = sys.exc_info()[1]
            _audit(spec, observer, completed=primary is None, primary=primary)

    env.close = close
    return env
