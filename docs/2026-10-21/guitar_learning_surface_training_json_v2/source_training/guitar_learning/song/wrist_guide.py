"""Soft wrist positioning from the agreed pose in the live guitar frame.

The prepared pose has a measured clean index/fret5 contact candidate. Only
the song's hand anchor is used; legacy absolute wrist offsets are not targets.
This guide measures posture, not calibrated pressure or musical success.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from guitar_learning.core.geometry_v1 import frame


SCHEMA = 'guitar_learning.song_wrist_guide.v1'
POSITION_RADIUS_M = .04
ORIENTATION_RADIUS_RAD = .6


def load_anchor_track(bundle):
    """Read the manifest-verified 60Hz anchor track, ignoring wrist offsets."""
    root = Path(bundle).resolve()
    relative = 'training/hand_position_targets.json'
    payload = (root / relative).read_bytes()
    manifest = json.loads((root / 'manifest.json').read_text())
    entry = manifest.get('files', {}).get(relative)
    if (not isinstance(entry, dict) or entry.get('bytes') != len(payload) or
            entry.get('sha256') != hashlib.sha256(payload).hexdigest()):
        raise ValueError('hand anchor manifest fingerprint mismatch')
    document = json.loads(payload)
    if (document.get('schema') != 'tab2body.hand_position_targets.v1' or
            document.get('coordinate_frame') != 'guitar local'):
        raise ValueError('guitar-local hand anchor schema required')
    frames = document.get('frames')
    if not isinstance(frames, list) or not frames:
        raise ValueError('nonempty hand anchor frames required')
    anchors = []
    for index, row in enumerate(frames):
        if not isinstance(row, dict) or type(row.get('frame')) is not int or row['frame'] != index:
            raise ValueError('sequential integer hand anchor frames required')
        timestamp, anchor = row.get('t'), row.get('anchor_fret')
        if (type(timestamp) not in (int, float) or not math.isfinite(timestamp) or
                abs(timestamp - index / 60.) > 5e-5):
            raise ValueError('hand anchor time must match its 60Hz frame')
        if (type(anchor) not in (int, float) or not math.isfinite(anchor) or
                not 1 <= anchor <= 22):
            raise ValueError('finite hand anchor fret in1..22 required')
        anchors.append(float(anchor))
    return dict(times_s=[index / 60. for index in range(len(frames))],
                anchors=anchors, ignored_fields=['wrist_pos_guitar', 'allowed_radius_m', 'offsets_m'])


class WristGuide:
    def __init__(self, bundle, sample, human_names, guitar_names, pre_roll_s=3.):
        if type(pre_roll_s) not in (int, float) or not math.isfinite(pre_roll_s) or pre_roll_s < 0:
            raise ValueError('finite nonnegative wrist guide pre-roll required')
        self.track = load_anchor_track(bundle)
        self.human_names, self.guitar_names = tuple(human_names), tuple(guitar_names)
        self.pre_roll_s = float(pre_roll_s)
        self.reference_wrist, self.reference_rotation, self.reference_frets = self._sample(sample)

    def _sample(self, sample):
        native, geometry = sample['native'], sample['geometry']
        step = native['physics_step']
        if (isinstance(step, bool) or not isinstance(step, (int, np.integer)) or step < 0 or
                geometry['physics_step'] != step):
            raise ValueError('matching native/geometry physics steps required')
        if (len(set(self.human_names)) != len(self.human_names) or
                len(set(self.guitar_names)) != len(self.guitar_names) or
                len(native['human_body_states']) != len(self.human_names) or
                len(native['guitar_body_states']) != len(self.guitar_names)):
            raise ValueError('unique aligned wrist guide body names required')
        wrist = native['human_body_states'][self.human_names.index('L_Wrist')]
        guitar = native['guitar_body_states'][self.guitar_names.index('guitar')]
        wp, wr = frame(wrist)
        gp, gr = frame(guitar)
        frets = np.asarray(geometry['fret_markers_G_m'], dtype=float)
        if frets.shape != (23, 3) or not np.isfinite(frets).all():
            raise ValueError('finite live nut and22 fret markers required')
        return gr.inv().apply(wp - gp), gr.inv() * wr, frets.copy()

    def metadata(self):
        return dict(schema=SCHEMA, reference_anchor_fret=5,
                    position_radius_m=POSITION_RADIUS_M,
                    orientation_radius_rad=ORIENTATION_RADIUS_RAD,
                    position_full_score_radius_m=.02,
                    reference='actual reset wrist in guitar frame; fret5 clean contact candidate',
                    target='reset wrist x/z and live anchor-to-fret5 y displacement',
                    orientation='weak actual reset relative wrist posture prior',
                    ignored_legacy_wrist_offsets=True,
                    scope='soft posture shaping; not reachability, pressure or musical success')

    def measure(self, sample, now_s):
        if not np.isfinite(now_s) or now_s < 0:
            raise ValueError('finite nonnegative wrist guide time required')
        wrist, rotation, frets = self._sample(sample)
        if not np.allclose(frets, self.reference_frets, atol=1e-5, rtol=0):
            raise ValueError('local fret geometry changed during wrist guidance')
        anchor = float(np.interp(float(now_s) - self.pre_roll_s,
                                 self.track['times_s'], self.track['anchors']))
        fret_y = float(np.interp(anchor, np.arange(1, 23), frets[1:, 1]))
        target = self.reference_wrist + np.array([0., fret_y - frets[5, 1], 0.])
        delta = target - wrist
        rotation_error = (self.reference_rotation.inv() * rotation).as_rotvec()
        distance, angle = float(np.linalg.norm(delta)), float(np.linalg.norm(rotation_error))
        return dict(schema=SCHEMA, anchor_fret=anchor, target_G_m=target.tolist(),
                    wrist_G_m=wrist.tolist(), delta_G_m=delta.tolist(),
                    rotation_error_rad=rotation_error.tolist(), distance_m=distance,
                    angle_rad=angle,
                    position_score=math.exp(-(max(0., distance - .02) / POSITION_RADIUS_M) ** 2),
                    orientation_score=math.exp(-(angle / ORIENTATION_RADIUS_RAD) ** 2),
                    ready=bool(distance <= POSITION_RADIUS_M and angle <= ORIENTATION_RADIUS_RAD))
