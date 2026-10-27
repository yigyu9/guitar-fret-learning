# 최종 감사 로그의 기록 시점 정정

첫 root 감사의 27개 검사는 모두 통과했다. 다만 stdout을 같은 결과 폴더의 root_audit.log로 열어둔 상태에서 inventory를 작성해 해당 로그 항목을 최종 출력 전의 0byte로 기록했다. Source 검색·그림·이전 실험의 입력/출력 변조가 아니라 감사 로그의 기록 시점 오류다.

첫 artifact_inventory.json·final_verification.json·root_audit.log와 실행 소스를 그대로 보존한다. [별도 정정 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/root_post_log_seal.py:1)는 이전 inventory와 달라진 파일이 이 닫힌 stdout 로그 하나뿐인지 검사하고, 새 artifact_inventory_v2.json과 final_verification_v2.json에 정정 기록을 남긴다. 재검색·재렌더·물리 재실행은 없다. 이 정정 실행은 폴더 안 stdout 파일을 열지 않는다.

향후 보존 감사에서는 이 phase의 artifact_inventory_v2.json을 기준으로 사용한다. v1 metadata는 당시 기록으로 보존한다.
