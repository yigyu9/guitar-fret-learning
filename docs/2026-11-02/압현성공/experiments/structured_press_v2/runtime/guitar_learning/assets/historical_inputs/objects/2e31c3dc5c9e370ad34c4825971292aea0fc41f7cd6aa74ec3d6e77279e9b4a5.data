"""Recorded-session single-note contracts shared by current learning tests."""
import copy
from pathlib import Path

from guitar_learning.quality.musical_quality_environment import build_environment
from guitar_learning.tests.test_skill_environment import LongRecordedSession


def fixed_note_contract(folder, role='left'):
    sessions = []

    def factory(config, out):
        session = LongRecordedSession(config, out)
        sessions.append(session)
        return session

    def contacts(scene):
        return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])

    env = build_environment({}, Path(folder)/('environment_'+role), role=role,
        bundle='data/song_bundles/05_BN2-131-B_solo',
        session_factory=factory, contact_reader=contacts)
    try:
        env.reset()
        return copy.deepcopy(env.contract)
    finally:
        env.close()
