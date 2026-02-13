#!/usr/bin/env bash
set -euo pipefail

CAP_TABLE_DIR="${SURFACE_ROOT}/modules/shares/cap-table"
CLASSES_FILE="${CAP_TABLE_DIR}/classes.ledger"
HOLDERS_FILE="${CAP_TABLE_DIR}/holders.ledger"
EVENTS_FILE="${CAP_TABLE_DIR}/events.ledger"

# --- Helpers ---

die() { echo "error: $1" >&2; exit 1; }

# Parse classes into associative arrays
declare -A CLASS_NOMINAL CLASS_AUTHORISED
load_classes() {
  while read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    read -r _kw name nominal authorised <<< "$line"
    [[ "$_kw" == "class" ]] || continue
    CLASS_NOMINAL["$name"]="$nominal"
    CLASS_AUTHORISED["$name"]="$authorised"
  done < "$CLASSES_FILE"
}

# Parse holders into associative array
declare -A HOLDER_NAME
load_holders() {
  while read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    read -r _kw id rest <<< "$line"
    [[ "$_kw" == "holder" ]] || continue
    HOLDER_NAME["$id"]="$rest"
  done < "$HOLDERS_FILE"
}

# Parse events and compute holdings
# Populates HOLDINGS[holder:class] = count
declare -A HOLDINGS VESTING_START VESTING_MONTHS VESTING_CLIFF
load_events() {
  local last_holder="" last_class=""
  while IFS= read -r line; do
    # Skip comments and blank lines
    [[ "$line" =~ ^[[:space:]]*#.*$ || -z "$line" ]] && continue

    # Check for indented vesting line
    if [[ "$line" =~ ^[[:space:]]+vesting[[:space:]] ]]; then
      local trimmed
      trimmed=$(echo "$line" | xargs)
      read -r _kw start months cliff <<< "$trimmed"
      if [[ -n "$last_holder" && -n "$last_class" ]]; then
        VESTING_START["${last_holder}:${last_class}"]="$start"
        VESTING_MONTHS["${last_holder}:${last_class}"]="$months"
        VESTING_CLIFF["${last_holder}:${last_class}"]="$cliff"
      fi
      continue
    fi

    read -r date event_type holder_id share_class quantity <<< "$line"
    [[ -z "$quantity" ]] && continue

    local key="${holder_id}:${share_class}"
    local current="${HOLDINGS[$key]:-0}"

    case "$event_type" in
      grant|transfer-in)
        HOLDINGS["$key"]=$((current + quantity))
        ;;
      transfer-out|cancel)
        HOLDINGS["$key"]=$((current - quantity))
        ;;
    esac

    last_holder="$holder_id"
    last_class="$share_class"
  done < "$EVENTS_FILE"
}

# Compute vested shares for a holder:class key
compute_vested() {
  local key="$1"
  local total="${HOLDINGS[$key]}"
  local start="${VESTING_START[$key]:-}"

  if [[ -z "$start" ]]; then
    echo "$total"
    return
  fi

  local months="${VESTING_MONTHS[$key]}"
  local cliff="${VESTING_CLIFF[$key]}"
  local today
  today=$(date +%Y-%m-%d)

  # Calculate months elapsed
  local start_epoch today_epoch
  if date -j -f "%Y-%m-%d" "$start" "+%s" &>/dev/null; then
    # macOS
    start_epoch=$(date -j -f "%Y-%m-%d" "$start" "+%s")
    today_epoch=$(date -j -f "%Y-%m-%d" "$today" "+%s")
  else
    # Linux
    start_epoch=$(date -d "$start" "+%s")
    today_epoch=$(date -d "$today" "+%s")
  fi

  local days_elapsed=$(( (today_epoch - start_epoch) / 86400 ))
  local months_elapsed=$(( days_elapsed / 30 ))

  if (( months_elapsed < cliff )); then
    echo "0"
  elif (( months_elapsed >= months )); then
    echo "$total"
  else
    echo $(( total * months_elapsed / months ))
  fi
}

# --- Subcommands ---

cmd_check() {
  load_classes
  load_holders
  load_events

  local errors=0

  # Check events reference valid holders and classes
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*#.*$ || -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]] ]] && continue

    read -r date event_type holder_id share_class quantity <<< "$line"
    [[ -z "$quantity" ]] && continue

    if [[ -z "${HOLDER_NAME[$holder_id]:-}" ]]; then
      echo "error: unknown holder '$holder_id' in event: $line"
      errors=$((errors + 1))
    fi

    if [[ -z "${CLASS_NOMINAL[$share_class]:-}" ]]; then
      echo "error: unknown share class '$share_class' in event: $line"
      errors=$((errors + 1))
    fi
  done < "$EVENTS_FILE"

  # Check no negative holdings
  for key in "${!HOLDINGS[@]}"; do
    local count="${HOLDINGS[$key]}"
    if (( count < 0 )); then
      echo "error: negative holding for $key ($count shares)"
      errors=$((errors + 1))
    fi
  done

  # Check total issued does not exceed authorised per class
  declare -A CLASS_TOTAL
  for key in "${!HOLDINGS[@]}"; do
    local class="${key#*:}"
    local count="${HOLDINGS[$key]}"
    CLASS_TOTAL["$class"]=$(( ${CLASS_TOTAL[$class]:-0} + count ))
  done

  for class in "${!CLASS_TOTAL[@]}"; do
    local total="${CLASS_TOTAL[$class]}"
    local authorised="${CLASS_AUTHORISED[$class]:-0}"
    if (( total > authorised )); then
      echo "error: class '$class' has $total issued but only $authorised authorised"
      errors=$((errors + 1))
    fi
  done

  if (( errors > 0 )); then
    echo ""
    echo "$errors error(s) found"
    exit 1
  fi

  echo "OK"
}

