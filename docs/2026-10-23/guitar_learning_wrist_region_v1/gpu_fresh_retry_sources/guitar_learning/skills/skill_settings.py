"""Explicit hand-internal stage selection; no automatic curriculum promotion."""
import copy
from guitar_learning.skills.specialist_settings import settings_document as specialist_settings

SKILLS = dict(left=('reach', 'contact', 'hold', 'timed'),
              right=('ready', 'cross', 'timed'))


def settings_document(value):
    if not isinstance(value, dict):
        raise ValueError('settings object required')
    value = copy.deepcopy(value)
    skill = value.pop('skill', None)
    stage = value.get('specialist')
    role = stage.get('role') if isinstance(stage, dict) else None
    if role not in SKILLS or not isinstance(skill, str) or skill not in SKILLS[role]:
        raise ValueError('explicit skill matching left/right specialist role required')
    other = 'right' if role == 'left' else 'left'
    if stage.get(other+'_checkpoint') is not None:
        raise ValueError('hand-internal stages do not accept a frozen partner')
    settings = specialist_settings(value)
    settings['skill'] = skill
    return settings
