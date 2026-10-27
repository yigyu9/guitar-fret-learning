# 그래픽 충돌 방지 작업 준비

커널은 NVIDIA EGL 라이브러리의 SIGSEGV를 기록했다. HeadlessDeadlineScene은 카메라를 만들지 않지만 GraphicsGym.create_sim이 graphics device0을 강제한다. Isaac Gym 동봉문서는 sensor rendering 없는환경에서 device−1이면 graphics context를 생성하지 않는다고명시한다.

현재 long_on_v2의 다음30분checkpoint/전체평가가끝날때까지 A/main을변경하지않는다. 준비소스는 /tmp/stability_graphics_isolation_v1에두고, 마지막완료CP보존과기존프로세스종료를확인한뒤 새A파일과GRAPHICS_ISOLATION_PLAN_V1.md로적용한다. 기존소스와실험은보존한다.

1. [ ] 학습 create_sim graphics−1 / 기록평가 graphics0, 실제호출기록검사. CPUPhysX·CUDA학습·물리초기값/PD/관측/보상/81제어/기타자유·스트랩·baseline은유지한다.
2. [ ] 기존CP의모델/Adam/RMS/RNG/counter를그대로보존하고, source 추가만허용하는엄격한ABI이행검사. 기존code digest변경/물리제어계약변경은거절한다.
3. [ ] CPU회귀와별도검수→실제반복reset/한에피소드물리비교→CUDA1갱신/전체영상검증.
4. [ ] 5분복구용checkpoint(영상없음)와기존30분공식checkpoint/전체영상,11:40cutoff로학습재개. SEGFAULT완전방지를인증하지않으며장시간재현성은별도확인한다.
