"""CPU/PIL diagnostics for the virtual-pick strike task.

The strike detector operates on the live, finite ``G:string1..6`` segments in
the guitar frame.  This module visualizes that same geometry after clipping
each segment by guitar-local ``y``.  It is deliberately a post-processing
overlay: neither the colored ribbons nor ``RH:pick`` add collision geometry to
the Isaac Gym scene.

The public geometry helpers only depend on NumPy.  Torch-like values supplied
by a live task are converted through ``detach().cpu().numpy()`` without
importing torch at module load time.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont


N_GUITAR_STRINGS = 6
VISUAL_STRING_RIBBON_HALF_WIDTH_M = 0.002


OVERLAY_COLORS = {
    "string": (218, 224, 232, 215),
    "allowed": (41, 121, 255, 82),
    "allowed_outline": (71, 151, 255, 205),
    "preferred": (43, 207, 139, 102),
    "preferred_outline": (72, 235, 169, 220),
    "lane_outer": (255, 159, 40, 120),
    "lane_outer_outline": (255, 179, 70, 235),
    "lane_core": (255, 223, 64, 155),
    "lane_core_outline": (255, 237, 112, 245),
    "lane_center": (255, 255, 240, 255),
    "active_string": (255, 244, 145, 255),
    "pick": (255, 67, 140, 255),
    "pick_outline": (255, 245, 250, 255),
    "pick_trail": (255, 92, 157, 180),
    "legend_background": (8, 12, 20, 205),
    "legend_text": (245, 248, 252, 255),
}


@dataclass(frozen=True)
class CameraSpec:
    """Pinhole camera contract shared by the existing Isaac Gym overlays."""

    eye: tuple[float, float, float]
    target: tuple[float, float, float]
    width: int
    height: int
    horizontal_fov_deg: float = 55.0


def _numpy(value: Any, *, name: str) -> np.ndarray:
    """Convert NumPy/sequence/torch-like input to a detached CPU float array."""
    candidate = value
    detach = getattr(candidate, "detach", None)
    if callable(detach):
        candidate = detach()
    cpu = getattr(candidate, "cpu", None)
    if callable(cpu):
        candidate = cpu()
    as_numpy = getattr(candidate, "numpy", None)
    if callable(as_numpy):
        candidate = as_numpy()
    try:
        result = np.asarray(candidate, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be numeric array-like data") from exc
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain only finite values")
    return result


def _xyz(value: Any, *, name: str) -> np.ndarray:
    result = _numpy(value, name=name)
    if result.shape != (3,):
        raise ValueError(f"{name} must be one xyz triple")
    return result


def _finite_scalar(value: Any, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{name} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _ordered_interval(
        value: Sequence[float], *, name: str, allow_equal: bool = False
) -> tuple[float, float]:
    try:
        length = len(value)
    except TypeError as exc:
        raise TypeError(f"{name} must contain two finite bounds") from exc
    if length != 2:
        raise ValueError(f"{name} must contain two finite bounds")
    lo = _finite_scalar(value[0], name=f"{name}[0]")
    hi = _finite_scalar(value[1], name=f"{name}[1]")
    if lo > hi or (not allow_equal and lo == hi):
        relation = "<=" if allow_equal else "<"
        raise ValueError(f"{name} must satisfy low {relation} high")
    return lo, hi


def validate_camera_spec(spec: CameraSpec) -> CameraSpec:
    """Return a normalized camera specification or fail before drawing."""
    try:
        eye = tuple(float(value) for value in spec.eye)
        target = tuple(float(value) for value in spec.target)
        width = int(spec.width)
        height = int(spec.height)
        fov = float(spec.horizontal_fov_deg)
    except (AttributeError, TypeError, ValueError) as exc:
        raise TypeError(
            "camera_spec must expose eye, target, width, height and "
            "horizontal_fov_deg"
        ) from exc
    if len(eye) != 3 or len(target) != 3:
        raise ValueError("camera eye and target must be xyz triples")
    if not all(math.isfinite(value) for value in eye + target):
        raise ValueError("camera eye and target must be finite")
    if isinstance(spec.width, bool) or isinstance(spec.height, bool):
        raise TypeError("camera width and height must be integers")
    if width != spec.width or height != spec.height or width <= 0 or height <= 0:
        raise ValueError("camera width and height must be positive integers")
    if not math.isfinite(fov) or not 0.0 < fov < 179.0:
        raise ValueError("camera horizontal_fov_deg must be in (0, 179)")
    if np.linalg.norm(np.asarray(target) - np.asarray(eye)) < 1e-9:
        raise ValueError("camera eye and target must be distinct")
    return CameraSpec(eye, target, width, height, fov)


def camera_basis(
        camera_spec: CameraSpec,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return ``eye, right, up, forward`` using the established camera basis."""
    spec = validate_camera_spec(camera_spec)
    eye = np.asarray(spec.eye, dtype=np.float64)
    target = np.asarray(spec.target, dtype=np.float64)
    forward = target - eye
    forward /= np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    right = np.cross(forward, world_up)
    if np.linalg.norm(right) < 1e-8:
        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    up /= np.linalg.norm(up)
    return eye, right, up, forward


