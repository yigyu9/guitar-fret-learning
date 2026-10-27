# Palm-frame audit artifact index

이 인덱스는 이번 JSON 기반 산출물의 소유 경로와 근거 위치를 안내한다. 저장된 원자료, 산출물 생성 작업에서는 측정 코드, 계획을 수정하지 않았다. 최종 reviewer의 readiness-contract 지적을 반영한 9-check 자료를 canonical로 연결했다. 이전 `artifacts/`와 `measurements_cpu_address/`는 이력으로 보존한다.

## 이번 산출물

- Plotter: [`stability_adapter_2/plot_palm_frame_audit.py`](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_frame_audit.py:1) — JSON 입력 검사, 67개 embedded SHA 확인, 그래프 및 manifest 생성.
- 결과 안내: [`README.md`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/README.md:1) — 표, 한계, 재생성 명령.
- 그림: [`palm_frame_displacement.png`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/artifacts_validated/palm_frame_displacement.png) — 좌우 palm의 1초·3초 저장 변위.
- Provenance: [`plot_manifest.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/artifacts_validated/plot_manifest.json:1) — audit/Jacobian 및 embedded input, plotter, 출력 SHA.
- 누적 결과: [`VISUAL_REPORT.md` §35](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:776) — 그림 49와 해석 한계.

## 입력 및 관련 계획

- Raw audit: [`audit.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/measurements_validated/audit.json:1) — 9개 check, 세 저장 시점, 67개 embedded input SHA.
- CPU Jacobian descriptor: [`jacobian.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/measurements_validated/jacobian.json:1) — fixed-root shape, device, palm rows.
- Query 실행 이력: [`native_execution.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/native_execution.json:1), [`native_run.log`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/native_run.log:1), [`native_cpu_run.log`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/native_cpu_run.log:1), [`native_cpu_address_run.log`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/native_cpu_address_run.log:1), [최종 query 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/native_validated_run.log:1) — 네 query 종료 코드 1/1/0/0 및 steps=0 기록; 이전 성공 자료도 보존.
- Audit 코드 (readiness 보완 포함): [`audit_palm_frames.py`](/home/ajou/yigyu/3/stability_adapter_2/audit_palm_frames.py:33) — CLI/query 시작; CPU descriptor guards [79행](/home/ajou/yigyu/3/stability_adapter_2/audit_palm_frames.py:79), 복사 [86행](/home/ajou/yigyu/3/stability_adapter_2/audit_palm_frames.py:86), 준비 판정 [98행](/home/ajou/yigyu/3/stability_adapter_2/audit_palm_frames.py:98).
- 범위와 측정 제한: [`PALM_FRAME_AUDIT.md`](/home/ajou/yigyu/3/stability_adapter_2/PALM_FRAME_AUDIT.md:1), 결과 위치 [33행](/home/ajou/yigyu/3/stability_adapter_2/PALM_FRAME_AUDIT.md:33); [`PLAN.md` §43](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:856); [`README.md`](/home/ajou/yigyu/3/stability_adapter_2/README.md:143).
- FK/Jacobian 검증 제안: [`PALM_POSITION_CURRENT_PROPOSAL.md`](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_CURRENT_PROPOSAL.md:1) — 설계 검토 문서이며 새 제어 적용 승인이 아니다.

## 검증 상태

Plotter 문법 검사를 통과했다. 최종 `artifacts_validated/`와 새 `/tmp` 출력 PNG는 2040×944 RGBA로 픽셀 단위 일치했다. 최종 audit 9개 검사, embedded input 67개 SHA, Jacobian shape/device/palm-row descriptor를 확인했다. 기존 `artifacts/` 및 이전 측정 폴더는 수정하지 않고 보존했다. 그림 생성은 측정값만 읽었으며 native 실행이나 설정 변경을 하지 않았다.


## 최종 검수·보존

- [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/review.md:35): 준비 판정 및 표현 지적을 해결했고 남은 지적은 없다.
- [회귀 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/readiness_regression.json:1): 0/한쪽만 nonzero/양쪽 nonzero 데이터 판정, native 초기화·step 없이 검증.
- [최종 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/verification.json:1), [소스 보존본 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/source_final_manifest.json:1), [파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/file_inventory.json:1).
