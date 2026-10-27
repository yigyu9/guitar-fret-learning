# 엄지 안내 후면과 실제 넥 source geometry 대조

**현재 안내 후면이 OBJ의 face가 정의하는 playing neck1 후면과 다른 것은 확인됐다.** 현곡67개 안내 중심에서 안내면은 실제 source face 후면보다 **3.371–5.463mm 뒤**다. 기존 고정 witness는 안내 hull 기준0.300mm 안쪽이지만, 실제 neck1의 유한 삼각형까지는 **5.146mm 떨어져 있다**. 따라서 기존 “기하적으로 매우 가까운데 힘0”을 설명할 구체적인 좌표 원인 후보다.

다만 **PhysX가 최종 생성한 cooked collision hull 자체와의 불일치는 아직 확정하지 않았다.** 저장된 readback에 cooked vertex·face·shape local pose가 없기 때문이다. 이번 작업은 CPU 읽기·기하 계산뿐이며 GPU를 재실행하거나 활성 파일·자산·기존 결과를 수정하지 않았다. 수치와640개 입력 SHA는 [geometry_summary.json](geometry_summary.json)에 있다.

## 1. 서로 다른 꼭짓점 집합으로 만든 후면

[현재 후면 추출 함수](/home/ajou/yigyu/3/guitar_learning/gpu/episode_diagnostics.py:44)는 compound XML에서 physical `guitar_neck1/2` geom을 찾고, OBJ의 **모든 `v` 행**으로 각각 `ConvexHull`을 만든다. OBJ의 `f`가 참조하는 vertex만 고르지 않는다. 두 OBJ에 같은12개 vertex 목록이 있고 실제 face 참조 집합만 다르기 때문에, 현재 함수는 두 mesh 모두에 대해 합쳐진 긴 경사 후면을 만든다.

| source mesh | 실제 face 참조 vertex(1기반) | 미참조 vertex | 유한 Gy 범위(m) | 실제 face-only 후면 |
| --- | --- | --- | --- | --- |
| [neck1](/home/ajou/yigyu/3/guitar_learning/assets/tab2body/assets/mesh/guitar_neck1.obj) | 1–8 | 9–12 | −0.241803…0.217197 | `z=−0.008`, outward normal `(0,0,−1)` |
| [neck2 전환부](/home/ajou/yigyu/3/guitar_learning/assets/tab2body/assets/mesh/guitar_neck2.obj) | 1–4,9–12 | 5–8 | 0.217197…0.255333 | `−0.224286515099*y −0.974523247103*z +0.040918172243=0` |

현재 all-vertex 후면은 `−0.017652377636*y −0.999844184643*z −0.012267151347=0`이다. neck1 후면과 법선 방향은 약1.011° 차이라 뒤집힌 법선은 아니다. 중요한 차이는 playing neck 구간의 **평면 위치**다. neck2 평면을 그 유한 범위 밖으로 연장해 neck1 영역의 접촉면으로 취급하지 않았다.

## 2. compound 자산·좌표·엄지 오프셋

[현재 실제 로드 자산](/home/ajou/yigyu/3/guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml)은 위 두 OBJ를 physical mesh로 참조한다. 각 mesh scale은 `(1,1,1)`, geom translation은0, quaternion은 identity다. 원래 guitar source XML도 같은 파일·같은 변환을 사용한다. visual-only 중복 geom은 collision에서 제외했다. manifest의 논리 root offset은0이고 회전도 identity 수준이므로, 이번5mm 차이를 compound root의 추가 회전·이동으로 설명할 근거는 없다.

[manifest](/home/ajou/yigyu/3/guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json)의 physical body1개·collision shape89개, mass/COM/inertia·uniform scalar shape 속성 검증은 **cooked neck hull의 vertex 좌표 검증과 별개**다. 기존 두 thumb probe의 `diagnostic_guitar_mode`는 null이며 원래 자유 기타 장면이었다. 해당 결과에는 cooked neck geometry나 개별 shape local pose readback이 없다. 이번에는 장면을 바꾸지 않았다.

