#!/usr/bin/env bash
set -euo pipefail

# Export all Mermaid .mmd diagrams to PNG and SVG using mermaid-cli.
# Defaults:
#   - Source: AQ-NEW-NL2SQL/docs/diagrams
#   - Output: AQ-NEW-NL2SQL/docs/diagrams/generated
# Usage:
#   bash scripts/export_diagrams.sh
#   DIAGRAM_SRC=path/to/src DIAGRAM_OUT=path/to/out bash scripts/export_diagrams.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SRC_DIR="${DIAGRAM_SRC:-${REPO_ROOT}/AQ-NEW-NL2SQL/docs/diagrams}"
OUT_DIR="${DIAGRAM_OUT:-${SRC_DIR}/generated}"

echo "[INFO] Mermaid export: src='${SRC_DIR}' out='${OUT_DIR}'"

if ! command -v npx >/dev/null 2>&1; then
  echo "[ERROR] 'npx' not found. Please install Node.js. On macOS: brew install node" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

shopt -s nullglob
mmdfiles=("${SRC_DIR}"/*.mmd)
if [ ${#mmdfiles[@]} -eq 0 ]; then
  echo "[WARN] No .mmd files found in ${SRC_DIR}"
  exit 0
fi

THEME="neutral"
SCALE="1.5"

for f in "${mmdfiles[@]}"; do
  base="$(basename "${f}" .mmd)"
  echo "[INFO] Rendering ${base}.mmd -> PNG/SVG"
  # PNG
  npx -y @mermaid-js/mermaid-cli \
    -i "${f}" \
    -o "${OUT_DIR}/${base}.png" \
    --backgroundColor transparent \
    --theme "${THEME}" \
    --scale "${SCALE}"

  # SVG
  npx -y @mermaid-js/mermaid-cli \
    -i "${f}" \
    -o "${OUT_DIR}/${base}.svg" \
    --backgroundColor transparent \
    --theme "${THEME}"
done

echo "[INFO] Done. Generated files in ${OUT_DIR}"
