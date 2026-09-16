# StabilityAdapter 2100회 그립 영상

현재 v8 학습의 5000·10000·11000회 체크포인트 비교는
[현재 학습 영상과 분석](current_v8_checkpoint_comparison/README.md)을 참고한다.

## 파일

- `stability_2100_grip_front_side.mp4`: 동일 episode의 정면·측면 동시 비교 영상
- `stability_2100_front.mp4`, `stability_2100_side.mp4`: 원본 시점별 영상
- `stability_2100_contact_sheet.jpg`: 0.5초, 3.0초, 6.0초 비교 화면
- `stability_2100_front.json`, `stability_2100_side.json`: episode 수치와 종료 원인

## 재현 조건

- 체크포인트: `20260914_201105_adapter/checkpoints/stability_adapter_002100.pt`
- 정책: deterministic tanh mean
- seed: 100000
- episode 수: 시점별 fixed 1개 + validation 1개
- 결합 영상: 1920×540, 30fps, 7.167초

## 판독

정면과 측면 모두 같은 초기 상태와 정책을 사용한다. 약 0.5초에는 왼손이 넥에 접근해
`GRASP` 단계에 있고, 최초 획득 상태도 기록된다. 약 6초에는 내부 단계가 `TRANSPORT`까지
진입하지만, 안정적인 grasp와 방법 성공은 모두 false다.

영상의 첫 fixed episode는 369 frame에서 `failure_guitar_motion`으로 종료됐다. 종료 순간에는
왼손 힘 0N, 접촉 손가락 0개, 미끄럼 6.40m/s였고 기타 속도는 8.42m/s,
각속도는 21.32rad/s까지 증가했다. 위치 오차 38.5cm, 회전 오차 108.4°로 끝났다.
따라서 이 결과는 넥까지 접근하고 일시적으로 획득하지만, 엄지와 손가락의 대향 접촉을
유지하지 못해 기타를 놓치는 현상을 보여준다. 단순 최대 힘 부족보다 접촉 배치와 유지가
현재 병목이라는 로그 분석과 일치한다.

이 영상은 미검증 reference를 사용하는 진단 결과이며 최종 성공 영상이 아니다.
