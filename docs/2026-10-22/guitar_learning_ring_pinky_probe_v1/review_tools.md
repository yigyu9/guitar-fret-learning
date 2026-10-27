# 약지·소지 반전 도구 독립 검수

요약 판정: **문제없음 — 정적 계약 및 CPU 검사 범위 PASS.** 실제 GPU 관절 움직임·접촉·복귀 결과나 렌더 완료를 이 문서로 인증하지 않는다.

## 범위와 원문

읽기 대상은 새 phase의 `probe.py` / `test_probe.py`, `render_probe.py` / `test_render_probe.py`, root의 `analyze_probe.py`다. 활성 소스나 도구는 수정하지 않았다. GPU·Isaac context·MuJoCo·GL·렌더 main·실제 분석 main은 실행하지 않았다.

| 파일 | 검수한 SHA256 |
| --- | --- |
| probe.py | fbe9cf460b8fa793b7022a93254e2412d124ca70c8aa0976a4abb2f534c8425d |
| test_probe.py | 63be95c289799edc32aa2d6de34399e55b49f73fd95aad701e25fde1de38770f |
| render_probe.py | 15e4773c6e520b2d3429a622a843cb139eb4dede82ab3be93c725e9841fcc920 |
| test_render_probe.py | d75eeb7df993f15c3e9fce032058d9686c4b90574da6956fa836ab7e4a0d0a42 |
| analyze_probe.py | 6b748920744cf91bd1984a9ec5dab2c25b029478abe65e89b805054951a560f0 |

새 CPU 프로세스에서 CUDA를 숨겨 probe **6개 검사 PASS(0.014초)**, renderer의 순수 CPU **3개 검사 PASS**를 확인했다. 다섯 파일의 Python3.8 AST가 통과했다. 이전 press phase의 봉인 **881개 파일 / 788,097,551바이트** 및 지정 manifest SHA를 읽기 검증했고 활성 Python **435개** SHA도 원문 그대로다.

## 제어·안전·기록 계약

- 각 variant는 새 N18 pool을 사용한다. prepared는 prefix0, learned10은 실제 최종100회 결정 정책으로 **600 control tick**을 진행한다. 원 체크포인트를 strict load하며 모델·curriculum3331·PPO update100을 복원하고, 진단 중 PPO 학습/단계 진급은 없다.
- 8축×양·음 방향16행은 **0.2rad/s 1초 → 목표 유지0.5초 → 원래 목표 방향 최대0.2rad/s 1초 → 유지0.5초**다. LH21 누적식 4/60과 native clamp를 그대로 쓰며 현재 q를 덮어쓰지 않는다. 나머지 LH축은 action0이다.
- 비LH absolute18은 prefix 끝 target을 기존 비대칭 affine codec으로 역변환해 일정한 행동으로 제출한다. 단순 action0으로 초기 reference에 돌아가는 confound를 피한다. 제출된 비시험 active 목표의 실제 오차와 시험축 누적식 readback을 각각 검사한다.
- row16은 목표 유지 대조, row17은 8축을 준비 target 방향으로 최대0.2rad/s 동안3초 이동한다. 후자는 최대0.6rad의 제한 이동이며 모든 준비 target까지 도달한다고 주장하지 않는다. pulse의 native 한계에서 잘린 실제 target 변위를 계산하고 무여유 요청과 물리 추종 부족을 구분한다.
- 기존 pool의 안전·종료·PD·effort·관절 범위·물리·접촉 판정을 사용한다. 어느 행이든 첫 종료하면 해당 variant 전체를 멈추고 다른 행을 right-censored로 남긴다. finished flag 변경이나 종료 후 선택 reset으로 검사를 이어가지 않는다. 진단 정상 종료와 3초 schedule 완료도 별도 필드다.
- 60Hz는 t0와 모든 control 끝점의106body/q/qd/target105/action39/clock/segment다. 240Hz는 전체18행의 q/qd/target105 및 실제 native68 몸체 접촉 합력 norm을 기록한다. 4단계 target 일정·두 기록의 끝점 bitexact·개별 clock/global clock·유한성·quaternion 검사가 있다. 물리1부터 기록해 prefix600과 이후180tick의 경계가 정합한다.
- 네이티브 import 이전에 과거 봉인/현재 입력을 확인하고 완료 뒤 다시 확인한다. 종료/예외·cleanup·변경 입력·누락 import pin·native close를 결과에 남기며 원자료를 별도 새 출력에 쓴다. 실제 실패 또는 조기 종료가 있으면 정상3초 반전 성공으로 덮지 않는다.

## 도구 사이 정합성

probe가 쓰는 metadata의 cases/axes/native body names/시험 action·native indices/start target/prefix/native capture/path/SHA와 renderer·analyzer의 소비 키가 일치한다.

renderer는 각 조건의 실제 시작 target과 native 여유로 ring2/pinky1_z/pinky3의 한 방향씩을 선택하고 항상 coordinated17을 포함한다. 방향 선택에 q 움직임·하중·성공 결과를 쓰지 않는다. schedule 완료 및 정상 close 증거가 있어야 하며 **180끝점×4 = 720프레임/12초**만 원래 cadence로 연결한다. prefix/t0는 사진에서 제외하되 원 시각을 표시한다. 원106body 자세·원 메시·6현을 사용하고 새 물리나 보간은 없다. 기존 static-visual의 매프레임1e-9 pose/time0 guard 및 renderer 전후 상태 불변 검사, 고정 카메라의 전체 손/넥 bounds와 자막 여백 projection 검사도 유지한다. 실제 GL에서의 성공은 앞으로 확인할 사항이다.

analyzer는 native 한계로 잘린 실제 pulse target 변위를 분모로 두며 p90의 유지 후 q, p180의 복귀 후 q와 hold row의 대응 움직임을 분리한다. hold-row 보정은 고정 ID 사이의 기술적 비교이며 인과 인증이 아니다. prefix 이후 native force 구간은 push240 / hold120 / return240 / posthold120 표본으로 맞는다. 마지막 속도 RMS는 **posthold 마지막0.1초**임을 수정된 필드명이 명시한다. 모든 경우를 자동으로 '끼임'으로 분류하지 않는다.

## 한계와 종료

Critical / 수정이 필요한 Warning: 없음. 실제 q가 pulse 방향으로 충분히 움직이는지, 원래 목표로 돌아오는지, target 여유가 있었는데도 추종하지 못하는지 및 native 합력의 변화는 root가 실행한 원자료에서 별도로 판단해야 한다. 고정 환경 ID·prefix 후 물리 차이·한 속도/짧은 pulse의 범위를 유지하고 native net norm을 충돌 상대·접촉 witness·압력·관절 반력으로 해석하지 않는다. 반전이 가능해도 모든 자세의 끼임 부재 또는 학습 개선을 증명하지 않는다.

이 검수 문서만 새로 작성했으며 작성 종료했다.