[엄지 표면 로더](/home/ajou/yigyu/3/guitar_learning/gpu/thumb_support.py:40)는 실제 loaded human XML의 `LH:thumb3` mesh를 읽는다. scale `(1,.95,.95)`와 geom offset `(-.00825,0,0)m`를 먼저 적용하고 body-local128개 점·normal을 만든다. 환경은 이 점을 thumb3 body pose로 world에 옮긴 뒤 live guitar root 기준으로 바꾼다. geom offset을 두 번 더하거나 source G와 world를 섞은 흔적은 확인되지 않았다. native point Jacobian 계산에서 COM offset을 빼는 것과 표면 위치의 body-origin 변환도 구분돼 있다.

안내는 source rear 중앙50% 폭·guide center Gy±40mm이다. gap0…3mm에서 거리 품질이 최대이고, candidate는 동일 점의 gap−1…+0.5mm·영역 안·facing≥.1·thumb3 rear-normal resultant≥.01N을 요구한다. 실제 shape readback의 contact offset은 엄지와 기타 각각 약0.1mm, rest/thickness는0이다. 이 scalar margin은5mm 차이를 없앤다는 근거가 아니다.

`G:thumb_support_proxy`와 `G:pluck_range`는 visual·질량만 유지하고 collision을 끈 의도적 구성이다. 그 proxy가 없다는 사실을 오류로 판단하지 않았으며, 위 비교는 실제 physical neck mesh를 대상으로 했다.

## 3. 기존 witness를 유한 면·hull 양쪽에서 확인

[기존 witness63](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/01_control/thumb/limited_rear_probe/witness_last_check.json)의 G 좌표는 `(0.0074706152,0.0666800961,−0.0131462105)m`다.

| 검사 | 결과 |
| --- | ---: |
| 현재 all-v hull의 최대 halfspace | −0.300052mm, 내부 |
| face-only neck1 hull의 최대 halfspace | +5.146210mm, 외부 |
| neck1 유한 삼각형까지 최단거리 | 5.146210mm |
| neck1의 실제 최근접 점 | 같은 Gx/Gy, `Gz=−0.008m` |
| neck2 유한 삼각형까지 최단거리 | 150.604853mm |
| witness에서 현재 안내 평면의 실제 투영점 | `(0.0074706152,0.0666747995,−0.0134462152)m` |
| 그 안내 투영점과 neck1 후면의 차이 | 5.446215mm |

따라서 이 witness의 차이는 AABB만 보거나 무한 평면의 잘못된 연장으로 생긴 판단이 아니다. 실제 face 삼각형의 최근접 점과 convex halfspace를 함께 검사했다. 기존 source-hull 내부 판정은 all-v 집합에 대해서는 맞았지만 **face-referenced source hull의 내부 판정으로 확대할 수 없다**.

기존 제한15초·후속20초 probe의 selected 기하 품질1·thumb3 resultant0·normal load0·candidate0은 그대로 신뢰한다. selected point와 고정 제어 witness63은 다른 점일 수 있다. 이번 확인만으로 cooked hull 오류·전체 엄지 범위의 도달 불가능성·접촉 쌍을 확정하지 않는다.

## 4. 현곡67음과 neck1만 선택할 때의 범위

현재 hand-position track1622행의 `allowed_fret_range` 외곽 cell 경계 midpoint로 work center를 계산하고, 각 원래 음 onset에서 실제 안내식과 같은 선형 보간을 적용했다. 물리 trace를 재생하거나 전체 과거 로그를 다시 계산하지 않았다.

| 범위 확인 | 결과 |
| --- | ---: |
| 67음의 guide center Gy | −0.050887…0.067640m |
| 각 center±40mm 영역의 합집합 | −0.090887…0.107640m |
| center가 neck1에 포함 | 67/67 |
| ±40mm 전체 영역도 neck1에 포함 | 67/67 |
| center가 neck2 전환부에 포함 | 0/67 |
| 전체1622행 center의 최소·최대 | 위67음 범위와 동일 |

현재 곡·현재 guide track에서는 실제 neck1 rear만 선택해도 요청 Gy 범위를 빠뜨리지 않는다. 다른 곡이나 neck2까지 안내하는 일반 계약의 동등성은 별도다. 음별 ID·시각·center·coverage는 JSON에 보존했다.

