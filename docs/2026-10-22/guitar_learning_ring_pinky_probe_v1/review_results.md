# 약지·소지 실제 반전 결과 독립 검수

요약 판정: **문제없음 — 실제 기록·분석·영상의 검수 범위 PASS.** 두 자세에서 제한된 반전 움직임은 확인되지만 모든 자세의 끼임 부재, 완벽한 추종 또는 접촉 원인의 확정은 아니다.

## 범위와 방법

실제 `native_run`의 36개 case NPZ, 2개 native240 NPZ, metadata/계약/report/입력 pins, `analysis.json`, `prefix_comparison.json`, 정상 종료 로그·프로세스 결과를 CPU로 읽었다. 별도 코드로 시계·행동·목표·실제 q·힘 구간과 주요 분석 수치를 재검산했다. learned10 영상 v1의 MP4·보고서·presentation·전체 pose audit·입력 pins도 읽고 독립 CPU ffprobe를 수행했다. GPU·native physics·GL·렌더·기존 분석 main은 실행하지 않았으며 이 새 검수 문서 외 파일은 수정하지 않았다.

## 실행·무결성

- 실제 prepared는 **180 control tick / 720 physical step**, learned10은 **600 정책 prefix + 180 검사 tick / 3,120 physical step**이다. 각 N18의 3초 검사 구간이 끝났고 종료 episode는 0, native simulator 두 개는 각각 정상 닫혔다. variant마다 reset은 초기 1회뿐이며 실제 GDB inferior 정상 종료와 exit 0이 기록과 일치한다.
- 두 variant 각각 **1,463개 pin**, 분석의 **1,508개 입력 SHA**가 현재 파일과 일치한다. 원 source435 및 이전 press phase 881개 봉인을 포함한 입력은 변경되지 않았다. source checkpoint100·strict 계약 및 PPO0/model/curriculum3331 불변은 동결 실행 도구의 검사와 실제 report에 근거한다. 원 NPZ에 전체 모델 tensor가 없으므로 모델 불변 자체를 NPZ만으로 재입증했다고 주장하지 않는다.
- 전체 36개 case의 유한값·shape·60Hz clock/global clock, 실제 native240 q/qd/target 끝점과의 bitexact 대응 및 control 안 target 일정성을 직접 확인했다. 원시 force norm은 **native68** 몸체이며 논리106 marker에 힘을 나눠 기록하지 않았다.
- prefix 행동은 실제 raw policy action과 같고, 검사 구간 raw-policy sentinel은0이다. 각 case의 39개 제출 행동에서 비시험 LH축0·absolute18의 일정한 역변환 행동·허용된 시험축만의 움직임이 맞는다. 해당 역변환이 prefix 끝 목표를 재생성하며, 비시험 active 목표 유지 오차는0이다. 시험8축의 float32 `clip(previous+4*action/60,native bounds)`와 기록 target도 전 step에서 bitexact다.
- pulse/hold/return/posthold의60Hz 경계와240Hz 힘 구간 240/120/240/120개가 정합한다. 원래 target으로의 복귀 오차와 clipped pulse 예상 변위가 허용오차 안이고, actual q는 target과 별도로 측정됐다. native 한계 때문에 실제 target 이동이 없거나 작은 방향을 물리적으로 막힌 사례로 분류하지 않는다.

## 실제 움직임 및 힘

아래 실제 q 변화는 pulse 1초 뒤 **0.5초 유지까지 지난 검사1.5초 endpoint**를 시작 endpoint와 비교했다. 복귀 q 변화는 검사3초 endpoint 기준이다. 단위는 rad다.

| 조건·행 | 허용 target 변화 | 실제 q 변화(1.5초) | 실제 q 복귀 후 시작 대비(3초) |
| --- | ---: | ---: | ---: |
| prepared ring2, case5 | −0.19999981 | −0.19960892 | −0.00035393 |
| learned10 ring2, case5 | −0.19999981 | −0.19958043 | −0.00032473 |
| prepared pinky1_z, case10 | +0.19999990 | +0.10077648 | +0.00030236 |
| learned10 pinky1_z, case10 | +0.19999981 | +0.13981813 | −0.00395811 |

분석에서 실제 target 이동0.05rad 이상으로 표시한 방향은 각 자세16개 pulse 중12개이며, 그12개 모두 실제 q 변화가 target 변화와 같은 방향이다. 나머지 방향은 작은 native 여유·무여유 사례로 따로 봐야 한다. 0.05rad는 이 진단의 이동량 구분값이며 보편적 끼임 판정 문턱이 아니다.

