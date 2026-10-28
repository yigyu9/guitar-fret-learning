# 2초 전에 남은 하중이 이미 있었는가 — 기존 raw 후속 확인

전체128 첫 시도의 source와 증분 억제 조건은 첫480 물리 endpoint 모든30필드가 exact다. 아래 힘은 body resultant이며 접촉쌍 압력이 아니다. 추가 제어 구현·GPU 실행은 하지 않았다.

| 관찰 | 전체128 분포 |
|---|---|
| 최초 norm≥0.01N loaded | clock413~422, 1.72083~1.75833s; 중앙1.74583s |
| 최초 signed press-normal>0.01N | norm-loaded와 모든 환경에서 같은 clock |
| 최초 원래 candidate | 1.73750~2.01250s; 중앙1.75000s |
| clock480/2s 중지 합력 | min17.52 / p5031.98 / p9533.91 / max55.38N |
| 같은 시각 고정Jn·(old target−q) | p50−30.683 / p95−23.992mm;128/128 음수 |
| 증분 억제 뒤 audible 환경별 중지 힘 중앙값 | 환경간 p5030.24 / p9534.25N |
| 환경별 audible 중앙값 ÷ 그 환경 clock480 힘 | p500.9770 / p951.5037; 범위0.5493~1.7054 |

**증분 억제를 시작하기 전 이미 모든 환경에 상당한 하중과 안쪽 선형 target 오차가 있었다.** 개입 직전 힘 중앙31.98N과 이후 음 구간 약30N은 비슷한 수준이며, 기존 preload가 남았다는 가설과 부합한다. 다만 환경별 힘이 같은 상수로 유지된 것은 아니다. 환경별 audible 중앙값−clock480 힘의 차이는 중앙−0.748N, 범위−24.96~+12.36N이다. 자세/J/접선운동과 팔 feedback이 달라졌으므로 이것만으로 잔류30N의 원인이 오직 초기 누적오차라고 확정할 수 없다. Jn의 mm는 국소 선형 외삽이며 실제 침투깊이가 아니다.

고정 material sample은 source clock480의 실제 nearest sample이다. global index(중지 local index는128을 뺌)는 **135:5,157:22,166:5,186:9,187:56,196:6,197:20,198:5환경**의8종이다.128개 전부 원래 raw와 exact 일치한다. 이 고정점이 더 이른 최초 접촉의 any-candidate witness였다는 증거는 아니다. candidate 첫시각이 loaded보다 늦은 환경도 있으므로 최초 body-load를 실제 목표현 압현으로 부르면 안 된다.

## 최소 후속 제안 — 아직 구현/실행하지 않음

기존 `no_new_inward` 수학·tape·고정 source material point·PD/범위·기존0.01N signed gate·팔 teacher를 그대로 두고, **clock≥480 제한만 제거하여 최초 유효 loaded control snapshot부터** 같은 증분 억제를 허용하는 단일 timing 조건은 원인 분리에 타당하다. 네 physics endpoint 중간에 target을 바꾸지 않고 다음60Hz 경계에서만 적용한다. 첫 load 전 원본 exact와 첫 override 시각을 검증하고, 이후에도 현재 signed load·first attempt·실패/reset/finite gate를 그대로 만족한 행만 작동시킨다. 최초 하중을 과거 source clock으로 강제 예약하거나 candidate/force 기준을 새로 완화하지 않는다.

원래 무개입·2초부터 증분 억제 결과를 대조군으로 재사용할 수 있지만, 새 timing 조건도 같은 source/strict checkpoint/tape의 무개입 prefix exact를 확인해야 한다. 하중·target 오차가 더 낮아지고 성공이 유지되면 더 이른 누적 억제 가설을 지지한다. 하중 감소 없이 성공만 사라지거나 비슷한 잔류 하중이면 단순히 시작시각만으로 해결된다는 설명은 약해진다. 실패128분모·실패 endpoint censor·접선변경·teacher 요청차·동일 고정점 J 속도잔차를 함께 비교해야 한다.

초기 접촉은 clock480에서 선택한 material point와 다른 점일 수 있고 손가락 자세/접촉 강성/엄지035/teacher 반응도 섞인다. 따라서 이 단일 시점 진단은 작은 가설 검사이며 실제 자유 손 압현 개선이나 생산 controller 채택 근거로 확대할 수 없다. 추가 누적오차 완화·force cap·보상 변경을 섞지 않는다. 세부 per-env clock·분위수·6입력 SHA는 preload_followup.json이다.
