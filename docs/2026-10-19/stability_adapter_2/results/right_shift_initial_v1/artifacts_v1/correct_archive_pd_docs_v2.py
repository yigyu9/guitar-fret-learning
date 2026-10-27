#!/usr/bin/env python3
"""Add corrected archive README versions; preserve all consumed originals."""
from pathlib import Path
import hashlib, json, re, sys

P = Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1")
I = Path("/home/ajou/yigyu/3/docs/2026-10-19/initial")
V_INDEX = Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX_v4.md")
BASE = I / "current_neck_support_v1"
CAND = I / "right_shift10_comparison_v1"
inputs = {
 "baseline_readme_v2": BASE / "README_v2.md",
 "candidate_readme_v2": CAND / "README_v2.md",
 "baseline_initial_values": BASE / "archive/native_off_v1/initial_values.json",
 "baseline_native_properties": BASE / "archive/native_off_v1/native_properties.json",
 "candidate_initial_values": CAND / "archive_v2/native_right10_v1/initial_values.json",
 "candidate_native_properties": CAND / "archive_v2/native_right10_v1/native_properties.json",
 "candidate_files_v2": CAND / "FILES_v2.md",
 "result_readme_v4": P / "README_v4.md",
 "video_index_v4": V_INDEX,
 "video_provenance_v2": P / "provenance_v2.json",
}
outputs = {
 "baseline_readme_v3": BASE / "README_v3.md",
 "candidate_readme_v3": CAND / "README_v3.md",
 "provenance": P / "archive_pd_correction_provenance_v2.json",
}
pin_path = P / "archive_pd_correction_preflight_v2.json"
producer = Path(__file__)

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def link_targets(text):
 for m in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)",text):
  yield m.group(1).strip().split()[0].strip("<>")
def check_doc(path, expected_outputs=()):
 text=path.read_text(encoding="utf-8")
 if re.search(r"\{[^}]+\}",text): raise SystemExit(f"template token in {path}")
 for target in link_targets(text):
  if not target.startswith("/"): raise SystemExit(f"nonabsolute target {target} in {path}")
  raw=target.rsplit(":",1)
  dest=Path(raw[0])
  if not dest.exists() and dest not in expected_outputs: raise SystemExit(f"missing target {target} in {path}")
  if len(raw)==2 and raw[1].isdigit() and dest.exists():
   if dest.suffix.lower() in {".png",".mp4",".jpg",".jpeg",".webp"}: raise SystemExit(f"binary line suffix {target}")
   lines=dest.read_text(encoding="utf-8",errors="replace").splitlines()
   if int(raw[1])<1 or int(raw[1])>len(lines): raise SystemExit(f"text line out of range {target}")

if len(sys.argv)!=2: raise SystemExit("usage: correct_archive_pd_docs_v2.py PREFLIGHT.json")
pin_file=Path(sys.argv[1]); pin=json.loads(pin_file.read_text(encoding="utf-8"))
if pin.get("producer_path")!=str(producer) or pin.get("producer_sha256_before")!=sha(producer): raise SystemExit("producer pin mismatch")
if pin.get("inputs")!={k:{"path":str(v),"sha256_before":sha(v)} for k,v in inputs.items()}: raise SystemExit("input SHA pin mismatch")
if any(p.exists() for p in outputs.values()): raise SystemExit("refusing to overwrite")
# Verify the property names in the two preserved native archives.
for role in ("baseline","candidate"):
 initial=json.loads(inputs[f"{role}_initial_values"].read_text(encoding="utf-8"))
 props=json.loads(inputs[f"{role}_native_properties"].read_text(encoding="utf-8"))
 if "PD_properties" not in initial: raise SystemExit(f"{role}: initial_values.json lacks PD_properties")
 if not {"imported","requested","applied"}.issubset(props): raise SystemExit(f"{role}: native_properties.json lacks mass-property groups")
 if not isinstance(props["applied"],list): raise SystemExit(f"{role}: native_properties.applied is not a list")
