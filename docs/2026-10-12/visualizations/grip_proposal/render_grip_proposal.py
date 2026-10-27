"""Inspect proposed grip regions in the shared Isaac Gym initial scene.

This is a static geometry preview, not the new free-guitar/strap environment.
Overlays are projected from real asset coordinates; they do not add contacts.
"""
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

import isaacgym  # noqa: F401 - before torch
from isaacgym import gymapi
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tab2body.env.base import GuitarEnvBase
from tab2body.tools.fretboard_visualization import CameraSpec, _project

OUT = Path(__file__).resolve().parent
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
COLORS = {"center": (255, 215, 45), "front": (60, 210, 115),
          "thumb": (255, 120, 185), "palm": (60, 190, 255)}


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def neck_slice(y):
    """Slice the referenced neck triangles, ignoring unused OBJ vertices."""
    vertices, faces = [], []
    for line in (ROOT / "tab2body/assets/mesh/guitar_neck1.obj").read_text().splitlines():
        if line.startswith("v "):
            vertices.append([float(value) for value in line.split()[1:]])
        elif line.startswith("f "):
            faces.append([int(value.split("/")[0]) - 1 for value in line.split()[1:]])
    vertices = np.asarray(vertices)
    points = []
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            start, end = vertices[a], vertices[b]
            if abs(end[1] - start[1]) > 1e-10:
                t = (y - start[1]) / (end[1] - start[1])
                if 0 <= t <= 1:
                    points.append(start + t * (end - start))
    return np.min(points, axis=0), np.max(points, axis=0)


def world(env, local):
    import torch
    from tab2body.env.base import quat_rotate
    gp, gq = env.guitar_frame()
    local = torch.as_tensor(np.asarray(local), dtype=gp.dtype, device=gp.device)
    return (quat_rotate(gq.expand(len(local), -1), local) + gp[0]).cpu().numpy()


