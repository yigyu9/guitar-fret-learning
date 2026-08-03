# ELGAR (SIGGRAPH25 첼로, 물리 없는 diffusion) 분석 — 구성·제약(손실)·환경

> 출처=related_work/ELGAR 코드 + docs/Elgar.pdf. 최종 2026-07-17. **우리 노벨티(물리 기반)의 비교축 = 물리 없는 kinematic diffusion.**
>
> Qiu et al.(SIGGRAPH Conf. Papers 2025, arXiv 2505.04203)의 **오디오→전신 첼로 연주 모션 diffusion**을
> **우리 tab2body 문서와 같은 틀**(§규칙=`task_*_design.md`, §환경=`learning_env_design.md`, 형제 분석서=
> `related_work_analysis/{GPS,guitar}.md`)로 재정리한 분석서. 단 ELGAR는 **RL이 아니라 kinematic diffusion**
> 이므로 틀을 그 특성에 맞게 조정한다 — **§2 규칙 = 학습 손실·기하 제약**(보상 아님), **§3 환경 = diffusion
> 학습셋업**(MDP·보상·멀티크리틱 없음). GPS/guitar가 "물리 RL 도너/이식원본"인 것과 달리, **ELGAR는 우리
> 노벨티("물리 있음")의 정확한 반대편 비교축** — 물리 없이 손실만으로 접촉을 강제하는 접근이 무엇을 못 하는지가
> 우리 기여의 근거다. 각 값은 `related_work/ELGAR/{model/pdm.py, diffusion/gaussian_diffusion.py,
> utils/parser_util.py, data_process/*, validation/*}` 실측 + 논문(`docs/Elgar.pdf`)에서 왔다.
> 파일:라인은 §5에 모았다(경로 접두 `related_work/ELGAR/` 생략).
> 표기: **[코드]**=ELGAR 코드 실측 · **[논문]**=Elgar.pdf 서술 · **[확인 필요]**=코드/논문 대조 미완.

---

## §0. 개요

- **한 줄 정의**: ELGAR = **원음(raw audio)만 입력하면 SMPL-X 전신 + 양손(MANO) + 보우의 첼로 연주 모션을
  end-to-end로 생성**하는 **kinematic conditional diffusion**. MIDI/악보 같은 상징(symbolic) 입력이 없고, **물리
  시뮬레이터·보상·정책이 전혀 없다**. 접촉은 미분가능 **기하 손실**(HICL/BICL)로만 부드럽게 강제한다.
- **학습 범위**: OpenAI Jukebox(5B, layer 66) 오디오 특징(4800차원)이 DiT/adaLN-Zero 트랜스포머 **디코더**에
  cross-attention으로 주입되어, 5초(150프레임@30fps) 윈도의 rot6d 모션 텐서 `[B, 52, 6, T]`(21 body + 15 LH +
  15 RH + 1 bow)를 denoise한다. 첼로(11-keypoint 정적 템플릿)와 몸통 root 방향은 **생성하지 않고 고정**한다.
- **핵심 대비 (우리 노벨티의 비교축)**:
  **오디오 → kinematic diffusion (물리 없음)** vs **우리: 오디오 → 전사(탭) → 물리 RL**.
  - ELGAR: 오디오가 **직접** 모션으로 사상됨(상징 중간표현 없음). 접촉·관통·미끄러짐·역학은 **물리로 보장되지
    않고** 손실로만 근사됨. 저자 스스로 "BICL를 써도 보우가 종종 현에서 떨어진다"고 보고(§5 한계).
  - 우리: 오디오→탭(전사)→**Isaac Gym 물리 시뮬 안에서 멀티크리틱 PPO**로 학습. 접촉은 **손실 항이 아니라
    물리적 귀결**이고, 관통·미끄러짐은 시뮬레이터가 원천 차단. 압현력·역학이 실재.
  - **∴ ELGAR가 "물리 없이 못 하는 것"(관통 방지·현 접촉 유지·압현력·역학적 타당성)이 곧 우리 기여**다.
    ELGAR는 논문에서 물리-RL과의 **정량 비교를 전혀 제시하지 않으며**(FID·baseline 표 없음, §3-6), 물리적
    정확성을 입증하지도(할 수도) 않는다 — 정확히 물리-RL이 채울 수 있는 공백.

---

## §1. 구성 (configuration)

### 1-1. 생성 모션 표현 (`model/pdm.py`, `model/rotation2xyz.py`)

- **모델 I/O 텐서** `x = [bs, njoints=52, nfeats=6, nframes=150]` **[코드]** (rotation2xyz.py:35, pdm.py 입력).
  `input_feats = 52×6 = 312`(pdm.py:40), `data_rep='rot6d'`. **회전표현 = 6D 연속회전**(Zhou 2019),
  `rotation_6d_to_matrix`로 복원.
- **관절 슬라이싱** (rot6d 생성텐서, generate.py:157-159 / rotation2xyz.py:37-40):

  | 슬롯 | 내용 | 차원 | 비고 |
  |---|---|---|---|
  | `x[:, :21]` | **BODY** 21 SMPL 관절 | 21×6 | root(pelvis) **미포함**·미생성 |
  | `x[:, 21:36]` | **LEFT HAND** 15 MANO 관절 | 15×6 | 손목(wrist) **드롭**(16→15) |
  | `x[:, 36:51]` | **RIGHT HAND** 15 MANO 관절 | 15×6 | 〃 |
  | `x[:, 51]` | **BOW** | (6 중 앞 3만) | 3D 보우 방향 단위벡터, 뒤 3은 0-패딩 |

