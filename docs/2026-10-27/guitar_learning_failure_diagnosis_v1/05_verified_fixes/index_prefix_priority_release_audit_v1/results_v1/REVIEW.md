# 독립 CPU 검수

판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

새7파일과 직접입력18개의 현재 SHA를 확인했다. 원모델 CPU 추론과 24행 입력교체를 메모리에서 재실행해 comparison/verification JSON 및 rows.csv 전체 exact를 확인했고, 그림도 메모리 재생 픽셀이 일치했다. 직접 그림을 검토했다. 첫4행의 자기복사 입력·출력은 exact이며 나머지20행에서 priority0/1만 같은행의 유효한 main A4/B7 token으로 교체했다. state/events/mask/priority_mask·나머지6priority와 모델73 tensor는 불변이다.

원 rawgoal CPU 잔차1.4901161193847656e−7은 기존2.384185791015625e−7 이내다. 예정desired RMS(PIP/DIP)는 .964335/1.251069°에서1.595820/2.046847°로, full N RMS는1.930298/2.489373°에서2.542935/3.260546°로 변했다. JSON24행에서 RMS와 최대변화4축을 별도로 재집계해 exact를 확인했다.

이는4관측환경의 고정상태 민감도다. 공통 encoder와 index head를 함께 바꾼 효과이며, 정보부재·학습 인과·실제 해제성공·다른124환경의 결과를 증명하지 않는다. 새 clock·물리 실행·fit/PPO는 없고 원자료와 모델은 변경하지 않았다. 검수된 release_window의 같은행 기준각을 재사용했으며 상위 입력 재귀감사나 CUDA 전체상태 복원은 수행하지 않았다. 최종7파일 SHA는 review.json에 기록했다.
