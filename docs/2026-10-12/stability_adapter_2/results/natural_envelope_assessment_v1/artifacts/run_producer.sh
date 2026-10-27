#!/usr/bin/env bash
set -u
ROOT=/home/ajou/yigyu/3
OUT="$ROOT/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts"
for path in "$OUT/run_producer.sh.archived" "$OUT/producer.log" "$OUT/producer_execution.json" "$OUT/natural_envelope_limits.png" "$OUT/artifact_manifest.json" "$OUT/source_snapshot.json" "$OUT/source_snapshot"; do
  if [ -e "$path" ]; then
    echo "refusing to overwrite existing execution evidence: $path" >&2
    exit 2
  fi
done
cp "$0" "$OUT/run_producer.sh.archived"
set +e
cd "$ROOT"
MPLBACKEND=Agg /home/ajou/miniconda3/bin/python "$ROOT/stability_adapter_2/make_natural_envelope_artifacts.py" --out-dir "$OUT" > "$OUT/producer.log" 2>&1
status=$?
set -e
printf '{"command":["/home/ajou/miniconda3/bin/python","%s/make_natural_envelope_artifacts.py","--out-dir","%s"],"environment":{"MPLBACKEND":"Agg"},"exit_code":%s}\n' "$ROOT/stability_adapter_2" "$OUT" "$status" > "$OUT/producer_execution.json"
exit "$status"
