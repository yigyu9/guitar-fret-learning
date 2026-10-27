# 두 checkpoint 연결 및 첫 source terminal 기록

기타 초기값은 현재 shoulder-forward 10 mm 조건과 같게 유지했고, Fret 035000 및 Strike 010000 frozen baseline을 실제 연결했습니다. 이 결과는 초기 연결/전환 smoke test이며 곡 완주가 아닙니다.

![native2 실제 native 전신과 손 0.00초, 2.00초, 2.05초 frame](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/native_v2_whole_and_hands_0_2_2p05.png)

각 패널은 capture.json의 physics step 0/480/492에 해당하는 실제 native renderer frame입니다. 2.05초 terminal frame을 포함하지만, video encode 길이는 2.1초(63 frames×30fps)이며 정지 프레임 연장으로 물리 시간을 늘리지 않았습니다. 손 카메라의 줄은 물리 상호작용 없는 화면 표시입니다.

## Checkpoint와 연결 검증

| Actor | Frozen checkpoint | SHA-256 |
|---|---|---|
| Fret | `/home/ajou/yigyu/3/fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt` | `a6f0c303f69686eb02ebed5f7dce743fdc223fd89c8a8fb2b40303d0abeab5ca` |
| Strike | `/home/ajou/yigyu/3/strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt` | `9244b33c87426afb28c10a1176b88f23832a50a57605586d4e28084a48160e87` |

Connection verification v3 reports actor-action replay errors 0, frozen weights, baseline initial/PD/mass exact, the first 2.0 s of q/root position exact, normalized physical orientation difference 0, and right effort commands exact for 480 preparation ticks. This confirms the state/connection checks only.

## Terminal result and guitar state

Native1 stopped before physics (0 steps) because the camera key `OM_appearance` was missing. It is preserved as setup failure and has no movie. Native2 ran 492 physics steps/123 control ticks: 2.0 s PREP (120 ticks), then only 0.05 s PLAY (3 paired inference ticks) before the first Fret source terminal. Fret wrist-safety and finger-back termination were true; Fret `goal_finished` was false. Strike `done` and `goal_finished` were false, physical target hit false. No music completion, press, joint-resolved event or joint crossing was observed. Therefore this test does not establish any completed musical performance or a failure rate for the whole song.

At terminal, the left wrist source-local G position was `[0.128451675, -0.093393892, -0.568670034] m`; source wrist safety and finger-back termination were true, with finger-back minimum local z values about −0.470 to −0.462 m. The final hand view shows its guitar-relative placement at the terminal. These are the recorded source detector coordinates/results, not a claim of a native guitar physical press.

The guitar body bounding-box center changed 9.617284 mm and total SO(3) orientation 2.983343° at the terminal; run maxima were 10.455249 mm and 3.343712°. The observed 2.00→2.05 s changes were 0.037970 mm and 0.012452°. These endpoint values are descriptive and not attributed causally to the actor connection. Upper-arm contact presence was 458/492; left hand, head and distal-arm contact were 0.

Strap OFF, free guitar, root/lower fixed, no direct guitar force, training updates 0. The stopped PLAY window is too short to judge Fret/Strike performance. The planned next step is a guitar-relative left-hand READY/wrist/finger-safe transition during PREP while preserving existing safety and source handoff behavior.

The corrected analysis authority is [connection_verification_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/connection_verification_v3.json). Earlier analyzer v1 quaternion-representation check and v2 raw-OBJ bounding-box coordinate issue are documented, not used as this conclusion. V3 uses the XML body offset; the guitar body bounding-box center in G is `[0, −0.4, −0.055937985] m`. [Analysis notes](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/ANALYSIS_NOTES_V1.md) · [native1 setup failure report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/native_v1/report.json) · [native2 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/native_v2/report.json) · [video index](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/INDEX_V1.md) · [SHA/ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/manifest_v1.json)
