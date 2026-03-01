#!/usr/bin/env bash
set -euo pipefail

: "${PLAYDATE_SDK_PATH:?Set PLAYDATE_SDK_PATH to your Playdate SDK path}"
PDC="$PLAYDATE_SDK_PATH/bin/pdc"
OUTDIR="build"
mkdir -p "$OUTDIR"
"$PDC" source "$OUTDIR/Match3Prototype.pdx"
echo "Built $OUTDIR/Match3Prototype.pdx"
