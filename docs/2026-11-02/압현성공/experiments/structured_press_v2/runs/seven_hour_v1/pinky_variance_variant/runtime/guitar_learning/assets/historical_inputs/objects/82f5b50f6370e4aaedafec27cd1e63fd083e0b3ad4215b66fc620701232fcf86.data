"""Add measured post-fetch contacts to the short-preparation training environment."""
from guitar_learning.core.environment_v4 import FreeGuitarEnvironment


class FrettingEnvironment(FreeGuitarEnvironment):
    def __init__(self, *args, fret_target, fret_contract, note_start_step, note_end_step,
                 contact_reader=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fret_target, self.fret_contract = fret_target, fret_contract
        self.note_start_step, self.note_end_step = note_start_step, note_end_step
        self.contact_reader = contact_reader
        self.contact_names = None
        self.fretting_tracker = None

    def reset(self):
        from guitar_learning.core.fretting_v1 import FrettingTracker
        self.contact_names = None
        self.fretting_tracker = FrettingTracker(self.fret_contract, self.note_start_step, self.note_end_step)
        sample, metadata = super().reset()
        metadata['fretting_scope'] = ('Contact-conditioned single-target fretting candidate; '
                                      'no string pressure, sound or intentional-release certification')
        metadata['contact_sampling'] = ('Query after fetch at the recorded physics step; '
                                        'internal CC_LAST_SUBSTEP feature generation time is not certified')
        return sample, metadata

    def _snapshot(self):
        from guitar_learning.core.fretting_v1 import measure_sample
        sample = super()._snapshot()
        scene = self.session.scene
        if self.contact_reader is None:
            from guitar_learning.native.native_contacts import body_names, read_contacts
            if self.contact_names is None:
                self.contact_names = body_names(scene.gym, scene.env)
            contacts = read_contacts(scene.gym, scene.env, self.contact_names)
        else:
            contacts = self.contact_reader(scene)
        if scene.native() != sample['native']:
            raise RuntimeError('Contact query changed the physical state')
        step = sample['native']['physics_step']
        contact_row = dict(physics_step=step, time_s=step / 240., contacts=contacts)
        measured = measure_sample(sample['native'], scene.human_bodies, scene.guitar_bodies,
                                  contact_row, self.fret_target, self.fret_contract)
        sample['native_contacts'] = contact_row
        sample['fretting_measurement'] = measured
        sample['fretting_progress'] = self.fretting_tracker.update(step, measured)
        return sample
