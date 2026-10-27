#!/usr/bin/env python3
"""Create final additive README/index corrections; never overwrite prior artifacts."""
from pathlib import Path
import hashlib,json,re,sys
P=Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1")
V=Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1")
I=Path("/home/ajou/yigyu/3/docs/2026-10-19/initial")
inputs={
 "readme_v3":P/"README_v3.md",
 "index_v3":V/"INDEX_v3.md",
 "successful_video_provenance_v2":P/"provenance_v2.json",
 "comparison_v1":Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/comparison_v1.json"),
 "baseline_initial_values":Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/initial_values.json"),
 "candidate_initial_values":Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/native_right10_v1/initial_values.json"),
 "baseline_readme_v2":I/"current_neck_support_v1/README_v2.md",
 "archive_readme_v2":I/"right_shift10_comparison_v1/README_v2.md",
}
outputs={
 "readme_v4":P/"README_v4.md",
 "index_v4":V/"INDEX_v4.md",
 "provenance":P/"correction_provenance_v4.json",
}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def links(s):
 for m in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)",s):yield m.group(1).strip().split()[0].strip("<>")
def check_doc(s,label):
 if re.search(r"\{(?:AR|A|P|V)\}",s):raise SystemExit(f"template token in {label}")
 for t in links(s):
  if not t.startswith("/"):raise SystemExit(f"nonabsolute link in {label}: {t}")
  q=Path(t.split("#",1)[0].split(":",1)[0])
  if not q.exists() and q not in outputs.values():raise SystemExit(f"missing link target in {label}: {t}")
if len(sys.argv)!=2:raise SystemExit("usage: correct_readmes_v4.py PREFLIGHT.json")
pinfile=Path(sys.argv[1]);pin=json.loads(pinfile.read_text())
producer=Path(__file__)
if pin.get("producer_path")!=str(producer) or pin.get("producer_sha256_before")!=sha(producer):raise SystemExit("producer pin mismatch")
if pin.get("inputs")!={k:{"path":str(v),"sha256_before":sha(v)} for k,v in inputs.items()}:raise SystemExit("input pin mismatch")
if any(x.exists() for x in outputs.values()):raise SystemExit("refusing to overwrite existing output")
prov=json.loads(inputs["successful_video_provenance_v2"].read_text())
video={x["destination"]:x["output_sha256"] for x in prov["outputs"] if x.get("kind")=="video" and "/video/right_shift_initial_v1/video_v2/" in x["destination"]}
if len(video)!=3:raise SystemExit("expected three successful V2 video outputs")
for path,digest in video.items():
 q=Path(path)
 if not q.is_file() or sha(q)!=digest:raise SystemExit(f"success-output path/SHA mismatch: {path}")
# Verify the native initial-state quaternion arrays and intended common translation.
b=json.loads(inputs["baseline_initial_values"].read_text())
c=json.loads(inputs["candidate_initial_values"].read_text())
if len(b["native_initial_state"]["guitar_body_states"])!=39 or len(c["native_initial_state"]["guitar_body_states"])!=39:raise SystemExit("unexpected guitar body count")
for x,y in zip(b["native_initial_state"]["guitar_body_states"],c["native_initial_state"]["guitar_body_states"]):
 if x["pose"]["r"]!=y["pose"]["r"]:raise SystemExit("guitar quaternion raw values differ")
# The comparison's stated actor/root shift is the applied common translation; allow its documented <=3um residual.
shift=(0.00999254,0.00038654,0.0)
max_residual=0.0
for x,y in zip(b["native_initial_state"]["guitar_body_states"],c["native_initial_state"]["guitar_body_states"]):
 p1=x["pose"]["p"];p2=y["pose"]["p"]
 residual=sum((p2[k]-p1[k]-shift[i])**2 for i,k in enumerate("xyz"))**0.5
 max_residual=max(max_residual,residual)
if max_residual>=3e-6:raise SystemExit(f"guitar translation residual exceeds 3um: {max_residual}")
text=inputs["readme_v3"].read_text()
old="기타 39개 body의 quaternion/translation 초기 상태도 exact였고 FK를 검증했습니다."
new="기타 39개 body의 초기 quaternion 원시값은 exact였고, 의도한 공통 이동 대비 translation 잔차는 3 µm 미만이었으며 FK를 검증했습니다."
if text.count(old)!=1:raise SystemExit("expected unique guitar wording not found")
text=text.replace(old,new)
text=text.replace("/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/README.md", "/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/FILES.md")
text=text.replace("/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README.md", "/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README_v2.md")
text=text.replace("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX.md", "/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX_v4.md")
idx=inputs["index_v3"].read_text().replace("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/README.md", "/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/README_v4.md")
for label,doc in (("README_v4",text),("INDEX_v4",idx)):
 check_doc(doc,label)
 linked={t.split(":",1)[0] for t in links(doc) if t.endswith(".mp4")}
 if linked!=set(video):raise SystemExit(f"{label} video targets differ from provenance V2 output map")
for key,doc in (("readme_v4",text),("index_v4",idx)):
 with outputs[key].open("x",encoding="utf-8",newline="") as f:f.write(doc)
# Revalidate written documents and all original inputs/source remain unchanged.
for key in ("readme_v4","index_v4"):check_doc(outputs[key].read_text(),key)
input_after={k:sha(v) for k,v in inputs.items()}
input_before={k:v["sha256_before"] for k,v in pin["inputs"].items()}
producer_after=sha(producer)
if input_after!=input_before or producer_after!=pin["producer_sha256_before"]:raise SystemExit("input or producer changed")
record={"schema":"readme_correction_provenance_v3","producer":{"path":str(producer),"sha256_before":pin["producer_sha256_before"],"sha256_after":producer_after},"preflight_pin":{"path":str(pinfile),"sha256":sha(pinfile)},"inputs":{k:{"path":str(v),"sha256_before":input_before[k],"sha256_after":input_after[k]} for k,v in inputs.items()},"outputs":{k:{"path":str(v),"sha256":sha(v),"bytes":v.stat().st_size} for k,v in outputs.items() if k!="provenance"},"successful_v2_videos":{p:{"sha256":d} for p,d in video.items()},"validation":{"inputs_unchanged":True,"producer_unchanged":True,"markdown_targets_absolute_existing":True,"no_template_tokens":True,"video_links_match_successful_provenance_paths_and_sha":True,"raw_guitar_quaternion_exact":True,"common_translation_residual_max_m":max_residual,"guitar_translation_tolerance_m":3e-6,"exclusive_outputs":True}}
with outputs["provenance"].open("x",encoding="utf-8") as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps(record,ensure_ascii=False,indent=2))
