# Palm-frame audit 산출물

2026-10-07. 이 문서는 최종 `measurements_validated/audit.json`과 `jacobian.json`에 저장된 값을 요약한다. 그림 생성은 JSON만 읽으며 추가 native 실행이나 physics step을 수행하지 않는다. 최종 `measurements_validated/` JSON과 audit에 포함된 67개 입력 SHA를 확인했다. 기존 `measurements_cpu_address/`와 그 그림은 이전 검수 단계 기록으로 그대로 보존한다.

## 그림

![저장된 0초 대비 1초·3초 palm 기준점 변위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/artifacts_validated/palm_frame_displacement.png)

양쪽 panel은 1초와 3초 저장 표본에서 source convex-hull volume center, palm body origin, wrist origin이 초기(0초) 좌표에서 얼마나 이동했는지 mm로 보여준다. 이는 세 시점의 이산 관측이며 연속 궤적은 아니다. 각 palm의 hull volume center는 source 형상의 계산점으로, 접촉점·해부학적 중심·native COM을 뜻하지 않는다.

| 손 | 점 | 1초 변위 (mm) | 3초 변위 (mm) |
|---|---|---:|---:|
| LH | source hull volume center | 138.278237 | 144.535203 |
| LH | palm body origin | 127.095115 | 131.941556 |
| LH | wrist origin | 119.911379 | 124.346851 |
| RH | source hull volume center | 20.822106 | 25.635409 |
| RH | palm body origin | 22.885533 | 28.264217 |
| RH | wrist origin | 25.630233 | 31.254596 |

초기 local offset으로 world 형상 중심을 재구성한 오차는 모든 표본에서 2.3×10⁻¹⁶ m 미만이다. 최종 audit의 9개 검사는 모두 통과했으며 fixed-root Jacobian descriptor는 CPU, shape `(1, 65, 6, 105)`이고 palm 행 17(LH), 43(RH)는 0이 아니다. 이 준비 상태는 Jacobian 기준점/frame, native FK, 해부학적 COM, 접촉 또는 위치 제어의 정확성을 검증하지 않는다. 실제 FK 유한차분 검증은 별도 계측 단계다.

기록상 네 query 시도는 모두 physics step 없이 끝났다(종료 코드 1, 1, 0, 0). reviewer가 이전 성공 JSON에 양쪽 palm 행의 nonzero 검사가 빠진 readiness 계약 문제를 확인해 이를 추가했고, 마지막 `measurements_validated/` audit은 9개 검사 모두 통과했다. 저장 점과 tensor는 직전 성공 자료와 동일하다. 실패 및 이전 성공 자료는 보존되어 있으며, 시도별 상태는 `native_execution.json`과 각 run log에서 확인할 수 있다. 의존성 설치나 제어 변경은 하지 않았다.

## 재생성 및 provenance

```bash
python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_frame_audit.py \
  --audit /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/measurements_validated/audit.json \
  --out-dir /tmp/palm_frame_audit_reproduction
```

Plotter는 비어 있지 않은 출력 폴더를 덮어쓰지 않는다. 입력 검사, plotter SHA, 이미지 SHA는 `artifacts_validated/plot_manifest.json`에 기록한다. 독립 `/tmp` 재생성 그림은 canonical PNG와 픽셀 단위로 일치했다. 상위 실험 맥락과 다음 검토 단계는 [PALM_FRAME_AUDIT 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_FRAME_AUDIT.md:33)에 정리되어 있다.


## 검수와 보존 기록

수정된 준비 판정의 순수 배열 회귀에서 0 tensor 및 한쪽만 nonzero인 경우를 거부했다.
Root의 실제 JSON plot CLI 재생성은 canonical PNG와 byte가 같고 그림을 직접 확인했다.
[독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/review.md:35), [최종 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/verification.json:1),
[소스 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/source_final_manifest.json:1), [전체 파일 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/file_inventory.json:1)에 기록한다.
