# 저장된 전체 Fret 실행의 바디 중심·손 접근 진단

실시간 진단 v1/동일재시험/v2가 세 번 native 카메라 API에서 exit139로 중단됐다. 마지막 완전 프레임은 각각0.866667/0.833333/1.0초다. 물리 평형/원본 task 종료가 아니고 원인 미확정이며 원본과 부분영상은 보존한다. 새 full live 검증은 미완료로 남긴다.

이번 산출물은 이미 완료·보존된 `fret_fingers_arm_hold_v1/native/data`의 실제 Isaac Gym 전체389frame/12.916667초·native trace·60Hz controls·420D 관측·terminal_info를 **읽기만 하여** 생성한다. 초기값·물리·제어를 새로 실행하거나 바꾸지 않는다. 새 결과 경로는 `results/saved_fret_diagnostic_v1/`이다.

## 정확한 시점과 표시

- body-center/RFU·조건부 사용자 위치box·회전 변화는 저장 native trace의 동일 physics step으로 계산한다. 질량중심/전체 회전집합 판정이 아니다.
- PLAY 구간은 같은 step의 **다음 제어 직전 저장 관측**을 사용한다. 이전 물리 평가/goal.advance 후의 목표여서 이전 live capture의 평가 전 목표와 혼동하지 않는다. 마지막은 별도 저장 terminal_observation이다. 준비 구간에는 목표를 추정·보간하지 않고 미측정으로 표시한다.
- O_hand_geometry 손끝 marker는 실제 native top body 위치와 1µm 이내 정렬 검증한다. 목표는 현재 기타 local 관측의 `tip_G+target_vector_G`를 저장 native p/q로 world 변환한다. 손목 값은 저장 관측의 목표벡터 길이이며 실제 native 손목의 기타 상대 좌표도 별도 기록한다. marker 거리·실제 pad 압착·음악 성공을 구분한다.
- contacts는 같은 step의 기존 pre-integration PhysX records를 쓴다. 마지막 frame에는 정확한 접촉 record가 없으므로 미측정이다. 실제 기타 pair와 pluck_range proxy를 구분하고 raw lambda를 힘으로 부르지 않는다. 접촉표시는 body 원점이며 표면 접촉점/관통 깊이 인증이 아니다.
- 기존 기록에는 camera matrix/depth가 없다. v2의 같은 초기상태/동일고정카메라 matrix를 사용하고 초기 및 공통 prefix의 raw RGBA 픽셀·camera source SHA를 대조한다. 모든 v2 저장 matrix가 일정한지 검사한다. depth 자료가 없으므로 선은 **투시 설명선**, 가려짐 판정 없음으로 표시한다. 기존 프레임을 새 native 실행이나 live 성공으로 부르지 않는다.

## 검증·담당·산출물

1. 원본 native report 완료/실패판정·step/time·image SHA·관측/native손끝·원본고정camera 근거 검증.
2. 두 카메라 전체 진단 MP4, 초기/2초/5초/8초/10초/종료 PNG, 수치CSV·추세도·결과설명.
3. 원본 입력SHA 불변, 이전1327보호파일 불변, 별도 결과 검수와 최종 봉인.

root: 새 build_saved_fret_diagnostic.py·분석·main PLAN·최종감사. reviewer: 새phase/review.md만. Luna: 확정brief에 따른 새phase/README.md·FILE_INDEX.md만. 기존 모든 소스/결과는 유지한다.

- [ ] 구현·사전검수
- [ ] 전체 실제기록 후처리·정렬/보존 검사
- [ ] 실패 원인 해석·영상/설명·독립 검수

다음 제어는 현재 기타 기준 왼팔 접근을 손가락 정책과 분리하는 제한된 목표 보정으로 설계한다. 본 작업에서 제어/학습을 추가하지 않는다. 다음 fresh run 전에 native 카메라 API 반복 조회 오류를 별도로 해결해야 한다.
