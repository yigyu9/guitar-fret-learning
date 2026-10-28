# CPU 분석 준비

`analyze.py`만으로 네 native 관찰 조건의 완료를 확인하고, 전부 완료된 뒤 `results_v1/`에 수치 CSV·그림·한국어 RESULTS·독립 verification을 만든다. 원자료·봉인된 관찰 도구·활성 소스는 수정하지 않는다. NumPy/Matplotlib만 사용하며 Torch/Isaac/native 실행을 import하지 않는다. 완료 전 호출은 누락/미완료 상태만 출력한다. 기존 결과 폴더는 덮어쓰지 않는다.

```bash
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_load_probe/analysis/analyze.py --self-test
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_load_probe/analysis/analyze.py
```

해석을 위한 분모·부호·구간을 먼저 고정한다. 성과는 원래 모든128 first-attempt 평가를 독립 재계산한다. 하중/투영 통계는 `first_attempt & ~failure_latched`만 사용해 최초 실패 endpoint와 이후를 제외한다. 시각 구간은 audible 전/onset≤t≤end/후다. pooled endpoint 통계와 모든128 환경별 audible 최대/노출 유무를 별도로 보관하며, 실패도 환경 분모에 남긴다.

중지와 엄지의 signed normal은 같은 실제 press-plane world normal로 계산하고 resultant와 분리한다. 엄지 own rear-plane 성분도 별도 기록한다. Jn·(target−q) 및 Jn·(4×executed_action)은 국소 선형 proxy이며 실제 침투/제어 운동/원인 증거가 아니다. 전체 DOF 예측 point velocity와 실제 point velocity의 잔차 RMS·최대를 원래 probe report와 독립 재검산한다. 실제 잔차와 속도 규모를 검토하기 전 방향 해석은 보류한다. any-sample positive와 nearest-point facing 불일치는 따로 집계한다. body resultant는 pair 압력이 아니며 새 힘 한계나 정책 단독 원인을 설정하지 않는다.

원래 baseline의 initial.zero/reference, cp50.policy, final300.policy 전체 evaluation JSON과 관찰 재실행 결과를 실제로 비교한다. exact 여부·차이 수·최대 숫자 차이·첫 차이 경로를 남기며 동일성을 가정하거나 재현 보장으로 확대하지 않는다. 모든 raw가 완료된 뒤 root 통보를 받아 실제 분석·독립 검수를 진행한다.
