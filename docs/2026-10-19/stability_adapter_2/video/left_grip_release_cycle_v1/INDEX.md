# Left grip/release cycle videos

V2 is the recommended repeat: same initial state and exact full guitar root/quaternion trace as V1, with corrected V2 evidence classification. Each video is an unmodified native Isaac Gym capture, 30 fps, 481 frames (16.033 s encoded duration for the 16 s simulation).

## V2 · recommended

### Whole body

![V2 native whole body, full 16 s cycle](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/whole_body.mp4)

### Hands

![V2 native hands, full 16 s cycle](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/hands.mp4)

### Thumb back

![V2 native thumb-back view, full 16 s cycle](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/thumb_back.mp4)

## V1 · original run

V1 is retained as captured. Its pre-run config-hash gap and raw LHip contact classification/evidence-scope issue are historical limitations; the V2 correction is not a retroactive certification of V1.

### Whole body

![V1 native whole body, full 16 s cycle](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v1/whole_body.mp4)

### Hands

![V1 native hands, full 16 s cycle](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v1/hands.mp4)

### Thumb back

![V1 native thumb-back view, full 16 s cycle](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v1/thumb_back.mp4)

## Timeline

| Simulation time | Observed stage |
|---|---|
| 0–2 s | Prepare |
| 2–3 s | Close on A |
| 3–4.5 s | Hold A; thumb plus another finger positive contact in all 360 samples |
| 4.5–6 s | Release transition A |
| 6–7 s | Open A; no left-hand/guitar contact in all 240 samples |
| 7–8.5 s | Move to B with left hand open; no left-hand/guitar contact in all 360 samples |
| 8.5–10 s | Close on B |
| 10–11.5 s | Hold B; thumb plus another finger positive contact in all 360 samples |
| 11.5–13 s | Release transition B |
| 13–16 s | Open B; no left-hand/guitar contact in all 720 samples |

The measured mean wrist displacement from A to B projected on the current guitar neck axis was 36.727 mm against a requested 40 mm. The result includes finite right upper-arm and right-hip support contacts, so it does not establish unsupported/passive equilibrium or force closure. See [the evidence summary](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/README.md) and [V2 copy hash manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/copy_manifest_v2.json).