## 5. 힘을 읽는 body가 마커인가

[환경](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:537)과 기존 probe는 **`human/LH:thumb3`**의 native net force를 읽는다. [scene 복사 경로](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:333)는 human prefix를 그대로 전달한다. thumb3를 collision 없는 marker로 잘못 인덱싱한 근거는 없다.

| body | 기존 native shape 수 | 기타 collision | 현재 하중에 포함 |
| --- | ---: | --- | --- |
| thumb1 | 1 | enabled | 아니오 |
| thumb2 | 1 | enabled | 아니오 |
| thumb3 | 1 | enabled | 예 |
| thumb_pad | 1 capsule | filter로 disabled | 아니오 |
| thumb_top | 0 | shape 없음 | 아니오 |

source와 [기존 실제 readback](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/teacher_fixed_B/human_shape_and_force_readback.json)이 일치한다. 다른 엄지 마디가 닿는 상황은 현재 thumb3 candidate에 합산되지 않는다. 이는 현재 계측 정의이며, 기존 probe에서 thumb1/2 접촉이 실제 있었다는 주장은 아니다. resultant 자체도 특정 thumb-neck 접촉 쌍이나 압력 인증은 아니다.

## 6. 최소 수정 후보와 다음 native A/B 검사안

아래는 **제안이며 이번 작업에서 구현·적용하지 않았다**.

1. OBJ face index가 참조하는 vertex만 사용해 hull을 만든다. 동시에 current playing neck 범위를 명시적으로 선택해야 한다. neck1·neck2를 face-only로 바꾸면 두 rear plane이 달라져 기존 `common source rear neck plane` 검사가 실패한다. 단순히 vertex filter 한 줄만 고치면 충분하지 않다.
2. 현곡의 최소 후보는 physical **neck1 face-only rear**를 선택하는 것이다. guitar G 좌표·미터·outward−Gz 부호·반환 tuple/array shape·유한 trapezoid와 helper 판정식은 유지한다. bounds는 실제 neck1의 source 범위를 쓴다. 위 coverage 때문에 현곡 요청 영역은 빠지지 않는다. neck2까지 계속 지원해야 한다면 단일 plane을 억지로 연장하지 말고 별도의 piecewise 유한 면 계약이 필요하다.
3. root GPU 인계 후 docs-only wrapper에서 기존 probe를 재사용해 **현행 안내 A / face-only neck1 안내 B**를 별도 새 출력으로 비교한다. active 파일·OBJ·물리 asset은 그대로 두고, wrapper의 안내 geometry 입력만 바꿔 condition·source SHA·실제 rear vertices/plane을 봉인한다. 새 A/B 양쪽은 같은 **고정 기타**·035 초기 상태·엄지5축·±15°·tick0.5°·기존 codec/PD/힘 상한·2N 보호·후보 문턱·900제어틱·원래−0.3mm 깊이 스케줄을 사용한다. 과거 두 probe는 자유 기타였으므로 새 고정 기타 A/B와 같은 조건의 표본으로 합치지 않는다. 본 검사는 아직 실행하지 않았다.
4. 실제 현재/고정 witness의 G점·유한 face 투영·signed gap·region excess·facing·native thumb3 force와 rear-normal load·candidate를240Hz로 남긴다. 제어 witness/selected sample ID도 기록한다. 동일 알고리즘이라도 geometry가 달라지면 선택 sample과 궤적은 달라질 수 있다. thumb1/2 힘은 읽기 전용 보조 자료로 구분하고 기존 candidate에 합산하지 않는다.
5. 실제 최초 접촉→유지→해제→재접촉과 source projection의 정합을 확인한 뒤 채택 여부를 판단한다. 힘이나 가동범위·보상 가중치를 바꿔 성공을 만들지 않는다. 실패하면 cooked neck·thumb3 hull의 vertex/face·각 shape local pose·실제 importer의 미참조 vertex 처리 또는 접촉 상대 자료가 더 필요하다.

현재 확보한 것은 **source face와 안내의 좌표 불일치 및 body 계측 경로 확인**이다. 실제 native 접촉면 정합과 접촉 프로토콜 통과는 다음 단계의 측정 대상이다.
