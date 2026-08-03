"""Actual-geometry fretboard overlays for Isaac Gym camera images.

The overlay is diagnostic only: it reads the live ``G:nut``, ``G:fretN`` and
``G:stringN`` rigid-body positions and projects them into a camera image.  It
never adds collision shapes or changes the physics scene.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.env.rewards.thumb import (
    NECK_BACK_Z,
    NECK_BODY_HALF_WIDTH,
    NECK_BODY_Y,
    NECK_NUT_HALF_WIDTH,
    NECK_NUT_Y,
)
from tab2body.env.safety import palm_inward_normal


NECK_FRONT_Z = 0.0093


@dataclass(frozen=True)
class CameraSpec:
    eye: tuple[float, float, float]
    target: tuple[float, float, float]
    width: int
    height: int
    horizontal_fov_deg: float = 55.0


def camera_from_guitar(env, width=1280, height=720, horizontal_fov_deg=55.0):
    """Return a stable close-up camera derived from the live guitar geometry."""
    fret_lo = env.gbody_pos("G:fret1")[0].detach().cpu()
    fret_hi = env.gbody_pos("G:fret12")[0].detach().cpu()
    high_e = env.gbody_pos("G:string1")[0].detach().cpu()
    low_e = env.gbody_pos("G:string6")[0].detach().cpu()
    center = 0.5 * (fret_lo + fret_hi)
    neck = fret_hi - fret_lo
    across = high_e - low_e
    normal = torch.linalg.cross(neck, across)
    normal = normal / normal.norm().clamp_min(1e-8)
    if normal[2] < 0:
        normal = -normal
    eye = center + 0.30 * normal + torch.tensor([0.0, 0.0, 0.18])
    return CameraSpec(tuple(float(x) for x in eye),
                      tuple(float(x) for x in center),
                      int(width), int(height), float(horizontal_fov_deg))


def _as_np(tensor):
    return tensor[0].detach().cpu().numpy().astype(np.float64)


def _camera_basis(spec):
    eye = np.asarray(spec.eye, dtype=np.float64)
    target = np.asarray(spec.target, dtype=np.float64)
    forward = target - eye
    forward /= max(np.linalg.norm(forward), 1e-12)
    world_up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    right = np.cross(forward, world_up)
    if np.linalg.norm(right) < 1e-8:
        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    up /= np.linalg.norm(up)
    return eye, right, up, forward


def _project(points, spec):
    points = np.asarray(points, dtype=np.float64)
    eye, right, up, forward = _camera_basis(spec)
    rel = points - eye
    x = rel @ right
    y = rel @ up
    z = rel @ forward
    focal = spec.width / (2.0 * math.tan(math.radians(spec.horizontal_fov_deg) / 2.0))
    px = 0.5 * spec.width + focal * x / np.maximum(z, 1e-8)
    py = 0.5 * spec.height - focal * y / np.maximum(z, 1e-8)
    return np.stack([px, py], axis=-1), z


def _guitar_local_to_world(env, local_points):
    """Transform diagnostic geometry from the live guitar frame to world space."""
    local_points = np.asarray(local_points, dtype=np.float64)
    guitar_pos, guitar_quat = env.guitar_frame()
    pos = guitar_pos[0].detach().cpu().numpy().astype(np.float64)
    x, y, z, w = guitar_quat[0].detach().cpu().numpy().astype(np.float64)
    rotation = np.array([
        [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w),
         2.0 * (x * z + y * w)],
        [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z),
         2.0 * (y * z - x * w)],
        [2.0 * (x * z - y * w), 2.0 * (y * z + x * w),
         1.0 - 2.0 * (x * x + y * y)],
    ], dtype=np.float64)
    return local_points @ rotation.T + pos


def wrist_safety_box_geometry(env, bounds_min=(-0.20, -0.35, -0.30),
                              bounds_max=(0.30, 0.35, 0.25)):
    """Return the eight world-space corners of a guitar-local safety box."""
    lo = np.asarray(bounds_min, dtype=np.float64)
    hi = np.asarray(bounds_max, dtype=np.float64)
    if lo.shape != (3,) or hi.shape != (3,) or np.any(lo >= hi):
        raise ValueError("wrist safety bounds must be two ordered xyz triples")
    corners_local = np.array([
        [x, y, z]
        for x in (lo[0], hi[0])
        for y in (lo[1], hi[1])
        for z in (lo[2], hi[2])
    ], dtype=np.float64)
    return _guitar_local_to_world(env, corners_local)


def camera_for_wrist_safety_box(env, width=1600, height=900,
                                horizontal_fov_deg=55.0,
                                bounds_min=(-0.20, -0.35, -0.30),
                                bounds_max=(0.30, 0.35, 0.25)):
    """Pull the standard guitar camera back far enough to contain the box."""
    close = camera_from_guitar(env, width, height, horizontal_fov_deg)
    corners = wrist_safety_box_geometry(env, bounds_min, bounds_max)
    center = corners.mean(axis=0)
    view = np.asarray(close.eye) - np.asarray(close.target)
    view /= max(np.linalg.norm(view), 1e-12)
    radius = max(np.linalg.norm(corners - center, axis=1))
    vertical_fov = 2.0 * math.atan(
        (height / width) * math.tan(math.radians(horizontal_fov_deg) / 2.0))
    limiting_half_fov = min(math.radians(horizontal_fov_deg) / 2.0,
                            vertical_fov / 2.0)
    distance = 1.20 * radius / max(math.sin(limiting_half_fov), 1e-8)
    eye = center + distance * view
    return CameraSpec(tuple(float(x) for x in eye), tuple(float(x) for x in center),
                      int(width), int(height), float(horizontal_fov_deg))


def camera_for_wrist_safety_box_view(env, local_view_direction, width=1600,
                                     height=900, horizontal_fov_deg=55.0,
                                     bounds_min=(-0.20, -0.35, -0.30),
                                     bounds_max=(0.30, 0.35, 0.25)):
    """Frame the box while looking toward it along a guitar-local direction."""
    direction = np.asarray(local_view_direction, dtype=np.float64)
    if direction.shape != (3,) or np.linalg.norm(direction) < 1e-8:
        raise ValueError("local_view_direction must be a non-zero xyz triple")
    direction /= np.linalg.norm(direction)
    origin_and_direction = _guitar_local_to_world(
        env, np.stack([np.zeros(3, dtype=np.float64), direction]))
    world_direction = origin_and_direction[1] - origin_and_direction[0]
    world_direction /= max(np.linalg.norm(world_direction), 1e-12)

    corners = wrist_safety_box_geometry(env, bounds_min, bounds_max)
    center = corners.mean(axis=0)
    radius = max(np.linalg.norm(corners - center, axis=1))
    vertical_fov = 2.0 * math.atan(
        (height / width) * math.tan(math.radians(horizontal_fov_deg) / 2.0))
    limiting_half_fov = min(math.radians(horizontal_fov_deg) / 2.0,
                            vertical_fov / 2.0)
    distance = 1.20 * radius / max(math.sin(limiting_half_fov), 1e-8)
    eye = center + distance * world_direction
    return CameraSpec(tuple(float(x) for x in eye), tuple(float(x) for x in center),
                      int(width), int(height), float(horizontal_fov_deg))


def finger_back_limit_geometry(env, limit_z=-0.050, half_x=0.16,
                               y_min=-0.32, y_max=0.28, arrow_length=0.075):
    """Finite drawing patch for the infinite guitar-local R8 z-limit plane."""
    if half_x <= 0 or y_min >= y_max or arrow_length <= 0:
        raise ValueError("invalid finger back-limit display extent")
    boundary = np.array([
        [-half_x, y_min, limit_z], [half_x, y_min, limit_z],
        [half_x, y_max, limit_z], [-half_x, y_max, limit_z],
    ], dtype=np.float64)
    neck_back = np.array([
        [-NECK_BODY_HALF_WIDTH, NECK_BODY_Y, NECK_BACK_Z],
        [NECK_BODY_HALF_WIDTH, NECK_BODY_Y, NECK_BACK_Z],
        [NECK_NUT_HALF_WIDTH, NECK_NUT_Y, NECK_BACK_Z],
        [-NECK_NUT_HALF_WIDTH, NECK_NUT_Y, NECK_BACK_Z],
    ], dtype=np.float64)
    arrow_origins = np.array([
        [-0.10, -0.18, limit_z], [0.10, -0.18, limit_z],
        [0.0, 0.0, limit_z], [-0.10, 0.18, limit_z], [0.10, 0.18, limit_z],
    ], dtype=np.float64)
    arrow_ends = arrow_origins.copy()
    arrow_ends[:, 2] -= arrow_length
    return {
        "boundary": _guitar_local_to_world(env, boundary),
        "neck_back": _guitar_local_to_world(env, neck_back),
        "arrow_origins": _guitar_local_to_world(env, arrow_origins),
        "arrow_ends": _guitar_local_to_world(env, arrow_ends),
        "all": _guitar_local_to_world(
            env, np.concatenate([boundary, neck_back, arrow_origins, arrow_ends], axis=0)),
    }


def camera_for_finger_back_limit_view(env, local_view_direction, width=1600,
                                      height=900, horizontal_fov_deg=55.0,
                                      limit_z=-0.050):
    """Frame the guitar-wide R8 z-limit plane from a guitar-local direction."""
    direction = np.asarray(local_view_direction, dtype=np.float64)
    if direction.shape != (3,) or np.linalg.norm(direction) < 1e-8:
        raise ValueError("local_view_direction must be a non-zero xyz triple")
    direction /= np.linalg.norm(direction)
    origin_and_direction = _guitar_local_to_world(
        env, np.stack([np.zeros(3, dtype=np.float64), direction]))
    world_direction = origin_and_direction[1] - origin_and_direction[0]
    world_direction /= max(np.linalg.norm(world_direction), 1e-12)

    points = finger_back_limit_geometry(env, limit_z=limit_z)["all"]
    center = points.mean(axis=0)
    radius = max(np.linalg.norm(points - center, axis=1))
    vertical_fov = 2.0 * math.atan(
        (height / width) * math.tan(math.radians(horizontal_fov_deg) / 2.0))
    limiting_half_fov = min(math.radians(horizontal_fov_deg) / 2.0,
                            vertical_fov / 2.0)
    distance = 1.24 * radius / max(math.sin(limiting_half_fov), 1e-8)
    eye = center + distance * world_direction
    return CameraSpec(tuple(float(x) for x in eye), tuple(float(x) for x in center),
                      int(width), int(height), float(horizontal_fov_deg))


def palm_neck_direction_geometry(env, normal_length=0.12):
    """Build the live palm inward normal and direction to the nearest neck surface."""
    palm = env.hbody_pos("LH:palm")[0]
    wrist = env.hbody_pos("L_Wrist")[0]
    index = env.hbody_pos("LH:index1")[0]
    middle = env.hbody_pos("LH:middle1")[0]
    pinky = env.hbody_pos("LH:pinky1")[0]
    # Fixed anatomical ordering.  The sign is never flipped from the current
    # neck direction, otherwise an actually inverted palm could not be detected.
    inward, _valid = palm_inward_normal(wrist, index, middle, pinky)

    palm_local = env.to_guitar_frame(palm[None, None])[0, 0].detach().cpu().numpy()
    closest_local = palm_local.copy()
    closest_local[1] = np.clip(closest_local[1], NECK_BODY_Y, NECK_NUT_Y)
    alpha = ((NECK_NUT_Y - closest_local[1]) /
             (NECK_NUT_Y - NECK_BODY_Y))
    half_width = (NECK_NUT_HALF_WIDTH
                  + alpha * (NECK_BODY_HALF_WIDTH - NECK_NUT_HALF_WIDTH))
    closest_local[0] = np.clip(closest_local[0], -half_width, half_width)
    closest_local[2] = np.clip(closest_local[2], NECK_BACK_Z, NECK_FRONT_Z)
    closest = _guitar_local_to_world(env, closest_local[None])[0]

    palm_np = palm.detach().cpu().numpy().astype(np.float64)
    inward_np = inward.detach().cpu().numpy().astype(np.float64)
    to_neck = closest - palm_np
    distance = max(np.linalg.norm(to_neck), 1e-12)
    to_neck_unit = to_neck / distance
    alignment = float(np.dot(inward_np, to_neck_unit))
    arrow_length = max(float(normal_length), 0.02)
    neck_arrow_length = min(max(distance, 0.055), 0.16)
    return {
        "palm": palm_np,
        "inward": inward_np,
        "closest_neck": closest,
        "to_neck_end": palm_np + neck_arrow_length * to_neck_unit,
        "inward_end": palm_np + arrow_length * inward_np,
        "opposite_end": palm_np - arrow_length * to_neck_unit,
        "alignment": alignment,
        "neck_distance": distance,
        "all": np.stack([palm_np, closest, palm_np + neck_arrow_length * to_neck_unit,
                         palm_np + arrow_length * inward_np,
                         palm_np - arrow_length * to_neck_unit]),
    }


def palm_world_direction_geometry(env, normal_length=0.14, plane_half_size=0.13):
    """Return the palm inward normal and fixed world up/down reference geometry."""
    palm_geometry = palm_neck_direction_geometry(env, normal_length=normal_length)
    palm = palm_geometry["palm"]
    inward = palm_geometry["inward"]
    up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    down = -up
    s = float(plane_half_size)
    plane = np.array([
        palm + [-s, -s, 0.0], palm + [s, -s, 0.0],
        palm + [s, s, 0.0], palm + [-s, s, 0.0],
    ], dtype=np.float64)
    return {
        "palm": palm,
        "inward_end": palm + normal_length * inward,
        "up_end": palm + 0.10 * up,
        "down_end": palm + 0.14 * down,
        "horizontal_plane": plane,
        "world_z": float(inward[2]),
        "all": np.concatenate([
            plane,
            np.stack([palm, palm + normal_length * inward,
                      palm + 0.10 * up, palm + 0.14 * down]),
        ], axis=0),
    }


def camera_for_palm_world_direction_view(env, local_view_direction, width=1600,
                                         height=900, horizontal_fov_deg=55.0):
    """Frame the palm vector and world-horizontal reference plane."""
    direction = np.asarray(local_view_direction, dtype=np.float64)
    if direction.shape != (3,) or np.linalg.norm(direction) < 1e-8:
        raise ValueError("local_view_direction must be a non-zero xyz triple")
    direction /= np.linalg.norm(direction)
    origin_and_direction = _guitar_local_to_world(
        env, np.stack([np.zeros(3, dtype=np.float64), direction]))
    world_direction = origin_and_direction[1] - origin_and_direction[0]
    world_direction /= max(np.linalg.norm(world_direction), 1e-12)

    geometry = palm_world_direction_geometry(env)
    neck_local = np.array([
        [-NECK_BODY_HALF_WIDTH, NECK_BODY_Y, NECK_BACK_Z],
        [NECK_BODY_HALF_WIDTH, NECK_BODY_Y, NECK_FRONT_Z],
        [-NECK_NUT_HALF_WIDTH, NECK_NUT_Y, NECK_BACK_Z],
        [NECK_NUT_HALF_WIDTH, NECK_NUT_Y, NECK_FRONT_Z],
    ])
    points = np.concatenate([geometry["all"], _guitar_local_to_world(env, neck_local)], axis=0)
    center = points.mean(axis=0)
    radius = max(np.linalg.norm(points - center, axis=1))
    vertical_fov = 2.0 * math.atan(
        (height / width) * math.tan(math.radians(horizontal_fov_deg) / 2.0))
    half_fov = min(math.radians(horizontal_fov_deg) / 2.0, vertical_fov / 2.0)
    distance = 1.25 * radius / max(math.sin(half_fov), 1e-8)
    eye = center + distance * world_direction
    return CameraSpec(tuple(float(x) for x in eye), tuple(float(x) for x in center),
                      int(width), int(height), float(horizontal_fov_deg))


def camera_for_palm_neck_direction_view(env, local_view_direction, width=1600,
                                        height=900, horizontal_fov_deg=55.0):
    """Frame the left palm, neck and R13 direction arrows."""
    direction = np.asarray(local_view_direction, dtype=np.float64)
    if direction.shape != (3,) or np.linalg.norm(direction) < 1e-8:
        raise ValueError("local_view_direction must be a non-zero xyz triple")
    direction /= np.linalg.norm(direction)
    origin_and_direction = _guitar_local_to_world(
        env, np.stack([np.zeros(3, dtype=np.float64), direction]))
    world_direction = origin_and_direction[1] - origin_and_direction[0]
    world_direction /= max(np.linalg.norm(world_direction), 1e-12)

    geometry = palm_neck_direction_geometry(env)
    neck_local = np.array([
        [-NECK_BODY_HALF_WIDTH, NECK_BODY_Y, NECK_BACK_Z],
        [NECK_BODY_HALF_WIDTH, NECK_BODY_Y, NECK_FRONT_Z],
        [-NECK_NUT_HALF_WIDTH, NECK_NUT_Y, NECK_BACK_Z],
        [NECK_NUT_HALF_WIDTH, NECK_NUT_Y, NECK_FRONT_Z],
    ])
    points = np.concatenate([geometry["all"], _guitar_local_to_world(env, neck_local)], axis=0)
    center = points.mean(axis=0)
    radius = max(np.linalg.norm(points - center, axis=1))
    vertical_fov = 2.0 * math.atan(
        (height / width) * math.tan(math.radians(horizontal_fov_deg) / 2.0))
    half_fov = min(math.radians(horizontal_fov_deg) / 2.0, vertical_fov / 2.0)
    distance = 1.25 * radius / max(math.sin(half_fov), 1e-8)
    eye = center + distance * world_direction
    return CameraSpec(tuple(float(x) for x in eye), tuple(float(x) for x in center),
                      int(width), int(height), float(horizontal_fov_deg))


def _string_edge_at(center, string_start, string_end, neck_axis):
    direction = string_end - string_start
    denom = float(np.dot(direction, neck_axis))
    if abs(denom) < 1e-10:
        return string_start
    t = float(np.dot(center - string_start, neck_axis) / denom)
    return string_start + np.clip(t, 0.0, 1.0) * direction


def fretboard_overlay_geometry(env, max_fret=12, optimal_band=(0.10, 0.30),
                               falloff_band=(0.30, 0.85), approach_x=0.20):
    """Build world-space wire and press-band geometry from live rigid bodies.

    Fractions use the playable wood between wire surfaces: x=0 is the target
    wire's nut-side surface and x=1 is the previous wire's bridge-side surface.
    """
    if not (1 <= max_fret <= 22):
        raise ValueError("max_fret must be in [1, 22]")
    for name, band in (("optimal_band", optimal_band), ("falloff_band", falloff_band)):
        if len(band) != 2 or not (0.0 <= band[0] <= band[1] <= 1.0):
            raise ValueError(f"{name} must satisfy 0 <= low <= high <= 1")
    if not (0.0 <= approach_x <= 1.0):
        raise ValueError("approach_x must be in [0, 1]")

    wires = [_as_np(env.gbody_pos("G:nut"))]
    wires += [_as_np(env.gbody_pos(f"G:fret{i}")) for i in range(1, max_fret + 1)]
    high_start = _as_np(env.gbody_pos("G:string1"))
    high_end = _as_np(env.gbody_pos("G:string1_end"))
    low_start = _as_np(env.gbody_pos("G:string6"))
    low_end = _as_np(env.gbody_pos("G:string6_end"))
    neck_axis = wires[-1] - wires[0]
    neck_axis /= max(np.linalg.norm(neck_axis), 1e-12)

    def edge_pair(center, pad=0.003):
        high = _string_edge_at(center, high_start, high_end, neck_axis)
        low = _string_edge_at(center, low_start, low_end, neck_axis)
        across = high - low
        across /= max(np.linalg.norm(across), 1e-12)
        return high + pad * across, low - pad * across

    result = []
    for fret in range(1, max_fret + 1):
        previous, target = wires[fret - 1], wires[fret]
        toward_previous = previous - target
        cell_length = max(np.linalg.norm(toward_previous), 1e-12)
        toward_previous /= cell_length
        previous_half = 0.000955 if fret == 1 else 0.0007
        target_edge = target + 0.0007 * toward_previous
        previous_edge = previous - previous_half * toward_previous
        wood = previous_edge - target_edge

        def center_at(x):
            return target_edge + x * wood

        target_hi, target_lo = edge_pair(target)
        optimal_near_hi, optimal_near_lo = edge_pair(center_at(optimal_band[0]))
        optimal_far_hi, optimal_far_lo = edge_pair(center_at(optimal_band[1]))
        falloff_near_hi, falloff_near_lo = edge_pair(center_at(falloff_band[0]))
        falloff_far_hi, falloff_far_lo = edge_pair(center_at(falloff_band[1]))
        approach_hi, approach_lo = edge_pair(center_at(approach_x))
        result.append({
            "fret": fret,
            "wire": np.stack([target_lo, target_hi]),
            "optimal": np.stack([optimal_near_lo, optimal_near_hi,
                                  optimal_far_hi, optimal_far_lo]),
            "falloff": np.stack([falloff_near_lo, falloff_near_hi,
                                  falloff_far_hi, falloff_far_lo]),
            "approach": np.stack([approach_lo, approach_hi]),
            "label": target_hi + 0.010 * (target_hi - target_lo) /
                     max(np.linalg.norm(target_hi - target_lo), 1e-12),
        })
    return result


def string_overlay_geometry(env):
    """Return the six live string centerlines in high-e to low-E order."""
    names = ("1 high-e", "2 B", "3 G", "4 D", "5 A", "6 low-E")
    result = []
    for string_no, name in enumerate(names, start=1):
        start = _as_np(env.gbody_pos(f"G:string{string_no}"))
        end = _as_np(env.gbody_pos(f"G:string{string_no}_end"))
        # Put the label near one end but still on the visible string centerline.
        label = start + 0.08 * (end - start)
        result.append({"string": string_no, "name": name,
                       "line": np.stack([start, end]), "label": label})
    return result


def draw_fretboard_overlay(image_path, env, camera_spec, max_fret=12,
                           optimal_band=(0.10, 0.30), falloff_band=(0.30, 0.85),
                           approach_x=0.20,
                           active_frets=(), show_strings=False):
    """Annotate an Isaac camera PNG with exact fret wires and press ranges."""
    image_path = Path(image_path)
    base = Image.open(image_path).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.load_default()
    active = {int(f) for f in active_frets if 1 <= int(f) <= max_fret}

    geometry = fretboard_overlay_geometry(env, max_fret=max_fret,
                                          optimal_band=optimal_band,
                                          falloff_band=falloff_band,
                                          approach_x=approach_x)
    for item in geometry:
        optimal_px, optimal_z = _project(item["optimal"], camera_spec)
        falloff_px, falloff_z = _project(item["falloff"], camera_spec)
        approach_px, approach_z = _project(item["approach"], camera_spec)
        wire_px, wire_z = _project(item["wire"], camera_spec)
        label_px, label_z = _project(item["label"][None], camera_spec)
        if min(optimal_z.min(), falloff_z.min(), approach_z.min(),
               wire_z.min(), label_z.min()) <= 0:
            continue

        is_active = item["fret"] in active
        falloff_color = (30, 220, 110, 90 if is_active else 45)
        optimal_color = (255, 205, 40, 145 if is_active else 85)
        wire_color = (255, 80, 170, 255) if is_active else (80, 230, 255, 245)
        draw.polygon([tuple(p) for p in falloff_px], fill=falloff_color)
        draw.polygon([tuple(p) for p in optimal_px], fill=optimal_color)
        draw.line([tuple(p) for p in wire_px], fill=(5, 10, 15, 230), width=6)
        draw.line([tuple(p) for p in wire_px], fill=wire_color, width=3)
        draw.line([tuple(p) for p in approach_px], fill=(255, 80, 170, 255), width=3)

        x, y = (float(label_px[0, 0]), float(label_px[0, 1]))
        text = str(item["fret"])
        box = draw.textbbox((x, y), text, font=font, anchor="mm")
        draw.rounded_rectangle((box[0] - 4, box[1] - 3, box[2] + 4, box[3] + 3),
                               radius=3, fill=(0, 0, 0, 210))
        draw.text((x, y), text, font=font, anchor="mm", fill=wire_color)

    string_colors = (
        (255, 105, 180, 255), (255, 145, 55, 255), (255, 220, 70, 255),
        (80, 230, 130, 255), (70, 190, 255, 255), (170, 125, 255, 255),
    )
    if show_strings:
        for item, color in zip(string_overlay_geometry(env), string_colors):
            line_px, line_z = _project(item["line"], camera_spec)
            label_px, label_z = _project(item["label"][None], camera_spec)
            if min(line_z.min(), label_z.min()) <= 0:
                continue
            draw.line([tuple(p) for p in line_px], fill=(0, 0, 0, 220), width=7)
            draw.line([tuple(p) for p in line_px], fill=color, width=3)
            x, y = (float(label_px[0, 0]), float(label_px[0, 1]))
            text = item["name"]
            box = draw.textbbox((x, y), text, font=font, anchor="mm")
            draw.rounded_rectangle((box[0] - 5, box[1] - 3, box[2] + 5, box[3] + 3),
                                   radius=4, fill=(0, 0, 0, 220), outline=color, width=2)
            draw.text((x, y), text, font=font, anchor="mm", fill="white")

    legend_height = 178 if show_strings else 100
    legend = Image.new("RGBA", (390, legend_height), (0, 0, 0, 185))
    ld = ImageDraw.Draw(legend)
    ld.rectangle((12, 13, 34, 25), fill=(255, 205, 40, 170))
    ld.text((42, 11), "position quality max: x=10-30%", font=font, fill="white")
    ld.rectangle((12, 36, 34, 48), fill=(30, 220, 110, 140))
    ld.text((42, 34), "position bonus fades: x=30-85%", font=font, fill="white")
    ld.line((12, 61, 34, 61), fill=(255, 80, 170, 255), width=3)
    ld.text((42, 55), "approach target: x=20%", font=font, fill="white")
    ld.line((12, 84, 34, 84), fill=(80, 230, 255, 255), width=3)
    ld.text((42, 78), "actual G:fretN rigid-body position", font=font, fill="white")
    if show_strings:
        ld.text((12, 104), "strings (player view):", font=font, fill="white")
        for index, (name, color) in enumerate(zip(
                ("1 high-e", "2 B", "3 G", "4 D", "5 A", "6 low-E"),
                string_colors)):
            column = index % 3
            row = index // 3
            x = 12 + column * 124
            y = 126 + row * 24
            ld.line((x, y, x + 18, y), fill=color, width=3)
            ld.text((x + 24, y - 6), name, font=font, fill="white")
    layer.alpha_composite(legend, dest=(16, 16))

    Image.alpha_composite(base, layer).convert("RGB").save(image_path, quality=95)
    return image_path


def draw_wrist_safety_box_overlay(image_path, env, camera_spec,
                                  bounds_min=(-0.20, -0.35, -0.30),
                                  bounds_max=(0.30, 0.35, 0.25)):
    """Draw a translucent solid box for the proposed guitar-local wrist envelope."""
    image_path = Path(image_path)
    base = Image.open(image_path).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.load_default()
    corners = wrist_safety_box_geometry(env, bounds_min, bounds_max)
    pixels, depths = _project(corners, camera_spec)

    # Corner index bits are x/y/z. Paint far faces first, then a strong wireframe.
    faces = (
        (0, 1, 3, 2), (4, 6, 7, 5),
        (0, 4, 5, 1), (2, 3, 7, 6),
        (0, 2, 6, 4), (1, 5, 7, 3),
    )
    face_order = sorted(faces, key=lambda face: float(depths[list(face)].mean()),
                        reverse=True)
    for face in face_order:
        if depths[list(face)].min() <= 0:
            continue
        draw.polygon([tuple(pixels[i]) for i in face],
                     fill=(45, 145, 255, 38), outline=(75, 190, 255, 125))

    edges = (
        (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
        (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7),
    )
    for a, b in edges:
        if min(depths[a], depths[b]) > 0:
            draw.line([tuple(pixels[a]), tuple(pixels[b])],
                      fill=(45, 185, 255, 235), width=4)

    lo = tuple(float(v) for v in bounds_min)
    hi = tuple(float(v) for v in bounds_max)
    legend = Image.new("RGBA", (510, 84), (0, 0, 0, 195))
    ld = ImageDraw.Draw(legend)
    ld.rectangle((12, 14, 36, 30), fill=(45, 145, 255, 95),
                 outline=(75, 200, 255, 255), width=2)
    ld.text((46, 12), "proposed wrist safety envelope (guitar-local)",
            font=font, fill="white")
    ld.text((12, 39), f"min xyz = ({lo[0]:.2f}, {lo[1]:.2f}, {lo[2]:.2f}) m",
            font=font, fill=(185, 225, 255, 255))
    ld.text((12, 59), f"max xyz = ({hi[0]:.2f}, {hi[1]:.2f}, {hi[2]:.2f}) m",
            font=font, fill=(185, 225, 255, 255))
    layer.alpha_composite(legend, dest=(16, base.height - legend.height - 16))

    Image.alpha_composite(base, layer).convert("RGB").save(image_path, quality=95)
    return image_path


def draw_finger_back_limit_overlay(image_path, env, camera_spec, limit_z=-0.050):
    """Draw the R8 z-limit as one plane with arrows toward its forbidden side."""
    image_path = Path(image_path)
    base = Image.open(image_path).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.load_default()
    geometry = finger_back_limit_geometry(env, limit_z=limit_z)
    boundary_px, boundary_depth = _project(geometry["boundary"], camera_spec)
    neck_px, neck_depth = _project(geometry["neck_back"], camera_spec)
    origins_px, origins_depth = _project(geometry["arrow_origins"], camera_spec)
    ends_px, ends_depth = _project(geometry["arrow_ends"], camera_spec)

    if boundary_depth.min() > 0:
        polygon = [tuple(p) for p in boundary_px]
        draw.polygon(polygon, fill=(245, 45, 55, 52))
        draw.line(polygon + [polygon[0]], fill=(255, 65, 70, 255), width=6, joint="curve")
    if neck_depth.min() > 0:
        polygon = [tuple(p) for p in neck_px]
        draw.polygon(polygon, fill=(255, 205, 40, 35))
        draw.line(polygon + [polygon[0]], fill=(255, 215, 55, 245), width=4, joint="curve")

    for start, end, start_z, end_z in zip(origins_px, ends_px, origins_depth, ends_depth):
        if min(start_z, end_z) <= 0:
            continue
        start, end = np.asarray(start), np.asarray(end)
        draw.line([tuple(start), tuple(end)], fill=(255, 70, 75, 245), width=5)
        direction = end - start
        length = max(np.linalg.norm(direction), 1e-8)
        unit = direction / length
        normal = np.array([-unit[1], unit[0]])
        head_a = end - 15 * unit + 7 * normal
        head_b = end - 15 * unit - 7 * normal
        draw.polygon([tuple(end), tuple(head_a), tuple(head_b)], fill=(255, 70, 75, 255))

    legend = Image.new("RGBA", (570, 116), (0, 0, 0, 205))
    ld = ImageDraw.Draw(legend)
    ld.rectangle((12, 15, 36, 29), fill=(255, 215, 55, 80),
                 outline=(255, 215, 55, 255), width=2)
    ld.text((46, 14), "actual neck-back surface: z=-8 mm", font=font, fill="white")
    ld.rectangle((12, 43, 36, 57), fill=(255, 65, 70, 90),
                 outline=(255, 65, 70, 255), width=2)
    ld.text((46, 42), f"R8 boundary plane: guitar-local z={1000 * limit_z:.0f} mm",
            font=font, fill="white")
    ld.text((12, 70), "red arrows: terminate side (z below boundary); plane is infinite",
            font=font, fill=(255, 185, 185, 255))
    ld.text((12, 94), "checked: index/middle/ring/pinky segments | thumb excluded",
            font=font, fill=(190, 225, 255, 255))
    layer.alpha_composite(legend, dest=(16, base.height - legend.height - 16))

    Image.alpha_composite(base, layer).convert("RGB").save(image_path, quality=95)
    return image_path


def draw_palm_neck_direction_overlay(image_path, env, camera_spec):
    """Draw R13 palm/neck direction arrows without changing the simulation."""
    image_path = Path(image_path)
    base = Image.open(image_path).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.load_default()
    geometry = palm_neck_direction_geometry(env)
    palm = geometry["palm"]

    def arrow(end, color, width=7):
        points, depth = _project(np.stack([palm, end]), camera_spec)
        if depth.min() <= 0:
            return
        start, finish = points
        draw.line([tuple(start), tuple(finish)], fill=color, width=width)
        vector = finish - start
        length = max(np.linalg.norm(vector), 1e-8)
        unit = vector / length
        normal = np.array([-unit[1], unit[0]])
        a = finish - 18 * unit + 8 * normal
        b = finish - 18 * unit - 8 * normal
        draw.polygon([tuple(finish), tuple(a), tuple(b)], fill=color)

    # Draw the forbidden direction first so the two anatomical arrows remain clear.
    arrow(geometry["opposite_end"], (255, 65, 75, 245), 7)
    arrow(geometry["to_neck_end"], (40, 215, 255, 255), 8)
    arrow(geometry["inward_end"], (70, 235, 120, 255), 8)
    closest_px, closest_depth = _project(geometry["closest_neck"][None], camera_spec)
    if closest_depth[0] > 0:
        x, y = closest_px[0]
        draw.ellipse((x - 7, y - 7, x + 7, y + 7),
                     fill=(40, 215, 255, 255), outline=(0, 0, 0, 230), width=2)

    legend = Image.new("RGBA", (600, 140), (0, 0, 0, 210))
    ld = ImageDraw.Draw(legend)
    rows = (
        ((40, 215, 255, 255), "direction from palm to nearest neck surface"),
        ((70, 235, 120, 255), "anatomical palm inward normal (fixed sign)"),
        ((255, 65, 75, 255), "opposite/termination direction"),
    )
    for index, (color, label) in enumerate(rows):
        y = 16 + 28 * index
        ld.line((12, y + 7, 38, y + 7), fill=color, width=6)
        ld.text((48, y), label, font=font, fill="white")
    ld.text((12, 102), f"current alignment dot = {geometry['alignment']:+.3f}",
            font=font, fill=(210, 235, 255, 255))
    ld.text((12, 122), "candidate reset: dot < -0.3 for 3 consecutive frames",
            font=font, fill=(255, 185, 190, 255))
    layer.alpha_composite(legend, dest=(16, base.height - legend.height - 16))
    Image.alpha_composite(base, layer).convert("RGB").save(image_path, quality=95)
    return image_path


def draw_palm_world_direction_overlay(image_path, env, camera_spec):
    """Draw the palm inward vector against the fixed world floor direction."""
    image_path = Path(image_path)
    base = Image.open(image_path).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.load_default()
    geometry = palm_world_direction_geometry(env)
    palm = geometry["palm"]

    plane_px, plane_depth = _project(geometry["horizontal_plane"], camera_spec)
    if plane_depth.min() > 0:
        polygon = [tuple(p) for p in plane_px]
        draw.polygon(polygon, fill=(80, 170, 255, 35))
        draw.line(polygon + [polygon[0]], fill=(100, 190, 255, 180), width=3)

    def arrow(end, color, width=8):
        points, depth = _project(np.stack([palm, end]), camera_spec)
        if depth.min() <= 0:
            return
        start, finish = points
        draw.line([tuple(start), tuple(finish)], fill=color, width=width)
        vector = finish - start
        length = max(np.linalg.norm(vector), 1e-8)
        unit = vector / length
        normal = np.array([-unit[1], unit[0]])
        a = finish - 18 * unit + 8 * normal
        b = finish - 18 * unit - 8 * normal
        draw.polygon([tuple(finish), tuple(a), tuple(b)], fill=color)

    arrow(geometry["up_end"], (80, 180, 255, 235), 6)
    arrow(geometry["down_end"], (255, 65, 75, 255), 8)
    arrow(geometry["inward_end"], (70, 235, 120, 255), 9)

    legend = Image.new("RGBA", (610, 140), (0, 0, 0, 210))
    ld = ImageDraw.Draw(legend)
    rows = (
        ((70, 235, 120, 255), "anatomical palm inward vector"),
        ((80, 180, 255, 255), "world up (+Z) / horizontal reference plane"),
        ((255, 65, 75, 255), "world floor direction (-Z)"),
    )
    for index, (color, label) in enumerate(rows):
        y = 16 + 28 * index
        ld.line((12, y + 7, 38, y + 7), fill=color, width=6)
        ld.text((48, y), label, font=font, fill="white")
    ld.text((12, 102), f"current palm vector world-z = {geometry['world_z']:+.3f}",
            font=font, fill=(210, 235, 255, 255))
    ld.text((12, 122), "candidate reset: world-z < -0.3 for 3 consecutive frames",
            font=font, fill=(255, 185, 190, 255))
    layer.alpha_composite(legend, dest=(16, base.height - legend.height - 16))
    Image.alpha_composite(base, layer).convert("RGB").save(image_path, quality=95)
    return image_path
