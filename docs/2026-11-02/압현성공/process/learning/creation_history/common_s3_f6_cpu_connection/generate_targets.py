"""실제 학습기에 넣을 단일 손가락 합성 목표 네 개를 생성·검증한다.

무음 WAV는 에피소드 시간축만 제공하며 음향 추론이나 연주 성과를 뜻하지 않는다.
목적 번들이 이미 있으면 덮어쓰지 않고 내용·해시·현재 학습기 계약만 검사한다.
"""
import hashlib
import json
from pathlib import Path
import sys
import wave


ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / 'guitar_learning/train.py').is_file())
sys.path.insert(0, str(ROOT))

from guitar_learning.tool import (build_fret_training_data,
                                 build_strike_training_data,
                                 build_strike_plan, register_song_bundle)
from guitar_learning.song.task import make_task, load_anchor_track
from guitar_learning.training.launch import build_settings


OUT = Path(__file__).resolve().parents[1]
FINGERS = ('index', 'middle', 'ring', 'pinky')
PURPOSE = 'synthetic_virtual_single_finger_press_diagnostic'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def fingerprint(path):
    return dict(bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def generate(bundle, finger):
    """줄 변환은 기존 builder에 맡기고 원본은 0=low-E 관례로 기록한다."""
    bundle.mkdir(parents=True)
    source_string = 5 - (3 - 1)
    anchor = max(1, min(22, 6 - finger + 1))
    note = dict(t_on=0., t_off=2.5, string=source_string, fret=6,
                midi=55 + 6, finger=finger, barre=False, grip=None)
    mapping = dict(
        purpose=PURPOSE,
        convention='string 0 = low-E; generated virtual diagnostic, not a recorded song',
        notes=[note], presses=[dict(finger=finger, string=source_string,
            fret=6, barre=False, t_press=0., t_release=2.5, strikes=[0.])],
        hand=[dict(t=0., P=anchor, grip=None)],
        stats=dict(dropped_invalid_fret=0), diagnostics=[], violations=[])
    mapping_path = bundle / 'mapping/fingering.json'
    write_json(mapping_path, mapping)
    register_song_bundle.write_tablature_if_missing(bundle)
    audio = bundle / 'source/audio.wav'
    audio.parent.mkdir(parents=True)
    with wave.open(str(audio), 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b'\0\0' * 40000)
    training = bundle / 'training'
    training.mkdir()
    build_fret_training_data.main(['--fingering', str(mapping_path),
        '--audio', str(audio), '--out', str(training / 'fret_training.json')])
    raw = training / 'strike_training.json'
    build_strike_training_data.main([str(mapping_path), '--out', str(raw)])
    build_strike_plan.main([str(raw), '--out', str(training / 'strike_plan.json')])
    register_song_bundle.write_manifest(bundle.name, bundle, dict(
        registration_mode=PURPOSE,
        generated_by=str(Path(__file__).resolve().relative_to(ROOT)),
        generator_sha256=fingerprint(Path(__file__))['sha256'],
        audio='2.5 seconds of digital silence; clock only, no acoustic inference',
        source='explicit virtual target; not transcription or recorded-performance data'))


def validate(bundle, finger):
    """학습기와 동일한 score/설정 생성 경로로 단일 목표·시간·해시를 검사한다."""
    manifest = json.loads((bundle / 'manifest.json').read_text())
    assert manifest['provenance']['registration_mode'] == PURPOSE
    actual_paths = {str(p.relative_to(bundle)) for p in bundle.rglob('*')
                    if p.is_file() and p.name != 'manifest.json'}
    assert actual_paths == set(manifest['files'])
    for relative, expected in manifest['files'].items():
        assert fingerprint(bundle / relative) == expected, relative
    with wave.open(str(bundle / 'source/audio.wav'), 'rb') as stream:
        assert stream.getnframes() / stream.getframerate() == 2.5
        assert not any(stream.readframes(stream.getnframes()))
    task = make_task(bundle)
    assert len(task.targets) == 1
    target = task.targets[0]
    assert (target.string, target.fret, target.finger) == (2, 6, finger)
    assert (target.onset_s, target.end_s, task.duration_s) == (3., 5.5, 6.)
    mapping = json.loads((bundle / 'mapping/fingering.json').read_text())
    assert mapping['purpose'] == PURPOSE
    assert mapping['hand'][0]['P'] == 7 - finger
    load_anchor_track(bundle)
    settings = build_settings('left', song=bundle.name, updates=100,
        num_envs=64, horizon=32, size='large', learning_family='finger-skill',
        device='cuda:0', physics='gpu')
    assert settings['song']['left_fraction'] == .4
    assert settings['song_training']['target_count'] == 1
    assert settings['song_training']['control_ticks'] == 360
    return dict(song_id=bundle.name, finger=finger,
        physical_string_1based=3, runtime_string_0based=2, source_string_0based=3,
        fret=6, hand_anchor=7-finger, source_note_s=[0., 2.5],
        policy_note_s=[3., 5.5], episode_s=6., control_ticks=360,
        continuous_achievement_required_s=1., left_fraction=.4,
        manifest=fingerprint(bundle / 'manifest.json'), files=manifest['files'])


def main():
    rows = []
    for finger, name in enumerate(FINGERS, 1):
        bundle = ROOT / 'data/song_bundles' / ('virtual_finger_v9_' + name + '_s3_f6')
        if not bundle.exists():
            generate(bundle, finger)
        rows.append(validate(bundle, finger))
    write_json(OUT / 'targets.json', dict(
        purpose=PURPOSE, validation='make_task/build_settings/manifest/WAV passed',
        audio_scope='silent clock only; no acoustic success claim',
        hand_anchor_assumption='existing fingering convention: clamp(fret-finger+1,1,22); unchanged builder wrist span',
        initial_pose='production left_standby_v9; selected by the actual learning environment',
        generator=fingerprint(Path(__file__)), targets=rows))
    print(json.dumps(dict(validated=len(rows), targets=str(OUT / 'targets.json'))))


if __name__ == '__main__':
    main()
