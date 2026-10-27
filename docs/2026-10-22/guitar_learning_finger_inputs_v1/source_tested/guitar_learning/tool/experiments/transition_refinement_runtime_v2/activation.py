"""Scope JSON changes to this process and restore them on ordinary exit."""
from contextlib import contextmanager

from guitar_learning.tool.experiments.transition_refinement_runtime_v2.serialization import install, restore


@contextmanager
def activated(observer):
    observer.check()
    token = install(guard=observer.check)
    try:
        yield observer
    finally:
        restore(token)
