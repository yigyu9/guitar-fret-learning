__all__ = ["FretTask", "StrikeTask"]


def __getattr__(name):
    """Keep the two Isaac tasks independent until one is explicitly used."""
    if name == "FretTask":
        from .task_fret import FretTask
        return FretTask
    if name == "StrikeTask":
        from .task_strike import StrikeTask
        return StrikeTask
    raise AttributeError(name)
