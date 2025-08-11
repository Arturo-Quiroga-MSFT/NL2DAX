#!/usr/bin/env bash
set -euo pipefail
# Export Mermaid diagrams in README.md to PNG/SVG using @mermaid-js/mermaid-cli (mmdc)
# Prereqs: Node.js and mmdc
# Install once:
#   npm install -g @mermaid-js/mermaid-cli
# Usage:
#   ./docs/export-diagrams.sh

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
OUT_DIR="$ROOT_DIR/docs/images"
README="$ROOT_DIR/README.md"

mkdir -p "$OUT_DIR"

# Extract mermaid fenced blocks and export each to PNG/SVG
awk -v outdir="$OUT_DIR" '
  BEGIN{inblk=0; idx=0; buf=""}
  /^```mermaid[ \t]*$/ {inblk=1; buf=""; next}
  /^```[ \t]*$/ && inblk==1 {
    file=sprintf("%s/diagram_%d.mmd", outdir, idx);
    printf "%s", buf > file;
    close(file);
    cmd=sprintf("mmdc -i \"%s\" -o \"%s/diagram_%d.png\" -b transparent", file, outdir, idx);
    system(cmd);
    cmd=sprintf("mmdc -i \"%s\" -o \"%s/diagram_%d.svg\" -b transparent", file, outdir, idx);
    system(cmd);
    printf("Exported diagram_%d.(png|svg)\n", idx);
    idx++; inblk=0; buf=""; next;
  }
  inblk==1 { buf = buf $0 "\n" }
' "$README"

echo "All diagrams exported to $OUT_DIR"
