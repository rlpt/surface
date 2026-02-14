#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://upload.zolanic.space"
OUT_DIR="${SURFACE_ROOT}/out/image-upload"

# --- Help ---

cmd_help() {
  echo "image-upload — upload images from your phone via QR code"
  echo ""
  echo "Usage: image-upload [help]"
  echo ""
  echo "  (no args)   Start an upload session (displays QR code)"
  echo "  help        Show this help"
  echo ""
  echo "Images are saved to out/image-upload/<session-id>/"
}

# --- Upload flow ---

cmd_upload() {
  echo "Creating upload session..."
  if ! RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 -X POST "$BASE_URL/api/session"); then
    echo "Error: Could not reach $BASE_URL (is the server running?)"
    exit 1
  fi
  SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id')
  UPLOAD_URL=$(echo "$RESPONSE" | jq -r '.upload_url')

  if [ -z "$SESSION_ID" ] || [ "$SESSION_ID" = "null" ]; then
    echo "Error: Failed to create upload session"
    echo "Response: $RESPONSE"
    exit 1
  fi

  echo ""
  echo "Scan this QR code with your phone:"
  echo ""
  qrencode -t UTF8 "$UPLOAD_URL"
  echo ""
  echo "Or open: $UPLOAD_URL"
  echo ""
  echo "Waiting for image upload..."

  TIMEOUT=300
  ELAPSED=0
  while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(curl -s --connect-timeout 5 --max-time 10 "$BASE_URL/$SESSION_ID/status")
    UPLOAD_STATUS=$(echo "$STATUS" | jq -r '.status')

    if [ "$UPLOAD_STATUS" = "ready" ]; then
      FILENAME=$(echo "$STATUS" | jq -r '.filename')
      echo "Image received: $FILENAME"

      LOCAL_DIR="$OUT_DIR/$SESSION_ID"
      mkdir -p "$LOCAL_DIR"
      LOCAL_PATH="$LOCAL_DIR/$FILENAME"

      curl -s --connect-timeout 5 --max-time 30 -o "$LOCAL_PATH" "$BASE_URL/$SESSION_ID/image"

      echo ""
      echo "$LOCAL_PATH"
      if command -v pbcopy &>/dev/null; then
        echo -n "$LOCAL_PATH" | pbcopy
        echo "(path copied to clipboard)"
      fi
      exit 0
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))
    if [ $((ELAPSED % 10)) -eq 0 ]; then
      printf "."
    fi
  done

  echo ""
  echo "Error: Timed out waiting for upload (5 minutes)"
  exit 1
}

# --- Routing ---

case "${1:-}" in
  help)  cmd_help ;;
  "")    cmd_upload ;;
  *)     cmd_help ;;
esac
