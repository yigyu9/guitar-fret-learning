# Root 검증 기록

## 실제 영상 QA와 실행 범위

Root는 실제 Isaac Gym hands의0초/5초 PNG와 whole_body의0초 PNG를 직접 열었다.
배치·기타·양손·고정 하체와 주황 strap 경로가 표시된다. 주황 실선은 보이는 실제
route, 옅은 점선은 scene geometry 뒤로 가려진 route다. 천 strap mesh를 추가한 영상이 아니다.
Source witness 그림을 native 렌더로 대체하지 않았다.

새 actual은 한 초기화/1200step이고 각 카메라151frame이다. 녹화가 멈춘 정지화면으로
5초를 채운 것이 아니다. 저장 trace/states는0~1200, controls/contacts는1~1200이며
capture는0~1200을8step마다 저장한다. 모든604 원/표시PNG SHA와 렌더 read-only 검사가
분석16checks에 포함된다. MP4는 끝 장면 포함151/30≈5.033333초다.

Fresh native t0의14checks와 all native-allowed graph>2 및 same-left 비인접1188쌍 source
교차0을 확인했다. 같은 왼손110쌍을 포함한다. Source screen은 cooked penetration 인증이 아니다.
CUDA context/visual geom/articulation warning은 실행 로그에 원문 보존했다.
이번 실행은 CPU PhysX의1200step 완료·실제PNG·종료코드0으로 확인했다.

## 판정과 비교 한계

새 초기18각 및 그에 대응하는 PD 유지 목표만 바뀌었고 원33offset은 유지한다.
기타 초기 body state·LA·PD/물리·목표파형은 기준과 같고 held63목표는1200행 exact다.
초기 route 길이는 Thorax 초기 변경으로 달라졌으므로 같은 것으로 설명하지 않는다.

Palm source 거리 상한 감소와 실제 palm 양의 raw lambda0을 구분한다.
최대 초기 G오차와2초 기준 후기 변화가 모두 소폭 늘어 새 초기각을 채택하지 않는다.
2초는 분석 구간이며 연주 전 대기나 WAIT 순서의 필수 조건이 아니다.
Raw contact lambda를 N으로 표시하지 않는다. Cable 장력은 재구성한 제출 법칙값이다.
Wrist fit은 actual scalar q−원 static baseline의2~5초 constant/trend/1Hz 성분이며
관절 bone 회전량 또는 새 초기조건을 제거한 causal gain 추정이 아니다.

목표 유지와 실제 몸통 고정은 다르다. Body9 실제 scalar 좌표 최대 초기 편차약3.5382°와
actual native bound 초과약0.00010rad를 원자료대로 공개한다.
한 후보 한 실행의 비교이며 전체 동작 범위·반복 재현·완전 grip 인증은 아니다.

## 연주 학습 후속

현재 G 기준 fret/strike 목표와 초기 world G p/q 유지 목표를 함께 평가한다.
현재 source18 탐색은 최종66 제어권을 제한하지 않는다. 완전 palm 고정 접촉을
연주의 선행 조건으로 두지 않는다. 다음은 실제 checkpoint 선별/동결 prior의 residual0
관측·action·history 연결이며, 이번 actor 추론/학습update는0이다.

## 비교 그림 QA와 보존 누락 복구

Root는 첫 PNG와 현재 revised PNG를 각각 직접 열었다. 위치mm/회전deg/cable 법칙N의
두 actual trace와 별도16개 이산 source 거리 상한을 구분한다. 범례가 데이터 표본을 가리지
않고, source fraction0 미통과는 접근 방향을 제안하지 않은 기준행이라는 설명을 포함한다.
Native trace와 source snapshot을 같은 연속 실행으로 연결하지 않는다.

Luna가 첫 producer/출력 일식을 사전 보존하지 않고 범례·라벨을 수정/재생성했다.
Root가 최초 관측한 source SHA61ea48b82…와 PNG SHAdb6c6964…를 기준으로,
역구성 source와 별도 재생성 PNG가 각각 exact 일치함을 다시 확인했다.
복구 소스는 [영구 파일](/home/ajou/yigyu/3/stability_adapter_2/make_palm_witness_artifacts_v1_recovered.py:1)과
recovered_v1/producer_source.py에 보존했다. 첫 source/PNG는 byte 복구되었지만,
첫 실행의 manifest/log/metadata 전체 byte 복구를 인증하지 않는다. Recovered manifest는
새 재생성 실행 기록이며 원본 실행 manifest로 표시하지 않는다.

현재 revised source4c4b2ccf…/PNGcaea7d49…와 manifest/log/metadata는 별도
artifact_revised_preserved에 exact 복사했다. [복구 범위 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifact_revision_preservation.json:1)에 근거를 남긴다.
이 후처리 수정/복구로 새 native·physics·actor추론·학습은 실행하지 않았다.
Actual 원자료와 영상·소비된 physics source/plan/inputs는 유지했다.
