#!/usr/bin/env bash
set -euo pipefail

MARKETING_DIR="${SURFACE_ROOT}/modules/marketing"
THEMES_DIR="${MARKETING_DIR}/themes"
DECKS_DIR="${MARKETING_DIR}/decks"
HANDBOOK_DIR="${MARKETING_DIR}/handbook"
DIAGRAMS_DIR="${MARKETING_DIR}/diagrams"
LEGAL_DIR="${SURFACE_ROOT}/legal"
INVESTOR_DIR="${MARKETING_DIR}/investor"
OUT_DIR="${SURFACE_ROOT}/out/marketing"
GDRIVE_CONFIG="${HOME}/.config/formabi/gdrive.json"

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

cmd_legal_build() {
  mkdir -p "$OUT_DIR/legal"

  # Collect legal docs in a specific reading order
  local md_files=()
  local order=(
    "investor-readiness.md"
    "first-time-founder.md"
    "articles-of-association.md"
    "articles-guide.md"
    "ip-assignment.md"
    "founder-service-agreement.md"
    "seis-eis-guide.md"
    "early-supporter-shares.md"
    "document-management.md"
    "brand-document-system.md"
  )

  for f in "${order[@]}"; do
    if [ -f "$LEGAL_DIR/$f" ]; then
      md_files+=("$LEGAL_DIR/$f")
    fi
  done

  # Append board minutes
  if [ -d "$LEGAL_DIR/board-minutes" ]; then
    for f in "$LEGAL_DIR/board-minutes"/*.md; do
      [ -f "$f" ] && md_files+=("$f")
    done
  fi

  if [ ${#md_files[@]} -eq 0 ]; then
    echo "No legal documents found in $LEGAL_DIR" >&2
    return 1
  fi

  pandoc "${md_files[@]}" \
    --from markdown --to html5 --standalone \
    --template "$THEMES_DIR/handbook.html" \
    --toc --toc-depth=2 \
    --metadata title="Legal & Governance" \
    -o "$OUT_DIR/legal/legal.html"

  echo "Legal handbook built to $OUT_DIR/legal/ (${#md_files[@]} documents)"
}

cmd_legal_serve() {
  cmd_legal_build
  echo "Serving legal handbook at http://localhost:8001"
  python3 -m http.server 8001 -d "$OUT_DIR/legal/"
}

cmd_legal_pdf() {
  local file="${1:-}"

  if [ -z "$file" ]; then
    echo "Usage: marketing legal-pdf <file.md>       Build one legal doc to PDF" >&2
    echo "       marketing legal-pdf --all            Build all legal docs to PDF" >&2
    return 1
  fi

  mkdir -p "$OUT_DIR/legal/pdf"

  if [ "$file" = "--all" ]; then
    local count=0
    for f in "$LEGAL_DIR"/*.md; do
      [ -f "$f" ] || continue
      local name
      name=$(basename "$f" .md)
      pandoc "$f" --from markdown --to pdf \
        --pdf-engine=tectonic \
        --variable geometry:margin=2.5cm \
        --variable fontsize=11pt \
        --variable mainfont="Inter" \
        --variable monofont="JetBrains Mono" \
        -o "$OUT_DIR/legal/pdf/${name}.pdf" 2>/dev/null || \
      pandoc "$f" --from markdown --to pdf \
        --variable geometry:margin=2.5cm \
        --variable fontsize=11pt \
        -o "$OUT_DIR/legal/pdf/${name}.pdf"
      count=$((count + 1))
    done
    # Board minutes
    if [ -d "$LEGAL_DIR/board-minutes" ]; then
      for f in "$LEGAL_DIR/board-minutes"/*.md; do
        [ -f "$f" ] || continue
        local name
        name=$(basename "$f" .md)
        pandoc "$f" --from markdown --to pdf \
          --pdf-engine=tectonic \
          --variable geometry:margin=2.5cm \
          --variable fontsize=11pt \
          --variable mainfont="Inter" \
          --variable monofont="JetBrains Mono" \
          -o "$OUT_DIR/legal/pdf/board-minutes-${name}.pdf" 2>/dev/null || \
        pandoc "$f" --from markdown --to pdf \
          --variable geometry:margin=2.5cm \
          --variable fontsize=11pt \
          -o "$OUT_DIR/legal/pdf/board-minutes-${name}.pdf"
        count=$((count + 1))
      done
    fi
    echo "Built $count PDFs to $OUT_DIR/legal/pdf/"
  else
    if [ ! -f "$file" ]; then
      # Try relative to legal dir
      file="$LEGAL_DIR/$file"
    fi
    if [ ! -f "$file" ]; then
      echo "Error: File not found: $file" >&2
      return 1
    fi
    local name
    name=$(basename "$file" .md)
    pandoc "$file" --from markdown --to pdf \
      --pdf-engine=tectonic \
      --variable geometry:margin=2.5cm \
      --variable fontsize=11pt \
      --variable mainfont="Inter" \
      --variable monofont="JetBrains Mono" \
      -o "$OUT_DIR/legal/pdf/${name}.pdf" 2>/dev/null || \
    pandoc "$file" --from markdown --to pdf \
      --variable geometry:margin=2.5cm \
      --variable fontsize=11pt \
      -o "$OUT_DIR/legal/pdf/${name}.pdf"
    echo "Built $OUT_DIR/legal/pdf/${name}.pdf"
  fi
}

cmd_diagrams() {
  mkdir -p "$OUT_DIR/diagrams"
  for mmd in "$DIAGRAMS_DIR"/*.mmd; do
    name=$(basename "$mmd" .mmd)
    mmdc -i "$mmd" -o "$OUT_DIR/diagrams/$name.svg"
  done
  echo "Built diagrams to $OUT_DIR/diagrams/"
}

# --- Google Docs push ---

gdrive_get_token() {
  if [ ! -f "$GDRIVE_CONFIG" ]; then
    echo "Error: No Google Drive credentials found." >&2
    echo "Run 'marketing push-doc-setup' first." >&2
    return 1
  fi

  local client_id client_secret refresh_token
  client_id=$(jq -r '.client_id' "$GDRIVE_CONFIG")
  client_secret=$(jq -r '.client_secret' "$GDRIVE_CONFIG")
  refresh_token=$(jq -r '.refresh_token' "$GDRIVE_CONFIG")

  curl -s -X POST "https://oauth2.googleapis.com/token" \
    -d "client_id=${client_id}" \
    -d "client_secret=${client_secret}" \
    -d "refresh_token=${refresh_token}" \
    -d "grant_type=refresh_token" | jq -r '.access_token'
}

cmd_push_doc_setup() {
  echo "=== Google Drive setup for push-doc ==="
  echo ""
  echo "You need a Google Cloud project with the Drive API enabled."
  echo "Create OAuth credentials (Desktop app) at:"
  echo "  https://console.cloud.google.com/apis/credentials"
  echo ""

  read -rp "Client ID: " client_id
  read -rp "Client Secret: " client_secret

  local auth_url="https://accounts.google.com/o/oauth2/v2/auth?client_id=${client_id}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&scope=https://www.googleapis.com/auth/drive.file&access_type=offline"

  echo ""
  echo "Open this URL in your browser and authorize:"
  echo ""
  echo "  ${auth_url}"
  echo ""

  read -rp "Paste the authorization code: " auth_code

  local token_response
  token_response=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
    -d "client_id=${client_id}" \
    -d "client_secret=${client_secret}" \
    -d "code=${auth_code}" \
    -d "redirect_uri=urn:ietf:wg:oauth:2.0:oob" \
    -d "grant_type=authorization_code")

  local refresh_token
  refresh_token=$(echo "$token_response" | jq -r '.refresh_token')

  if [ "$refresh_token" = "null" ] || [ -z "$refresh_token" ]; then
    echo "Error: Failed to get refresh token." >&2
    echo "Response: $token_response" >&2
    return 1
  fi

  mkdir -p "$(dirname "$GDRIVE_CONFIG")"
  jq -n \
    --arg cid "$client_id" \
    --arg cs "$client_secret" \
    --arg rt "$refresh_token" \
    '{ client_id: $cid, client_secret: $cs, refresh_token: $rt }' > "$GDRIVE_CONFIG"
  chmod 600 "$GDRIVE_CONFIG"

  echo ""
  echo "Credentials saved to $GDRIVE_CONFIG"
  echo "You can now use 'marketing push-doc <file.md>'"
}

cmd_push_doc() {
  local file="" title="" doc_id="" folder_id=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --title)   title="$2"; shift 2 ;;
      --update)  doc_id="$2"; shift 2 ;;
      --folder)  folder_id="$2"; shift 2 ;;
      -*)        echo "Unknown option: $1" >&2; return 1 ;;
      *)         file="$1"; shift ;;
    esac
  done

  if [ -z "$file" ]; then
    echo "Usage: marketing push-doc <file.md> [--title \"Title\"] [--update <doc-id>] [--folder <folder-id>]" >&2
    return 1
  fi

  if [ ! -f "$file" ]; then
    echo "Error: File not found: $file" >&2
    return 1
  fi

  # Default title from filename
  if [ -z "$title" ]; then
    title=$(basename "$file" .md)
  fi

  # Convert markdown to docx
  local tmp_docx
  tmp_docx=$(mktemp /tmp/push-doc-XXXXXX.docx)
  trap "rm -f '$tmp_docx'" EXIT

  echo "Converting $file → docx..."
  pandoc "$file" -o "$tmp_docx"

  # Get access token
  local access_token
  access_token=$(gdrive_get_token)

  if [ -z "$access_token" ] || [ "$access_token" = "null" ]; then
    echo "Error: Failed to get access token. Run 'marketing push-doc-setup'." >&2
    return 1
  fi

  if [ -n "$doc_id" ]; then
    # Update existing document
    echo "Updating document ${doc_id}..."
    curl -s -X PATCH \
      -H "Authorization: Bearer ${access_token}" \
      -H "Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
      --data-binary @"$tmp_docx" \
      "https://www.googleapis.com/upload/drive/v3/files/${doc_id}?uploadType=media" > /dev/null

    echo "Updated: https://docs.google.com/document/d/${doc_id}"
  else
    # Create new document
    echo "Uploading as '${title}'..."

    # Build metadata
    local metadata
    metadata=$(jq -n --arg name "$title" --arg folder "$folder_id" \
      'if $folder != "" then { name: $name, mimeType: "application/vnd.google-apps.document", parents: [$folder] }
       else { name: $name, mimeType: "application/vnd.google-apps.document" } end')

    local response
    response=$(curl -s -X POST \
      -H "Authorization: Bearer ${access_token}" \
      -F "metadata=${metadata};type=application/json" \
      -F "file=@${tmp_docx};type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
      "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart")

    local new_id
    new_id=$(echo "$response" | jq -r '.id')

    if [ "$new_id" = "null" ] || [ -z "$new_id" ]; then
      echo "Error: Upload failed." >&2
      echo "Response: $response" >&2
      return 1
    fi

    echo "Created: https://docs.google.com/document/d/${new_id}"
  fi
}

cmd_help() {
  echo "marketing — pitch decks, handbook, legal docs & diagrams"
  echo ""
  echo "Usage: marketing <command>"
  echo ""
  echo "Commands:"
  echo "  serve              Live preview decks with hot reload"
  echo "  build              Build all decks to out/marketing/"
  echo "  handbook-build     Build handbook to out/marketing/handbook/"
  echo "  handbook-serve     Build + serve handbook at :8000"
  echo "  legal-build        Build legal docs to out/marketing/legal/"
  echo "  legal-serve        Build + serve legal handbook at :8001"
  echo "  legal-pdf <file>   Build a legal doc to PDF (or --all for all)"
  echo "  diagrams           Build .mmd diagrams to out/marketing/diagrams/"
  echo "  push-doc <file>    Push markdown to Google Docs (formatted)"
  echo "  push-doc-setup     One-time Google Drive OAuth setup"
  echo "  help               Show this help"
  echo ""
  echo "push-doc options:"
  echo "  --title \"Title\"    Set the document title (default: filename)"
  echo "  --update <doc-id>  Update an existing Google Doc instead of creating new"
  echo "  --folder <id>      Upload into a specific Google Drive folder"
}

# --- Routing ---

case "${1:-help}" in
  serve)          cmd_serve ;;
  build)          cmd_build ;;
  handbook-build) cmd_handbook_build ;;
  handbook-serve) cmd_handbook_serve ;;
  legal-build)    cmd_legal_build ;;
  legal-serve)    cmd_legal_serve ;;
  legal-pdf)      shift; cmd_legal_pdf "$@" ;;
  diagrams)        cmd_diagrams ;;
  push-doc)        shift; cmd_push_doc "$@" ;;
  push-doc-setup)  cmd_push_doc_setup ;;
  help|*)          cmd_help ;;
esac