corrected="PD 속성 배열은 `initial_values.json`의 `PD_properties`에 있습니다. `native_properties.json`은 기타 imported/requested/applied 질량·COM·관성 기록을 담습니다."
base=inputs["baseline_readme_v2"].read_text(encoding="utf-8")
old_base="함께 둔 `native_properties.json`에는 초기 PD/물성 정보가 있고,"
if base.count(old_base)!=1: raise SystemExit("expected baseline PD sentence not uniquely found")
base=base.replace(old_base,corrected+" ")
cand=inputs["candidate_readme_v2"].read_text(encoding="utf-8")
old_cand="`native_properties.json`에는 native 초기 PD/property 데이터가 있습니다."
if cand.count(old_cand)!=1: raise SystemExit("expected candidate PD sentence not uniquely found")
cand=cand.replace(old_cand,corrected)
# Latest delivery crosslinks only; keep archive media and other evidence links untouched.
cand=cand.replace("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/README.md", "/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/README_v4.md")
cand=cand.replace("/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README.md", "/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README_v3.md")
cand=cand.replace("/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/FILES.md", "/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/FILES_v2.md")
index_link="\n영상 색인은 [성공 native MP4 납품 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX_v4.md:1)을 참조하세요."
cand=cand.replace("\n보존 파일별 색인은", index_link+"\n보존 파일별 색인은")
expected=(outputs["baseline_readme_v3"],outputs["candidate_readme_v3"])
for label,text in (("baseline",base),("candidate",cand)):
 if re.search(r"\{[^}]+\}",text): raise SystemExit(f"placeholder in {label} README")
 for target in link_targets(text):
  if not target.startswith("/"): raise SystemExit(f"nonabsolute target {target} in {label}")
  dest=Path(target.rsplit(":",1)[0])
  if not dest.exists() and dest not in expected: raise SystemExit(f"missing link target {target} in {label}")
# Ensure candidate's four navigation links point at approved current documents.
for target in (P/"README_v4.md",V_INDEX,BASE/"README_v3.md",CAND/"FILES_v2.md"):
 if str(target) not in cand: raise SystemExit(f"missing latest crosslink: {target}")
# Exclusive create; original readmes and archived JSON stay untouched.
for key,text in (("baseline_readme_v3",base),("candidate_readme_v3",cand)):
 with outputs[key].open("x",encoding="utf-8",newline="") as f:f.write(text)
for key in ("baseline_readme_v3","candidate_readme_v3"):check_doc(outputs[key],expected)
input_before={k:v["sha256_before"] for k,v in pin["inputs"].items()}
input_after={k:sha(v) for k,v in inputs.items()}
producer_after=sha(producer)
if input_after!=input_before or producer_after!=pin["producer_sha256_before"]: raise SystemExit("input/producer changed during correction")
record={"schema":"archive_pd_correction_provenance_v2","producer":{"path":str(producer),"sha256_before":pin["producer_sha256_before"],"sha256_after":producer_after},"preflight_pin":{"path":str(pin_file),"sha256":sha(pin_file)},"inputs":{k:{"path":str(v),"sha256_before":input_before[k],"sha256_after":input_after[k]} for k,v in inputs.items()},"outputs":{k:{"path":str(v),"sha256":sha(v),"bytes":v.stat().st_size} for k,v in outputs.items() if k!="provenance"},"verified_native_property_keys":{"baseline_initial_values":"PD_properties","baseline_native_properties":["imported","requested","applied"],"candidate_initial_values":"PD_properties","candidate_native_properties":["imported","requested","applied"]},"validation":{"inputs_unchanged":True,"producer_unchanged":True,"all_markdown_targets_absolute_existing_or_mutual_output":True,"text_lines_in_range_binary_line_suffixes_absent":True,"template_tokens_absent":True,"latest_candidate_crosslinks":True,"exclusive_outputs":True}}
with outputs["provenance"].open("x",encoding="utf-8") as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write("\\n")
print(json.dumps(record,ensure_ascii=False,indent=2))