- **생성하지 않고 유도되는 것** [코드]: ① 몸통 **root 방향** = `smpl_info/rest_pose.json`의 고정 상수
  (rotation2xyz.py:69-71) → **연주자는 앉은 고정 포즈**, 이동(locomotion)·global translation 생성 없음
  **[확인 필요]**(root orient 고정은 확정, 잔여 global translation 완전 부재는 코드상 100% 명시는 아님).
  ② 손 **손목 글로벌 회전** = 몸통 kinematic chain 누적으로 계산(rotation2xyz.py:78-91). ③ **보우 끝점** =
  RH 관절 평균으로 frog 재구성 후 `bow_end = frog + 단위벡터×0.75m`(rotation2xyz.py:99-106; 데이터빌드는 0.8,
  postprocess는 0.75 사용).
- **논문 표현 vs 코드 텐서** [논문][코드]: 논문 §3.1은 `x = {r, v̂} ∈ R³⁰⁹`, `r ∈ R³⁰⁶ = (21+15+15)·6`(pelvis
  제외 rot6d) + `v̂ ∈ R³`(보우 단위방향). 코드는 보우를 6-dim 관절로 **0-패딩**해 D=312로 저장 → **논문 309 vs
  코드 312**는 보우 패딩 차이(실질 동일). **[확인 필요]**(패딩 규약).
- **FK(rot2xyz) 출력 레이아웃**(시각화/손실/평가용, postprocess.py:119-121): `[:21]`=LH xyz 21 · `[21:42]`=RH
  xyz 21 · `[42:44]`=보우 2점(frog=42, tip=43) · `[44:]`=body xyz 22(끝 2 = LH/RH 손목). **주의**: 생성 rot6d
  관절순서(body→LH→RH→bow)와 FK xyz 관절순서(LH→RH→bow→body)가 **다르다** — §2 손실의 인덱스는 FK xyz 기준.
- **시퀀스 길이** `SEQ_LEN=150 = 5s @ FRAME_RATE=30`(data_normalization.py:26-28). 생성 시 `max_frames=150`,
  `n_frames=min(150, motion_length·30)`. (parser `num_frames` 기본=90이나 a2p 콜레이트는 배치 최대로 패딩 →
  캐논 윈도는 150. **[확인 필요]**: 90 vs 150.)

### 1-2. 데이터셋 (SPD-GEN, 첼로 서브셋)

- **SPD-GEN** = SPD(String Performance Dataset, Jin 2024a) MoCap에서 파생, **첼로 전용**(`instrument='cello'`
  하드코딩, data_segmentation.py:60). Google Form 게이트(README).
- 클립 `cello01…cello85`(README). partial-train split은 81개 클립 인덱스(`np.arange(81)`), 홀드아웃 테스트 9개
  `[0,4,7,11,24,43,44,54,55]`(string_performance_dataset.py:84-86). 논문 §3.1 = **SPD 81 첼로곡, ~7000초**
  전신 첼로 모션 [논문].
- **원시 프레임 데이터**: `kp3d = 155개 3D keypoint`(assert 155, data_normalization.py:46), `hand_rot = 32
  MANO axis-angle`(좌16+우16). 몸통 = kp 0..22(23점), 첼로 = kp 133..139 → 11점 템플릿, 보우 = kp 140..141,
  접촉점 = kp 150, 손끝 = `[99,103,107,111]`.
- **윈도잉** → 총 **~6665개 학습 샘플**(sliding window, 코멘트). 단위 mm→m 변환(/1000). 오디오 44.1kHz.
- **프레임별 접촉 주석**(손실 앵커로만 사용, 오디오 조건과 별개): `cp_info=[활성현∈{0,1,2,3}, 진동길이∈[0,1]]`
  (find_cp_position), `used_finger_idx∈{0,1,2,3,-1}`(어느 손끝이 누르는가, -1=없음). `motion.hdf5`에 저장.
  **[논문]** 접촉점 cp는 **오디오에서 추출**(CREPE 피치→지판 위치 매핑, §1-4·§2 참조) — 학습이 아니라
  오디오 유래 감독신호.

### 1-3. 오디오 컨디셔닝 (`audio_encoder/encode.py`, `model/pdm.py`)

- **기본 = OpenAI Jukebox(5B)**, `jukemirlib`로 **layer 66, 차원 4800** 추출(pdm.py:53 `audio_cond_dim=4800`,
  encode.py `layers=[66]`) **[코드]**. `JUKEBOX_SAMPLE_RATE=44100`. librosa로 `pose_freq=30×seq_len`에 리샘플해
  오디오 프레임을 30fps 모션에 정렬 → 윈도당 `[150, 4800]`.
- **Jukebox = 동결(frozen)** 인코더 [논문]. ELGAR의 novelty가 아니라 **차용 인프라**(Dhariwal 2020 +
  Castellon jukemirlib).
- **네트 내 오디오 경로**: `EmbedAudio = Linear(4800→512)` → LayerNorm → 2-layer TransformerEncoder
  `cond_encoder` → 디코더 memory(cross-attn) + mean-pool해 diffusion time token에 가산(pdm.py). **CFG용
  조건 마스킹** `cond_mask_prob=0.1`(10% 드롭).
