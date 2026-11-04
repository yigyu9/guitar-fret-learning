__all__ = ["StrikeTask"]


def __getattr__(name):
    """Load the Isaac task only when explicitly requested."""
    if name == "StrikeTask":
        from .task_strike import StrikeTask
        return StrikeTask
    raise AttributeError(name)
