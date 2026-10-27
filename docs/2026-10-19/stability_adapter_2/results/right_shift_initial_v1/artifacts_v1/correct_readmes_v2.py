#!/usr/bin/env python3
"""Create additive corrections for two consumed artifact READMEs; never overwrite."""
from pathlib import Path
import hashlib, json, re, sys

P = Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1")
I = Path("/home/ajou/yigyu/3/docs/2026-10-19/initial")
inputs = {
    "baseline_readme": I / "current_neck_support_v1/README.md",
    "candidate_readme_v2": P / "README_v2.md",
    "video_index_v2": Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX_v2.md"),
    "successful_v2_provenance": P / "provenance_v2.json",
    "baseline_whole_frame": I / "current_neck_support_v1/archive/native_off_v1/media/frames/whole_body/00000.png",
    "baseline_hands_frame": I / "current_neck_support_v1/archive/native_off_v1/media/frames/hands/00000.png",
    "baseline_thumb_back_frame": I / "current_neck_support_v1/archive/native_off_v1/media/frames/thumb_back/00000.png",
}
outputs = {
    "baseline_readme_v2": I / "current_neck_support_v1/README_v2.md",
    "candidate_readme_v3": P / "README_v3.md",
    "video_index_v3": Path("/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX_v3.md"),
    "provenance": P / "correction_provenance_v2.json",
}
pin_path = P / "correction_preflight_v1.json"
producer = Path(__file__)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def ensure_absent(paths):
    exists=[str(p) for p in paths if p.exists()]
    if exists: raise SystemExit("Refusing overwrite: " + ", ".join(exists))

def targets(text):
    # Markdown image/link destinations, excluding optional title text.
    for m in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", text):
        raw=m.group(1).strip().split()[0].strip("<>")
        yield raw

def validate_doc(path):
    text=path.read_text(encoding="utf-8")
    if re.search(r"\{(?:AR|A|P|V)\}", text): raise SystemExit(f"template token in {path}")
    for target in targets(text):
        if not target.startswith("/"): raise SystemExit(f"non-absolute target in {path}: {target}")
        dest=Path(target.split("#",1)[0].split(":",1)[0])
        if not dest.exists(): raise SystemExit(f"missing markdown target in {path}: {target}")
    return text

if len(sys.argv) != 2: raise SystemExit("usage: correct_readmes_v2.py PREFLIGHT.json")
pin=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if pin.get("producer_path") != str(producer) or pin.get("producer_sha256_before") != sha(producer):
    raise SystemExit("producer does not match its preflight pin")
if pin.get("inputs") != {k:{"path":str(v),"sha256_before":sha(v)} for k,v in inputs.items()}:
    raise SystemExit("input set/hash mismatch against preflight pin")
ensure_absent(outputs.values())
base=inputs["baseline_readme"].read_text(encoding="utf-8")
base=base.replace("![Native 손 0초]({AR}/native_off_v1/media/frames/hands/00000.png)", "![Native 손 0초](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/archive/native_off_v1/media/frames/hands/00000.png)")
base=base.replace("![Native 엄지 뒤 0초]({AR}/native_off_v1/media/frames/thumb_back/00000.png)", "![Native 엄지 뒤 0초](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/archive/native_off_v1/media/frames/thumb_back/00000.png)")
if "{AR}" in base: raise SystemExit("baseline README correction did not remove all {AR} tokens")
cand=inputs["candidate_readme_v2"].read_text(encoding="utf-8")
video_index=inputs["video_index_v2"].read_text(encoding="utf-8")
video_prov=json.loads(inputs["successful_v2_provenance"].read_text(encoding="utf-8"))
video_outputs={x["destination"]:x["output_sha256"] for x in video_prov["outputs"] if x.get("kind")=="video" and "/video/right_shift_initial_v1/video_v2/" in x["destination"]}
if len(video_outputs)!=3: raise SystemExit("successful V2 provenance does not contain exactly three videos")
for video_path,digest in video_outputs.items():
    vp=Path(video_path)
    if not vp.is_file() or sha(vp)!=digest: raise SystemExit(f"successful V2 media path/SHA mismatch: {vp}")
for doc_label,doc_text in (("candidate README v3",cand),("video INDEX v3",video_index)):
    linked_videos={t.split(":",1)[0] for t in targets(doc_text) if t.endswith(".mp4")}
    if linked_videos != set(video_outputs): raise SystemExit(f"{doc_label} video links do not equal successful V2 output destinations")
old="G 39개 body 회전과 기타 초기 예측값은 exact였고 FK·57 body·9 head·6 finger·42 guitar 초기각도도 exact였습니다."
new="몸통 9개·머리 6개·손가락 42개, 합계 57개 초기 DOF 각도는 exact였습니다. 기타 39개 body의 quaternion/translation 초기 상태도 exact였고 FK를 검증했습니다."
if cand.count(old) != 1: raise SystemExit("expected unique inaccurate sentence not found")
cand=cand.replace(old,new)
# Validate all destination links/images before creating outputs.
for label,text in (("baseline README v2",base),("candidate README v3",cand),("video INDEX v3",video_index)):
    if re.search(r"\{(?:AR|A|P|V)\}",text): raise SystemExit(f"template token in {label}")
    for target in targets(text):
        if not target.startswith("/"): raise SystemExit(f"non-absolute link in {label}: {target}")
        dest=Path(target.split("#",1)[0].split(":",1)[0])
        if not dest.exists(): raise SystemExit(f"missing link target in {label}: {target}")
# Exclusive creation; if any step fails, outputs are retained and a fresh version is required.
for key,text in (("baseline_readme_v2",base),("candidate_readme_v3",cand),("video_index_v3",video_index)):
    with outputs[key].open("x",encoding="utf-8",newline="") as f: f.write(text)
for key in ("baseline_readme_v2","candidate_readme_v3","video_index_v3"): validate_doc(outputs[key])
input_after={k:sha(v) for k,v in inputs.items()}
input_before={k:v["sha256_before"] for k,v in pin["inputs"].items()}
producer_after=sha(producer)
if input_after != input_before or producer_after != pin["producer_sha256_before"]:
    raise SystemExit("input or producer changed during correction")
record={
 "schema":"readme_correction_provenance_v1",
 "purpose":"Add corrected versions without modifying consumed README or native/media sources.",
 "producer":{"path":str(producer),"sha256_before":pin["producer_sha256_before"],"sha256_after":producer_after},
 "preflight_pin":{"path":str(Path(sys.argv[1])),"sha256":sha(Path(sys.argv[1]))},
 "inputs":{k:{"path":str(v),"sha256_before":input_before[k],"sha256_after":input_after[k]} for k,v in inputs.items()},
 "outputs":{k:{"path":str(v),"sha256":sha(v),"bytes":v.stat().st_size} for k,v in outputs.items() if k!="provenance"},
 "successful_video_mapping":{path:{"sha256":digest} for path,digest in video_outputs.items()},
 "validation":{"inputs_unchanged":True,"producer_unchanged":True,"all_markdown_targets_absolute_and_existing":True,"template_tokens_absent":True,"video_links_match_successful_v2_provenance_paths_and_sha":True,"exclusive_outputs":True}
}
with outputs["provenance"].open("x",encoding="utf-8") as f: json.dump(record,f,ensure_ascii=False,indent=2); f.write("\n")
print(json.dumps(record,ensure_ascii=False,indent=2))