- **코드에 존재하나 ELGAR 기본 아님**: wav2clip(512)/STFT(2049)/mel(512)/DAC/EnCodec, 그리고 오디오 대신
  `instrument`(21-dim) 조건 모드. **릴리즈 파이프라인은 jukebox만 사용**(train_script.sh `--cond_mode audio`).

### 1-4. 데이터 파이프라인 (정규화 · 정준화 · 세그먼트)

- **정규화**(data_normalization.py): 첼로 end-pin(kp139)을 원점으로 평행이동 → **Kabsch 정렬**로 첼로 지판
  keypoint를 고정 레퍼런스 첼로에 맞춤(모든 프레임에서 **악기를 정적 캐논 템플릿**으로) → 전역회전 후 손목
  trans/rot 재계산 → rotvec→matrix→6d → Savitzky-Golay 스무딩.
- **정준화/정렬**(data_alignment.py, `R_of_orientating`): 3회 강체회전 — R1(tailpiece FG를 yz평면으로),
  **R2(FG가 y축과 `TARGET_ANGLE=40°`가 되게 x축 회전)**, R3(bridge 평면 ⟂ yz). 월드/첼로 프레임 정의.
- **아치형 브리지 재구성** [논문]: SPD의 평평한 브리지 대신 **아치형 브리지**를 재구성해, 가운데 두 줄을 그을 때
  인접 줄과의 **의도치 않은 접촉(관통)을 방지**(Fig 2, §3.1). → **관통이 시뮬이 아니라 데이터 전처리 기하
  해킹으로 처리됨**을 보여주는 핵심 증거(§4).
- **IK**: 정규화 3D 몸통 → VPoser 기반 IK **2~3라운드**로 SMPL-X 관절회전 복원(script_ik_joints). SMPL-X
  NEUTRAL, betas/trans/scale 평균 → `body_mean.json`, rest pose 캐시.
- **세그먼트**(data_segmentation.py): sliding window `SEQ_LEN=150, HOP_LEN=30`(1초 stride), 꼬리<150 edge-pad.
  body rotvec→6d(21×6=126), 손 6d에서 손목 드롭(15×6=90). `motion.hdf5`에 {bow, lh_pose, rh_pose, cp_info,
  cp_pos, body, instrument(정적), used_finger, sample_num} + `audio.npy`(jukebox 특징) 기록.

### 1-5. 리타게팅 / 후처리 (`data_process/postprocess.py`, `retargeting/`)

- **후처리 = 타당성 보정 IK가 아님** [코드]: `postprocess.py`는 ① 150프레임(5s) 청크 **overlap-add 페이드
  블렌딩**(장시퀀스 stitching, seq_len 150 step 30) + ② rot6d→xyz FK + ③ 쿼터니언 부호 일관성만 한다.
  **생성 후 접촉 교정 IK/가이던스 없음.** (test-time 편집 `edit.py`는 MDM 표준 inpainting(in-between/upper-body
  마스크)뿐, 첼로 특화 가이던스 아님.)
- **리타게팅**: SMPL-X FK → npz → Blender SMPL-X 애드온 → FBX(Y-forward/Z-up) → **UE5.5 MetaHuman**. README·
  논문 모두 "interactive contact 때문에 리타게팅이 **suboptimal**"이라고 명시 [논문] — 상호작용 디테일이
  상용/기존 학술 리타게팅에서 보존되지 않음(§5 한계).

---

## §2. 규칙 (=손실 · 기하 제약)

**RL이 아니므로 "규칙" = 학습 손실 항 + 물리 없이 연주 타당성을 강제하는 방식**이다. 모든 손실은
`diffusion/gaussian_diffusion.py:training_losses`(L1282-1800)에서 조립된다. 기하/접촉 손실은 **FK(`enc.rot2xyz`)로
얻은 3D xyz** 위에서 계산된다(L1310-1312). **보상·env·멀티크리틱 없음** — supervised MSE 회귀 + 기하 정칙화.

### 2-1. 손실 마스터 표 (항목 | 분류 | 손실/제약 | 비고)

