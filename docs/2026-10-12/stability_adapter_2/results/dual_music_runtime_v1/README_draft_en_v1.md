# Dual music runtime diagnostic

## Scope and execution accounting

This phase connected the frozen Fret and Strike actors in one native scene after selecting a static preload diagnostic. It measures runtime wiring and early behavior; it does not implement the final policy ABI, certify performance, or train an agent.

| Entry | Condition | New physics steps | Result |
|---|---|---:|---|
| `run_dual_music_v2` | preload 0.5 | 1200 | 5 s diagnostic |
| `run_dual_music_v2` | preload 1.0 | 1200 | 5 s diagnostic; selected for pair trial |
| `run_dual_music_v3` | pair 1.0 | 0 | Preserved import failure: Ninja unavailable in active `PATH` before scene creation |
| `run_dual_music_v4` | pair 1.0 | 924 | 2 s preparation then 1.85 s PLAY; stopped on first source terminal |

The count is three new native runs and 3324 physics steps. The saved neutral baseline was reused and is not a new run. A separate old-schema analyzer attempt failed before physics (`KeyError human_body_names`); the v2 analyzer corrected that schema issue. Both failed attempts are preserved in [early_attempts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/early_attempts.json). No learning updates occurred.

## Static preload comparison and selected initial state

All three preload comparisons use the same captured initial physical state. The guitar remains free, the humanoid root and lower body are fixed, self-collision is enabled, and the strap is off. The selected factor changes a bounded static target correction for the initial pose: arm channels are bounded to ±0.15 rad, finger channels to ±0.05 rad, and body/head corrections are zero. PD gains and rate bounds stay the same. The recorded initial physical joint state and guitar pose are reused exactly; the median actual error only describes the static preload target construction.

| Initial condition | Max guitar displacement (mm) | Final displacement (mm) | Max geodesic rotation (°) | Final rotation (°) | Core position-box max outside (mm) | Outside samples |
|---|---:|---:|---:|---:|---:|---:|
| Neutral, factor 0 | 111.790 | 111.787 | 19.486 | 19.485 | 34.335 | 288/301 |
| Preload 0.5 | 75.331 | 75.330 | 13.910 | 12.294 | 11.262 | 273/301 |
| **Preload 1.0 · selected** | **46.306** | **46.298** | **9.179** | **7.626** | **0.000** | **0/301** |

Factor 1.0 was selected because its maximum core actor-root position-box excess was zero, while its maximum initial guitar displacement and rotation were also lower than the neutral reference. This diagnostic selection does not establish full SO(3) allowed-region membership, contact support, successful music events, or stability; `stability_success` and `training_ready` both remain false.

### Preload images

![세 조건의 native whole-body 초기 상태 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_comparison_v2.png)

![60 Hz trace의 기타 위치 변위와 회전 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_curves_v2.png)

The montage uses saved native camera frames. The curve panel reports guitar position displacement from the initial actor position and shortest-path geodesic rotation change; its core position-box statistic does not check rotation-region membership. Details and input provenance are in [preload artifact note v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_artifact_note_v2.md).

## Frozen actor pair and runtime result

The pair run used Fret checkpoint `fret_035000.pt` and Strike checkpoint `strike_010000.pt`, both for Jazz bundle 42 on the canonical 60 Hz score clock. One physical owner submitted an 81-joint target once per control interval, followed by four physics steps. After 2.0 s of preparation, the two frozen actors produced 111 simultaneous ticks. The connected actors each provided 30 action channels; the other 21 joint targets held the selected preload. The logged 1299-element observation is a candidate diagnostic record, not the final Actor ABI. The planned 81-joint observation and 512→256 policy are not implemented or trained in this work unit.

| Pair measurement | Recorded result |
|---|---:|
| Pair physics / control steps | 924 / 231 |
| Preparation / PLAY | 2.00 s / 1.85 s |
| Simultaneous frozen-actor ticks | 111 |
| Maximum guitar displacement from initial | 403.605 mm |
| Maximum guitar rotation from initial | 63.992° |
| Core position-box maximum outside norm | 261.953 mm |
| Resolved joint events / successes | 4 / 0 |
| Joint crossings | 1, reason `wrong_string` |
| Strike source per-control target hits / misses | 0 / 4 |

The first terminal was Fret's native guitar-local wrist-X safety boundary at `0.3488265 m` (logged value `0.34882652759552 m`) after 3.85 physical seconds, or 1.85 s of PLAY. This is a position safety bound, not a wrist-angle limit. Fret ended; Strike was not done, and the song did not complete. The earlier static preload improvement did not persist through this frozen-source PLAY segment.