def project_world_points(
        points_world: Any, camera_spec: CameraSpec
) -> tuple[np.ndarray, np.ndarray]:
    """Project world xyz points with the current horizontal-FOV contract.

    Pixel coordinates are returned even for points outside the image.  The
    paired positive depth is the authoritative visibility test; callers must
    not draw points with depth at or behind zero.
    """
    points = _numpy(points_world, name="points_world")
    if points.ndim == 1:
        if points.shape != (3,):
            raise ValueError("points_world must end in xyz")
        points = points[None, :]
    if points.ndim < 2 or points.shape[-1] != 3:
        raise ValueError("points_world must have shape (..., 3)")
    spec = validate_camera_spec(camera_spec)
    original_shape = points.shape[:-1]
    flat = points.reshape(-1, 3)
    eye, right, up, forward = camera_basis(spec)
    relative = flat - eye
    x_camera = relative @ right
    y_camera = relative @ up
    depth = relative @ forward
    focal = spec.width / (
        2.0 * math.tan(math.radians(spec.horizontal_fov_deg) / 2.0)
    )
    safe_depth = np.maximum(depth, 1e-8)
    pixel_x = 0.5 * spec.width + focal * x_camera / safe_depth
    pixel_y = 0.5 * spec.height - focal * y_camera / safe_depth
    pixels = np.stack([pixel_x, pixel_y], axis=-1)
    return pixels.reshape(original_shape + (2,)), depth.reshape(original_shape)


def clip_segment_to_y_interval(
        start_g: Any,
        end_g: Any,
        y_interval: Sequence[float],
        *,
        epsilon: float = 1e-12,
) -> np.ndarray | None:
    """Clip one finite guitar-local xyz segment to an inclusive ``y`` band.

    The output preserves the input segment direction and has shape ``(2, 3)``.
    ``None`` means the finite segment never enters the requested interval.
    A segment with constant ``y`` is either kept in full or rejected.
    """
    start = _xyz(start_g, name="start_g")
    end = _xyz(end_g, name="end_g")
    lo, hi = _ordered_interval(
        y_interval, name="y_interval", allow_equal=True
    )
    eps = _finite_scalar(epsilon, name="epsilon")
    if eps <= 0.0:
        raise ValueError("epsilon must be positive")
    delta = end - start
    if np.linalg.norm(delta) <= eps:
        raise ValueError("string segment endpoints must be distinct")
    delta_y = float(delta[1])
    if abs(delta_y) <= eps:
        if lo - eps <= start[1] <= hi + eps:
            return np.stack([start, end])
        return None
    at_lo = (lo - start[1]) / delta_y
    at_hi = (hi - start[1]) / delta_y
    enter = max(0.0, min(at_lo, at_hi))
    leave = min(1.0, max(at_lo, at_hi))
    if enter > leave + eps:
        return None
    enter = min(max(enter, 0.0), 1.0)
    leave = min(max(leave, 0.0), 1.0)
    return np.stack([start + enter * delta, start + leave * delta])


