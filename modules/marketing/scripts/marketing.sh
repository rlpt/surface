#!/usr/bin/env bash
set -euo pipefail

MARKETING_DIR="${SURFACE_ROOT}/modules/marketing"
THEMES_DIR="${MARKETING_DIR}/themes"
DECKS_DIR="${MARKETING_DIR}/decks"
HANDBOOK_DIR="${MARKETING_DIR}/handbook"
DIAGRAMS_DIR="${MARKETING_DIR}/diagrams"
OUT_DIR="${SURFACE_ROOT}/out/marketing"

# --- Subcommands ---

cmd_serve() {
  marp --server "$DECKS_DIR" --theme-set "$THEMES_DIR"
}

cmd_build() {
  mkdir -p "$OUT_DIR"
  marp "$DECKS_DIR" --theme-set "$THEMES_DIR" --html -o "$OUT_DIR"
  echo "Built decks to $OUT_DIR"
}

cmd_handbook_build() {
  mkdir -p "$OUT_DIR/handbook"
  local md_files
  md_files=$(ls "$HANDBOOK_DIR"/*.md | sort)

  pandoc $md_files \
    --from markdown --to html5 --standalone \
    --template "$THEMES_DIR/handbook.html" \
    --toc --toc-depth=2 \
    --metadata title="Company Handbook" \
    -o "$OUT_DIR/handbook/handbook.html"

  echo "Handbook built to $OUT_DIR/handbook/"
}

cmd_handbook_serve() {
  cmd_handbook_build
  echo "Serving handbook at http://localhost:8000"
  python3 -m http.server 8000 -d "$OUT_DIR/handbook/"
}

cmd_diagrams() {
  mkdir -p "$OUT_DIR/diagrams"
  for mmd in "$DIAGRAMS_DIR"/*.mmd; do
    name=$(basename "$mmd" .mmd)
    mmdc -i "$mmd" -o "$OUT_DIR/diagrams/$name.svg"
  done
  echo "Built diagrams to $OUT_DIR/diagrams/"
}

cmd_help() {
  echo "marketing — pitch decks, handbook & diagrams"
  echo ""
  echo "Usage: marketing <command>"
  echo ""
  echo "Commands:"
  echo "  serve              Live preview decks with hot reload"
  echo "  build              Build all decks to out/marketing/"
  echo "  handbook-build     Build handbook to out/marketing/handbook/"
  echo "  handbook-serve     Build + serve handbook at :8000"
  echo "  diagrams           Build .mmd diagrams to out/marketing/diagrams/"
  echo "  help               Show this help"
}

# --- Routing ---

case "${1:-help}" in
  serve)          cmd_serve ;;
  build)          cmd_build ;;
  handbook-build) cmd_handbook_build ;;
  handbook-serve) cmd_handbook_serve ;;
  diagrams)       cmd_diagrams ;;
  help|*)         cmd_help ;;
esac
