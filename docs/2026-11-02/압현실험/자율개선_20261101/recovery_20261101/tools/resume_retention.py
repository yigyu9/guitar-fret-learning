"""분석기의 음 종료 후 후보 오판을 보존·검증한 뒤 독립 학습률 비교를 재개한다.

원래 감독의 failed 상태나 학습 결과를 덮어쓰지 않는다. 미완료 H/I/T를 완료로
취급하지 않고, 별도 model-only 비교에 GPU를 먼저 배정한다.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
TOOLS=Path(__file__).resolve().parent
BASE=TOOLS.parents[1]
ORIGINAL=ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3'
sys.path.insert(0,str(TOOLS))


def load_driver():
    spec=importlib.util.spec_from_file_location('retention_recovery_driver',BASE/'tools_v2/run_study.py')
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    return driver


def main():
    import analyzer
    driver=load_driver();study=driver.study
    original=ORIGINAL/'runs/continuation_v1/progress.json'
    before=json.loads(original.read_text())
    if before['status']!='failed' or before.get('error')!='같은 줄6/7프렛 모순된 동시 성공 후보':
        raise ValueError('분석한 중단 사유와 다름; 자동 우회하지 않음')
    study.check_sources(before)
    old_retention=BASE/'runs_v2/progress.json'
    old_state=json.loads(old_retention.read_text());study.check_sources(old_state)
    if old_state['status']!='failed' or old_state.get('jobs'):
        raise ValueError('새 비교가 이미 실행됐거나 상태가 달라짐')
    proof=json.loads((BASE/'validation_v2/preflight.json').read_text())
    if not (proof.get('completed') and proof.get('source_unchanged') and proof.get('preceding_driver_resumed')
            and len(proof['operations'])==7 and all(row['completed'] and row['exit_code']==0 for row in proof['operations'])):
        raise ValueError('기존 native 사전검사 미통과')
    label='H128_s7_u250_mean_std1.0_n32'
    job=before['jobs'][label]
    target=Path(job['out']);report=json.loads((target/'report.json').read_text())
    if (job['status']!='complete' or not report.get('completed')
            or any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))):
        raise ValueError('원래 평가 자체가 실패한 경우에는 분석만 교체하지 않음')
    for path,sha in job['evidence'].items():
        if study.sha(path)!=sha:raise ValueError('원래 평가 근거 변경')
    recovery=TOOLS.parent
    corrected=analyzer.analyze(target,32,result_path=recovery/'H128_seed7_u250_corrected_analysis.json')
    amended=json.loads(original.read_text())
    amended['status']='original_failed_analysis_corrected_HIT_incomplete'
    amended['analysis_correction']=dict(original_progress=str(original),original_sha256=study.sha(original),
        reason='post-audible raw candidates are not simultaneous audible success',
        remaining_H_seed17_I_T='not run; not called complete')
    amended['results'][label]=dict(condition='H128',seed=7,total=250,checkpoint=str(ORIGINAL/'runs/continuation_v1/jobs/H128_s7_u250_train/J/final.pt'),mode='mean',metrics=corrected)
    corrected_progress=recovery/'PRECEDING_RESULTS_CORRECTED_COPY.json'
    study.write(corrected_progress,amended)
    driver.CONTINUATION=corrected_progress
    original_seal=study.seal
    def seal():
        pins=original_seal()
        pins.update({str(p.relative_to(ROOT)):study.sha(p) for p in TOOLS.glob('*.py')})
        return pins
    study.seal=seal
    study.analyze=analyzer.analyze
    def ready(state,out):
        study.check_sources(before);study.check_sources(old_state)
        occupied=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
        if occupied:raise RuntimeError('다른 GPU 작업 사용 중: '+occupied)
        state['status']='running'
        state['original_analysis_failure_preserved']=dict(path=str(original),sha256=study.sha(original))
        state['interpretations'].append('선행 H/I/T는 분석기 오류로 미완료. 원본 failed 상태를 보존하고 가중치 이전 학습률 비교부터 독립 재개.')
        state['interpretations'].append('음 종료 후 두 프렛 원시 후보는 성공 모순이 아님. A발음 중 높은 프렛 간섭의 유효성 검사는 유지.')
        driver.update(state,out)
    driver.wait_for_original=ready
    driver.main()


if __name__=='__main__':main()
