"""Deterministic first-episode evaluation through strict native checkpoint replay."""
def evaluate(manifest, checkpoint, out):
    from .native_probe import run
    return run(manifest, out, checkpoint=checkpoint)