def patch(y0, y1, face, side):
    low0, high0 = neck_slice(y0)
    low1, high1 = neck_slice(y1)
    if face in ("front", "thumb"):
        z0, z1 = (high0[2], high1[2]) if face == "front" else (low0[2], low1[2])
        return [[low0[0], y0, z0], [high0[0], y0, z0],
                [high1[0], y1, z1], [low1[0], y1, z1]]
    x0 = high0[0] if side > 0 else low0[0]
    x1 = high1[0] if side > 0 else low1[0]
    return [[x0, y0, low0[2]], [x0, y0, high0[2]],
            [x1, y1, high1[2]], [x1, y1, low1[2]]]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = GuitarEnvBase(num_envs=1, control_dofs=("LH:",),
                        device="cuda:0", headless=True, reset_noise=0)
    try:
        env.reset()
        env.refresh()
        # reset body tensors become valid only after a physics step.
        env.step_physics()
        env.refresh()
        root = ET.parse(ROOT / "tab2body/assets/guitar_asset.xml").getroot()
        nut_y = float(root.find(".//body[@name='G:nut']").get("pos").split()[1])
        # Proximal end of the face-referenced neck mesh, not the headstock.
        proximal_y = -0.241803
        center_y = proximal_y + (nut_y - proximal_y) * 2 / 3
        low, high = neck_slice(center_y)
        center = (low + high) / 2
        axes_w = world(env, np.eye(3)) - world(env, [[0, 0, 0]])
        side = 1 if axes_w[0, 2] < 0 else -1
        palm = center.copy()
        palm[0] = high[0] if side > 0 else low[0]
        approach = palm + np.array([side * .02, 0, 0])
        regions = {name: patch(center_y - .025, center_y + .025, name, side)
                   for name in ("front", "thumb", "palm")}
        markers = {"center": center, "palm": palm}
        gp = world(env, [[0, 0, 0]])[0]
        cameras = []
        for slug, title, direction, distance in (
            ("overview", "초기 배치와 넥의 2/3 지점", (0.1, 1.0, 0.35), 2.0),
            ("front", "정면 · 손가락 접촉 영역", (side * .9, -.35, 1.5), .38),
            ("back", "뒤쪽 · 엄지 접촉 영역", (side * .9, -.35, -1.5), .38),
        ):
            target = (gp + np.array([0, 0, -.10])) if slug == "overview" else world(env, [center])[0]
            direction = np.asarray(direction, dtype=float)
            if slug != "overview":
                direction = direction @ axes_w
            direction /= np.linalg.norm(direction)
            spec = CameraSpec(tuple(target + distance * direction), tuple(target), 1400, 1000, 45)
            cp = gymapi.CameraProperties()
            cp.width, cp.height, cp.horizontal_fov = spec.width, spec.height, spec.horizontal_fov_deg
            camera = env.gym.create_camera_sensor(env.envs[0], cp)
            env.gym.set_camera_location(camera, env.envs[0], gymapi.Vec3(*spec.eye), gymapi.Vec3(*spec.target))
            cameras.append((slug, title, camera, spec))
        env.gym.step_graphics(env.sim)
        env.gym.render_all_camera_sensors(env.sim)
        paths = []
        for slug, title, camera, spec in cameras:
            path = OUT / f"{slug}.png"
            env.gym.write_camera_image_to_file(env.sim, env.envs[0], camera, gymapi.IMAGE_COLOR, str(path))
            image = Image.open(path).convert("RGBA")
            layer = Image.new("RGBA", image.size)
            draw = ImageDraw.Draw(layer)
            for name, polygon in regions.items():
                if (slug == "front" and name == "thumb") or (slug == "back" and name == "front"):
                    continue
                pixels, depths = _project(world(env, polygon), spec)
                if np.all(depths > 0):
                    draw.polygon([tuple(point) for point in pixels], fill=(*COLORS[name], 90))
                    draw.line([tuple(point) for point in pixels] + [tuple(pixels[0])], fill=(*COLORS[name], 255), width=5)
            if slug == "overview":
                axis = [[0, proximal_y, high[2] + .004],
                        [0, nut_y, high[2] + .004]]
                axis_pixels, _ = _project(world(env, axis), spec)
                draw.line([tuple(point) for point in axis_pixels], fill=(255, 230, 130, 255), width=4)
            pixels, _ = _project(world(env, [approach, palm]), spec)
            draw.line([tuple(point) for point in pixels], fill=(*COLORS["palm"], 255), width=7)
            for name, point in markers.items():
                pixel = _project(world(env, [point]), spec)[0][0]
                x, y = pixel
                draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(*COLORS[name], 255))
            draw.rectangle((0, 0, 1400, 112), fill=(15, 18, 25, 235))
            draw.text((24, 10), title, font=font(32), fill="white")
            draw.text((24, 58), "정지 장면 / 색 영역은 제안 표시 (가려진 면도 표시)", font=font(23), fill="white")
            Image.alpha_composite(image, layer).convert("RGB").save(path)
            paths.append(path)

        sheet = Image.new("RGB", (1600, 1320), (20, 24, 32))
        for i, path in enumerate(paths):
            sheet.paste(Image.open(path).resize((800, 571)), ((i % 2) * 800, (i // 2) * 571))
        draw = ImageDraw.Draw(sheet)
        draw.text((825, 595), "같은 그립 지점의 단면 개념도", font=font(28), fill="white")
        draw.text((825, 638), "길이축을 따라 바라본 넥 · 실제 폭/두께 비율", font=font(20), fill="white")
        cx, cy, scale = 1200, 840, 5500
        x0, x1 = cx + low[0] * scale, cx + high[0] * scale
        z0, z1 = cy - high[2] * scale, cy - low[2] * scale
        draw.rectangle((x0, z0, x1, z1), fill=(135, 103, 75), outline="white", width=3)
        draw.line((x0, z0, x1, z0), fill=COLORS["front"], width=8)
        draw.line((x0, z1, x1, z1), fill=COLORS["thumb"], width=8)
        xp = x1 if side > 0 else x0
        draw.line((xp, z0, xp, z1), fill=COLORS["palm"], width=8)
        draw.text((1015, 716), "초록: 지판 쪽 — 손가락", font=font(25), fill=COLORS["front"])
        draw.text((1015, 905), "분홍: 넥 뒤쪽 — 엄지", font=font(25), fill=COLORS["thumb"])
        draw.text((825, 974), "파랑: 아래쪽 측면 — 손바닥", font=font(25), fill=COLORS["palm"])
        draw.text((825, 1020), "아래쪽 = 초기 자세에서 아래를 향하는 ±X 면", font=font(20), fill="white")
        draw.text((30, 1160), "노랑: 넥–바디 연결부 → 너트 구간의 2/3 중심", font=font(28), fill=COLORS["center"])
        draw.text((30, 1210), "표시 영역: 중심 ±2.5 cm / 접근 간격 2 cm — 이해를 위한 예시, 미확정", font=font(24), fill="white")
        draw.text((30, 1255), "자유 기타·스트랩·손바닥 표면 기준점·실제 접촉/그립 성공은 아직 검증하지 않음", font=font(22), fill="white")
        sheet.save(OUT / "grip_proposal_multiview.png")
        metadata = {"scene": "shared initial pose, static geometry inspection; no strap",
                    "proximal_y_m": proximal_y, "nut_y_m": nut_y,
                    "grip_center_G_m": center.tolist(), "lower_side_sign_x": side,
                    "section_min_G_m": low.tolist(), "section_max_G_m": high.tolist(),
                    "illustrative_region_half_length_m": .025,
                    "illustrative_approach_gap_m": .02,
                    "regions_G_m": regions, "guitar_origin_W_m": gp.tolist()}
        (OUT / "geometry.json").write_text(json.dumps(metadata, indent=2))
        print(json.dumps(metadata, indent=2))
        print(OUT / "grip_proposal_multiview.png")
    finally:
        env.gym.destroy_sim(env.sim)


if __name__ == "__main__":
    main()
