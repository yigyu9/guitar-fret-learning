#!/usr/bin/env bash
set -u
ROOT=/home/ajou/yigyu/3
OUT="$ROOT/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts"
LOG=/tmp/finger_contact_map_artifact_run.log
MPLDIR=/tmp/finger_contact_map_artifact_mplconfig
mkdir -p "$MPLDIR"
MPLCONFIGDIR="$MPLDIR" MPLBACKEND=Agg /home/ajou/miniconda3/envs/rl38/bin/python "$ROOT/stability_adapter_2/make_finger_contact_map_artifacts.py" > "$LOG" 2>&1
status=$?
cp "$LOG" "$OUT/producer.log"
cat "$LOG"
exit "$status"
