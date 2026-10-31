"""Exact recorded body poses on MuJoCo source geometry, without physics."""
import argparse
import json
import subprocess
from pathlib import Path
from .replay_v6 import selected_rows, frame_indices, original_expected_inputs, sha, save
from .static_visual_v7 import asset_paths, build_model, set_body_poses, add_strings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--free-run', type=Path, required=True)
    parser.add_argument('--regrasp-run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--cpu-check', action='store_true')
    args = parser.parse_args()
    import mujoco
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    # This module never creates an Isaac Gym environment or invokes MuJoCo dynamics.
    def forbidden_step(*args, **kwargs):
        raise RuntimeError('Static saved-body visualization forbids mj_step')
    mujoco.mj_step = forbidden_step
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    runs = [args.free_run.resolve(), args.regrasp_run.resolve()]
    initial_paths = [run / 'initial_values.json' for run in runs]
    initial = [json.loads(path.read_text()) for path in initial_paths]
    sources = {Path(__file__).resolve(), Path(__file__).with_name('static_visual_v7.py'), Path(__file__).with_name('replay_v6.py')}
    font_path = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    root = Path(__file__).resolve().parents[2]
    sources.update((font_path, root / 'paper/initial_pose/current_v3/presentation_60fps_v1/BRIEF_v3.md'))
    for run in runs:
        sources.update(run / name for name in ('initial_values.json', 'states240.json', 'attempt.json', 'support_wrapper.json'))
    assets = set()
    for value in initial:
        for asset in value['loaded_assets']:
            assets.update(asset_paths(Path(asset['path'])))
    sources.update(assets)
    pins = {str(path): sha(path) for path in sorted(sources)}
    save(out / 'inputs_before.json', pins)
    parity = []
    for run, value in zip(runs, initial):
        expected = original_expected_inputs(run)
        for asset in assets:
            if expected.get(str(asset.resolve())) != sha(asset):
                raise RuntimeError('Original asset expected SHA mismatch: ' + str(asset))
        assert value['human_body_names'] == initial[0]['human_body_names'] and value['guitar_body_names'] == initial[0]['guitar_body_names']
        assert value['loaded_assets'] == initial[0]['loaded_assets'] and value['chair_initial_placement'] == initial[0]['chair_initial_placement']
        parity.append({'run': str(run), 'all_model_XML_and_declared_mesh_SHA_exact': True, 'asset_count': len(assets)})
    save(out / 'original_asset_parity.json', parity)
    model, data, mapping, xml = build_model(initial[0])
    (out / 'flattened_source_scene.xml').write_text(xml)
    presentation = {'renderer': 'MuJoCo source geometry', 'scope': 'Recorded world body poses, normalized quaternions, no joint FK and no integration; not Isaac Gym cooked rendering or physics replay', 'source_visual_selection': 'Per source body: visible alpha>0 geoms only; explicit group=1 visual meshes preferred over duplicate collision geoms when present; original geom local position/orientation/size/mesh retained. Invisible support proxies omitted. Gray human/guitar, green LH, pink RH. Source visual meshes differ from native PhysX cooked geometry.', 'body_mapping': [{'actor': actor, 'saved_body_index': index, 'MuJoCo_body_id': body_id, 'name': name} for actor, index, body_id, name in mapping], 'fps': 60, 'source_hz': 240, 'stride': 4, 'physics_steps': 0, 'camera': {'position_m': [0, 3.1, .8], 'target_m': [0, 0, .72], 'horizontal_fov_deg': 55, 'width': 1280, 'height': 720, 'x_axis_W': [-1, 0, 0], 'y_axis_W': [0, -.08 / (3.1 ** 2 + .08 ** 2) ** .5, 3.1 / (3.1 ** 2 + .08 ** 2) ** .5], 'z_axis_W': [0, 3.1 / (3.1 ** 2 + .08 ** 2) ** .5, .08 / (3.1 ** 2 + .08 ** 2) ** .5]}, 'strings': 'six depth-tested 3D capsules following saved endpoint body world positions'}
    save(out / 'attempt.json', presentation)
    font, small = ImageFont.truetype(str(font_path), 21), ImageFont.truetype(str(font_path), 17)
    renderer = encoder = None
    records = []
    try:
        if not args.cpu_check:
            renderer = mujoco.Renderer(model, height=720, width=1280)
        if not args.preview and not args.cpu_check:
            encoder = subprocess.Popen(['ffmpeg', '-nostdin', '-n', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '60', '-i', '-', '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', str(out / 'front_full_body_60fps.mp4')], stdin=subprocess.PIPE)
        segments = [(0, 17, 18), (0, 29, 30), (1, 44, 45)] if args.preview or args.cpu_check else [(0, 17, 40), (1, 40, 49)]
        indices = [(initial[0]['guitar_body_names'].index('G:string%d' % i), initial[0]['guitar_body_names'].index('G:string%d_end' % i)) for i in range(1, 7)]
        for segment_number, (run_index, start, end) in enumerate(segments):
            if encoder and segment_number == 1:
                card = Image.new('RGB', (1280, 720), (20, 25, 32))
                draw = ImageDraw.Draw(card)
                draw.text((405, 300), '별도 시험으로 전환', font=font, fill='white')
                draw.text((350, 340), '왼손 넥 재접촉 및 준비 복귀', font=font, fill='white')
                for _ in range(60):
                    encoder.stdin.write(card.tobytes())
            for row in selected_rows(runs[run_index] / 'states240.json', start, end, args.preview or args.cpu_check):
                errors = set_body_poses(model, data, mapping, row['state'])
                before = (data.xpos.copy(), data.xquat.copy(), float(data.time))
                if renderer:
                    renderer.update_scene(data, camera='front')
                    endpoints = np.array([[[row['state']['guitar_body_states'][i]['pose']['p'][axis] for axis in 'xyz'] for i in pair] for pair in indices])
                    add_strings(renderer.scene, endpoints)
                    image = Image.fromarray(renderer.render())
                    draw = ImageDraw.Draw(image)
                    draw.rectangle((0, 0, 1280, 58), fill=(18, 23, 29))
                    caption = '[시험 1] 왼손 해제 · 오른손 타현' if run_index == 0 else '[시험 2] 넥 재접촉 · 준비 복귀'
                    draw.text((18, 2), '%s | 기록 시각 %.3f초 | 60fps' % (caption, row['time_s']), font=font, fill='white')
                    draw.text((18, 31), '저장된 몸체 자세 재생 · 두 개별 시험 편집', font=small, fill=(205, 215, 225))
                    if args.preview:
                        image.save(out / ('preview_%s_%05d.png' % (runs[run_index].name, row['physics_step'])))
                    else:
                        encoder.stdin.write(image.tobytes())
                assert np.array_equal(before[0], data.xpos) and np.array_equal(before[1], data.xquat) and before[2] == data.time == 0
                records.append(dict(frame_indices(len(records), segment_number, args.preview or args.cpu_check), run=str(runs[run_index]), time_s=row['time_s'], physics_step=row['physics_step'], transform_readback=errors, rendering_preserves_transforms=True))
                if len(records) % 60 == 0:
                    print('rendered', len(records), 'saved-body frames', flush=True)
        if encoder:
            encoder.stdin.close()
            if encoder.wait() != 0:
                raise RuntimeError('ffmpeg encoding failed')
        assert all(sha(path) == digest for path, digest in pins.items())
        save(out / 'replay_report.json', dict(presentation, not_Isaac_Gym_cooked_rendering=True, new_physics_steps=0, clock_s=float(data.time), inputs_unchanged=True, measured_frames=len(records), transition_card_frames=60 if encoder else 0, frames=records))
    finally:
        if encoder and encoder.poll() is None:
            encoder.kill()
            encoder.wait()
        if renderer:
            renderer.close()


if __name__ == '__main__':
    main()