The music-event check was a geometric fret press at 240 Hz using the highest fret, a diagnostic 240 Hz pickup-zone sample, an 8-physics-frame rearm, a 0.1 s dwell, and a conservative endpoint bracket. It is not subframe pressure measurement, physical contact proof, or a certified detector. The source Strike per-control results were four misses and zero target hits; the joint diagnostic recorded one wrong-string crossing and no successes. These are different measurements and are reported separately.

Fret source history reconstruction had maximum error `0.66246 rad` (`0.63746 rad` during PLAY) with 146 clipped control samples; Strike's was `8.94e-8 rad` with no clipped samples. The inherited source ABI copies native COM linear velocity while the physical adapter converts that velocity to body-origin coordinates. Fret's clipped reconstruction and Strike's near-zero reconstruction therefore do not establish source-ABI equivalence.

### Pair native-frame montage

![Pair run native whole-body and hands views at start, 2 seconds, and final physical time 3.85 seconds](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_montage_v2.png)

The six panels use the actual pair-run Isaac Gym camera PNGs: whole-body and hands views at capture frames 00000, 00060, and 00116, corresponding to physics steps 0, 480, and 924. The final frame is the actual recorded endpoint at 3.85 physical seconds. The montage adds only Korean labels and margins; it does not add contact, fret, or press markers.

### Pair videos

![Pair run native whole-body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/media/whole_body.mp4)

![Pair run native hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/media/hands.mp4)

Each pair video contains 117 native frames at 30 fps and is encoded as 3.9 s; the simulated physics endpoint is 3.85 s. The videos stop at the Fret safety terminal and are not complete song performances.

## Preserved attempts and remaining work

The first v3 pair import failed because the `Ninja` executable was outside the active `PATH`, before scene creation and with zero physics steps. The preserved v1 analysis attempt also stopped before physics because the saved neutral baseline lacked `human_body_names`; the correction is preserved as v2. The successful v4 retry used the `rl38` environment binaries in `PATH`. These failures remain in the execution accounting and were not folded into the pair runtime duration.

The first `producer_pair_artifact_v1.py` attempt also stopped at pre-render validation because `videos.json` stores `nb_read_frames` as the string `"117"`. It produced no image or manifest and made no native/physics call. There was no source snapshot or execution-time source SHA seal for that attempt; [pair_artifact_attempt_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_artifact_attempt_v1.json) points to a clearly labeled reconstructed source copy, not a sealed execution source. The corrected v1 producer later generated the preserved [v1 montage](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_montage_v1.png) and [v1 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_artifact_manifest_v1.json). A versioned v2 producer and montage are the current reviewed artifact paths.

The v4 runtime source did not guard the expected Strike goal/grip SHA. The actual inputs match the intended files, so the v4 measurements above remain attributable to the recorded inputs. A separate v5 run adds that SHA guard; its CPU counterexamples passed, and the same pair is being rerun without physics or action changes. This README reports the completed v4 pair only until root confirms v5. Root's [provenance note](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/PROVENANCE_NOTE.md) records this guard follow-up. A consolidated `execution_summary_v2.json` is planned after root closes the extra run.

No reward v4/fatal ledger, final Actor observation ABI, PPO/GPU training, or learning update is completed here. Remaining gates include reconciling source action representability with the physical support pose, current-guitar joint control and full SO(3) acceptance membership, sustain/dropout/fatal-ledger behavior, and then a final ABI/PPO pilot. The pair's early termination, four Strike misses, and absent joint successes remain visible results.

## Provenance and artifact records

The current pair montage producer and its manifest are [producer_pair_artifact_v2.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/producer_pair_artifact_v2.py) and [pair_artifact_manifest_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_artifact_manifest_v2.json). It renders only the selected six pair-native frames; it hashes the approved analyses, native inputs and metadata, companion preload figures, preserved v1 outputs, and the declared font. The manifest records input SHA256 values before and after generation, output SHA256, `native_calls: 0`, and `physics_steps: 0`.

The original measurement sources are [execution_summary_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v1.json), [preload_analysis_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_analysis_v2.json), and [pair_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_analysis_v1.json). The pair's exact initial 81-joint/guitar state is in [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/initial_values.json); runtime targets and samples are in [controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/controls.json), [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/trace.json), [source_contract.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/source_contract.json), [music_physics_samples.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/music_physics_samples.json), [joint_crossings.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/joint_crossings.json), and [joint_events.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/joint_events.json). The native pair [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/report.json), [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/media/capture.json), and [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/media/videos.json) record completion and media metadata.

The reviewer record is planned at [final_review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/final_review.md). Root-owned [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/final_verification.json), [artifact_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/artifact_inventory.json), and [source_final/manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/source_final/manifest.json) are planned audit outputs. They are not authored here.
