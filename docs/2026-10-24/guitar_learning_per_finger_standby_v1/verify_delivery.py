"""Seal v17 implementation/documentation evidence without native execution."""
from pathlib import Path
import ast,datetime,hashlib,json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DOCS=ROOT/'docs/2026-10-26/왼손보상구조'
ARCHIVE=ROOT/'guitar_learning/archive/20261024_before_per_finger_standby_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 final=json.loads((HERE/'final_source_manifest.json').read_text())['source']
 active={str(p.relative_to(ROOT)) for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.relative_to(ROOT/'guitar_learning').parts}
 assert len(active)==451 and set(final)==active
 for name,digest in final.items():
  assert sha(ROOT/name)==digest,name
  ast.parse((ROOT/name).read_text(),filename=name)
 before=json.loads((ARCHIVE/'manifest.json').read_text())['files_sha256']
 assert len(before)==471
 for name,digest in before.items():assert sha(ARCHIVE/name)==digest,name
 changed=sorted(name for name in final if final[name]!=before[name])
 production=[name for name in changed if not name.startswith('guitar_learning/tests/')]
 assert set(production)=={'guitar_learning/gpu/finger_reward.py','guitar_learning/gpu/environment.py','guitar_learning/song/curriculum_runtime.py','guitar_learning/skills/specialist_policy.py'}
 assert len(changed)==13
 # Preserve exact source and document evidence of the previous completed run.
 v16=ROOT/'docs/2026-10-23/guitar_learning_long_training_v16'
 oldpins=json.loads((v16/'training_source_manifest.json').read_text())['source']
 for name,digest in oldpins.items():
  relative=Path(name).relative_to(ROOT)
  assert sha(v16/'source_training'/relative)==digest,name
  assert sha(ARCHIVE/relative)==digest,name
 olddocs=ARCHIVE/'docs/2026-10-26/왼손보상구조'
 oldverify=json.loads((olddocs/'verification.json').read_text())
 for name,digest in oldverify['files_sha256'].items():assert sha(olddocs/name)==digest,name
 cpu=json.loads((HERE/'cpu_tests.json').read_text())
 assert cpu['all_passed'] and len(cpu['modules'])==28 and cpu['total_tests']==279
 logs={}
 for row in cpu['modules']:
  assert row['returncode']==0
  logs[row['log']]=logs.get(row['log'],0)+row['tests']
 for name,count in logs.items():
  log=(HERE/name).read_text();match=re.search(r'Ran (\d+) tests?',log)
  assert match and int(match[1])==count and '\nOK\n' in log,(name,count)
 audit=dict(schema='guitar_learning.per_finger_standby_source_audit.v1',
  checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reward_schema='guitar_learning.gpu_tensor_song_reward.v17',
  preparation_schema='guitar_learning.gpu_finger_preparation_rate.v2',active_python_count=len(final),
  source_manifest='final_source_manifest.json',source_manifest_sha256=sha(HERE/'final_source_manifest.json'),
  archive_manifest=str(ARCHIVE/'manifest.json'),archive_manifest_sha256=sha(ARCHIVE/'manifest.json'),
  preserved_original_files=len(before),changed_python_files=changed,changed_production_files=production,
  previous_run_frozen_sources_verified=len(oldpins),previous_document_seal_files_verified=len(oldverify['files_sha256']),
  scope='CPU source, test logs and preserved evidence only; no GPU/native/training')
 write(HERE/'source_audit.json',audit)
 prose=[DOCS/'README.md']+sorted(DOCS.glob('[0-9][0-9]_*.md'))
 general=[ROOT/p for p in ['guitar_learning/README.md','guitar_learning/AGENTS.md','CURRENT_STATUS.md','docs/2026-10-26/learning_flow/README.md']]
 review_path=HERE/'independent_review.json';review=json.loads(review_path.read_text()) if review_path.exists() else None
 if not review:write(HERE/'pre_review_source_audit.json',audit)
 missing=[];links=[]
 for p in prose+general+[HERE/'README.md',HERE/'independent_review.md',DOCS/'independent_review.md']:
  if not p.exists():missing.append(str(p));continue
  for href in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if href.startswith(('http:','https:','mailto:','#')):continue
   link=Path(re.sub(r':\d+$','',href.split('#')[0]));link=link if link.is_absolute() else p.parent/link
   links.append(str(link))
   if not link.exists():missing.append(str(link))
 result=dict(completed=bool(review),phase='final' if review else 'pre_final_review',reward_schema=audit['reward_schema'],
  preparation_schema=audit['preparation_schema'],active_python_AST_and_SHA_verified=451,preserved_original_files_verified=471,
  cpu_test_modules=28,cpu_tests=279,source_audit_record=str(HERE/('source_audit.json' if review else 'pre_review_source_audit.json')),source_audit_sha256=sha(HERE/'source_audit.json'),
  local_links_checked=len(links),missing_links=sorted(set(missing)),review_pending=not bool(review),
  new_gpu_native_or_training_executed=False,naturalness_or_pressing_performance_verified=False)
 if review:
  assert review['verdict']=='PASS' and not review['unresolved_findings']
  assert set(review['reviewed_prose_sha256'])=={p.name for p in prose} and len(prose)==12
  for p in prose:assert sha(p)==review['reviewed_prose_sha256'][p.name],p
  assert set(review['reviewed_general_documents_sha256'])=={str(p.relative_to(ROOT)) for p in general}
  for p in general:assert sha(p)==review['reviewed_general_documents_sha256'][str(p.relative_to(ROOT))],p
  assert not missing,missing
  result['independent_review_sha256']=sha(review_path)
  result['reviewed_documents_sha256']={str(p.relative_to(ROOT)):sha(p) for p in prose+general}
  write(HERE/'verification.json',result)
  for name,target in [('source_audit.json','source_audit.json'),('verification.json','verification.json'),('verification_pre_review.json','verification_pre_review.json')]:
   write(DOCS/name,dict(reward_schema=audit['reward_schema'],record=str(HERE/target),sha256=sha(HERE/target),scope='Current v17 record; prior complete v16 originals preserved under the archive manifest'))
 else:
  write(HERE/'verification_pre_review.json',result)
  # Keep a resolvable planned link until the independent review is sealed.
  write(HERE/'verification.json',dict(completed=False,review_pending=True,pre_review='verification_pre_review.json'))
 print(json.dumps({k:result[k] for k in ['phase','cpu_tests','active_python_AST_and_SHA_verified','local_links_checked','review_pending','missing_links']}))
if __name__=='__main__':main()
