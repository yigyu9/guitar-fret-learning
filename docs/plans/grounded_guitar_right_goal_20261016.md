# V12: 정착한 접촉면을 고려한 유한 오른팔 목표

V11의 실제 6축 목표는 끝까지 전달됐다. Chest의 상대 전진도 발생했지만, 기타 표면이 함께 움직여 마지막1초 간격0.072744~0.096578mm가 남았다. 초기 source에서 −0.301515mm는 목표 변경에 의한 **간격 변화량**이며 실제 목표 간격은 −0.001490mm뿐이었다. 기존 실패·분석 스키마 오류와 수정 버전은 모두 보존한다. 자세·힘의 미세 증가를 계속하지 않는다.

## 관측과 검증할 가설

실제 V11 정착 human을 고정한 순수 기하 질의에서 기타 body 중심0.175419mm/회전0.086987° 변경으로 Chest source gap−0.2mm를 얻고, Spine/RHip/RShoulder의 source gap 악화는 각각0.001mm 이하였다. 전체 기타 회전·넥·좌우 및 BOX도 허용 범위다. 상완 접촉면의 움직임은 약0.275mm의 접선 이동이므로 압력을 더하는 대신 유한 오른팔 지지 방향을 바꾸는 후보로 삼는다. 이는 source의 동시 근접 가능성이고 실제 마찰·접촉·지지 성공 증거는 아니다.

새 `right_goal_v1` producer는 실제 `native_static_v11` 정착 상태를 사전 pin하고 미소6DOF query를 재현한다. Chest 목표−0.2mm, 다른 세 지지 gap은 현재보다0.05mm 이상 악화하지 않고 −0.25mm 이내로 유지한다. body 중심 변경≤1mm/회전 변경≤0.5°, 기존 기타 전체 기준·활성 충돌 관련성·BOX/chair를 검사한다. source cooked 차이와 의도한 Chest preload는 공개한다.

**실행 시 기타에는 이 pose를 설정하지 않는다.** query의 world 미소 변환 `R_delta`, `translation_W_m`을 초기 actual 오른손 palm/상완 material/task world 목표에만 똑같이 적용한다. palm 방향에도 같은 회전만 적용한다. 기존 human IK·PD·task gain·cap·rate로 움직이며 기타는 원래 초기값에서 자유롭게 반응한다. 원 source4 초기/target2 finite상체6축/Root/cube/발/105채널·zero8/원 native collision policy는 유지한다. 직접 기타 힘·부착·고정·지속 state overwrite는0이다.

1. 새 query/spec/config의 입력 SHA·기하·원 제한·실제 mask·앵커 변환을 검증하고 독립 검수를 받는다.
2. 새 runtime/run/analyzer v14에서 기존17개 실제 기준을 그대로 유지하고 human 앵커만 변환됐는지 추가 검증한다. 명령 변경 시점은 초기부터이므로 과거 prefix 동일성을 요구하지 않는다.
3. 새 `native_static_v12`로 실제5초를 검증한다. 실패하면 목표 변환과 실제 상완/G 움직임·마찰 접촉을 먼저 진단한다. 성공한 경우 같은 설정을 재현한다.
4. 전체 통과와 재현 후 압현·타현, 이어 왼손 해제15초를 검증한다. 새 PPO는 시작하지 않는다.

- [ ] query/spec 사전·사후 감사 및 source 가능성 판정
- [ ] 새 코드·실제 앵커 변환의 검수/문법검사
- [ ] 정지5초 전체 기준 판정
- [ ] 통과 반복→압현/타현→왼손 해제

이 계획은 소비 후 수정하지 않고 같은 자료 디렉터리에 새 결과와 실패를 기록한다.