def point_on_segment_at_y(
        start_g: Any, end_g: Any, y_g: float, *, epsilon: float = 1e-12
) -> np.ndarray | None:
    """Return the finite-segment point at guitar-local ``y``, if it exists."""
    clipped = clip_segment_to_y_interval(
        start_g, end_g, (y_g, y_g), epsilon=epsilon
    )
    if clipped is None:
        return None
    return 0.5 * (clipped[0] + clipped[1])


def ribbon_polygon(
        clipped_segment_g: Any,
        *,
        half_width_m: float = VISUAL_STRING_RIBBON_HALF_WIDTH_M,
    ) -> np.ndarray:
    """Expand a clipped centerline to a physical-width guitar-local polygon."""
    segment = _numpy(clipped_segment_g, name="clipped_segment_g")
    if segment.shape != (2, 3):
        raise ValueError("clipped_segment_g must have shape (2, 3)")
    half_width = _finite_scalar(half_width_m, name="half_width_m")
    if half_width <= 0.0:
        raise ValueError("half_width_m must be positive")
    tangent_xy = segment[1, :2] - segment[0, :2]
    length_xy = float(np.linalg.norm(tangent_xy))
    if length_xy <= 1e-12:
        raise ValueError(
            "cannot construct a string ribbon from a degenerate xy centerline"
        )
    normal_xy = np.array(
        [-tangent_xy[1], tangent_xy[0]], dtype=np.float64
    ) / length_xy
    offset = np.array(
        [half_width * normal_xy[0], half_width * normal_xy[1], 0.0],
        dtype=np.float64,
    )
    return np.stack(
        [
            segment[0] - offset,
            segment[1] - offset,
            segment[1] + offset,
            segment[0] + offset,
        ]
    )


def _string_array(value: Any, *, name: str) -> np.ndarray:
    result = _numpy(value, name=name)
    if result.ndim == 3 and result.shape[1:] == (N_GUITAR_STRINGS, 3):
        result = result[0]
    if result.shape != (N_GUITAR_STRINGS, 3):
        raise ValueError(
            f"{name} must have shape (6, 3) or (N, 6, 3)"
        )
    return result


def _target_index(value: Any) -> int:
    array = _numpy(value, name="target_string").reshape(-1)
    if array.size != 1:
        raise ValueError("target_string must contain one zero-based index")
    scalar = float(array[0])
    if not scalar.is_integer():
        raise ValueError("target_string must be a zero-based integer")
    result = int(scalar)
    if not 0 <= result < N_GUITAR_STRINGS:
        raise ValueError("target_string must be in [0, 5]")
    return result


