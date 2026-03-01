#!/usr/bin/env bash
set -euo pipefail

if [ -z "${PLAYDATE_SDK_PATH:-}" ]; then
  # auto-detect SDK under home if env var is not set
  CAND=$(find "$HOME" -maxdepth 1 -type d -name "PlaydateSDK*" | sort | tail -n1 || true)
  if [ -n "$CAND" ]; then
    PLAYDATE_SDK_PATH="$CAND"
  else
    echo "Set PLAYDATE_SDK_PATH to your Playdate SDK path" >&2
    exit 1
  fi
fi
PDC="$PLAYDATE_SDK_PATH/bin/pdc"
OUTDIR="build"
mkdir -p "$OUTDIR"
"$PDC" -sdkpath "$PLAYDATE_SDK_PATH" source "$OUTDIR/Match3Prototype.pdx"
echo "Built $OUTDIR/Match3Prototype.pdx"