cmd_table() {
  load_classes
  load_holders
  load_events

  # Calculate total issued
  local total_issued=0
  for key in "${!HOLDINGS[@]}"; do
    local count="${HOLDINGS[$key]}"
    total_issued=$((total_issued + count))
  done

  if (( total_issued == 0 )); then
    echo "No shares issued."
    return
  fi

  # Header
  printf "%-20s %-12s %10s %8s %10s\n" "Holder" "Class" "Held" "%" "Vested"
  printf "%-20s %-12s %10s %8s %10s\n" "--------------------" "------------" "----------" "--------" "----------"

  # Sort by holder name for consistent output
  for key in $(echo "${!HOLDINGS[@]}" | tr ' ' '\n' | sort); do
    local count="${HOLDINGS[$key]}"
    (( count == 0 )) && continue

    local holder_id="${key%%:*}"
    local class="${key#*:}"
    local name="${HOLDER_NAME[$holder_id]:-$holder_id}"
    local pct
    pct=$(awk "BEGIN { printf \"%.1f\", ($count / $total_issued) * 100 }")
    local vested
    vested=$(compute_vested "$key")

    printf "%-20s %-12s %10d %7s%% %10d\n" "$name" "$class" "$count" "$pct" "$vested"
  done

  echo ""
  echo "Total issued: $total_issued"
}

cmd_export() {
  load_classes
  load_holders
  load_events

  echo "holder,share_class,shares_held,percentage,vested,total_granted,notes"

  local total_issued=0
  for key in "${!HOLDINGS[@]}"; do
    total_issued=$((total_issued + ${HOLDINGS[$key]}))
  done

  for key in $(echo "${!HOLDINGS[@]}" | tr ' ' '\n' | sort); do
    local count="${HOLDINGS[$key]}"
    (( count == 0 )) && continue

    local holder_id="${key%%:*}"
    local class="${key#*:}"
    local name="${HOLDER_NAME[$holder_id]:-$holder_id}"
    local pct
    pct=$(awk "BEGIN { printf \"%.1f\", ($count / $total_issued) * 100 }")
    local vested
    vested=$(compute_vested "$key")
    local notes=""

    if [[ -n "${VESTING_START[$key]:-}" ]]; then
      notes="vesting ${VESTING_MONTHS[$key]}m cliff ${VESTING_CLIFF[$key]}m from ${VESTING_START[$key]}"
    fi

    echo "\"$name\",\"$class\",$count,$pct,$vested,$count,\"$notes\""
  done
}

cmd_holders() {
  load_holders
  load_events

  printf "%-12s %-25s %10s\n" "ID" "Name" "Total"
  printf "%-12s %-25s %10s\n" "------------" "-------------------------" "----------"

  for holder_id in $(echo "${!HOLDER_NAME[@]}" | tr ' ' '\n' | sort); do
    local name="${HOLDER_NAME[$holder_id]}"
    local total=0
    for key in "${!HOLDINGS[@]}"; do
      if [[ "${key%%:*}" == "$holder_id" ]]; then
        total=$((total + ${HOLDINGS[$key]}))
      fi
    done
    printf "%-12s %-25s %10d\n" "$holder_id" "$name" "$total"
  done
}

cmd_history() {
  local filter="${1:-}"

  echo "Date         Event          Holder        Class        Qty"
  echo "-----------  -------------  ------------  -----------  --------"

  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*#.*$ || -z "$line" ]] && continue

    # Print vesting lines indented if we're showing the parent event
    if [[ "$line" =~ ^[[:space:]] ]]; then
      if [[ "$show_vesting" == "1" ]]; then
        echo "             $line"
      fi
      continue
    fi

    show_vesting=0
    read -r date event_type holder_id share_class quantity <<< "$line"
    [[ -z "$quantity" ]] && continue

    if [[ -z "$filter" || "$holder_id" == "$filter" ]]; then
      printf "%-11s  %-13s  %-12s  %-11s  %8d\n" "$date" "$event_type" "$holder_id" "$share_class" "$quantity"
      show_vesting=1
    fi
  done < "$EVENTS_FILE"
}

cmd_help() {
  echo "shares — cap table management"
  echo ""
  echo "Usage: shares <command> [args]"
  echo ""
  echo "Commands:"
  echo "  table              Show current cap table with percentages"
  echo "  export             Output cap table as CSV (pipe to file)"
  echo "  holders            List all shareholders with totals"
  echo "  history [holder]   Show share events (optionally filter by holder)"
  echo "  check              Validate ledger consistency"
  echo "  help               Show this help"
}

# --- Routing ---

case "${1:-help}" in
  table)    cmd_table ;;
  export)   cmd_export ;;
  holders)  cmd_holders ;;
  history)  shift; cmd_history "${1:-}" ;;
  check)    cmd_check ;;
  help|*)   cmd_help ;;
esac