| 항목 | 분류 | 손실 / 제약 | 계수 · 근거 · 차용/고유 |
|---|---|---|---|
| **rot_mse** (L_simple) | 재구성(rotation) | `masked_l2(x0_target, model_output)`; START_X 모드라 target=x_start | 항상 1.0(base). L1370. **MDM 차용**. |
| **rcxyz_mse** (L_pos) | 기하(FK 관절위치) | `masked_l2(FK(target), FK(out))` | λ_rcxyz=**1.0**. L1374-1377. **MDM 차용**. FK가 rot→xyz 다리. |
| **vel_mse** (L_rotvel) | 재구성(회전속도) | rot6d 1차차분 masked_l2 | λ_vel=**1.0**. L1749-1756. **MDM 차용**. |
| **vel_xyz_mse** (L_posvel) | 기하(위치속도) | xyz 1차차분 masked_l2 (dataset 'spd') | λ_vel_rcxyz=**1.0**. L1379-1385. **MDM 차용**. 사람+보우 keypoint 모두. |
| **accel_xyz_mse** | 기하(위치가속) | xyz 2차차분 masked_l2 | λ_accel_rcxyz=**0 (OFF)**. L1387-1395. **MDM 차용**, 비활성. |
| **fc** (L_foot) | 접촉(발-바닥) | GT 발\|vel\|≤0.01 프레임에서 pred 발속도=0 강제; body 발 idx 44+{7,8,10,11} | λ_fc=**1.0**. L1729-1746. **MDM 차용**. 좌식 첼로라 실효 낮으나 켜짐 **[확인 필요]**. |
| **HICL** (L_hand) | **접촉(손끝↔현/지판)** | (a) `contact_loss=masked_l2(‖cp_pos − 사용손끝‖, 0)` → 누르는 손끝을 정확한 접촉점에 **거리 0**(=올바른 음정 위치) + (b) `interactive_loss`: 비사용 손가락들의 손끝↔cp 거리를 GT와 일치 | **λ_hicl=2** (train_script.sh). L1466-1512. **ELGAR 고유**. 손끝 idx `[16,17,19,18]`(FK LH), `used_finger`로 gather, cp가 NaN인 프레임 제외. |
| **BICL** (L_bow) | **접촉(보우↔현)** | (a) `bow_contact_loss=masked_l2(skew-line dist(보우, 활성현), 0)`, dist=`\|diff·(v1×v2)\|/\|v1×v2\|` → 보우선-현선 **교차(접촉)** + (b) bow_frog(42)·(c) bow_tip(43)의 점-선 수직거리를 GT와 일치 | **λ_bicl=3** (train_script.sh). L1566-1663. **ELGAR 고유**. 현 = instrument keypoint 쌍 `[[2,4],[8,10],[7,9],[1,3]]`, 활성현 = `cp_info[:,0]`. |
| **최종 조립** | — | `loss = rot_mse + fc + vel_mse + rcxyz_mse + vel_xyz_mse + λ_hicl·hicl + λ_bicl·bicl` (use_awl=False) | L1788-1795. 논문 Eq 8. use_awl=True면 AWL로 감쌈(§2-3). |

### 2-2. 물리 없이 연주 타당성을 강제하는 방식 (핵심)

- **후처리 IK/가이던스가 아니라 학습 손실로 강제** [코드]: HICL/BICL이 FK xyz에서 계산되어 **학습 중** 미분가능
  페널티로 작용한다. test-time에는 어떤 접촉 보정 IK도 없음(§1-5).
- **"올바른 음정 위치"** = HICL contact_loss가 누르는 손끝을 **오디오 유래 접촉점 cp_pos**(지판 위 정확한 음정
  지점)에 거리 0으로 붙임. cp는 **CREPE 피치 추정 → freq→fingerboard 위치 매핑**으로 오디오에서 추출 [논문]
  (validation `_cal_cp_coordinates`, freq_position). 학습 대상이 아니라 감독신호.
- **"보우 접촉"** = BICL bow_contact_loss가 보우선-현선 skew-line 거리 0으로 강제.
- **조건입력(=diffusion 데이터 앵커)**: `cp_pos`(접촉점 xyz), `cp_info`(활성현 idx), `used_finger`, `instrument`
  (정적 keypoint)이 `model_kwargs['y']`로 주입(get_spd_data.py) — "어디에 접촉해야 하는가"의 GT. **오디오는
  별도 조건**(jukebox 인코더). **[확인 필요]**: cp_pos/used_finger가 mocap GT인지 오디오추론인지 로딩만 확인.
- **한계(물리 부재의 직접 대가)** [논문 §5]: (i) **BICL를 써도 보우가 종종 현에서 떨어짐** — soft loss ≠ 접촉
  보장. (ii) **압현력이 binary(눌림/안눌림)로 단순화** — 미세 압력은 force sensor 없이는 불가. (iii) **첼로가
  정적** — 악기 자연스러운 동역학 없음. (iv) **관통은 아치 브리지 기하해킹 + soft loss로만**(§1-4), 비관통
  물리보장 없음. (v) **물리적 타당성 전반 보장 없음**(data-driven).

### 2-3. AutomaticWeightedLoss (옵션, 손실 자동가중)

- **수식**(Kendall-style uncertainty weighting, AutomaticWeightedLoss.py): `Σᵢ[0.5/σᵢ²·Lᵢ + log(1+σᵢ²)]`,
  σᵢ = 학습가능 파라미터. training_loop에서 `AutomaticWeightedLoss(7)`(7개 손실 의도)를 AdamW에 함께 최적화.
- **기본 OFF**(use_awl 기본 False, parser_util.py:160) → 릴리즈는 **수동 λ**(hicl 2·bicl 3) 사용.
- **⚠️코드상 실동작(사실)** [코드]: gaussian_diffusion.py:1779에서 `awl(...)` 인자가 **전부 '+'로 합쳐진 단일
  텐서** → `forward(*x)`가 1-튜플만 받아 **params[0]만** 사용. 즉 "7-way" 자동가중이 실제로는 **합에 대한 단일
  학습 스칼라로 축소**(항별 σ 미적용). 논문 의도와 코드 구현 불일치 가능. **[확인 필요]**(arXiv 본문 대조).

### 2-4. 평가 지표 (`validation/`, `sample`/`eval_testset.py`) — 로깅/평가 전용, 손실 아님

