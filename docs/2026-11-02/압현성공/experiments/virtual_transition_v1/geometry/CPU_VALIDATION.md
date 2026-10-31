# ABAB 번들·B 준비 자세 CPU 점검

새 번들은 무음 WAV 7.5초이며 실제 make_task 4개 목표가 물리 3–4.5/5–6.5/7–8.5/9–10.5초, 전체 11초를 구성한다. 표준3번줄 runtime index2·중지2·프렛6/7/6/7이며 원본 저음E 기준 줄 index3에서 현재 builder가 변환했다. 손 anchor는 5/6/5/6이며 기존 builder의 마지막 0.25초 미리 이동을 그대로 사용한다. A→B 손목 안내의 기타 y 이동은 −26.127mm다. 번들 manifest와 모든 등록 파일 SHA를 다시 검증했다. generator_source provenance를 함께 보존했다.

B는 활성 full_fk와 native 검증된 A(중지6프렛)의 q105/state를 함께 기준으로 사용했다. A의 안쪽 유효 패드 local sample55를 고정해 점 전환을 피하고 F7 중앙의 13.5mm 높이로 팔12축만 최적화했다. 목표점 접선 오차 9.33e−10m, normal cosine 0.993596, 셀 양끝 2mm inset 충족, 적격 패드점7개다. 손목 방향 변화는 약1.01e−6도, A기준 손목 안내 B 오차는0.890mm다. 손가락·오른팔·하체 q는 A와 exact 동일하며 hold_target의 팔12축만 B q로 갱신했다. FK로 모든 인간 body pose·DOF 및 0속도를 일치시키고 기타·의자 상태는 A와 동일하게 보존했다.

B의 비목표 검지/약지/소지 distal 유효 패드 최저 plane 높이는12.727/10.375/5.930mm이며 유한 넥·줄 근접·높이−1..3mm·동일점 법선조건을 함께 만족하는 점은 각0개다. 중지와 검지/약지/소지 표본 사이 최소 거리는9.318/9.323/33.821mm로 A와 같다. 전체 mesh·다른 지골·엄지·cooked 충돌 또는 native 물리 접촉과 하중을 검사한 결과는 아니다. 특히 GPU settling 이후 선접촉 여부는 후속 실제 검사에서 확인해야 한다.

팔 최적화축은 native bounds를 지킨다. 보존한 A 원본 자체에 fixed0 R_Knee_y/z에서2.49e−6/2.30e−6rad의 작은 이탈이 있어 이를 원본 그대로 기록했다. B는 이를 증가시키지 않았고 하체를 고치지 않았다.

Python3.8/CPU/단일 스레드에서 6개 회귀검사를 통과했다: 실제 clock/string/finger·무음, 팔만 변경·bounds·hold, A기준 FK/actor 보존, 동일 패드 셀/높이/법선·타 손가락 근접, provenance/손목 안내, 기존 번들 덮어쓰기 거부. 최종 입력 SHA 재검증도 통과했다. **native_verified=false**이며 CPU 기하 적격성을 실제 압현 성공이나 학습 승인으로 바꾸지 않는다. GPU를 실행하지 않았고 기존 번들·활성 학습 패키지·이전 실험 파일은 수정하지 않았다.

인터페이스: candidate_B.json의 q105, hold_target105, state/body_snapshot은 episode 경계용이며 시뮬레이션 도중 덮어쓰는 궤적이 아니다. geometry 후보는 학습 팔 이동을 대신하는 teacher 명령이 아니다. source_sha256으로 현재 FK·자산·생성기·번들을 추적한다.
