# base.py 참조연구 종합 분석 (자동 생성, 2026-07-09)

> 최종 갱신: 2026-08-03. 이 문서는 base 환경의 연구 근거와 과거 검증을 보존한다. 과거
> `env_base_smoke` 명칭은 현재 파일로 제공되지 않으며, 현재 검증은 공용
> `python -m tab2body.train --task fret --smoke` 또는 `--task strike --smoke`를 사용한다.

> 4개 레퍼런스(guitar/·DIGIT/·GPS/·현 base.py)를 병렬 분석해 종합한 결과.
> base.py 설계 근거의 원자료. 요약·적용은 tab2body/env/README.md(설계 문서) 참조.
> 태그: [G]=guitar/ [D]=DIGIT/ [P]=docs+GPS [C]=현 base.py.

# base.py Synthesis — Stable, Complete Physics-RL Env Core for a Seated 105-DOF Guitar Humanoid

Cross-analysis tags: **[G]** = guitar-env (canonical port `guitar/`), **[D]** = digit-fail (`DIGIT/`), **[P]** = gps-papers (design docs + GPS sibling), **[C]** = current-base (`tab2body/env/base.py` today).

---

## 1. What base.py must provide

The downstream pipeline is **fret [A] ∥ strike [B] → combine [A+B] → guitar staging G0/G1/G2**. Every task instantiates the *same* env core and only swaps `control_dofs`, the goal source, and the reward module. base.py must therefore be a task-less shared sim + obs + step core. Below, each element is marked and justified.

### A. Shared sim + scene core
| Element | Status | Justification |
|---|---|---|
| GPU pipeline, TGS solver, PhysX params, Z-up, gravity −9.81 | **[DONE]** [C] | `_create_sim`: `dt=1/60, substeps=4, pos_iter=4, vel_iter=2, contact_offset=0.002`. Matches [G]'s `Env.setup_sim_params` shape; `vel_iter` correctly raised from [G]'s 0 to damp contact chatter. |
| 2 separate actors (humanoid + guitar) + chair + footrest, sequential per-env creation | **[DONE]** [C][P] | Separate-actor load is the §5.1 mandate so G0→G2 is a flag flip, not an asset rewrite. Sequential creation respects trap #7. **Footrest is dormant** (no `footrest` key in `seated_pose.json`) — resolve intentionally. |
| Per-shape `contact_offset=1e-4, rest_offset=0` on humanoid/guitar | **[DONE]** [C][G][P] | Trap #4: PhysX default 2 cm offset → phantom contacts push joints. [G]'s hands also used `1e-4`. |
| Collision convention humanoid=1 / guitar=2 / chair=footrest=0 | **[DONE]** [C][P] | Trap #2: shared filter bits disable *inter-actor* collision; 1&2=0 → humanoid↔guitar collide (audit valid). **See §2/§3 for the self-collision conflict with [P] P2.** |
| Hybrid PD (implicit drive damping + explicit stiffness torque, joint-group 20~300 clamp) | **[DONE]** [C][P] | Trap #3, detailed in §3. |
| Lower-body limit-pinch lock (Hip/Knee/Ankle/Toe → `lower=upper=pose±1e-4`) | **[DONE]** [C][D] | DIGIT recipe; soft hold drifts 60°. |
| `control_dofs` prefix partition → `controlled`/`ctrl_idx`/`num_actions` | **[DONE]** [C][P] | The single switch enabling fret [A] (torso+L-arm+L-hand) ∥ strike [B] (R-arm+R-hand) to share one env. Idle DOFs held at init pose by hybrid PD — this *is* the "R-arm fixed / torso+L-arm fixed" requirement. |
| `guitar_frame()` live guitar root (pos + xyzw quat) | **[DONE]** [C] | Reads `root_state[:,1]` live → auto-tracks moving guitar in G1/G2; static in G0. Nothing consumes it yet. |
| Init pose from `joints_isaac` (not `joints`) | **[DONE]** [C] | Trap #1: MuJoCo↔Isaac multi-hinge FK differs 8.4 cm at the wrist. |

