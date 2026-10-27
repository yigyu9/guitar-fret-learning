"""Read-only preparation preflight for initial-pose qualification artifacts.

This intentionally does not copy media, render figures, create final docs, or
write a copy manifest. Those steps require the root's final brief and all five
closed condition reports.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1')
CLOSED = {
    'baseline': ('analysis_baseline_v1.json', 'visual_baseline_v1/report.json'),
    'static': ('analysis_static_v1.json', 'visual_static_v1/report.json'),
    'strike': ('analysis_strike_v1.json', 'visual_strike_v1/report.json'),
}
PENDING = {
    'left_cycle': ('native_left_cycle_v2', 'visual_left_cycle_v1'),
    'z_plus3mm': ('native_z_plus3mm_v2', 'visual_z_plus3mm_v1'),
}
VIDEO_KEYS = ('front', 'right_side', 'top', 'combined')

def main() -> None:
    results = {}
    for name, (analysis_rel, visual_rel) in CLOSED.items():
        analysis_path = ROOT / analysis_rel
        visual_path = ROOT / visual_rel
        analysis = json.loads(analysis_path.read_text())
        visual = json.loads(visual_path.read_text())
        snapshot_paths = [Path(x['path']) for x in visual.get('snapshots', [])]
        results[name] = {
            'analysis_exists': analysis_path.is_file(),
            'visual_report_exists': visual_path.is_file(),
            'visual_inputs_unchanged': visual.get('inputs_unchanged'),
            'videos_present': sorted(visual.get('videos', {}).keys()),
            'snapshot_count': len(snapshot_paths),
            'snapshot_files_present': all(p.is_file() for p in snapshot_paths),
        }
        if not (results[name]['analysis_exists'] and results[name]['visual_report_exists']
                and results[name]['snapshot_files_present']
                and all(k in visual.get('videos', {}) for k in VIDEO_KEYS)):
            raise SystemExit(f'closed-condition preflight failed: {name}')
    print(json.dumps({'mode': 'read_only_preparation_only', 'closed_conditions': results,
                      'pending_conditions': PENDING,
                      'final_production_enabled': False}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