def build_strike_overlay_geometry(
    string_start_g: Any,
    string_end_g: Any,
    *,
    allowed_y: Sequence[float],
    preferred_y: Sequence[float],
    target_lane_y: float,
    lane_outer_half_width_m: float,
    lane_core_half_width_m: float,
    target_string: int,
    ribbon_half_width_m: float = VISUAL_STRING_RIBBON_HALF_WIDTH_M,
) -> dict[str, Any]:
    """Build exact guitar-local strike ribbons from six finite segments.

    The returned arrays remain in guitar-local metres and are convenient for
    pure CPU tests.  Each string includes clipped allowed/preferred/lane
    centerlines and their physical-width polygons.  ``target_string`` is
    zero-based internally while ``string_number`` is the visible 1..6 label.
    """
    starts = _string_array(string_start_g, name="string_start_g")
    ends = _string_array(string_end_g, name="string_end_g")
    allowed = _ordered_interval(allowed_y, name="allowed_y")
    preferred = _ordered_interval(preferred_y, name="preferred_y")
    if not (
        allowed[0] <= preferred[0]
        and preferred[1] <= allowed[1]
    ):
        raise ValueError("preferred_y must be contained in allowed_y")
    lane_y = _finite_scalar(target_lane_y, name="target_lane_y")
    outer = _finite_scalar(
        lane_outer_half_width_m, name="lane_outer_half_width_m"
    )
    core = _finite_scalar(
        lane_core_half_width_m, name="lane_core_half_width_m"
    )
    if core < 0.0 or outer <= 0.0 or core >= outer:
        raise ValueError(
            "lane widths must satisfy 0 <= core < outer"
        )






    tolerance = 1e-7
    lane_within_preferred = (
        preferred[0] - tolerance
        <= lane_y
        <= preferred[1] + tolerance
    )
    lane_outer = (lane_y - outer, lane_y + outer)
    lane_core = (lane_y - core, lane_y + core)
    if (
        lane_outer[0] < allowed[0] - tolerance
        or lane_outer[1] > allowed[1] + tolerance
    ):
        raise ValueError("the target outer lane must stay inside allowed_y")
    target_index = _target_index(target_string)
    half_width = _finite_scalar(
        ribbon_half_width_m, name="ribbon_half_width_m"
    )
    if half_width <= 0.0:
        raise ValueError("ribbon_half_width_m must be positive")

    intervals = {
        "allowed": allowed,
        "preferred": preferred,
        "lane_outer": lane_outer,
        "lane_core": lane_core,
    }
    strings = []
    for index, (start, end) in enumerate(zip(starts, ends)):
        if np.linalg.norm(end - start) <= 1e-12:
            raise ValueError(
                f"string {index + 1} segment endpoints must be distinct"
            )
        item: dict[str, Any] = {
            "string_index": index,
            "string_number": index + 1,
            "active": index == target_index,
            "segment": np.stack([start, end]),
        }
        for label, interval in intervals.items():
            centerline = clip_segment_to_y_interval(start, end, interval)
            if centerline is None:
                item[label] = None
            else:
                item[label] = {
                    "centerline": centerline,
                    "polygon": ribbon_polygon(
                        centerline, half_width_m=half_width
                    ),
                }
        item["lane_center"] = point_on_segment_at_y(start, end, lane_y)
        strings.append(item)
    return {
        "allowed_y": allowed,
        "preferred_y": preferred,
        "target_lane_y": lane_y,
        "target_lane_within_preferred": lane_within_preferred,
        "lane_outer_y": lane_outer,
        "lane_core_y": lane_core,
        "target_string": target_index,
        "target_string_number": target_index + 1,
        "ribbon_half_width_m": half_width,
        "strings": strings,
    }


def quaternion_xyzw_rotation(quaternion_xyzw: Any) -> np.ndarray:
    """Return a normalized 3x3 rotation for an Isaac Gym xyzw quaternion."""
    quaternion = _numpy(quaternion_xyzw, name="quaternion_xyzw")
    if quaternion.shape != (4,):
        raise ValueError("quaternion_xyzw must have shape (4,)")
    norm = float(np.linalg.norm(quaternion))
    if norm <= 1e-12:
        raise ValueError("quaternion_xyzw must be non-zero")
    x, y, z, w = quaternion / norm
    return np.array(
        [
            [
                1.0 - 2.0 * (y * y + z * z),
                2.0 * (x * y - z * w),
                2.0 * (x * z + y * w),
            ],
            [
                2.0 * (x * y + z * w),
                1.0 - 2.0 * (x * x + z * z),
                2.0 * (y * z - x * w),
            ],
            [
                2.0 * (x * z - y * w),
                2.0 * (y * z + x * w),
                1.0 - 2.0 * (x * x + y * y),
            ],
        ],
        dtype=np.float64,
    )


def guitar_local_to_world(
    points_g: Any, guitar_position_world: Any, guitar_quaternion_xyzw: Any
) -> np.ndarray:
    """Transform guitar-local xyz points to world coordinates."""
    points = _numpy(points_g, name="points_g")
    if points.ndim == 1:
        if points.shape != (3,):
            raise ValueError("points_g must end in xyz")
    elif points.ndim < 2 or points.shape[-1] != 3:
        raise ValueError("points_g must have shape (..., 3)")
    position = _xyz(guitar_position_world, name="guitar_position_world")
    rotation = quaternion_xyzw_rotation(guitar_quaternion_xyzw)
    return points @ rotation.T + position


def _first_environment(value: Any, *, name: str, trailing_shape: tuple[int, ...]):
    array = _numpy(value, name=name)
    if array.shape == trailing_shape:
        return array
    if array.ndim == len(trailing_shape) + 1 and array.shape[1:] == trailing_shape:
        return array[0]
    raise ValueError(
        f"{name} must have shape {trailing_shape} or (N,) + {trailing_shape}"
    )


