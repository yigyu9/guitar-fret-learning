"""왼손 fret 학습 goal 로더.

`build_fret_training_data.py`가 만든 60 Hz JSON을 GPU 텐서로 올리고, 환경별 재생
인덱스·룩어헤드 관측·손가락별 13-D next-goal·정규화된 곡 진행률·기타 로컬 손목 soft target을 제공한다.
줄 축은 파일에 저장된 Isaac 순서(index 0=high-e, 5=low-E)를 그대로 쓴다.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np
import torch


FINGER_EVENT_DIM = 13
FINGER_EVENT_TIME_SCALE_S = 1.0
N_GUITAR_STRINGS = 6
MAX_ASSET_FRET = 22
# Gross-corruption bounds, deliberately much wider than the current G0 workspace.
# They catch unit/frame mistakes without constraining later guitar-placement stages.
MAX_WRIST_TARGET_ABS_COORD_M = 2.0
MAX_WRIST_TARGET_RADIUS_M = 1.0
FINGER_EVENT_FIELDS = (
    "next_string_mask_0", "next_string_mask_1", "next_string_mask_2",
    "next_string_mask_3", "next_string_mask_4", "next_string_mask_5",
    "next_fret", "time_to_next_goal", "next_valid",
    "time_to_current_change", "relation_keep", "relation_move", "relation_rest",
)


def _is_integer(value):
    return isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_))


def _is_finite_number(value):
    return (isinstance(value, (int, float, np.integer, np.floating))
            and not isinstance(value, (bool, np.bool_))
            and math.isfinite(float(value)))


def _validate_hand_position_fields(
        frame, frame_idx, *, prefix="frame",
        anchor_key="hand_anchor_fret",
        allowed_key="hand_allowed_fret_range"):
    """Validate the per-goal hand-anchor and allowed-fret-band fields."""
    anchor = frame.get(anchor_key)
    if not _is_finite_number(anchor):
        raise ValueError(
            f"{prefix} {frame_idx}: {anchor_key} must be a finite number")
    anchor = float(anchor)
    if not 1.0 <= anchor <= float(MAX_ASSET_FRET):
        raise ValueError(
            f"{prefix} {frame_idx}: {anchor_key} {anchor} is outside "
            f"1..{MAX_ASSET_FRET}")

    allowed = frame.get(allowed_key)
    if (not isinstance(allowed, (list, tuple, np.ndarray))
            or len(allowed) != 2):
        raise ValueError(
            f"{prefix} {frame_idx}: {allowed_key} must contain "
            "exactly [low, high]")
    if not all(_is_finite_number(value) for value in allowed):
        raise ValueError(
            f"{prefix} {frame_idx}: {allowed_key} must be finite")
    low, high = (float(allowed[0]), float(allowed[1]))
    if not (1.0 <= low <= high <= float(MAX_ASSET_FRET)):
        raise ValueError(
            f"{prefix} {frame_idx}: {allowed_key} [{low}, {high}] "
            f"must be ordered inside 1..{MAX_ASSET_FRET}")
    if not low <= anchor <= high:
        raise ValueError(
            f"{prefix} {frame_idx}: {anchor_key} {anchor} must lie inside "
            f"{allowed_key} [{low}, {high}]")
    return anchor, (low, high)


def validate_hand_position_target_frames(source, *, required_start_t=None,
                                         required_end_t=None):
    """Validate interpolated wrist-target samples before NumPy consumes them.

    Samples may be sparse, but time and optional frame indices must increase
    strictly.  Wrist positions are guitar-local xyz metres and the allowed
    radius is a positive metre value.  Generous gross bounds catch accidental
    centimetre/millimetre or world-frame input while leaving later G1/G2 poses
    unconstrained.
    """
    if not isinstance(source, (list, tuple)) or not source:
        raise ValueError("hand target JSON frames must be a non-empty sequence")

    previous_t = None
    previous_frame = None
    for target_idx, target in enumerate(source):
        if not isinstance(target, dict):
            raise ValueError(
                f"hand target {target_idx}: target record must be an object")
        timestamp = target.get("t")
        if not _is_finite_number(timestamp):
            raise ValueError(f"hand target {target_idx}: t must be finite")
        timestamp = float(timestamp)
        if timestamp < 0.0:
            raise ValueError(f"hand target {target_idx}: t must be non-negative")
        if previous_t is not None and timestamp <= previous_t:
            raise ValueError(
                "hand target timestamps must be strictly increasing; "
                f"sample {target_idx} has t={timestamp} after t={previous_t}")
        previous_t = timestamp

        stored_frame = target.get("frame")
        if not _is_integer(stored_frame) or int(stored_frame) < 0:
            raise ValueError(
                f"hand target {target_idx}: frame must be a non-negative integer")
        stored_frame = int(stored_frame)
        if previous_frame is not None and stored_frame <= previous_frame:
            raise ValueError(
                "hand target frame indices must be strictly increasing; "
                f"sample {target_idx} has frame={stored_frame} after "
                f"frame={previous_frame}")
        previous_frame = stored_frame

        _validate_hand_position_fields(
            target, target_idx, prefix="hand target",
            anchor_key="anchor_fret", allowed_key="allowed_fret_range")

        wrist = target.get("wrist_pos_guitar")
        if (not isinstance(wrist, (list, tuple, np.ndarray))
                or len(wrist) != 3):
            raise ValueError(
                f"hand target {target_idx}: wrist_pos_guitar must contain xyz")
        if not all(_is_finite_number(value) for value in wrist):
            raise ValueError(
                f"hand target {target_idx}: wrist_pos_guitar must be finite")
        if any(abs(float(value)) > MAX_WRIST_TARGET_ABS_COORD_M for value in wrist):
            raise ValueError(
                f"hand target {target_idx}: wrist_pos_guitar is outside the "
                f"gross +/-{MAX_WRIST_TARGET_ABS_COORD_M}m range")

        radius = target.get("allowed_radius_m")
        if not _is_finite_number(radius):
            raise ValueError(
                f"hand target {target_idx}: allowed_radius_m must be finite")
        radius = float(radius)
        if not 0.0 < radius <= MAX_WRIST_TARGET_RADIUS_M:
            raise ValueError(
                f"hand target {target_idx}: allowed_radius_m {radius} must be in "
                f"(0, {MAX_WRIST_TARGET_RADIUS_M}]")

    start_t = float(source[0]["t"])
    end_t = float(source[-1]["t"])
    tolerance = 1e-4
    if (required_start_t is not None
            and start_t > float(required_start_t) + tolerance):
        raise ValueError(
            f"hand targets start at {start_t}, after required goal time "
            f"{float(required_start_t)}")
    if (required_end_t is not None
            and end_t < float(required_end_t) - tolerance):
        raise ValueError(
            f"hand targets end at {end_t}, before required goal time "
            f"{float(required_end_t)}")
    return {
        "contract_valid": True,
        "n_samples": len(source),
        "start_t": start_t,
        "end_t": end_t,
    }


def validate_fret_goal_frames(frames, fps=None, allow_barre=False,
                              require_timeline=False):
    """Validate the physical guitar-asset and per-frame goal contract.

    The current asset has six strings and frets 1..22.  ``-1`` and ``0`` are
    reserved for NO_PRESS and DONT_CARE.  A fretted target must name exactly one
    of the four policy-controlled fretting fingers.  Multi-string use of one
    finger is disabled in S0; the optional extension only accepts an explicit,
    contiguous index-finger barre at one fret.

    ``require_timeline`` is used by the JSON loader.  The lower-level future-goal
    builder also calls this function without it so synthetic frame lists need not
    repeat the frame/time fields.
    """
    if not isinstance(frames, (list, tuple)) or not frames:
        raise ValueError("fret goal frames must be a non-empty sequence")
    if require_timeline and (not _is_integer(fps) or int(fps) <= 0):
        raise ValueError("fret goal timeline requires a positive integer fps")

    press_targets = 0
    max_fret = 0
    multistring_finger_frames = 0
    previous_t = None
    for frame_idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError(f"frame {frame_idx}: frame record must be an object")
        if require_timeline:
            stored_idx = frame.get("frame")
            if not _is_integer(stored_idx):
                raise ValueError(f"frame {frame_idx}: frame index must be an integer")
            if int(stored_idx) != frame_idx:
                raise ValueError(
                    f"frame {frame_idx}: frame indices must start at 0 and be contiguous; "
                    f"stored index is {stored_idx}")
            timestamp = frame.get("t")
            if not _is_finite_number(timestamp):
                raise ValueError(f"frame {frame_idx}: timestamp must be finite")
            timestamp = float(timestamp)
            if previous_t is not None and timestamp <= previous_t:
                raise ValueError(f"frame {frame_idx}: timestamps must be strictly increasing")
            expected_t = frame_idx / float(fps)
            if abs(timestamp - expected_t) > 1e-4:
                raise ValueError(
                    f"frame {frame_idx}: timestamp {timestamp} does not match "
                    f"frame/fps ({expected_t})")
            previous_t = timestamp

        # These fields are required by the JSON loader.  Lower-level synthetic
        # future-goal tests may omit them entirely, but a partial pair is never
        # accepted because it would later create a malformed observation.
        if (require_timeline or "hand_anchor_fret" in frame
                or "hand_allowed_fret_range" in frame):
            _validate_hand_position_fields(frame, frame_idx)

        arrays = {}
        for field in ("fret_goal", "finger_goal", "barre_goal"):
            values = frame.get(field)
            if not isinstance(values, (list, tuple, np.ndarray)) or len(values) != N_GUITAR_STRINGS:
                raise ValueError(
                    f"frame {frame_idx}: {field} must contain exactly "
                    f"{N_GUITAR_STRINGS} strings")
            arrays[field] = values

        fret_goal = arrays["fret_goal"]
        finger_goal = arrays["finger_goal"]
        barre_goal = arrays["barre_goal"]
        for string in range(N_GUITAR_STRINGS):
            fret = fret_goal[string]
            finger = finger_goal[string]
            barre = barre_goal[string]
            if not _is_integer(fret):
                raise ValueError(
                    f"frame {frame_idx}, string {string}: fret must be an integer")
            if int(fret) < -1 or int(fret) > MAX_ASSET_FRET:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: fret {fret} is outside "
                    f"the asset contract -1..{MAX_ASSET_FRET}")
            if not _is_integer(finger):
                raise ValueError(
                    f"frame {frame_idx}, string {string}: finger must be an integer")
            if int(finger) < 0 or int(finger) > 4:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: finger {finger} is outside 0..4")
            if not isinstance(barre, (bool, np.bool_)):
                raise ValueError(
                    f"frame {frame_idx}, string {string}: barre must be boolean")

            fret = int(fret)
            finger = int(finger)
            barre = bool(barre)
            if fret > 0 and finger == 0:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: PRESS fret requires finger 1..4")
            if fret <= 0 and finger != 0:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: non-PRESS goal requires finger 0")
            if barre and (fret <= 0 or finger != 1):
                raise ValueError(
                    f"frame {frame_idx}, string {string}: barre requires an index-finger PRESS")
            if barre and not allow_barre:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: barre is disabled (allow_barre=False)")
            if fret > 0:
                press_targets += 1
                max_fret = max(max_fret, fret)

        for finger in range(1, 5):
            active = [string for string in range(N_GUITAR_STRINGS)
                      if int(finger_goal[string]) == finger
                      and int(fret_goal[string]) > 0]
            if len(active) <= 1:
                continue
            multistring_finger_frames += 1
            frets = {int(fret_goal[string]) for string in active}
            if not allow_barre:
                raise ValueError(
                    f"frame {frame_idx}, finger {finger}: one finger targets multiple "
                    f"strings {active} while allow_barre=False")
            if finger != 1 or len(frets) != 1:
                raise ValueError(
                    f"frame {frame_idx}, finger {finger}: a barre must use the index "
                    f"finger at one fret, got frets {sorted(frets)}")
            if not all(bool(barre_goal[string]) for string in active):
                raise ValueError(
                    f"frame {frame_idx}, finger {finger}: multi-string targets must be "
                    "marked as an explicit barre")
            if active[-1] - active[0] + 1 != len(active):
                raise ValueError(
                    f"frame {frame_idx}, finger {finger}: barre strings must be contiguous")

    return {
        "contract_valid": True,
        "max_fret": int(max_fret),
        "press_targets": int(press_targets),
        "multistring_finger_frames": int(multistring_finger_frames),
        "allow_barre": bool(allow_barre),
    }


def build_sustain_event_raster(frames, boundary_grace_frames=3):
    """Assign a stable id and evaluation mask to every per-string PRESS run.

    A run is maximal while string, fret and assigned finger remain unchanged.
    Long notes ignore a small attack/release boundary; short notes are evaluated
    in full so trimming never erases the event.
    """
    if boundary_grace_frames < 0:
        raise ValueError("sustain boundary grace must be non-negative")
    n_frames = len(frames)
    event_id = np.full((n_frames, 6), -1, dtype=np.int32)
    eligible = np.zeros((n_frames, 6), dtype=bool)
    events = []
    next_id = 0
    for string in range(6):
        start = 0
        while start < n_frames:
            frame = frames[start]
            fret = int(frame["fret_goal"][string])
            finger = int(frame["finger_goal"][string])
            if fret <= 0 or finger <= 0:
                start += 1
                continue
            end = start + 1
            while end < n_frames:
                following = frames[end]
                if (int(following["fret_goal"][string]) != fret
                        or int(following["finger_goal"][string]) != finger):
                    break
                end += 1
            length = end - start
            # Preserve short notes; use full boundary grace only when at least
            # three interior frames remain after trimming both sides.
            grace = (boundary_grace_frames
                     if length >= 2 * boundary_grace_frames + 3 else 0)
            event_id[start:end, string] = next_id
            eligible[start + grace:end - grace, string] = True
            events.append({
                "event_id": next_id,
                "string": string,
                "fret": fret,
                "finger": finger,
                "start_frame": start,
                "end_frame": end,
                "length_frames": length,
                "boundary_grace_frames": grace,
                "eligible_frames": length - 2 * grace,
            })
            next_id += 1
            start = end
    return event_id, eligible, events


def build_finger_next_goal_vectors(frames, fps,
                                   time_scale_s=FINGER_EVENT_TIME_SCALE_S,
                                   allow_barre=False):
    """Build a 13-D future-goal vector for every frame and fretting finger.

    Contract::

        [next_string_mask(6), next_fret, time_to_next_goal, next_valid,
         time_to_current_change, KEEP, MOVE, REST]

    The source of truth is the already rasterized 60 Hz goal, rather than raw
    note events.  With ``allow_barre=True``, an explicit same-fret barre becomes
    a multi-string mask; S0 rejects any same-finger multi-string target.
    String-mask order is the stored Isaac order: 0=high-e, 5=low-E.
    """
    n_frames = len(frames)
    if n_frames < 1 or fps <= 0 or time_scale_s <= 0:
        raise ValueError("finger next-goal rasterization requires positive sizes")
    validation = validate_fret_goal_frames(frames, allow_barre=allow_barre)
    vectors = np.zeros((int(n_frames), 4, FINGER_EVENT_DIM), dtype=np.float32)
    vectors[:, :, 12] = 1.0  # REST when no later active goal exists.
    masks = np.zeros((n_frames, 4, 6), dtype=np.float32)
    frets = np.zeros((n_frames, 4), dtype=np.int16)
    explicit_barre = np.zeros((n_frames, 4), dtype=bool)

    for frame_idx, frame in enumerate(frames):
        fret_goal = np.asarray(frame["fret_goal"], dtype=np.int16)
        finger_goal = np.asarray(frame["finger_goal"], dtype=np.int16)
        barre_goal = np.asarray(frame["barre_goal"], dtype=bool)
        for finger in range(1, 5):
            active = (finger_goal == finger) & (fret_goal > 0)
            active_frets = np.unique(fret_goal[active])
            if active_frets.size > 1:
                raise ValueError(
                    f"frame {frame_idx}, finger {finger}: one finger cannot target "
                    f"multiple frets {active_frets.tolist()}")
            if active_frets.size == 1:
                masks[frame_idx, finger - 1, active] = 1.0
                frets[frame_idx, finger - 1] = active_frets[0]
                explicit_barre[frame_idx, finger - 1] = bool(np.any(barre_goal[active]))

    relation_counts = {"keep": 0, "move": 0, "rest": 0}
    for finger_idx in range(4):
        # Maximal runs of an identical (string mask, fret) state.
        runs = []
        start = 0
        for frame_idx in range(1, n_frames + 1):
            changed = (frame_idx == n_frames or
                       frets[frame_idx, finger_idx] != frets[start, finger_idx] or
                       not np.array_equal(masks[frame_idx, finger_idx],
                                          masks[start, finger_idx]))
            if changed:
                runs.append((start, frame_idx,
                             masks[start, finger_idx].copy(),
                             int(frets[start, finger_idx])))
                start = frame_idx

        for run_idx, (run_start, run_end, current_mask, current_fret) in enumerate(runs):
            next_idx = next((idx for idx in range(run_idx + 1, len(runs))
                             if runs[idx][3] > 0), None)
            for frame_idx in range(run_start, run_end):
                out = vectors[frame_idx, finger_idx]
                if current_fret > 0:
                    out[9] = min((run_end - frame_idx) / float(fps),
                                 time_scale_s) / time_scale_s
                if next_idx is None:
                    relation_counts["rest"] += 1
                    continue

                next_start, _, next_mask, next_fret = runs[next_idx]
                out[0:6] = next_mask
                out[6] = next_fret / 22.0
                out[7] = min(max(next_start - frame_idx, 0) / float(fps),
                             time_scale_s) / time_scale_s
                out[8] = 1.0
                out[10:13] = 0.0
                keep = (current_fret > 0 and next_idx == run_idx + 1
                        and current_fret == next_fret
                        and bool(np.any(current_mask * next_mask)))
                out[10 if keep else 11] = 1.0
                relation_counts["keep" if keep else "move"] += 1

    multi = masks.sum(axis=-1) > 1
    active_indices = np.flatnonzero(multi)
    noncontiguous = 0
    for flat_idx in active_indices:
        frame_idx, finger_idx = np.unravel_index(flat_idx, multi.shape)
        strings = np.flatnonzero(masks[frame_idx, finger_idx])
        noncontiguous += int(strings[-1] - strings[0] + 1 != len(strings))
    return vectors, {
        "contract_valid": validation["contract_valid"],
        "allow_barre": bool(allow_barre),
        "multistring_finger_frames": int(multi.sum()),
        "explicit_barre_finger_frames": int((multi & explicit_barre).sum()),
        "implicit_barre_finger_frames": int((multi & ~explicit_barre).sum()),
        "noncontiguous_mask_frames": int(noncontiguous),
        "relation_frame_counts": relation_counts,
        "time_scale_s": float(time_scale_s),
    }


class FretGoalSequence:
    """한 곡의 고정 60 Hz goal을 병렬 반복 연습 환경에 공급한다."""

    def __init__(self, path, num_envs, device="cuda:0", hand_targets_path=None,
                 lookahead=(0, 6, 15), random_start=False, seed=0,
                 sustain_boundary_grace_frames=3, allow_barre=False):
        data = json.loads(Path(path).read_text())
        if data.get("schema") != "tab2body.fret_training.v1":
            raise ValueError(f"unsupported fret goal schema: {data.get('schema')}")
        raw_fps = data["metadata"]["fps"]
        if not _is_integer(raw_fps):
            raise ValueError(f"fret goal fps must be an integer, got {raw_fps!r}")
        fps = int(raw_fps)
        if fps != 60:
            raise ValueError(f"physics/goal clock mismatch: expected 60 Hz, got {fps}")
        frames = data["frames"]
        if not frames:
            raise ValueError("fret training JSON contains no frames")
        self.allow_barre = bool(allow_barre)
        self.validation_metadata = validate_fret_goal_frames(
            frames, fps=fps, allow_barre=self.allow_barre, require_timeline=True)

        self.path = str(Path(path).resolve())
        self.num_envs = int(num_envs)
        self.device = torch.device(device)
        self.fps = fps
        self.n_frames = len(frames)
        self.lookahead = tuple(int(x) for x in lookahead)
        self.random_start = bool(random_start)
        self.random_start_probability = 1.0 if self.random_start else 0.0
        self.generator = torch.Generator(device=self.device)
        self.generator.manual_seed(seed)

        self.fret = torch.tensor([f["fret_goal"] for f in frames],
                                 dtype=torch.float32, device=self.device)
        self.finger = torch.tensor([f["finger_goal"] for f in frames],
                                   dtype=torch.long, device=self.device)
        self.barre = torch.tensor([f["barre_goal"] for f in frames],
                                  dtype=torch.bool, device=self.device)
        self.anchor = torch.tensor([f["hand_anchor_fret"] for f in frames],
                                   dtype=torch.float32, device=self.device)
        self.allowed = torch.tensor([f["hand_allowed_fret_range"] for f in frames],
                                    dtype=torch.float32, device=self.device)
        self.wrist, self.wrist_radius, self.has_wrist_target = self._load_wrist_targets(
            frames, hand_targets_path)
        finger_events, self.finger_event_metadata = build_finger_next_goal_vectors(
            frames, self.fps, allow_barre=self.allow_barre)
        self.finger_events = torch.tensor(
            finger_events, dtype=torch.float32, device=self.device)
        sustain_ids, sustain_eligible, self.sustain_events = build_sustain_event_raster(
            frames, boundary_grace_frames=sustain_boundary_grace_frames)
        self.sustain_event_id = torch.tensor(
            sustain_ids, dtype=torch.long, device=self.device)
        self.sustain_eligible = torch.tensor(
            sustain_eligible, dtype=torch.bool, device=self.device)
        self.sustain_n_events = len(self.sustain_events)
        self.finger_event_fields = FINGER_EVENT_FIELDS
        self.string_mask_supports_barre = True
        self.barre_enabled = self.allow_barre
        self.frame_idx = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)

        # Fingertip-acquisition curriculum.  The source frames always come from
        # this song; no synthetic string/fret combinations are introduced.
        self.curriculum_stage = "full_song"
        self.practice_duration_frames = 0
        self.practice_remaining = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.practice_string = torch.full(
            (self.num_envs,), -1, dtype=torch.long, device=self.device)
        self.frozen_context_real_probability = 1.0
        self.frozen_context_real_mask = torch.ones(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.frozen_context_context_blend = torch.ones(
            self.num_envs, dtype=torch.float32, device=self.device)
        self.frozen_context_group_index = torch.full(
            (self.num_envs,), -1, dtype=torch.long, device=self.device)
        self.goal_pair_previous_frame = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.goal_pair_next_frame = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.goal_pair_before_remaining = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.goal_pair_group_index = torch.full(
            (self.num_envs,), -1, dtype=torch.long, device=self.device)
        self.goal_pair_incoming_finger = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.goal_pair_rehearsal_mask = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.goal_pair_sequence_mask = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.goal_pair_full_song_mask = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.goal_pair_preview_mask = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.goal_pair_rehearsal_probability = 0.0
        self.goal_pair_rehearsal_duration_frames = 150
        self.goal_pair_sequence_probability = 0.0
        self.goal_pair_sequence_duration_frames = 240
        self.goal_pair_sequence_full_song_fraction = 0.0
        self.goal_pair_preview_only = False
        self.goal_pair_transition_focus_finger = None
        self.goal_pair_transition_focus_probability = 1.0
        self.transition_max_changes = None
        self.practice_transition_count = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.practice_chord_focus_index = None
        self.practice_chord_focus_probability = 1.0
        events_by_finger = []
        event_groups_by_finger = []
        for finger in range(1, 5):
            rows = [(event["start_frame"], event["string"])
                    for event in self.sustain_events
                    if event["finger"] == finger]
            events_by_finger.append(torch.tensor(
                rows, dtype=torch.long, device=self.device).reshape(-1, 2))
            groups = {}
            for event in self.sustain_events:
                if event["finger"] == finger:
                    groups.setdefault((event["string"], event["fret"]), []).append(
                        (event["start_frame"], event["string"]))
            event_groups_by_finger.append(tuple(
                torch.tensor(group_rows, dtype=torch.long, device=self.device)
                for _, group_rows in sorted(groups.items())))
        self.practice_event_groups_by_finger = tuple(event_groups_by_finger)
        self.practice_available_fingers = tuple(
            index for index, rows in enumerate(events_by_finger) if rows.numel())

        # Static chords are sampled evenly by the number of active fingers.
        # The bridge catalogs retain only source-song states and transitions.
        run_starts = [0]
        for frame_idx in range(1, self.n_frames):
            changed = (not torch.equal(self.fret[frame_idx], self.fret[frame_idx - 1])
                       or not torch.equal(self.finger[frame_idx], self.finger[frame_idx - 1])
                       or not torch.equal(self.barre[frame_idx], self.barre[frame_idx - 1]))
            if changed:
                run_starts.append(frame_idx)
        chord_frames_by_finger_set = {}
        for frame_idx in run_starts:
            active = tuple(sorted({
                int(finger)
                for fret, finger in zip(
                    self.fret[frame_idx].tolist(),
                    self.finger[frame_idx].tolist())
                if fret > 0 and finger > 0
            }))
            if active:
                chord_frames_by_finger_set.setdefault(active, []).append(
                    frame_idx)
        preferred_sets = tuple(
            finger_set for finger_set in sorted(
                chord_frames_by_finger_set, key=lambda value: (len(value), value))
            if len(finger_set) >= 2)
        self.practice_available_chord_finger_sets = (
            preferred_sets or tuple(sorted(
                chord_frames_by_finger_set,
                key=lambda value: (len(value), value))))
        self.practice_chord_frames_by_finger_set = {
            finger_set: torch.tensor(
                rows, dtype=torch.long, device=self.device)
            for finger_set, rows in chord_frames_by_finger_set.items()
        }
        self.practice_transition_frames = torch.tensor(
            [frame for frame in run_starts[1:]
             if bool((self.fret[frame] > 0).any()
                     or (self.fret[frame - 1] > 0).any())],
            dtype=torch.long, device=self.device)
        change_flags = torch.zeros(
            self.n_frames, dtype=torch.long, device=self.device)
        if len(run_starts) > 1:
            change_flags[torch.tensor(
                run_starts[1:], dtype=torch.long,
                device=self.device)] = 1
        self.transition_change_prefix = change_flags.cumsum(dim=0)

        unique_states = {}
        for frame_idx in run_starts:
            if not bool((self.fret[frame_idx] > 0).any()):
                continue
            state = (
                tuple(int(value) for value in self.fret[frame_idx].tolist()),
                tuple(int(value) for value in self.finger[frame_idx].tolist()),
                tuple(bool(value) for value in self.barre[frame_idx].tolist()),
            )
            unique_states.setdefault(state, frame_idx)
        context_anchors = list(unique_states.values())
        context_anchors.extend(self.practice_transition_frames.tolist())
        context_anchors.extend(
            frame - 1 for frame in self.practice_transition_frames.tolist())
        context_anchors = sorted(dict.fromkeys(
            frame for frame in context_anchors
            if bool((self.fret[frame] > 0).any())))
        self.practice_frozen_context_frames = torch.tensor(
            context_anchors, dtype=torch.long, device=self.device)
        frozen_groups = {}
        for frame_idx in self.practice_frozen_context_frames.tolist():
            finger_set = tuple(sorted({
                int(finger)
                for fret, finger in zip(
                    self.fret[frame_idx].tolist(),
                    self.finger[frame_idx].tolist())
                if fret > 0 and finger > 0
            }))
            frozen_groups.setdefault(finger_set, []).append(frame_idx)
        self.practice_frozen_context_group_keys = tuple(
            sorted(frozen_groups, key=lambda value: (len(value), value)))
        self.practice_frozen_context_groups = tuple(
            torch.tensor(
                frozen_groups[key], dtype=torch.long, device=self.device)
            for key in self.practice_frozen_context_group_keys)

        def finger_targets(frame_idx):
            targets = {}
            fret_row = self.fret[frame_idx].tolist()
            finger_row = self.finger[frame_idx].tolist()
            for finger_number in range(1, 5):
                strings = tuple(
                    string for string, (fret, finger) in enumerate(
                        zip(fret_row, finger_row))
                    if fret > 0 and finger == finger_number)
                if strings:
                    targets[finger_number] = (
                        strings, int(max(fret_row[string] for string in strings)))
            return targets

        pair_groups = {}
        for transition in self.practice_transition_frames.tolist():
            previous = finger_targets(transition - 1)
            following = finger_targets(transition)
            kept = {
                finger for finger in previous.keys() & following.keys()
                if previous[finger] == following[finger]}
            incoming = tuple(sorted(
                finger for finger, target in following.items()
                if previous.get(finger) != target))
            outgoing = {
                finger for finger, target in previous.items()
                if following.get(finger) != target}
            if not previous and following:
                transition_type = "press"
            elif previous and not following:
                transition_type = "release"
            elif kept and len(following) > len(previous):
                transition_type = "add"
            elif kept and len(following) < len(previous):
                transition_type = "remove"
            elif incoming and outgoing:
                transition_type = "swap"
            elif incoming:
                transition_type = "move"
            else:
                transition_type = "context"
            group_key = (transition_type, incoming or (0,))
            pair_groups.setdefault(group_key, []).append(transition)
        self.practice_goal_pair_group_keys = tuple(sorted(pair_groups))
        self.practice_goal_pair_groups = tuple(
            torch.tensor(pair_groups[key], dtype=torch.long, device=self.device)
            for key in self.practice_goal_pair_group_keys)
        incoming_group_slots = {finger: [] for finger in range(1, 5)}
        no_incoming_group_slots = []
        for slot, (_, incoming) in enumerate(
                self.practice_goal_pair_group_keys):
            if incoming == (0,):
                no_incoming_group_slots.append(slot)
                continue
            for finger in incoming:
                incoming_group_slots[finger].append(slot)
        self.practice_goal_pair_groups_by_incoming = {
            finger: tuple(slots)
            for finger, slots in incoming_group_slots.items() if slots
        }
        self.practice_goal_pair_available_incoming_fingers = tuple(
            sorted(self.practice_goal_pair_groups_by_incoming))
        self.practice_goal_pair_no_incoming_group_slots = tuple(
            no_incoming_group_slots)
        incoming_group_count = sum(
            key[1] != (0,) for key in self.practice_goal_pair_group_keys)
        self.practice_goal_pair_incoming_group_fraction = (
            incoming_group_count / len(self.practice_goal_pair_group_keys)
            if self.practice_goal_pair_group_keys else 0.0)

        # per-lookahead: fret6 + finger6 + barre6 + anchor1 + allowed2 + wrist3 + dt1
        self.per_lookahead_dim = 25
        self.finger_event_dim = 4 * FINGER_EVENT_DIM
        # A fixed-song MLP must distinguish repeated, locally identical phrases.
        # The scalar phase supplies song context while physical state and explicit
        # goals remain responsible for feedback control.
        self.song_phase_dim = 1
        self.goal_dim = (len(self.lookahead) * self.per_lookahead_dim
                         + self.finger_event_dim + self.song_phase_dim)

    def _load_wrist_targets(self, train_frames, path):
        if path is None:
            self.wrist_validation_metadata = {
                "contract_valid": True, "source": "disabled",
                "n_samples": 0,
            }
            return (torch.zeros(self.n_frames, 3, device=self.device),
                    torch.full((self.n_frames,), 0.04, device=self.device), False)
        raw = json.loads(Path(path).read_text())
        if not isinstance(raw, dict):
            raise ValueError("hand target JSON root must be an object")
        if raw.get("schema") != "tab2body.hand_position_targets.v1":
            raise ValueError(f"unsupported hand target schema: {raw.get('schema')}")
        if raw.get("coordinate_frame") != "guitar local":
            raise ValueError(
                "hand target coordinate_frame must be 'guitar local'")
        source = raw.get("frames", [])
        dst_t = np.asarray([x["t"] for x in train_frames], dtype=np.float64)
        self.wrist_validation_metadata = validate_hand_position_target_frames(
            source, required_start_t=dst_t[0], required_end_t=dst_t[-1])
        src_t = np.asarray([x["t"] for x in source], dtype=np.float64)
        src_w = np.asarray([x["wrist_pos_guitar"] for x in source], dtype=np.float64)
        src_r = np.asarray([x["allowed_radius_m"] for x in source], dtype=np.float64)
        wrist = np.stack([np.interp(dst_t, src_t, src_w[:, k]) for k in range(3)], axis=1)
        radius = np.interp(dst_t, src_t, src_r)
        if not np.isfinite(wrist).all() or not np.isfinite(radius).all():
            raise ValueError("interpolated hand targets must remain finite")
        return (torch.tensor(wrist, dtype=torch.float32, device=self.device),
                torch.tensor(radius, dtype=torch.float32, device=self.device), True)

    def _sample_frozen_context_frames(
            self, count, focus_finger=None, focus_probability=0.0):
        if not self.practice_frozen_context_groups:
            raise RuntimeError(
                "frozen-context replay requires at least one source state")
        group_slot = torch.randint(
            len(self.practice_frozen_context_groups), (int(count),),
            generator=self.generator, device=self.device)
        if focus_finger is not None and focus_probability > 0.0:
            focus_slots = tuple(
                slot for slot, finger_set in enumerate(
                    self.practice_frozen_context_group_keys)
                if int(focus_finger) in finger_set)
            if focus_slots:
                focused = torch.rand(
                    int(count), generator=self.generator,
                    device=self.device) < float(focus_probability)
                focus_count = int(focused.sum())
                if focus_count:
                    options = torch.tensor(
                        focus_slots, dtype=torch.long, device=self.device)
                    group_slot[focused] = options[torch.randint(
                        len(focus_slots), (focus_count,),
                        generator=self.generator, device=self.device)]
        selected_frames = torch.zeros(
            int(count), dtype=torch.long, device=self.device)
        for slot, catalog in enumerate(self.practice_frozen_context_groups):
            selected = group_slot == slot
            selected_count = int(selected.sum())
            if selected_count == 0:
                continue
            frame_slot = torch.randint(
                catalog.numel(), (selected_count,),
                generator=self.generator, device=self.device)
            selected_frames[selected] = catalog[frame_slot]
        return selected_frames, group_slot

    def reset(self, env_ids):
        if env_ids.numel() == 0:
            return
        self.frame_idx[env_ids] = 0
        self.frozen_context_real_mask[env_ids] = True
        self.frozen_context_context_blend[env_ids] = 1.0
        self.frozen_context_group_index[env_ids] = -1
        self.goal_pair_previous_frame[env_ids] = 0
        self.goal_pair_next_frame[env_ids] = 0
        self.goal_pair_before_remaining[env_ids] = 0
        self.goal_pair_group_index[env_ids] = -1
        self.goal_pair_incoming_finger[env_ids] = 0
        self.goal_pair_rehearsal_mask[env_ids] = False
        self.goal_pair_sequence_mask[env_ids] = False
        self.goal_pair_full_song_mask[env_ids] = False
        self.goal_pair_preview_mask[env_ids] = False
        self.practice_transition_count[env_ids] = 0
        if self.curriculum_stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press"):
            available = torch.tensor(
                self.practice_available_fingers, dtype=torch.long, device=self.device)
            chosen_slot = torch.randint(
                len(self.practice_available_fingers), (len(env_ids),),
                generator=self.generator, device=self.device)
            chosen_fingers = available[chosen_slot]
            for finger_index in self.practice_available_fingers:
                selected = env_ids[chosen_fingers == finger_index]
                if selected.numel() == 0:
                    continue
                groups = self.practice_event_groups_by_finger[finger_index]
                group_index = torch.randint(
                    len(groups), (selected.numel(),),
                    generator=self.generator, device=self.device)
                for group_slot, catalog in enumerate(groups):
                    group_envs = selected[group_index == group_slot]
                    if group_envs.numel() == 0:
                        continue
                    event_index = torch.randint(
                        catalog.shape[0], (group_envs.numel(),),
                        generator=self.generator, device=self.device)
                    chosen = catalog[event_index]
                    self.frame_idx[group_envs] = chosen[:, 0]
                    self.practice_string[group_envs] = chosen[:, 1]
            self.practice_remaining[env_ids] = self.practice_duration_frames
            return
        if self.curriculum_stage in (
                "chord_reach", "chord_fine_reach", "static_chord"):
            if not self.practice_available_chord_finger_sets:
                raise RuntimeError(
                    "static-chord curriculum requires at least one PRESS state")
            available_sets = self.practice_available_chord_finger_sets
            if (self.curriculum_stage == "chord_fine_reach"
                    and self.practice_chord_focus_index is not None):
                focus_index = self.practice_chord_focus_index
                focus = torch.rand(
                    len(env_ids), generator=self.generator,
                    device=self.device
                ) < self.practice_chord_focus_probability
                finger_set_slot = torch.full(
                    (len(env_ids),), focus_index,
                    dtype=torch.long, device=self.device)
                if len(available_sets) > 1 and (~focus).any():
                    rehearsal_slot = torch.randint(
                        len(available_sets) - 1, (int((~focus).sum()),),
                        generator=self.generator, device=self.device)
                    rehearsal_slot += (rehearsal_slot >= focus_index).long()
                    finger_set_slot[~focus] = rehearsal_slot
            else:
                finger_set_slot = torch.randint(
                    len(available_sets), (len(env_ids),),
                    generator=self.generator, device=self.device)
            for slot, finger_set in enumerate(available_sets):
                selected = env_ids[finger_set_slot == slot]
                if selected.numel() == 0:
                    continue
                catalog = self.practice_chord_frames_by_finger_set[finger_set]
                frame_slot = torch.randint(
                    catalog.numel(), (selected.numel(),),
                    generator=self.generator, device=self.device)
                self.frame_idx[selected] = catalog[frame_slot]
            self.practice_remaining[env_ids] = self.practice_duration_frames
            self.practice_string[env_ids] = -1
            return
        if self.curriculum_stage == "frozen_context":
            selected_frames, group_slot = (
                self._sample_frozen_context_frames(len(env_ids)))
            self.frame_idx[env_ids] = selected_frames
            self.frozen_context_group_index[env_ids] = group_slot
            self.frozen_context_context_blend[env_ids] = (
                self.frozen_context_real_probability)
            self.frozen_context_real_mask[env_ids] = (
                self.frozen_context_real_probability >= 1.0)
            self.practice_remaining[env_ids] = self.practice_duration_frames
            self.practice_string[env_ids] = -1
            return
        if self.curriculum_stage == "goal_pair":
            if not self.practice_goal_pair_groups:
                raise RuntimeError(
                    "goal-pair curriculum requires at least one source transition")
            transitions = torch.zeros(
                len(env_ids), dtype=torch.long, device=self.device)
            group_slot = torch.full(
                (len(env_ids),), -1, dtype=torch.long, device=self.device)
            incoming_finger = torch.zeros(
                len(env_ids), dtype=torch.long, device=self.device)
            if self.goal_pair_sequence_probability <= 0.0:
                sequence = torch.zeros(
                    len(env_ids), dtype=torch.bool, device=self.device)
            elif self.goal_pair_sequence_probability >= 1.0:
                sequence = torch.ones(
                    len(env_ids), dtype=torch.bool, device=self.device)
            else:
                sequence = torch.rand(
                    len(env_ids), generator=self.generator,
                    device=self.device
                ) < self.goal_pair_sequence_probability
            rehearsal = (~sequence) & (torch.rand(
                len(env_ids), generator=self.generator,
                device=self.device
            ) < self.goal_pair_rehearsal_probability)

            def sample_group_rows(rows, slots):
                if rows.numel() == 0:
                    return
                slot_options = torch.tensor(
                    slots, dtype=torch.long, device=self.device)
                selected_slots = slot_options[torch.randint(
                    len(slots), (rows.numel(),),
                    generator=self.generator, device=self.device)]
                group_slot[rows] = selected_slots
                for slot in slots:
                    selected_rows = rows[selected_slots == slot]
                    if selected_rows.numel() == 0:
                        continue
                    catalog = self.practice_goal_pair_groups[slot]
                    candidate_slot = torch.randint(
                        catalog.numel(), (selected_rows.numel(),),
                        generator=self.generator, device=self.device)
                    transitions[selected_rows] = catalog[candidate_slot]

            transition_rows = torch.nonzero(
                ~rehearsal & ~sequence, as_tuple=False).squeeze(-1)
            has_incoming = bool(
                self.practice_goal_pair_available_incoming_fingers)
            has_no_incoming = bool(
                self.practice_goal_pair_no_incoming_group_slots)
            if transition_rows.numel() > 0:
                if has_incoming and has_no_incoming:
                    choose_incoming = torch.rand(
                        transition_rows.numel(),
                        generator=self.generator, device=self.device
                    ) < self.practice_goal_pair_incoming_group_fraction
                else:
                    choose_incoming = torch.full(
                        (transition_rows.numel(),), has_incoming,
                        dtype=torch.bool, device=self.device)
                incoming_rows = transition_rows[choose_incoming]
                if incoming_rows.numel() > 0:
                    available = torch.tensor(
                        self.practice_goal_pair_available_incoming_fingers,
                        dtype=torch.long, device=self.device)
                    focus_finger = self.goal_pair_transition_focus_finger
                    if focus_finger is None:
                        chosen_finger = available[torch.randint(
                            available.numel(), (incoming_rows.numel(),),
                            generator=self.generator, device=self.device)]
                    else:
                        focus = torch.rand(
                            incoming_rows.numel(), generator=self.generator,
                            device=self.device
                        ) < self.goal_pair_transition_focus_probability
                        chosen_finger = torch.full(
                            (incoming_rows.numel(),), focus_finger,
                            dtype=torch.long, device=self.device)
                        alternatives = available[available != focus_finger]
                        nonfocus_count = int((~focus).sum())
                        if alternatives.numel() and nonfocus_count:
                            alternative_slot = torch.randint(
                                alternatives.numel(), (nonfocus_count,),
                                generator=self.generator, device=self.device)
                            chosen_finger[~focus] = alternatives[
                                alternative_slot]
                    incoming_finger[incoming_rows] = chosen_finger
                    for finger in (
                            self.practice_goal_pair_available_incoming_fingers):
                        rows = incoming_rows[chosen_finger == finger]
                        sample_group_rows(
                            rows,
                            self.practice_goal_pair_groups_by_incoming[finger])
                sample_group_rows(
                    transition_rows[~choose_incoming],
                    self.practice_goal_pair_no_incoming_group_slots)

            previous = (transitions - 1).clamp_min(0)
            rehearsal_rows = torch.nonzero(
                rehearsal, as_tuple=False).squeeze(-1)
            if rehearsal_rows.numel() > 0:
                replay_frames, replay_groups = (
                    self._sample_frozen_context_frames(
                        rehearsal_rows.numel(),
                        focus_finger=self.goal_pair_transition_focus_finger,
                        focus_probability=
                            self.goal_pair_transition_focus_probability))
                previous[rehearsal_rows] = replay_frames
                transitions[rehearsal_rows] = replay_frames
                group_slot[rehearsal_rows] = -1
                self.frozen_context_group_index[
                    env_ids[rehearsal_rows]] = replay_groups

            pair_transition = ~rehearsal & ~sequence
            if bool((group_slot[pair_transition] < 0).any()):
                raise RuntimeError(
                    "goal-pair sampler left a transition environment unassigned")
            minimum_hold = int(round(0.75 * self.fps))
            maximum_hold = int(round(1.00 * self.fps))
            before = torch.randint(
                minimum_hold, maximum_hold + 1, (len(env_ids),),
                generator=self.generator, device=self.device)
            after = torch.randint(
                minimum_hold, maximum_hold + 1, (len(env_ids),),
                generator=self.generator, device=self.device)
            total = before + after
            rehearsal_duration = torch.full_like(
                total, self.goal_pair_rehearsal_duration_frames)
            total = torch.where(rehearsal, rehearsal_duration, total)
            before = torch.where(rehearsal, rehearsal_duration, before)
            preview = ~rehearsal & ~sequence & self.goal_pair_preview_only
            total = torch.where(preview, before, total)
            sequence_rows = torch.nonzero(
                sequence, as_tuple=False).squeeze(-1)
            full_song = torch.zeros_like(sequence)
            if sequence_rows.numel() > 0:
                full_song[sequence_rows] = torch.rand(
                    sequence_rows.numel(), generator=self.generator,
                    device=self.device
                ) < self.goal_pair_sequence_full_song_fraction
                window_rows = sequence_rows[~full_song[sequence_rows]]
                if window_rows.numel() > 0:
                    duration = min(
                        self.goal_pair_sequence_duration_frames,
                        self.n_frames)
                    if self.practice_transition_frames.numel() > 0:
                        slots = torch.randint(
                            self.practice_transition_frames.numel(),
                            (window_rows.numel(),), generator=self.generator,
                            device=self.device)
                        centers = self.practice_transition_frames[slots]
                    else:
                        centers = torch.randint(
                            self.n_frames, (window_rows.numel(),),
                            generator=self.generator, device=self.device)
                    latest = max(0, self.n_frames - duration)
                    starts = (centers - duration // 2).clamp(
                        min=0, max=latest)
                    previous[window_rows] = starts
                    transitions[window_rows] = starts
                    before[window_rows] = duration
                    total[window_rows] = duration
                full_rows = torch.nonzero(
                    full_song, as_tuple=False).squeeze(-1)
                if full_rows.numel() > 0:
                    previous[full_rows] = 0
                    transitions[full_rows] = 0
                    before[full_rows] = self.n_frames
                    total[full_rows] = self.n_frames
            self.goal_pair_previous_frame[env_ids] = previous
            self.goal_pair_next_frame[env_ids] = transitions
            self.goal_pair_before_remaining[env_ids] = before
            self.goal_pair_group_index[env_ids] = group_slot
            self.goal_pair_incoming_finger[env_ids] = incoming_finger
            self.goal_pair_rehearsal_mask[env_ids] = rehearsal
            self.goal_pair_sequence_mask[env_ids] = sequence
            self.goal_pair_full_song_mask[env_ids] = full_song
            self.goal_pair_preview_mask[env_ids] = preview
            self.frame_idx[env_ids] = previous
            self.practice_remaining[env_ids] = total
            self.practice_string[env_ids] = -1
            return
        if self.curriculum_stage == "transition_window":
            if self.practice_transition_frames.numel() == 0:
                raise RuntimeError(
                    "transition-window curriculum requires a source transition")
            maximum = min(
                self.practice_duration_frames, 3 * self.fps, self.n_frames - 1)
            minimum = min(self.fps, maximum)
            if minimum < 1:
                raise RuntimeError(
                    "transition-window curriculum requires at least two frames")
            if maximum == minimum:
                duration = torch.full(
                    (len(env_ids),), minimum,
                    dtype=torch.long, device=self.device)
            else:
                duration = torch.randint(
                    minimum, maximum + 1, (len(env_ids),),
                    generator=self.generator, device=self.device)
            latest_start = self.n_frames - 1 - duration
            if self.transition_max_changes is None:
                transition_slot = torch.randint(
                    self.practice_transition_frames.numel(), (len(env_ids),),
                    generator=self.generator, device=self.device)
                transition = self.practice_transition_frames[transition_slot]
                start = torch.minimum(
                    (transition - duration // 2).clamp_min(0),
                    latest_start)
            else:
                candidates = self.practice_transition_frames.unsqueeze(0)
                starts = torch.minimum(
                    (candidates - duration[:, None] // 2).clamp_min(0),
                    latest_start[:, None])
                ends = starts + duration[:, None] - 1
                counts = (
                    self.transition_change_prefix[ends]
                    - self.transition_change_prefix[starts])
                eligible = counts <= self.transition_max_changes
                if not bool(eligible.any(dim=1).all()):
                    minimum = counts.amin(dim=1)
                    raise RuntimeError(
                        "transition change limit is infeasible for sampled "
                        f"durations: limit={self.transition_max_changes}, "
                        f"minimum_required={int(minimum.max())}")
                scores = torch.rand(
                    counts.shape, generator=self.generator,
                    device=self.device)
                scores.masked_fill_(~eligible, 2.0)
                selected = scores.argmin(dim=1)
                row = torch.arange(len(env_ids), device=self.device)
                start = starts[row, selected]
            end = start + duration - 1
            count = (
                self.transition_change_prefix[end]
                - self.transition_change_prefix[start])
            self.frame_idx[env_ids] = start
            self.practice_remaining[env_ids] = duration
            self.practice_string[env_ids] = -1
            self.practice_transition_count[env_ids] = count
            return
        self.practice_remaining[env_ids] = 0
        self.practice_string[env_ids] = -1
        if self.random_start_probability > 0.0:
            # 끝 0.5초는 시작점에서 제외해 최소한의 유효 rollout을 보장한다.
            high = max(1, self.n_frames - self.fps // 2)
            sampled = torch.randint(
                high, (len(env_ids),), generator=self.generator, device=self.device)
            if self.random_start_probability >= 1.0:
                choose_random = torch.ones(len(env_ids), dtype=torch.bool, device=self.device)
            else:
                choose_random = torch.rand(
                    len(env_ids), generator=self.generator, device=self.device
                ) < self.random_start_probability
            self.frame_idx[env_ids] = torch.where(
                choose_random, sampled, self.frame_idx[env_ids])

    def set_random_start_probability(self, probability):
        """Set per-reset random-start probability for the per-song curriculum."""
        probability = float(probability)
        if not 0.0 <= probability <= 1.0:
            raise ValueError("random start probability must be in [0, 1]")
        self.random_start_probability = probability
        self.random_start = probability > 0.0

    def set_transition_max_changes(self, maximum):
        if maximum is None:
            normalized = None
        else:
            if isinstance(maximum, bool) or int(maximum) < 1:
                raise ValueError(
                    "transition maximum changes must be a positive integer")
            normalized = int(maximum)
        changed = normalized != self.transition_max_changes
        self.transition_max_changes = normalized
        return changed

    def set_frozen_context_real_probability(self, probability):
        probability = float(probability)
        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                "frozen-context real probability must be in [0, 1]")
        changed = probability != self.frozen_context_real_probability
        self.frozen_context_real_probability = probability
        return changed

    def set_goal_pair_rehearsal_probability(self, probability):
        probability = float(probability)
        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                "goal-pair rehearsal probability must be in [0, 1]")
        changed = probability != self.goal_pair_rehearsal_probability
        self.goal_pair_rehearsal_probability = probability
        return changed

    def set_goal_pair_rehearsal_duration(self, duration_frames):
        if (isinstance(duration_frames, bool)
                or int(duration_frames) != duration_frames
                or int(duration_frames) < 1):
            raise ValueError(
                "goal-pair rehearsal duration must be a positive integer")
        normalized = int(duration_frames)
        changed = normalized != self.goal_pair_rehearsal_duration_frames
        self.goal_pair_rehearsal_duration_frames = normalized
        return changed

    def set_goal_pair_sequence_sampling(
            self, probability, duration_frames=240,
            full_song_fraction=0.0):
        probability = float(probability)
        full_song_fraction = float(full_song_fraction)
        if (not 0.0 <= probability <= 1.0
                or not 0.0 <= full_song_fraction <= 1.0):
            raise ValueError(
                "goal-pair sequence probabilities must be in [0, 1]")
        if (isinstance(duration_frames, bool)
                or int(duration_frames) != duration_frames
                or int(duration_frames) < 1):
            raise ValueError(
                "goal-pair sequence duration must be a positive integer")
        duration_frames = int(duration_frames)
        changed = (
            probability != self.goal_pair_sequence_probability
            or duration_frames != self.goal_pair_sequence_duration_frames
            or full_song_fraction
                != self.goal_pair_sequence_full_song_fraction)
        self.goal_pair_sequence_probability = probability
        self.goal_pair_sequence_duration_frames = duration_frames
        self.goal_pair_sequence_full_song_fraction = full_song_fraction
        return changed

    def set_goal_pair_preview_only(self, enabled):
        normalized = bool(enabled)
        changed = normalized != self.goal_pair_preview_only
        self.goal_pair_preview_only = normalized
        return changed

    def set_goal_pair_transition_focus(self, finger, focus_probability=1.0):
        """Bias incoming transition rows without changing replay coverage."""
        focus_probability = float(focus_probability)
        if not 0.0 < focus_probability <= 1.0:
            raise ValueError(
                "goal-pair transition focus probability must be in (0, 1]")
        if finger is None:
            normalized = None
        else:
            if not _is_integer(finger) or not 1 <= int(finger) <= 4:
                raise ValueError(
                    "goal-pair transition focus finger must be one of 1..4")
            normalized = int(finger)
            if normalized not in self.practice_goal_pair_available_incoming_fingers:
                raise ValueError(
                    "goal-pair transition focus finger has no incoming transition")
        changed = (
            normalized != self.goal_pair_transition_focus_finger
            or focus_probability
            != self.goal_pair_transition_focus_probability)
        self.goal_pair_transition_focus_finger = normalized
        self.goal_pair_transition_focus_probability = focus_probability
        return changed

    def set_curriculum_stage(self, stage, duration_frames=None):
        stages = ("coarse_reach", "fine_reach",
                  "isolated_press", "integrated_press",
                  "chord_reach", "chord_fine_reach",
                  "static_chord", "frozen_context",
                  "goal_pair", "transition_window",
                  "coverage", "integration", "full_song")
        practice_stages = (
            "coarse_reach", "fine_reach",
            "isolated_press", "integrated_press",
            "chord_reach", "chord_fine_reach", "static_chord",
            "frozen_context", "goal_pair", "transition_window")
        if stage not in stages:
            raise ValueError(f"unknown fingertip curriculum stage: {stage}")
        if stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press"
        ) and not self.practice_available_fingers:
            raise ValueError(
                "fingertip approach curriculum requires at least one PRESS event")
        self.curriculum_stage = stage
        if stage in ("coarse_reach", "fine_reach"):
            default_duration = 120
        elif stage in ("chord_reach", "chord_fine_reach"):
            default_duration = 180
        elif stage == "static_chord":
            default_duration = 150
        elif stage == "frozen_context":
            default_duration = 150
        elif stage == "goal_pair":
            default_duration = 120
        elif stage in (
                "isolated_press", "integrated_press", "transition_window"):
            default_duration = 180
        else:
            default_duration = 0
        duration = default_duration if duration_frames is None else int(duration_frames)
        if duration < 0 or (stage in practice_stages and duration < 1):
            raise ValueError("practice curriculum duration must be positive")
        if stage == "transition_window" and duration < self.fps:
            raise ValueError(
                "transition-window duration must be at least one second")
        self.practice_duration_frames = duration

    def set_chord_focus_index(self, index, focus_probability=1.0):
        focus_probability = float(focus_probability)
        if not 0.0 < focus_probability <= 1.0:
            raise ValueError("chord focus probability must be in (0, 1]")
        if index is None or int(index) < 0:
            normalized = None
        else:
            normalized = int(index)
            if normalized >= len(self.practice_available_chord_finger_sets):
                raise ValueError("chord focus index is outside the available sets")
        changed = (
            normalized != self.practice_chord_focus_index
            or focus_probability
            != self.practice_chord_focus_probability)
        self.practice_chord_focus_index = normalized
        self.practice_chord_focus_probability = focus_probability
        return changed

    def curriculum_sampler_state_dict(self):
        return {"generator_state": self.generator.get_state().cpu()}

    def load_curriculum_sampler_state_dict(self, state):
        generator_state = state.get("generator_state")
        if generator_state is None:
            raise ValueError("curriculum sampler state is missing generator_state")
        self.generator.set_state(generator_state.cpu())

    def advance(self, env_mask=None):
        if self.curriculum_stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press",
                "chord_reach", "chord_fine_reach",
                "static_chord", "frozen_context",
                "goal_pair", "transition_window"):
            if env_mask is None:
                env_mask = torch.ones(
                    self.num_envs, dtype=torch.bool, device=self.device)
            active = env_mask & (self.practice_remaining > 0)
            if self.curriculum_stage == "goal_pair":
                before_active = (
                    active & ~self.goal_pair_sequence_mask
                    & (self.goal_pair_before_remaining > 0))
                switch = (
                    before_active & (self.goal_pair_before_remaining == 1))
                self.goal_pair_before_remaining[before_active] -= 1
                self.frame_idx[switch] = self.goal_pair_next_frame[switch]
                sequence_active = active & self.goal_pair_sequence_mask
                self.frame_idx[sequence_active] = (
                    self.frame_idx[sequence_active] + 1
                ).clamp(max=self.n_frames - 1)
            self.practice_remaining[env_mask] -= 1
            self.practice_remaining.clamp_(min=0)
            if self.curriculum_stage == "transition_window":
                self.frame_idx[active] = (
                    self.frame_idx[active] + 1).clamp(max=self.n_frames - 1)
            return
        if env_mask is None:
            self.frame_idx.add_(1).clamp_(max=self.n_frames - 1)
        else:
            self.frame_idx[env_mask] = (
                self.frame_idx[env_mask] + 1).clamp(max=self.n_frames - 1)

    @property
    def done(self):
        if self.curriculum_stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press",
                "chord_reach", "chord_fine_reach",
                "static_chord", "frozen_context",
                "goal_pair", "transition_window"):
            # The task evaluates completion before advancing the current frame.
            # A remaining count of one therefore means this is the final
            # practice frame, avoiding an extra duplicate sample.
            return self.practice_remaining <= 1
        return self.frame_idx >= self.n_frames - 1

    def _masked_practice_goal(self, tensor, fill_value):
        if self.curriculum_stage not in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press"):
            return tensor
        result = torch.full_like(tensor, fill_value)
        env_index = torch.arange(self.num_envs, device=self.device)
        result[env_index, self.practice_string] = tensor[
            env_index, self.practice_string]
        return result

    def _static_finger_events(self, fret, finger):
        events = torch.zeros(
            self.num_envs, 4, FINGER_EVENT_DIM,
            dtype=torch.float32, device=self.device)
        events[..., 12] = 1.0
        remaining = (
            self.practice_remaining.float() / float(self.fps)).clamp(max=1.0)
        if self.curriculum_stage in (
                "chord_reach", "chord_fine_reach", "static_chord",
                "frozen_context"):
            for finger_number in range(1, 5):
                active = (finger == finger_number) & (fret > 0)
                present = active.any(dim=1)
                if not present.any():
                    continue
                selected_fret = torch.where(
                    active, fret, torch.zeros_like(fret)).amax(dim=1)
                events[:, finger_number - 1, 0:6] = active.float()
                events[present, finger_number - 1, 6] = (
                    selected_fret[present] / 22.0)
                events[present, finger_number - 1, 8] = 1.0
                events[present, finger_number - 1, 9] = remaining[present]
                events[present, finger_number - 1, 10] = 1.0
                events[present, finger_number - 1, 12] = 0.0
            return events

        env_index = torch.arange(self.num_envs, device=self.device)
        selected_finger = finger[env_index, self.practice_string] - 1
        selected_fret = fret[env_index, self.practice_string]
        events[env_index, selected_finger, self.practice_string] = 1.0
        events[env_index, selected_finger, 6] = selected_fret / 22.0
        events[env_index, selected_finger, 8] = 1.0
        events[env_index, selected_finger, 9] = remaining
        events[env_index, selected_finger, 10] = 1.0
        events[env_index, selected_finger, 12] = 0.0
        return events

    def _finger_targets_at(self, frame_indices):
        fret = self.fret[frame_indices]
        finger = self.finger[frame_indices]
        finger_numbers = torch.arange(
            1, 5, dtype=torch.long, device=self.device).view(1, 1, 4)
        active = (
            (fret > 0)[..., None]
            & (finger[..., None] == finger_numbers))
        string_mask = active.permute(0, 2, 1)
        selected_fret = torch.where(
            active, fret[..., None], torch.zeros_like(fret[..., None])
        ).amax(dim=1)
        return string_mask, selected_fret

    def _goal_pair_finger_events(self):
        events = torch.zeros(
            self.num_envs, 4, FINGER_EVENT_DIM,
            dtype=torch.float32, device=self.device)
        previous_mask, previous_fret = self._finger_targets_at(
            self.goal_pair_previous_frame)
        next_mask, next_fret = self._finger_targets_at(
            self.goal_pair_next_frame)
        before = self.goal_pair_before_remaining > 0
        current_mask = torch.where(
            before[:, None, None], previous_mask, next_mask)
        current_fret = torch.where(
            before[:, None], previous_fret, next_fret)
        current_active = current_fret > 0
        next_active = next_fret > 0
        same_target = (
            current_active & next_active
            & (current_fret == next_fret)
            & (current_mask == next_mask).all(dim=-1))

        has_next = before[:, None] & next_active
        hold_current = ~before[:, None] & current_active
        guided_target = has_next | hold_current
        events[..., 0:6] = torch.where(
            guided_target[..., None], next_mask.float(),
            torch.zeros_like(next_mask, dtype=torch.float32))
        events[..., 6] = torch.where(
            guided_target, next_fret / 22.0, torch.zeros_like(next_fret))
        transition_time = (
            self.goal_pair_before_remaining.float() / float(self.fps)
        ).clamp(max=FINGER_EVENT_TIME_SCALE_S) / FINGER_EVENT_TIME_SCALE_S
        events[..., 7] = torch.where(
            has_next, transition_time[:, None],
            torch.zeros_like(next_fret))
        events[..., 8] = guided_target.float()

        end_time = (
            self.practice_remaining.float() / float(self.fps)
        ).clamp(max=FINGER_EVENT_TIME_SCALE_S) / FINGER_EVENT_TIME_SCALE_S
        current_change = torch.where(
            before[:, None] & ~same_target,
            transition_time[:, None], end_time[:, None])
        events[..., 9] = torch.where(
            current_active, current_change, torch.zeros_like(current_change))

        keep = (before[:, None] & same_target) | hold_current
        move = before[:, None] & next_active & ~same_target
        events[..., 10] = keep.float()
        events[..., 11] = move.float()
        events[..., 12] = (~keep & ~move).float()
        return events

    def _lookahead_indices(self, offset, practice_static):
        if self.curriculum_stage == "goal_pair":
            use_next = self.goal_pair_before_remaining <= int(offset)
            pair_index = torch.where(
                use_next,
                self.goal_pair_next_frame,
                self.goal_pair_previous_frame)
            replay_index = (
                self.frame_idx + int(offset)).clamp(
                    max=self.n_frames - 1)
            return torch.where(
                self.goal_pair_rehearsal_mask
                | self.goal_pair_sequence_mask,
                replay_index,
                pair_index)
        if self.curriculum_stage == "frozen_context":
            return (
                self.frame_idx + int(offset)).clamp(
                    max=self.n_frames - 1)
        if practice_static:
            return self.frame_idx
        return (self.frame_idx + int(offset)).clamp(max=self.n_frames - 1)

    def current(self):
        i = self.frame_idx
        fret = self._masked_practice_goal(self.fret[i], 0.0)
        finger = self._masked_practice_goal(self.finger[i], 0)
        barre = self._masked_practice_goal(self.barre[i], False)
        sustain_event_id = self.sustain_event_id[i]
        sustain_eligible = self.sustain_eligible[i]
        if self.curriculum_stage in (
                "chord_reach", "chord_fine_reach", "static_chord",
                "frozen_context", "goal_pair"):
            # A source run often starts inside sustain boundary grace.  Freezing
            # that frame must still evaluate the whole stage-local hold.
            sustain_eligible = fret > 0
            if self.curriculum_stage == "goal_pair":
                sustain_eligible = torch.where(
                    self.goal_pair_sequence_mask[:, None],
                    self.sustain_eligible[i], sustain_eligible)
        static_stage = self.curriculum_stage in (
            "coarse_reach", "fine_reach",
            "isolated_press", "integrated_press",
            "chord_reach", "chord_fine_reach", "static_chord")
        if self.curriculum_stage == "goal_pair":
            pair_event = self._goal_pair_finger_events()
            finger_event = torch.where(
                (self.goal_pair_rehearsal_mask
                 | self.goal_pair_sequence_mask)[:, None, None],
                self.finger_events[i],
                pair_event)
        elif self.curriculum_stage == "frozen_context" or static_stage:
            finger_event = self._static_finger_events(fret, finger)
        else:
            finger_event = self.finger_events[i]
        return {
            "fret": fret,
            "finger": finger,
            "barre": barre,
            "anchor": self.anchor[i],
            "allowed": self.allowed[i],
            "wrist": self.wrist[i],
            "wrist_radius": self.wrist_radius[i],
            "sustain_event_id": sustain_event_id,
            "sustain_eligible": sustain_eligible,
            # Runtime diagnostics may need the structured per-finger relation
            # without changing the flattened policy observation contract.
            "finger_event": finger_event,
        }

    def observe(self, clock_delay_frames=None):
        """Return the policy goal, optionally accounting for a frozen song clock.

        During the preparation window the selected frame does not advance.  Adding
        that remaining delay to the lookahead and per-finger time channels keeps
        their physical meaning truthful and makes preparation observable without
        growing the 128-D goal contract.
        """
        if clock_delay_frames is None:
            delay_s = torch.zeros(
                self.num_envs, 1, dtype=torch.float32, device=self.device)
        else:
            delay = torch.as_tensor(
                clock_delay_frames, dtype=torch.float32, device=self.device).reshape(-1)
            if delay.numel() != self.num_envs:
                raise ValueError(
                    f"clock delay must have {self.num_envs} rows, got {delay.numel()}")
            if delay.device.type == "cpu" and (
                    not torch.isfinite(delay).all() or (delay < 0).any()):
                raise ValueError("clock delay frames must be finite and non-negative")
            delay_s = (delay / float(self.fps)).unsqueeze(-1)
        practice_static = self.curriculum_stage in (
            "coarse_reach", "fine_reach",
            "isolated_press", "integrated_press",
            "chord_reach", "chord_fine_reach", "static_chord")
        chunks = []
        for offset in self.lookahead:
            idx = self._lookahead_indices(offset, practice_static)
            # 목표 범위를 대략 [-1,1] 안에 둔다. fret의 -1(NO_PRESS: open/release)은 음수 신호다.
            fret = self._masked_practice_goal(self.fret[idx], 0.0) / 22.0
            finger = self._masked_practice_goal(self.finger[idx], 0).float() / 4.0
            barre = self._masked_practice_goal(self.barre[idx], False).float()
            anchor = ((self.anchor[idx] - 1.0) / 21.0).unsqueeze(-1)
            allowed = (self.allowed[idx] - 1.0) / 21.0
            wrist = self.wrist[idx] / 0.25
            if self.curriculum_stage == "frozen_context":
                base_idx = self.frame_idx
                blend = self.frozen_context_context_blend[:, None]
                fret = torch.lerp(
                    self.fret[base_idx] / 22.0, fret, blend)
                finger = torch.lerp(
                    self.finger[base_idx].float() / 4.0,
                    finger, blend)
                barre = torch.lerp(
                    self.barre[base_idx].float(), barre, blend)
                anchor = torch.lerp(
                    ((self.anchor[base_idx] - 1.0) / 21.0).unsqueeze(-1),
                    anchor, blend)
                allowed = torch.lerp(
                    (self.allowed[base_idx] - 1.0) / 21.0,
                    allowed, blend)
                wrist = torch.lerp(
                    self.wrist[base_idx] / 0.25, wrist, blend)
            dt = delay_s + offset / float(self.fps)
            chunks.append(torch.cat([fret, finger, barre, anchor, allowed, wrist, dt], dim=-1))
        current = self.current()
        finger_events = current["finger_event"].clone()
        if self.curriculum_stage == "frozen_context":
            finger_events = torch.lerp(
                finger_events,
                self.finger_events[self.frame_idx],
                self.frozen_context_context_blend[:, None, None])
        delay_norm = (delay_s.squeeze(-1) / FINGER_EVENT_TIME_SCALE_S)[:, None]
        next_valid = finger_events[..., 8].clamp(0.0, 1.0)
        finger_events[..., 7] = (
            finger_events[..., 7] + delay_norm * next_valid
        ).clamp(max=1.0)
        finger_numbers = torch.arange(1, 5, device=self.device).view(1, 1, 4)
        current_active = (
            (current["fret"] > 0)[..., None]
            & (current["finger"][..., None] == finger_numbers)
        ).any(dim=1)
        finger_events[..., 9] = torch.where(
            current_active,
            (finger_events[..., 9] + delay_norm).clamp(max=1.0),
            finger_events[..., 9])
        finger_events = finger_events.reshape(self.num_envs, -1)
        phase = (self.frame_idx.float() / max(self.n_frames - 1, 1)).unsqueeze(-1)
        return torch.cat(chunks + [finger_events, phase], dim=-1)