| 지표 | 방향 | 정의 | 비고 |
|---|---|---|---|
| **FCD / LHCD** (Finger-Contact Dist) | mm ↓ | 누르는 손끝 ↔ 접촉점 유클리드 거리. tip_idx=[16,17,19,18] | 논문=FCD, 코드=LHCD. 최근접손가락 or 사용손가락 특정 두 변형. |
| **BSD / BCD** (Bow-String Dist) | mm ↓ | 보우 ↔ 그을 현의 line-to-line(skew-line) 거리 | 논문=BSD, 코드=BCD. |
| **BF1** (Bowing F1) | ↑ | 모션 검출 bow-change vs **CREPE 오디오** note-change; tolerance=**3프레임=0.1s**, direction match | Kao&Su 2020 방식. precision/recall/f1. |
| **BCS / CS** (Bowing Cosine Sim) | ↑ | frog-bridge 거리벡터(보우 이동량) pred vs gt, half_bow=**0.375m** 오프셋 제거 후 코사인유사도 | 부호=활 상/하반부. |

- **Table 1 어블레이션**(논문 유일 정량표, bold=최고) [논문]:

  | 설정 | FCD ↓ | BSD ↓ | BF1 ↑ | BCS ↑ |
  |---|---|---|---|---|
  | w/o ICL | 18.64 | 25.20 | 0.4332 | 0.6965 |
  | w/ HICL only | **14.56** | 23.98 | 0.4082 | 0.6646 |
  | w/ HICL+BICL | 15.60 | **5.40** | **0.4721** | **0.7515** |

  핵심: **BSD가 BICL 추가로 25.20→5.40mm 급락**(보우-현 상호작용이 큰 이득). FCD는 HICL-only가 최고(14.56),
  BICL 추가 시 15.60로 소폭 회귀. **FID·baseline·물리-RL과의 비교 수치 전무** — 내부 어블레이션뿐(§3-6).
  - **⚠️어블레이션 모델명** `hicl_0_bicl_0 / hicl_1_bicl_0 / hicl_1_bicl_1`(eval_testset.py, train_script 주석)
    → Table 1은 **λ=1**로 학습, 릴리즈 full 모델은 **λ_hicl=2·λ_bicl=3** → **불일치**. **[확인 필요]**.
  - **거리 단위** [확인 필요]: 논문 FCD/BSD는 mm로 보고되나, 코드 좌표계 스케일(m 추정)과의 환산은 미검증.

---

## §3. 환경 (=diffusion 학습셋업)

> **RL 아님을 명확히**: state/action/reward/transition·시뮬레이터·정책/가치망·advantage/critic·멀티크리틱이
> **전혀 없다**. "환경"은 **고정 forward diffusion(cosine, T=1000) + Jukebox 오디오 조건**이고, "학습"은 단일
> denoiser를 **supervised MSE + 기하 손실**로 회귀시키는 것(3~5초 클립 전체를 한 번에, step-wise 보상 아님).

### 3-0. 한 장 요약

