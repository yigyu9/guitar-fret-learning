"""Source collision geometry at recorded native poses; no native simulation."""
import json
from pathlib import Path
from types import SimpleNamespace

from .environment import ROOT, CONFIG_PATH  # Gym must load before MuJoCo
from .initial_overlap import build_probe


def recorded_probe(run, physics_step):
    report = json.loads((run/'report.json').read_text())
    states = json.loads((run/'states.json').read_text())
    state = next(s for s in states if s['physics_step']==physics_step)
    config = json.loads(CONFIG_PATH.read_text())
    # build_probe only reads body names/states and source geometry.
    names = [report['human_body_names'],report['guitar_body_names']]
    bodies = [state['human_body_states'],state['guitar_body_states']]
    scene = SimpleNamespace(config=config,human=0,guitar=1,env=None,
        gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:names[actor]),
        bodies=lambda actor:bodies[actor])
    return build_probe(scene)