def _environment_overlay_state(
    env: Any, pick_trail_world: Iterable[Any]
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    """Extract and validate one live environment without importing torch."""
    if not callable(getattr(env, "string_segments_g", None)):
        raise TypeError("env must expose string_segments_g()")
    starts_g, ends_g = env.string_segments_g()
    starts_g = _string_array(starts_g, name="env string starts")
    ends_g = _string_array(ends_g, name="env string ends")

    motion_target = getattr(env, "_current_motion_target", None)
    if callable(motion_target):
        target_value, lane_value = motion_target()
    else:
        if not callable(getattr(env, "_current_target_string", None)):
            raise TypeError("env must expose _current_target_string()")
        target_value = env._current_target_string()
        lane_value = getattr(env, "target_lane_y", None)
    target_string = _target_index(_numpy(
        target_value, name="target_string").reshape(-1)[:1])
    lane_y_array = _numpy(
        lane_value, name="env.target_lane_y").reshape(-1)
    if lane_y_array.size < 1:
        raise ValueError("env.target_lane_y must contain one value per environment")
    required = (
        "allowed_y",
        "preferred_y",
        "lane_allowed_half_width",
        "lane_core_half_width",
    )
    missing = [name for name in required if not hasattr(env, name)]
    if missing:
        raise TypeError(
            "env is missing strike-zone fields: " + ", ".join(missing)
        )
    geometry = build_strike_overlay_geometry(
        starts_g,
        ends_g,
        allowed_y=env.allowed_y,
        preferred_y=env.preferred_y,
        target_lane_y=lane_y_array[0],
        lane_outer_half_width_m=env.lane_allowed_half_width,
        lane_core_half_width_m=env.lane_core_half_width,
        target_string=target_string,
    )
    target_masks = getattr(env, "_current_target_masks", None)
    if callable(target_masks):
        traversal = _numpy(
            target_masks(), name="env target traversal mask")
        if traversal.ndim == 2:
            traversal = traversal[0]
        if traversal.shape != (N_GUITAR_STRINGS,):
            raise ValueError("env target traversal mask must have shape (N,6)")
        for index, string in enumerate(geometry["strings"]):
            string["active"] = bool(traversal[index])
        geometry["target_traversal_mask"] = [
            bool(value) for value in traversal.tolist()]
    progress = getattr(env, "_event_release_mask", None)
    if progress is not None:
        progress = _numpy(progress, name="env release progress mask")
        if progress.ndim == 2:
            progress = progress[0]
        geometry["completed_traversal_mask"] = [
            bool(value) for value in progress.tolist()]

    if not callable(getattr(env, "guitar_frame", None)):
        raise TypeError("env must expose guitar_frame()")
    guitar_position, guitar_quaternion = env.guitar_frame()
    guitar_position = _first_environment(
        guitar_position, name="guitar position", trailing_shape=(3,)
    )
    guitar_quaternion = _first_environment(
        guitar_quaternion, name="guitar quaternion", trailing_shape=(4,)
    )

    if not callable(getattr(env, "hbody_pos", None)):
        raise TypeError("env must expose hbody_pos()")
    pick_world = _first_environment(
        env.hbody_pos("RH:pick"),
        name="RH:pick world position",
        trailing_shape=(3,),
    )
    trail_items = list(pick_trail_world)
    if trail_items:
        trail_world = _numpy(trail_items, name="pick_trail_world")
        if trail_world.ndim == 3 and trail_world.shape[1:] == (1, 3):
            trail_world = trail_world[:, 0]
        if trail_world.ndim != 2 or trail_world.shape[1] != 3:
            raise ValueError("pick_trail_world must have shape (N, 3)")
    else:
        trail_world = np.empty((0, 3), dtype=np.float64)
    return (
        geometry,
        guitar_position,
        guitar_quaternion,
        np.concatenate([trail_world, pick_world[None]], axis=0),
    )


def _world_geometry(
    geometry_g: Mapping[str, Any],
    guitar_position: np.ndarray,
    guitar_quaternion: np.ndarray,
) -> dict[str, Any]:
    strings = []
    for item_g in geometry_g["strings"]:
        item_world: dict[str, Any] = {
            "string_index": item_g["string_index"],
            "string_number": item_g["string_number"],
            "active": item_g["active"],
            "segment": guitar_local_to_world(
                item_g["segment"], guitar_position, guitar_quaternion
            ),
        }
        for label in ("allowed", "preferred", "lane_outer", "lane_core"):
            layer_g = item_g[label]
            if layer_g is None:
                item_world[label] = None
            else:
                item_world[label] = {
                    "centerline": guitar_local_to_world(
                        layer_g["centerline"],
                        guitar_position,
                        guitar_quaternion,
                    ),
                    "polygon": guitar_local_to_world(
                        layer_g["polygon"],
                        guitar_position,
                        guitar_quaternion,
                    ),
                }
        center = item_g["lane_center"]
        item_world["lane_center"] = (
            None
            if center is None
            else guitar_local_to_world(
                center, guitar_position, guitar_quaternion
            )
        )
        strings.append(item_world)
    return {"strings": strings}


def _visible_pixels(
    points_world: np.ndarray, camera_spec: CameraSpec
) -> np.ndarray | None:
    pixels, depth = project_world_points(points_world, camera_spec)
    if np.any(depth <= 1e-6) or not np.all(np.isfinite(pixels)):
        return None
    return pixels


def _draw_polygon(
    draw: ImageDraw.ImageDraw,
    points_world: np.ndarray,
    camera_spec: CameraSpec,
    *,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    width: int = 1,
) -> bool:
    pixels = _visible_pixels(points_world, camera_spec)
    if pixels is None:
        return False
    xy = [tuple(float(value) for value in point) for point in pixels]
    draw.polygon(xy, fill=fill)
    draw.line(xy + [xy[0]], fill=outline, width=width, joint="curve")
    return True


def _draw_line(
    draw: ImageDraw.ImageDraw,
    points_world: np.ndarray,
    camera_spec: CameraSpec,
    *,
    fill: tuple[int, int, int, int],
    width: int,
) -> bool:
    pixels = _visible_pixels(points_world, camera_spec)
    if pixels is None:
        return False
    draw.line(
        [tuple(float(value) for value in point) for point in pixels],
        fill=fill,
        width=width,
        joint="curve",
    )
    return True


def _text_size(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont
) -> tuple[int, int]:
    if hasattr(draw, "textbbox"):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    return draw.textsize(text, font=font)


def _draw_legend(
    layer: Image.Image,
    target_string_number: int,
    target_lane_y: float,
) -> None:
    draw = ImageDraw.Draw(layer)
    font = ImageFont.load_default()
    lines = (
        (
            "X-ray diagnostic overlay (no collision geometry)",
            OVERLAY_COLORS["string"],
        ),
        ("Global allowed ribbon", OVERLAY_COLORS["allowed_outline"]),
        ("Global preferred ribbon", OVERLAY_COLORS["preferred_outline"]),
        ("Current lane outer", OVERLAY_COLORS["lane_outer_outline"]),
        ("Current lane core / center", OVERLAY_COLORS["lane_core_outline"]),
        (
            f"Active target: string {target_string_number}, "
            f"y_g={target_lane_y:+.4f} m",
            OVERLAY_COLORS["active_string"],
        ),
        (
            "RH:pick VIRTUAL POINT (no rigid geometry)",
            OVERLAY_COLORS["pick"],
        ),
    )
    padding = 9
    swatch = 15
    gap = 5
    line_height = max(
        _text_size(draw, text, font)[1] for text, _color in lines
    ) + gap
    text_width = max(
        _text_size(draw, text, font)[0] for text, _color in lines
    )
    box_width = padding * 3 + swatch + text_width
    box_height = padding * 2 + line_height * len(lines) - gap
    draw.rounded_rectangle(
        (12, 12, 12 + box_width, 12 + box_height),
        radius=7,
        fill=OVERLAY_COLORS["legend_background"],
        outline=(230, 235, 242, 150),
        width=1,
    )
    x = 12 + padding
    y = 12 + padding
    for text, color in lines:
        draw.rectangle(
            (x, y + 1, x + swatch, y + swatch - 1),
            fill=color,
            outline=(255, 255, 255, 180),
        )
        draw.text(
            (x + swatch + padding, y),
            text,
            font=font,
            fill=OVERLAY_COLORS["legend_text"],
        )
        y += line_height


def _serializable_overlay_state(
    geometry: Mapping[str, Any],
    pick_world: np.ndarray,
    trail_sample_count: int,
) -> dict[str, Any]:
    return {
        "schema": "tab2body.strike_visual_overlay.v1",
        "diagnostic_only": True,
        "adds_physics_geometry": False,
        "pick_representation": (
            "RH:pick virtual point rigidly attached to the hand; "
            "no rigid pick geometry"
        ),
        "string_representation": "six live fixed finite segments",
        "clipping_axis": "guitar_local_y_m",
        "visual_string_ribbon_half_width_m": float(
            geometry["ribbon_half_width_m"]
        ),
        "allowed_y_m": [float(value) for value in geometry["allowed_y"]],
        "preferred_y_m": [
            float(value) for value in geometry["preferred_y"]
        ],
        "target_lane_y_m": float(geometry["target_lane_y"]),
        "target_lane_outer_y_m": [
            float(value) for value in geometry["lane_outer_y"]
        ],
        "target_lane_core_y_m": [
            float(value) for value in geometry["lane_core_y"]
        ],
        "target_string_index": int(geometry["target_string"]),
        "target_string_number": int(geometry["target_string_number"]),
        "target_traversal_mask": list(geometry.get(
            "target_traversal_mask", [])),
        "completed_traversal_mask": list(geometry.get(
            "completed_traversal_mask", [])),
        "pick_world_m": [float(value) for value in pick_world],
        "pick_trail_sample_count": int(trail_sample_count),
        "colors_rgba": {
            key: [int(channel) for channel in value]
            for key, value in OVERLAY_COLORS.items()
        },
    }


def draw_strike_zone_pick_overlay(
    image_path: str | Path,
    env: Any,
    camera_spec: CameraSpec,
    *,
    pick_trail_world: Iterable[Any] = (),
) -> dict[str, Any]:
    """Overlay live strike ribbons and the virtual pick on one camera PNG.

    The input image is replaced atomically at the same path after all geometry
    validates.  The returned mapping contains only JSON-serializable values
    and explicitly records that the pick/ribbons are diagnostic, non-physical
    graphics.
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"camera image does not exist: {path}")
    spec = validate_camera_spec(camera_spec)
    geometry_g, guitar_position, guitar_quaternion, pick_path_world = (
        _environment_overlay_state(env, pick_trail_world)
    )
    geometry_world = _world_geometry(
        geometry_g, guitar_position, guitar_quaternion
    )

    with Image.open(path) as source:
        if source.size != (spec.width, spec.height):
            raise ValueError(
                "camera image dimensions do not match CameraSpec: "
                f"{source.size} != {(spec.width, spec.height)}"
            )
        base = source.convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")


    for layer_name, fill_name, outline_name in (
        ("allowed", "allowed", "allowed_outline"),
        ("preferred", "preferred", "preferred_outline"),
        ("lane_outer", "lane_outer", "lane_outer_outline"),
        ("lane_core", "lane_core", "lane_core_outline"),
    ):
        for string in geometry_world["strings"]:
            if (
                layer_name in ("lane_outer", "lane_core")
                and not string["active"]
            ):
                continue
            part = string[layer_name]
            if part is None:
                continue
            active = bool(string["active"])
            _draw_polygon(
                draw,
                part["polygon"],
                spec,
                fill=OVERLAY_COLORS[fill_name],
                outline=(
                    OVERLAY_COLORS["active_string"]
                    if active and layer_name in ("lane_outer", "lane_core")
                    else OVERLAY_COLORS[outline_name]
                ),
                width=3 if active else 1,
            )


    for string in geometry_world["strings"]:
        _draw_line(
            draw,
            string["segment"],
            spec,
            fill=(
                OVERLAY_COLORS["active_string"]
                if string["active"]
                else OVERLAY_COLORS["string"]
            ),
            width=4 if string["active"] else 2,
        )
        allowed = string["allowed"]
        if allowed is not None:
            label_pixels = _visible_pixels(
                allowed["centerline"][:1], spec)
            if label_pixels is not None:
                label_x, label_y = label_pixels[0]
                label = f"S{string['string_number']}"
                font = ImageFont.load_default()
                text_width, text_height = _text_size(draw, label, font)
                draw.rounded_rectangle(
                    (
                        label_x - text_width / 2 - 3,
                        label_y - text_height / 2 - 2,
                        label_x + text_width / 2 + 3,
                        label_y + text_height / 2 + 2,
                    ),
                    radius=3,
                    fill=OVERLAY_COLORS["legend_background"],
                    outline=(
                        OVERLAY_COLORS["active_string"]
                        if string["active"]
                        else OVERLAY_COLORS["string"]
                    ),
                    width=1,
                )
                draw.text(
                    (label_x, label_y),
                    label,
                    font=font,
                    anchor="mm",
                    fill=OVERLAY_COLORS["legend_text"],
                )
        if not string["active"]:
            continue
        center = string["lane_center"]
        if center is None:
            continue
        center_pixels = _visible_pixels(center[None], spec)
        if center_pixels is None:
            continue
        x, y = center_pixels[0]
        radius = 6 if string["active"] else 3
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=OVERLAY_COLORS["lane_center"],
            outline=(
                OVERLAY_COLORS["active_string"]
                if string["active"]
                else OVERLAY_COLORS["lane_core_outline"]
            ),
            width=2 if string["active"] else 1,
        )



    if len(pick_path_world) > 1:
        _draw_line(
            draw,
            pick_path_world,
            spec,
            fill=OVERLAY_COLORS["pick_trail"],
            width=3,
        )
    pick_pixels = _visible_pixels(pick_path_world[-1:], spec)
    if pick_pixels is not None:
        pick_x, pick_y = pick_pixels[0]
        radius = 8
        draw.ellipse(
            (
                pick_x - radius,
                pick_y - radius,
                pick_x + radius,
                pick_y + radius,
            ),
            fill=OVERLAY_COLORS["pick"],
            outline=OVERLAY_COLORS["pick_outline"],
            width=2,
        )
        label = "RH:pick virtual point"
        font = ImageFont.load_default()
        text_width, text_height = _text_size(draw, label, font)
        label_x = min(max(pick_x + 12, 4), spec.width - text_width - 8)
        label_y = min(max(pick_y - text_height - 9, 4), spec.height - text_height - 8)
        draw.rounded_rectangle(
            (
                label_x - 4,
                label_y - 3,
                label_x + text_width + 4,
                label_y + text_height + 3,
            ),
            radius=3,
            fill=OVERLAY_COLORS["legend_background"],
        )
        draw.text(
            (label_x, label_y),
            label,
            font=font,
            fill=OVERLAY_COLORS["pick_outline"],
        )

    _draw_legend(
        layer,
        geometry_g["target_string_number"],
        geometry_g["target_lane_y"],
    )
    composited = Image.alpha_composite(base, layer).convert("RGB")
    temporary = path.with_name(path.name + ".overlay.tmp")
    try:
        composited.save(temporary, format="PNG")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return _serializable_overlay_state(
        geometry_g,
        pick_path_world[-1],
        max(len(pick_path_world) - 1, 0),
    )


__all__ = [
    "CameraSpec",
    "N_GUITAR_STRINGS",
    "OVERLAY_COLORS",
    "VISUAL_STRING_RIBBON_HALF_WIDTH_M",
    "build_strike_overlay_geometry",
    "camera_basis",
    "clip_segment_to_y_interval",
    "draw_strike_zone_pick_overlay",
    "guitar_local_to_world",
    "point_on_segment_at_y",
    "project_world_points",
    "quaternion_xyzw_rotation",
    "ribbon_polygon",
    "validate_camera_spec",
]