learned10 case10의 pinky3 몸체 합력 norm은 이동 전 마지막0.5초에 양성이었고, 유지 구간의 실제 **240Hz 120표본 모두0**이었다. 복귀1초 구간에는 다시 양성인 표본이 있으며 posthold0.5초는 전부0.01N 이상이다. 반면 hold 대조 row16에서는 해당 몸체 norm이 계속 양성이다. 직접 재계산한 최대·평균·0.01N 이상 시간은 모든 분석 구간 값과 일치한다.

이 변화는 소지 기저축 방향 요청으로 실제 움직임과 합력 변화가 생겼다는 국소 증거다. **net norm0은 모든 접촉쌍이 없다는 증거가 아니며**, 서로 상쇄되는 접촉이나 상대 몸체·접촉 witness·압력은 이 기록으로 알 수 없다. 합력 감소가 운동을 일으켰는지, 운동이 하중을 바꿨는지도 확정하지 않는다.

소지1_z의 이동비율은 절대 target 추종오차와 구분해야 한다. learned10 case10은 시작부터 `q−target≈+0.09682rad`였고 유지 끝에는 `q−target≈+0.03664rad`다. 따라서 실제 이동량이 target 변화의 약69.9%라는 사실만으로 유지 끝에 목표에 못 미쳤다고 말할 수 없다. prepared 같은 방향은 유지 끝 `q−target≈−0.09922rad`여서 상당한 추종 오차가 실제로 남는다. 현 gain/관절 결합·기하 등 원인은 분리되지 않았으며 완벽한 운동을 인증하지 않는다.

coordinated row17은 제한3초 안에 기록된8개 **target**을 준비 reference까지 돌렸지만 실제 q/body를 준비 상태로 덮어쓰지 않았다. target 복귀와 실제 자세의 완전 복원을 혼동하지 않는다.

## 정책10초 자세와 이전 영상의 차이

prefix 비교의 입력 SHA 및 실제 frame600을 독립 대조했다. N18 hold row16과 이전 N1024 env0 사이 최대 차이는 q105 **0.00080967rad**, 시험8축 q **0.00021756rad**, target105 **0.00086945rad**, body106 위치 **0.000215803m**다. 이번18개 행끼리도 시작 q 최대 차이가 약0.00183rad다. 같은 checkpoint와 같은10초 곡 시각이지만 동일한 물리 상태·동일 반사실 궤적은 아니다. 고정 case ID·작은 행별 prefix 차이·한 속도와 두 국소 자세라는 범위를 유지한다.

## 실제 영상과 추가 closeup 도구

검수한 v1 `learned10_video`는 사전 native 여유 규칙으로 고른 case **5/10/14/17**의 실제3초씩을 연결한다. 600tick prefix를 화면에서 생략하고 원 시각은 남긴다. 원자료를 좋은 운동 결과로 다시 선택하거나 보간하지 않는다.

직접 재검산한 영상 입력 **1,487개 SHA**와 MP4 SHA가 맞는다. 독립 ffprobe는 **1280×720 / 60fps / 720프레임 / 12.000000초**다. 전체720개 pose audit 행의 clip/case/source frame/source clock이 정합하고 position/rotation 오차는1e-9 이내, 새 물리0·렌더러 시계0·화면 projection guard도 통과했다. 시각적 가독성 판단은 root의 preview QA 범위이며 이 검수에서 GL을 생성하지 않았다.

새 `render_probe_closeup_v2.py` SHA `956cc1acdedeff2eadfaeaa5a3d174c0cea99f2957978c536c3ad8f7a9427e3c`의 diff도 읽었다. v1 대비 LH geom만 camera fit/projection 범위에 넣고 neck 존재 검사는 전체 model로 분리하며 관련 문구를 바꾼 변경이다. source pose/시계/선택/720프레임/0time guard는 같다. 정적 blocker는 없지만 **v2 실제 렌더 완료는 이 검수 범위에 포함하지 않는다.**

## 판정과 종료

Critical / 수정이 필요한 Warning: 없음. 현 기록은 시험한 약지·소지의 허용 방향에서 반전·복귀 움직임이 가능함을 뒷받침하며, 관절이 완전히 고정되어 전혀 움직이지 못한다는 설명과 맞지 않는다. 모든 축의 완전 추종·모든 자세에서 끼임 없음·정확한 접촉 상대·학습 향상이나 장기 수렴은 별도 문제다.

- `analysis.json` SHA256: `31214cf084a2fa543fb3acf1a6817f646a0efbd9dc049b89256dd356c2f50a8a`
- `prefix_comparison.json` SHA256: `251f20d4778849c7bd0d1af42e160d41836444dcc02cd17f70284bf888115464`

이 검수 문서만 작성했으며 작성 종료했다.