### B. RL loop pieces the tasks depend on (mostly MISSING)
| Element | Status | Justification |
|---|---|---|
| **Guitar-relative observation builder** (world→guitar-frame transform: rel pos + rel quat + optional lin/ang vel, assembled to a flat vector) | **[MISSING]** [C][G][P] | The headline gap. This is [G]'s `observe_iccgan(parent_link=guitar)`. Without it the weld→free obs invariance (old pipeline 0.90→0.18 collapse) is not structurally guaranteed. **Must fix the quaternion conjugation correctly** — [G]'s L879/L884 bug is harmless only for a world-fixed guitar; ours moves in G1/G2. |
| **`step(actions)` gym API** with control-vs-sim decimation, auto-reset, returning `(obs, reward, done, info)` | **[MISSING]** [C][G] | Only `step_physics()` (one `simulate()`, physics-only) exists. [G]'s `Env.step`/`do_simulation` loops `frameskip`; ours needs an explicit control dt exposed so `goals.py` ticks in lockstep. |
| **Action EMA (α≈0.5) + scaled/relative target map** | **[MISSING]** [C][D][P] | `set_targets` is a raw absolute-to-limit map, no `prev_action` buffer. [D] item 12 raised α to 0.5 for responsiveness. All three policies must share identical action semantics or fret/strike won't compose in `full`. |
| **RSI reset** (random clip + random phase, per-env `set_dof_state_tensor_indexed`, root-state reset) | **[MISSING]** [C][G] | `reset()` is global + deterministic, DOF-only. [G]'s `ReferenceMotion.sample` + indexed reset is the pattern; source = surviving 190 s seated mocap. Per-env reset is required once episodes terminate independently. |
| **Termination / done / progress buffers, `max_episode_length`, timeout** | **[MISSING]** [C][G] | None exist. Port replaces [G]'s hand-box termination with **posture-based** termination (pelvis height/tilt bounds) + re-enabled fall/contact rule ([G] L662-674). |
| **Reward hooks + multi-critic `reward()→N×rew_dim`** | **[MISSING]** [C][G] | `rewards/*` are docstrings; base has no hook. [G]'s per-string multi-critic (Left 6 cols `[0.15]×6`, Right 1 col `0.5`, Two 7 cols `[0.075]×6+[0.5]`) transfers model-agnostically; add body-posture discriminator columns. |
| **Goal buffer + goal→obs concat + note↔`G:string` mapping hook** | **[MISSING]** [C][G][P] | [G]'s `load_notes`/`reset_goal`/`update_goal_tensor` machinery transfers unchanged (5-note lookahead, grace 5, resample range 10-20). String-index mapping (JSON 5=low-E vs GPS 6=low-E) is **unconfirmed** and belongs in `goals.py`, not base. |
| **Contact / net-force sensor tensor** | **[MISSING]** [C][D] | Needed for pluck detection, contact termination, G2 friction hold. [D] item 3: force sensors read zero without `<site>`/`<force>` in XML — **verify nonzero output before rewarding on them.** |
| **Interface bookkeeping**: `num_obs`/`ob_dim`, `act_dim`, `rew_dim`, `disc_dim`, `goal_dim=[lo,hi]`, `state_dim`, `ob_horizon`; `info` keys `lifetime/terminate/ob_seq_lens/disc_obs/disc_obs_expert` | **[MISSING]** [C][G] | Only `num_actions` exists. These are what `models.py`/`main.py` consume to size heads. |
| **Root / free-guitar reset plumbing** (`reset()` writes `root_state`) | **[MISSING]** [C][P] | `reset()` writes DOF only — fine for G0, zero support for G1/G2 free actor + strap + inertia + guitar-in-obs. |

**Minor/latent [C]:** viewer path is a no-op (`0 if not headless else 0`); no RNG/seeding.

---

## 2. Stability of the initial pose

