# 기타에 집중한 초기 화면

- [x] 카메라만 기타 중심에 가깝게 배치했다.
- [x] 전체 바디·넥·헤드와 양손이 화면 안에 들어오는 것을 확인했다.
- [x] 실제5초 실행의 초기값·물리 궤적·접촉·물성·shape·캐시가 직전 현 표시 실행과 동일했다.

![기타 중심 실제 초기 카메라와 6현 오버레이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/native_v1/media/initial_strings.png)

실제 Isaac Gym 카메라 화면 위에 물리 없는 6현 선을 표시한 초기 이미지다. 기타·휴머노이드 자세는 바꾸지 않았다. 외관 정지 이미지용 카메라만 이동했고 기존 전신/손 영상 카메라는 그대로다. 원본 이미지와 기존 자산·코드는 보존했다.

새 구현: [run_guitar_focused_view_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_focused_view_v1.py:14). 검증: [verification_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/verification_v1.json:1).