MDM/guided-diffusion 코드 기반. **Gaussian DDPM**(T=1000, cosine schedule, **x0 예측**, FIXED_SMALL variance,
MSE). AdamW lr 1e-4·batch 64·~100k step 학습. 추론은 **DDIM-50**. 네트워크 = **PDM**("Performance Diffusion
Model"), arch=`trans_dec_zero`(DiT/adaLN-Zero 트랜스포머 **디코더** + 오디오 cross-attn). 모션 `[B,52,6,T]`
rot6d, 오디오 조건 `[B,T,4800]`, 출력 = 예측 clean x0.

### 3-1. 알고리즘 — Gaussian DDPM (MDM/guided-diffusion 차용 인프라)

| 항목 | 값 | 근거 · 비고 |
|---|---|---|
| 알고리즘 | **Gaussian DDPM** (MDM/guided-diffusion 이식) | gaussian_diffusion.py 헤더 "based on guided-diffusion". **RL 아님**. |
| `diffusion_steps` T | **1000** | parser_util.py:75. |
| noise schedule | **cosine** | parser_util.py:73. `alpha_bar(t)=cos((t+0.008)/1.008·π/2)²`. |
| 예측 대상 | **x0 (START_X)**, ε 아님 | model_util.py "we always predict x_start". training target=x_start. |
| variance | **FIXED_SMALL** (sigma_small=True) | learn_sigma=False. |
| loss type | **MSE** | model_util.py. timestep sampler=Uniform. |
| CFG | 조건 10% 드롭(cond_mask_prob=0.1), `f=(1+w)f_c − w·f_∅` | pdm.py mask_cond. 표준 MDM. |
| 추론 | **DDIM 50-step**(η=0 결정적), clip_denoised=False | generate.py `timestep_respacing='ddim50'`. |
| 장시퀀스 | 5s 세그먼트를 4s overlap **linear 페이드 in-betweening** (train-free) | EDGE/Tseng 방식. postprocess.py. |

### 3-2. 네트워크 (`model/pdm.py`, `model/modules/transformer_modules.py`)

- **PDM**: njoints=52, nfeats=6 → input_feats=**312**. latent_dim=**512**, num_layers=**8**, num_heads=**4**,
  ff_size=**1024**, dropout=**0.1**, activation=gelu. **~55M params** [논문 §4.1].
- **실제 arch = `trans_dec_zero`**(train_script.sh) = DiT-style 트랜스포머 **디코더** + cross-attention +
  **adaLN-Zero** [코드][논문]. (parser 기본 `trans_enc`이나 릴리즈는 trans_dec_zero.) norm_first=True,
  use_rotary=False.
  - **InputProcess**: `Linear(312→512)`(noised motion x_t).
  - **오디오 분기**: `EmbedAudio Linear(4800→512)`+LayerNorm → PositionalEncoding → `cond_encoder`(2× TransformerEncoderLayer) → cond_emb `[T,B,512]`.
  - **Timestep embed**: sinusoidal PE → MLP(512→512, SiLU).
  - **Cross-attn memory** = time token(반복) + cond_emb. **글로벌 adaLN 조건** = to_time_hidden(t) + mean-pool(cond).
  - **seqTransDecoder** = 8× TransformerDecoderLayer(masked self-attn + cross-attn to memory + FFN), 각 서브블록 adaLN 변조(shift/scale/gate).
  - **OutputProcess**: adaLN 변조 + LayerNorm + `Linear(512→312)` → reshape `[B,52,6,T]`.
  - **"zero"** = adaLN-Zero init: 각 디코더층 최종 adaLN linear와 출력 adaLN을 **0-초기화** → 항등에서 출발.
- **차용 vs 고유**: diffusion/·cfg_sampler·fp16_util·respace·resample = MDM/guided-diffusion 인프라 · trans_dec_zero
  FiLM/adaLN 디코더 = EDGE 계열 · jukemirlib/jukebox = 외부. **PDM 모델 정의 + 오디오 경로 + HICL/BICL 손실이
  ELGAR 고유 기여** [논문 Acknowledgements].

### 3-3. 하이퍼파라미터 (train_script.sh + parser_util.py)

| 항목 | 값 | 근거 |
|---|---|---|
| optimizer | **AdamW**, lr=**1e-4**, weight_decay=0, LR anneal 없음 | parser_util.py:134, training_loop.py. |
| `batch_size` | **64** | parser_util.py:68 / 논문 §4.1. |
| `num_steps` | **100000** (ckpt=model000090000.pt; 논문 §4.1="90,000 steps") | train_script.sh. **[확인 필요]** 90k vs 100k. |
| log/save interval | 250 / 10000 | train_script.sh. |
| 손실 λ | rcxyz=1·vel=1·vel_rcxyz=1·accel=0·fc=1 · **hicl=2·bicl=3** | parser_util.py:99-105 + train_script.sh. |
| use_awl | **False** (수동 λ) | parser_util.py:160. |
| fps | **30** | encode.py pose_freq=30·seq_len; generate.py fps=30. |
| guidance_param | 기본 1(=CFG off) | generate.py; 특정 guidance scale은 README/논문 참조 **[확인 필요]**. |
| fp16 | 미사용(use_fp16=False) | training_loop.py. |
| 하드웨어 | **단일 NVIDIA H800** | 논문 §4.1. |

### 3-4. 학습 루프 (`train/training_loop.py`) — RL 대비

- `TrainLoop.run_loop`: 각 (motion, cond) 샘플에 대해 **uniform t 추출 → q_sample로 x_t noise → PDM이 x0 예측
  → `training_losses` → AdamW step**. **env/rollout/reward 없음** — 순수 supervised denoising 회귀.
- rot_mse(rot6d x0) + 기하항(rcxyz/vel_xyz/accel/vel/fc) + HICL/BICL. 기하항은 `enc.rot2xyz` FK로 얻은 xyz에서
  계산. 접촉은 **손실로 부드럽게 유도**되며 물리/충돌로 강제되지 않음 — 출력 사실성은 전적으로 데이터 + 손실에
  의존, **test-time 접촉 solving 부재**.

### 3-5. I/O type · shape

모든 텐서 배치축 `B`(=batch_size, 릴리즈 64). dtype float32.

| 대상 | shape | 내용 |
|---|---|---|
| **모션** x_start/x_t/출력 | `[B, 52, 6, T]` | rot6d. body 21 + LH 15 + RH 15 + bow 1(앞3만). flatten D=312. T=150. |
| **오디오 조건** `y['audio']` | `[B, T, 4800]` | Jukebox layer66 @30fps. (옵션 `y['stft']` `[B,T,2049]`, `y['mel']` `[B,T,512]`) |
| **접촉 앵커** `y['cp_pos']` | `[B,T,1,3]` | 접촉점 xyz. |
| `y['cp_info']` | `[B,T,2]` | 활성현 idx + 진동길이. |
| `y['used_finger']` | `[B,T]` | 손끝 id ∈ {0,1,2,3,-1}. |
| `y['instrument']` | `[B,·,7,3]` (=21) | 정적 첼로 keypoint. |
| `y['mask']` / `y['lengths']` | `[B,1,1,T]` / `[B]` | 유효 프레임. |
| **출력** | `[B,52,6,T]` | 예측 clean x0(rot6d). 하류 SMPL-X/MANO 리타게팅. |

- **관절 인덱싱 주의**(§1-1 반복): 생성 rot6d 순서(body→LH→RH→bow)와 손실 FK xyz 순서(LH 0-20 → RH 21-41 →
  bow frog42/tip43 → body 44-)가 **다르다**. 손실의 손끝 [16,17,19,18]·발 44+·현 [[2,4]…]은 **FK xyz 기준**.

### 3-6. RL 아님 — 명시 대조 (vs learning_env_design.md)

- **MDP 없음**: state/action/reward/transition·시뮬레이터·정책/가치망·advantage/critic 부재. 유일한 학습망 =
  PDM denoiser. "loss" = 전 클립 한 번에 대한 supervised MSE + 기하 정칙화(step-wise 보상 아님).
- "환경" ≈ 고정 forward diffusion(cosine, T=1000) + Jukebox 조건. "규칙/보상" ≈ FK xyz 위의 미분가능 기하 손실
  (rcxyz/vel/fc/**hicl/bicl**). **멀티크리틱·PopArt·GAE·PPO 전무**.
- **비교 미제시**: 논문은 **FID를 부적합**이라 명시(오디오 조건 HICL/BICL가 의도적으로 분포를 데이터에서
  이동시켜 FID를 악화시키되 사실성은 개선)하고, **baseline/물리-RL과의 정량 비교표를 전혀 제공하지 않는다**
  — 오직 자체 4지표 내부 어블레이션(Table 1).

---

## §4. 우리(tab2body)와의 대조

### 4-1. 축별 대조 (축 | ELGAR | 우리 tab2body | 함의)

| 축 | ELGAR | 우리 (tab2body) | 함의 |
|---|---|---|---|
| **물리** | **없음**(kinematic diffusion, 시뮬레이터 X) | **있음**(Isaac Gym + PhysX 완전 동역학) | **우리 노벨티의 핵심 대비축.** 접촉이 손실 근사 ↔ 물리적 귀결 |
| **학습 패러다임** | **conditional diffusion**(supervised denoising, MDP 아님) | **멀티크리틱 PPO**(on-policy RL) + 옵션 AMP | denoiser 1개 ↔ 정책+멀티헤드 크리틱+PopArt |
| **입력 경로** | **오디오 직접**(raw audio→motion, 상징 중간표현 없음) | **탭 경유**(오디오→전사→탭 goal→RL) | ELGAR: 음악지식 불요·end-to-end / 우리: 이산 goal로 물리제어 명세화 |
| **"규칙" 형태** | **손실**(HICL/BICL + MDM 기하손실, FK xyz) | **보상**(per-string 6채널 멀티크리틱 + 종료 −25) | 미분가능 페널티(soft) ↔ step-wise 보상+물리 종료(hard) |
| **접촉 강제 방식** | **soft 기하손실 + 데이터-타임 스냅 + 아치 브리지 기하해킹** | **물리 접촉(force/collision), 시뮬이 관통 원천차단** | ELGAR는 관통/미끄러짐을 **막지 못함**, 우리는 물리로 보장 |
| **악기** | **첼로**(fretless 연속 위치, 정적 11-keypoint 템플릿) | **기타**(이산 프렛, 물리 현/프렛) | 첼로=연속 음정 / 기타=이산 프렛(우리 goal이 프렛-이산) |
| **제어 부위** | **전신 SMPL-X + 양손 + 보우**(root 고정, 앉음) | **전신 SMPL**(act 42/33/75, 몸통+팔+손) | 둘 다 전신. ELGAR는 root/악기 고정, 우리는 물리 reach |
| **압현력/역학** | **binary(눌림/안눌림)**, 힘 없음 | 물리 **압현력·역학 실재** | ELGAR가 못 하는 것 → 우리 기여 |
| **비교/검증** | 내부 어블레이션 4지표(FID·baseline·물리-RL 비교 없음) | 물리 F1 + 물리적 타당성(관통·접촉 실측 가능) | ELGAR는 물리 정확성 입증 불가(구조상) |

### 4-2. ELGAR가 "물리 없이 못 하는 것" → 왜 우리 노벨티인가

ELGAR **저자 스스로 보고한 물리 부재의 대가**(§5 한계) = 정확히 물리-RL이 메우는 공백:

1. **현 접촉 유지 실패**: "BICL를 써도 보우가 종종 현에서 떨어진다"(§5). **soft loss ≠ 접촉 보장** — 물리
   시뮬은 접촉을 상태로 유지한다.
2. **관통 방지 불가**: 인접 현 관통을 **아치 브리지 재구성(데이터 전처리 기하해킹)** + soft loss로만 회피
   (§1-4, Fig 2). **비관통 물리보장 없음** — 물리 시뮬은 강체 충돌로 관통을 원천 차단.
3. **미끄러짐/압현력 부재**: 압력이 **binary**로 단순화, force sensor 없이는 미세압력 불가(§5). 물리는 마찰·
   접촉력이 실재.
4. **역학적 타당성 무보장**: data-driven이라 **물리적 타당성 전반 보장 없음**(§5). 리타게팅도 상호작용 보존
   실패(§1-5).
5. **정적 악기**: 첼로가 움직이지 않음 — 실제 연주의 악기 동역학 없음(§5).

∴ **우리의 "물리 있음"은 ELGAR의 5개 한계를 구조적으로 해결하는 축**이다. ELGAR는 논문에서 물리-RL과의 **정량
비교를 제시하지 않으며(할 수도 없으며)** — 물리적 정확성은 우리 접근만이 주장할 수 있는 영역. (역으로 ELGAR의
강점 = end-to-end 오디오·전신·스타일 다양성·시뮬 불요는 우리가 취하지 않는 축.)

### 4-3. 참고할 만한 ELGAR 요소 (물리축과 무관하게)

- **오디오 유래 접촉점**(CREPE 피치→지판 위치): 우리 탭 전사(Stage1)와 별개지만 오디오→위치 매핑의 선례.
- **접촉을 명시 감독신호로**(cp_pos/used_finger/cp_info를 데이터 앵커로): 우리 **명시 운지**(결정 #12)와 사상적
  으로 유사 — 다만 우리는 손실이 아니라 **goal 관측 + 보상 지정손가락**으로.
- **HICL의 손끝↔접촉점 거리 페널티**: 우리 fret 압점 기하(듀얼스케일 커널)와 목적 동일, **표현이 손실 vs 보상**.
- **다지표 평가**(FCD/BSD/BF1/BCS): 우리 fret F1·strike 평가지표 설계 시 참조 가능(단, 우리는 물리 접촉 실측 추가).

---

## §5. 참고

**경로 접두** `related_work/ELGAR/` 생략. 라인은 조사 시점 기준(재확인 권장).

| 약칭 | 파일 | 주요 라인 |
|---|---|---|
| pdm | `model/pdm.py` | njoints/nfeats/input_feats L21-40 · audio_cond_dim=4800 L52-53 · cond_mask_prob L45 · trans_dec_zero L109-152 · InputProcess/EmbedAudio · OutputProcess · adaLN-Zero init |
| gdiff | `diffusion/gaussian_diffusion.py` | cosine schedule L40-66 · masked_l2 L209-222 · masked_l2_expanded L224 · **training_losses L1282-1800** · rot_mse L1370 · rcxyz L1374-1377 · vel_xyz L1379-1395 · **HICL L1466-1512**(contact L1506·interactive L1510) · **BICL L1566-1663**(bow_contact L1611·frog L1637·tip L1661) · fc L1729-1746 · vel_mse L1749-1756 · AWL 합축소 L1779 · 최종조립 L1788-1795 |
| rot2xyz | `model/rotation2xyz.py` | 관절 슬라이스 L35-40 · root 고정 L69-71 · 손목 chain L78-91 · 보우 재구성 L99-106 |
| parser | `utils/parser_util.py` | batch_size=64 L68 · noise_schedule cosine L73 · diffusion_steps 1000 L75 · sigma_small L77 · lambda_rcxyz L99 · lambda_hicl 2 L103 · lambda_bicl 3 L104 · lambda_fc L105 · num_frames 90 L154 · use_awl False L160 |
| train_sh | `train_script.sh` | arch trans_dec_zero · cond_mode audio · train_mode total · num_steps 100000 · lambda_hicl 2 · lambda_bicl 3 · (주석) 어블 hicl_0/1·bicl_0/1 |
| encode | `audio_encoder/encode.py` | jukebox layer 66 → 4800 · pose_freq=30·seq_len 리샘플 · JUKEBOX_SAMPLE_RATE 44100 |
| dnorm | `data_process/data_normalization.py` | SEQ_LEN/FRAME_RATE L26-28 · kp3d 155 assert L46 · Kabsch align · 40° R2 · 접촉 스냅 · used_finger/cp_info |
| dalign | `data_process/data_alignment.py` | R_of_orientating(R1/R2 TARGET_ANGLE=40°/R3) |
| dseg | `data_process/data_segmentation.py` | instrument='cello' L60 · SEQ_LEN 150·HOP 30 · body/hands 6d · motion.hdf5 기록 |
| postp | `data_process/postprocess.py` | overlap-add stitching · FK · quaternion 부호일관 · 관절레이아웃 L119-121 · 보우 0.75 L85 |
| spd | `data_loaders/string_performance_dataset.py` | 81 clip / 홀드아웃 9 L84-86 · 보우 3→6 패딩 L293-297 · 조건 로딩 |
| collate | `data_loaders/get_spd_data.py` | model_kwargs['y'] 조립(cp_pos/cp_info/used_finger/instrument) |
| val | `validation/{validation,eval_testset,freq_position,pitch_detect}.py` | LHCD/BCD/BF1/BCS · CREPE 피치·freq2position · 어블 모델명 hicl_x_bicl_x |
| generate | `sample/generate.py` | ddim50 · fps=30 · max_frames=150 · CFG wrapper |
| awl | `utils/AutomaticWeightedLoss.py` | uncertainty weighting σ · (단일합 축소 이슈는 gdiff L1779) |

**논문**: `docs/Elgar.pdf`(Qiu et al., SIGGRAPH Conf. Papers 2025, arXiv 2505.04203). 문제·오디오선택·첼로선택 §1 /
관련연구(supervised GAN vs 물리-RL 비판) §2.2 / 모션표현 R³⁰⁹·데이터 파이프라인·아치브리지 §3.1 / diffusion §4.1 /
ICL(HICL Eq6·BICL Eq7)·기하손실 Eq5·총손실 Eq8 §3.3 / 4지표·Table 1 어블레이션 §4.2 / **한계(보우 접촉실패·binary
압력·정적악기·관통·리타게팅·물리보장 없음) §5-6**.

**미해결(코드/논문 대조 필요)**: ① 논문 R³⁰⁹ vs 코드 D=312(보우 3→6 패딩) · ② Table 1 어블 λ=1 vs 릴리즈 2/3
불일치 · ③ AWL 7-way 의도 vs 코드 단일합 축소(L1779) · ④ FCD/BSD 거리단위 mm vs 코드 좌표 스케일 · ⑤ 논문
§3.1 보우 frog "왼손" anchoring = 오른손 오타 추정(첼로 활은 오른손) · ⑥ 90k vs 100k step · ⑦ num_frames 90 vs
SEQ_LEN 150 · ⑧ 첼로 외 악기 일반성(전 코드 cello 하드코딩) · ⑨ cp_pos/used_finger가 mocap GT인지 오디오추론인지
· ⑩ 잔여 global body translation 완전 부재 여부(root orient 고정은 확정).
