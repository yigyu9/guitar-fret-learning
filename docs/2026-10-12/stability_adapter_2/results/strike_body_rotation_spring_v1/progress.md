# Strike body-rotation spring v1 진행 상태

- [x] Analysis summary/native report 대조: 1,200 physics steps, 151 frames, 24/24 checks, 5초 완료.
- [x] Native closure 1,091개 unchanged, 별도 analysis 입력 7개 SHA unchanged 확인.
- [x] 저장된 source phase0-only와 EFFORT activation/PD readback 구분; phase-1 damping quarter 전환이 관측되지 않았음을 명시.
- [x] Requested spring torque audit, 49 control/25 native trace prefix와 first actor obs/action exact, 1,004개 계산 및 125개 saved anchor 검사 범위를 문서화.
- [x] Force-dual 해석 미인증, pure math/velocity 검사 범위, NOT ADOPTED 결과를 구분.
- [x] Native 0·2·5초 전신/손 PNG 6개와 native MP4 2개를 README에 embed.
- [ ] Saved result의 독립 최종 검수.