### What the references establish
- **[D] — the proven-stable recipe:** weld the pelvis (`fix_base_link=True`, pinned in air at z=0.55, gravity on), lock hips at −90°, drive locked lower body with stiff PD `kp=20000/kd=2000`, and **belt-and-suspenders re-overwrite** the lower-body PD targets to the init pose every step. Upper body `kp=800/kd=120`. **Crucially, DIGIT had no chair and no ground/foot contact** — the feet float, so balance and tipping are designed entirely out of the problem, and *there was zero tremor because there was zero contact*.
- **[C] — current hold + the tremor:** same structural choice (root `fix_base_link=True`, lower-body limit-pinch `lower=upper=pose±1e-4`), but with **drive damping instead of stiff PD on the lock** (`stiffness=0, damping=kd`) plus a footrest/chair the feet rest against. Settle report: `locked_lower_worst_deg=1.20`, `max_qvel≈0.32`, ~30 Hz chatter, no NaN — passes the <6° smoke gate but flagged open. The dilemma is explicit: **pinch → ~30 Hz sub-degree tremor; soft (hybrid-PD only) → the left leg's disturbance torque saturates the ±300 clamp and drifts 60°+.** Mitigations already applied: `vel_iter` 0→2, and drive damping on the locked joints.
- **[G] — does not transfer:** hands hold pose via `fix_base_link=True` **+ `disable_gravity=True`** + feather masses; the "stability" is achieved by deleting gravity and inertia. For our gravity-loaded seated body, do **not** copy `disable_gravity`, `max_depenetration_velocity=1`, or `contact_offset=1e-4` at the *sim* level. SMPL-scale gains (§5) are the relevant reference, not the hand's stiffness=10.
- **[G] cross-check — self-collision:** [G] runs per-env isolation with self-collision governed by the MJCF contype/conaffinity. **[D] enabled humanoid self-collision** (`filter=0`). **[P] P2 explicitly found the opposite: "humanoid self-collision must be disabled"** (free root falls backward with self-collision active). **This is a real conflict — resolve it as: disable humanoid self-collision** (follow the measured [P] finding over [D]'s untested choice), since the seated posture packs limbs against the torso and spurious self-contacts inject exactly the kind of energy that feeds tremor.
- **[P] — no seated insight:** GPS has no torso/legs; contributes nothing here beyond confirming a position-servo at coarse control rate suffices.

### Concrete recommendation for the most stable lower-body hold
The root is already welded, so **the lower body bears no balance load — it is pure held posture.** That reframes the four candidate mechanisms:

| Mechanism | Verdict |
|---|---|
| **Pinch-lock + drive damping (current [C])** | Keep as the base. It cannot drift (hard limit) and adds no PD energy. Its only cost is the contact-driven ~30 Hz tremor. |
| **Stiff-PD (DIGIT `kp=20000`)** | **Redundant and slightly counterproductive when combined with the pinch.** DIGIT needed high kp because its lock relied on PD alone; with a hard `lower=upper` limit, a 20000 kp servo just pumps energy into the limit constraint every step. Do not add it on top of the pinch. |
| **Kinematic-freeze (`DOF_MODE_NONE`/free-teleport)** | Kills actuation chatter, but the pinned links still participate in contact and it discards contact realism. Acceptable *only* because the lower body never touches the guitar — but it removes the very drive damping that currently suppresses chatter, so not recommended. |
| **High-armature on the locked DOFs** | **The recommended lever for the tremor.** Raising `armature` on Hip/Knee/Ankle/Toe increases effective joint inertia, which directly attenuates the ~30 Hz mode without hardening the contact or adding servo energy. [G] and [D] both run `armature=0.01`; the SMPL MJCF already goes to 0.025 — pushing the *locked* lower joints to ~0.05–0.1 is a low-risk, physically clean damping of the chatter. |

**Recommendation:** keep pinch-lock + drive damping, **disable humanoid self-collision**, and attack the tremor first with **higher armature on the four locked lower-DOF groups**; if residual, **question whether the feet need footrest contact at all** — DIGIT's tremor-free result came precisely from *no* foot contact against the welded root. Do **not** layer stiff-PD on the pinch. The tremor constraint is a hard target: it currently sits at 1.2°/~30 Hz (inside the <6° gate) — treat sub-1° as the goal, and always verify any change against the unified task smoke's worst-deviation metric plus `max_qvel`.

---

## 3. Design rationale (backbone of the base.py design doc)

Each major decision, its WHY, and the anchoring reference/pitfall.

**Hybrid PD (implicit drive damping + explicit stiffness torque `τ=kp(q*−q)`, joint-group caps 20~300 N·m).**
Two measured failure modes force this split. (1) **Isaac native position-drive distorts multi-hinge D6 joints** — the shoulder converges to the same ~20° wrong answer regardless of kp (trap #3, [C]; [P] P2 confirms "native POS drive distorts multi-hinge → custom PD"). (2) **Pure explicit PD with zero damping goes bang-bang** — elbow overshoots to 235°, qd≈−90 rad/s, torque saturated ([C]). The fix: put damping in the solver drive (`stiffness=0, damping=kd, DOF_MODE_POS` → unconditionally stable) and inject stiffness as an explicit per-step torque. Residual deviation <2°. Note [G] and [D] both used Isaac's *native* PD successfully — but for hinge-dominant finger/hip chains, not the SMPL shoulder's stacked hinges; our finer-grained torso is exactly the case that breaks native drive.

**Pinch-lock of the lower body (`lower=upper=pose±1e-4`).**
Direct from the DIGIT recipe [D]: welding the root + pinching the hips designs balance/tipping out of the problem entirely (DIGIT's log never mentions tipping). [C] confirms the alternative fails: soft-holding the lower body saturates the ±300 clamp and the leg drifts 60°+. The pinch is a hard kinematic constraint, not a servo, so it cannot drift. DIGIT double-enforces it (pinch + per-step target overwrite); ours relies on the pinch + drive damping.

**Collision filters (humanoid=1 / guitar=2 / chair=footrest=0).**
Trap #2 ([C][P]): in Isaac, overlapping `create_actor` filter bits disable *inter-actor* collision. 1&2=0 → humanoid↔guitar **do** collide (required for contact-based fret/pluck audits to be valid); chair=0 shares no bits with either so it collides with both. Getting this wrong silently invalidates every penetration audit. Distinct from **self-collision within the humanoid**, which [P] P2 says must be **disabled** — a separate asset-level setting, and a point where the references conflict (see §2).

**Contact offsets (per-shape `1e-4`, global `0.002`, `rest_offset=0`).**
Trap #4 ([C][P]): PhysX's default 2 cm contact_offset creates phantom contacts that push joints out of pose. Forcing per-shape `1e-4` on humanoid+guitar kills the phantom gap; [G]'s hands independently arrived at the same `1e-4`. The global 0.002 (vs [G]'s 0.01, [D]'s 0.05) is a middle ground that keeps footrest/chair contacts from chattering while staying tight.

**Guitar-relative observations (`parent_link=guitar`).**
The core invariance ([G] `observe_iccgan`, [P] §5.1). Expressing all body states in the guitar's local frame makes the weld→free transition structurally invisible to the policy — in G0 guitar-frame ≡ world-frame, and the identical code path carries into G1/G2 where the guitar moves. This is the explicit fix for the old pipeline's 0.90→0.18 collapse. **Design-critical caveat:** [G]'s L879/L884 quaternion-conjugation bug is harmless *only* because its guitar is world-fixed (constant quat = constant learnable rotation). Ours moves, so base.py must do the conjugation **correctly** (use the true `orient_inv`), not port the bug.

**60 Hz control.**
[G] runs the hand configs at `fps=60, substeps=4, frameskip=1` → one `simulate()` per control step at dt=1/60; [C] mirrors this (`SIM_HZ=60, SUBSTEPS=4`). [P] notes GPS uses 30 Hz control / 300 Hz physics and confirms a coarse-control + fine-substep position servo is sufficient for fret precision — but 30 Hz is *not* inherited. The load-bearing requirement: **base must expose the control dt so `goals.py` ticks its note timer/lookahead against the exact same clock**, or goal countdowns desync from the physics.

---

## 4. Adaptations: guitar/ (27-DOF floating hands) → ours (105-DOF seated)

### Transfers directly
- The **`Env` + `ICCGANHumanoid` skeleton** (sim setup, tensor wrapping, env grid). [G]
- **RSI via `ReferenceMotion`** (random clip + random phase, indexed reset). [G]
- The **`observe_iccgan` encoder** — egocentric heading-only frame *and* the `parent_link` guitar-relative frame. [G]
- The **multi-critic `reward()→N×rew_dim` + AMP-discriminator weight-mixing** interface (auto-distributes disc weights so total ≤1, folds in task weights). [G]
- The entire **goal/note/timer machinery** (`load_notes`, `reset_goal`, `update_goal_tensor`, `observe_goal`) — it already targets frets+strings and is body-agnostic. [G]
- The **reward-side velocity/acceleration smoothing** pattern (wrist/fingertip velocity penalties, pick-accel penalty) as the anti-jitter mechanism in place of action filtering. [G]

### Must change
- **`fix_base_link` + `disable_gravity` semantics.** [G] floats the hands with gravity off. Ours keeps **gravity on** and welds the **pelvis root** (`fix_base_link=True` on the humanoid) — a *different* use of the same flag: [G] bolts the whole hand; we bolt only the pelvis and let the articulated body hang under gravity. `disable_gravity` must be **off** for the body. [G][D][C]
- **Gains.** Drop [G]'s hand stiffness=10/damping=0.2; adopt SMPL-scale gains via `mjcf_gains.json` + the cap/floor envelope (§5), because gains live in data, not env.py. [G][C]
- **PhysX solver.** `vel_iter` 0→2 (done, [C]); consider raising `pos_iter` toward [D]'s 16 if contact-rich; keep `max_depenetration_velocity=10` (not [G]'s hand override of 1). [G][C][D]
- **Termination.** [G]'s hand guitar-box bounds don't transfer; re-enable the `ICCGANHumanoid` fall/contact rule and add **seated-posture bounds** (pelvis height/tilt). [G][P]
- **`ob_horizon`.** [G]'s hands use 2; the humanoid default is 4 — revisit for the heavier body. [G]
- **Quaternion conjugation** — fix the L879/L884 bug (§3). [G]

### Genuinely new problems (no reference solves these)
- **Seated balance / lower-body hold under contact.** [G] never had a body; [D] avoided it by floating the pelvis with no foot contact. Our chair+footrest reintroduces contact → the ~30 Hz tremor (§2) is *ours to solve*. [C][D]
- **Full-body self-collision.** A 27-DOF hand had trivial self-collision; a seated 105-DOF body packs arms against torso against thighs. [P] P2 says disable it — a decision [G] never faced. [P]
- **Control partition of one body vs separate actor-classes.** [G] implements fret/strike as *separate env classes* (`ICCGANLeftHand`/`RightHand`/`TwoHands`, each its own actor set). Ours is **one env, one body, partitioned by `control_dofs` prefix** — so "combine" is not [G]'s TwoHands (two actors trained jointly) but **freezing the A and B policies and injecting AdaptNet into the same body with the torso released** (research-flow §5.0 ⑥, "the novel hard part"). No reference has done this. Base must let held (non-controlled, non-locked) DOFs stay put under the *other* hand's disturbance — verify under P3. [P][C]
- **Guitar coupling (G1/G2).** Strap soft-constraint (spring-damper to chest/shoulder) + guitar inertia (~2–3 kg) + thigh-support contact + guitar state in obs. [G] never had a free, body-coupled guitar; [D] held its free guitar by high damping + reset-on-tilt, not a strap. Base's separate-actor + live-`guitar_frame` design makes the G0→G1 switch a config flag, but the strap constraint and inertia are net-new. [P][D]

---

## 5. Concrete gain / param values

### Simulation / PhysX
| Param | Value | Source |
|---|---|---|
| `dt` | 1/60 | [C][G] |
| `substeps` | 4 | [C][G] (D used 2) |
| `solver_type` | 1 (TGS) | [C][G][D] |
| `num_position_iterations` | 4 (raise toward 8–16 if contact-rich) | [C][G]; D used 16 for finger contact |
| `num_velocity_iterations` | 2 | [C] (G=0, D=4) |
| `contact_offset` (global) | 0.002 | [C] (G=0.01, D=0.05) |
| `contact_offset` (per-shape, humanoid+guitar) | 1e-4 | [C][G][P] |
| `rest_offset` | 0.0 | [C][G] (D=0.01) |
| `max_depenetration_velocity` | 10.0 (do NOT use G's hand override of 1) | [G] |
| `gravity` | (0,0,−9.81), on for body | [C][D] |
| ground friction / restitution | 1.0 / 1.0 / 0 | [G][D] |
| `contact_collection` | last substep | [G] |
| `armature` (general) | 0.01 | [G][D][C] |
| `armature` (locked lower DOFs, tremor fix) | try 0.05–0.1 | derived (§2) |

### DOF gains
| Group | kp | kd | Source |
|---|---|---|---|
| Locked lower body (pinch) | stiffness=0 + drive damping `kd` | (do not add DIGIT's 20000/2000 on top) | [C]; D used 20000/2000 without a pinch |
| Upper body (general cap) | ≤ 600 | ≥ max(0.25·kp, mjcf_kd) | [C]; D used 800/120 |
| Fingers `LH:`/`RH:` | cap 20 | ,, | [C] |
| Wrist / Elbow twist | cap 60 | ,, | [C] |
| Neck / Head | floor 100, cap 150 | ,, | [C] |
| kp floor (all else) | 30 | — | [C] |
| SMPL MJCF reference | hips/knees 300/30, torso/spine/chest 600/60, ankles 200/20, neck/head/toes 5–50/2–50 | armature 0.01–0.025 | [G] |
| Explicit torque clamp | finger20 / wrist60 / elbow100 / shoulder·thorax150 / others300 N·m | — | [C], R14 update |

### Action / control
| Param | Value | Source |
|---|---|---|
| Action → target map | `[-1,1]` → per-DOF `[lower,upper]` (absolute) | [C][G][P] |
| **EMA smoothing** | α ≈ 0.5 (`a = 0.5·old + 0.5·new`) | [D] item 12; PROJECT_CONTEXT [P] |
| Action scale | 2× on the PD-target delta | [P] |
| Control rate | 60 Hz, frameskip=1 (one sim step/control) | [C][G] |
| `ob_horizon` | 4 (body) / 2 (hand default — revisit) | [G] |

### Goal / task
| Param | Value | Source |
|---|---|---|
| Note lookahead (`GOAL_HORIZON`) | 5 | [G] (GPS gym used 10 [P]) |
| `GRACE_PERIOD` | 5 empty frames | [G] |
| `GOAL_SAMPLING_RANGE` | (10, 20) notes | [G] |
| random pitch / bpm rate | 0.5 / 0.5 | [G] |
| Multi-critic weights | Left `[0.15]×6`, Right `[0.5]`, Two `[0.075]×6+[0.5]` | [G] |

### Reward shaping (belongs in `rewards/*`, listed for reference)
| Param | Value | Source |
|---|---|---|
| Distance kernel | **coarse+fine blend** `0.6·exp(-2d)+0.4·exp(-20d)` | [D] items 1,11 (AVOID single narrow `exp(-15d)`) |
| Press activation | `key_bound=0.2`, `ACTIVATION_THRESHOLD=0.2`, `MAX_FORCE=1` | [P] (GPS) |
| Finger bound | 0.01 m; per-fret x-bound = `LENGTH[fret]` (shrinks up neck) | [P] |
| Contact reward | **target-gated only** (force AND near assigned target); threshold >0.01 | [D] items 1,8 |
| Fret geometry | string spacing 8 mm, `BASE=17.84`, neck `LENGTH=0.645`; compression = 35% behind fret wire | [P] |
| PPO entropy_coef | 0.03 (prevents the DIGIT "frozen hand" failure) | [D] item 12 |

### DIGIT anti-patterns to bake into base/reward design as hard "don'ts"
From [D]'s 18 failed iterations — the base body was stable; the *policy froze*: never anchor a guidance reward to a **static point** when the target moves (item 11/16); never use position-only rewards (add velocity-toward-target, items 12/14); never AND-stack gates to zero the signal (items 1–7); verify force sensors output nonzero and geometric front/approach tests against the **actual world axis** (items 3,13,17); use sticky `(string,fret)`-keyed matching, not per-step greedy (item 5).
