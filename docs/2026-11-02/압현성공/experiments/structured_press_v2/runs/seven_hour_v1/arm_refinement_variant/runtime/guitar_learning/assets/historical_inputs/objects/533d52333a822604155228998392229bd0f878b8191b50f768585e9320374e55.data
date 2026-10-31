"""Reuse one native session while retaining the original episode reset logic.

Only the entry close of a successful reset is suppressed. Explicit close and
all reset failure paths still destroy the owned native session.
"""
import copy
import threading
from unittest.mock import patch
from . import training_environment
from .training_environment import ContactEnvironment

_CONSTRUCTION_LOCK = threading.RLock()


class PersistentContactEnvironment(ContactEnvironment):
    def __init__(self, *args, session_factory=None, **kwargs):
        if session_factory is None:
            from .persistent_session import PersistentHeadlessPreparedSession
            session_factory = PersistentHeadlessPreparedSession
        self._native_session_factory = session_factory
        self._skip_entry_close = False
        self._session_config = None
        super().__init__(*args, session_factory=self._episode_session, **kwargs)

    def _episode_session(self, config, out):
        if self.session is None:
            session = self._native_session_factory(config, out)
            # Assign ownership before validating so every failure is cleaned up.
            self.session = session
            if not callable(getattr(session, 'reset_episode', None)):
                raise TypeError('persistent session requires reset_episode(config, out)')
            if getattr(session, 'closed', False):
                raise RuntimeError('session factory returned a closed session')
            self._session_config = copy.deepcopy(config)
            return session
        if getattr(self.session, 'closed', False):
            raise RuntimeError('cannot reuse a closed native session')
        if config != self._session_config:
            raise ValueError('native session configuration changed between episodes')
        session = self.session
        session.reset_episode(config, out)
        if getattr(session, 'closed', False):
            raise RuntimeError('episode reset returned a closed native session')
        return session

    def reset(self):
        self._skip_entry_close = True
        try:
            return super().reset()
        except BaseException:
            # Covers failures before the base reset's own try block as well.
            self._skip_entry_close = False
            self.close()
            raise
        finally:
            self._skip_entry_close = False

    def close(self):
        if self._skip_entry_close:
            self._skip_entry_close = False
            self.ready = False
            return
        try:
            super().close()
        finally:
            self.session = None
            self._session_config = None


def build_persistent_environment(config, out, **kwargs):
    """Construct original legacy/dense/pool wrappers with persistent control.

    The module binding is restored before returning. Construction is serialized
    within this worker process; no source files or existing instances change.
    """
    from .task_sampling import build_environment
    with _CONSTRUCTION_LOCK:
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            return build_environment(config, out, **kwargs)
