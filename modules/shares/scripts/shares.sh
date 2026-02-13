#!/usr/bin/env bash
set -euo pipefail

CAP_TABLE_DIR="${SURFACE_ROOT}/modules/shares/cap-table"
CLASSES_FILE="${CAP_TABLE_DIR}/classes.ledger"
HOLDERS_FILE="${CAP_TABLE_DIR}/holders.ledger"
EVENTS_FILE="${CAP_TABLE_DIR}/events.ledger"
POOLS_FILE="${CAP_TABLE_DIR}/pools.ledger"

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

# Parse pools into arrays
# POOL_NAMES[i] = name, POOL_CLASS[name] = class, POOL_BUDGET[name] = budget
# POOL_MEMBERS[name] = space-separated holder-ids
declare -a POOL_NAMES_LIST=()
declare -A POOL_CLASS POOL_BUDGET POOL_MEMBERS
load_pools() {
  [[ -f "$POOLS_FILE" ]] || return 0
  local current_pool=""
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*#.*$ || -z "$line" ]] && continue

    if [[ "$line" =~ ^[[:space:]]+member[[:space:]] ]]; then
      local trimmed
      trimmed=$(echo "$line" | xargs)
      read -r _kw member_id <<< "$trimmed"
      if [[ -n "$current_pool" ]]; then
        POOL_MEMBERS["$current_pool"]="${POOL_MEMBERS[$current_pool]:-} $member_id"
      fi
      continue
    fi

    read -r _kw name class budget <<< "$line"
    [[ "$_kw" == "pool" ]] || continue
    current_pool="$name"
    POOL_NAMES_LIST+=("$name")
    POOL_CLASS["$name"]="$class"
    POOL_BUDGET["$name"]="$budget"
    POOL_MEMBERS["$name"]=""
  done < "$POOLS_FILE"
}

# Parse events and compute holdings
# Populates HOLDINGS[holder:class] = count
declare -A HOLDINGS VESTING_START VESTING_MONTHS VESTING_CLIFF
load_events() {
  local last_holder="" last_class=""
  local ev_date ev_type ev_holder ev_class ev_qty
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

    read -r ev_date ev_type ev_holder ev_class ev_qty <<< "$line"
    [[ -z "$ev_qty" ]] && continue

    local key="${ev_holder}:${ev_class}"
    local current="${HOLDINGS[$key]:-0}"

    case "$ev_type" in
      grant|transfer-in)
        HOLDINGS["$key"]=$((current + ev_qty))
        ;;
      transfer-out|cancel)
        HOLDINGS["$key"]=$((current - ev_qty))
        ;;
    esac

    last_holder="$ev_holder"
    last_class="$ev_class"
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

    local chk_date chk_type chk_holder chk_class chk_qty
    read -r chk_date chk_type chk_holder chk_class chk_qty <<< "$line"
    [[ -z "$chk_qty" ]] && continue

    if [[ -z "${HOLDER_NAME[$chk_holder]:-}" ]]; then
      echo "error: unknown holder '$chk_holder' in event: $line"
      errors=$((errors + 1))
    fi

    if [[ -z "${CLASS_NOMINAL[$chk_class]:-}" ]]; then
      echo "error: unknown share class '$chk_class' in event: $line"
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

# --- PDF helpers ---

DOWNLOADS_DIR="${SURFACE_ROOT}/downloads"

generate_pdf() {
  local output_file="$1"
  mkdir -p "$DOWNLOADS_DIR"
  local pdf_args=(--pdf-engine=typst -V mainfont="Helvetica" -V margin-top=2cm -V margin-bottom=2cm -V margin-left=2cm -V margin-right=2cm)
  pandoc "${pdf_args[@]}" -o "$output_file"
  echo "$output_file"
}

cmd_pdf_table() {
  load_classes
  load_holders
  load_events

  local today
  today=$(date +%Y-%m-%d)
  local output="${DOWNLOADS_DIR}/cap-table-${today}.pdf"

  local total_issued=0
  for key in "${!HOLDINGS[@]}"; do
    total_issued=$((total_issued + ${HOLDINGS[$key]}))
  done

  {
    echo "# Formabi — Cap Table"
    echo ""
    echo "Generated: $today"
    echo ""

    if (( total_issued == 0 )); then
      echo "No shares issued."
    else
      echo "| Holder | Class | Held | % | Vested |"
      echo "|--------|-------|-----:|--:|-------:|"

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
        echo "| $name | $class | $count | ${pct}% | $vested |"
      done

      echo ""
      echo "**Total issued:** $total_issued"
    fi
  } | generate_pdf "$output"
}

cmd_pdf_history() {
  load_classes
  load_holders
  load_events

  local today
  today=$(date +%Y-%m-%d)
  local output="${DOWNLOADS_DIR}/share-history-${today}.pdf"

  {
    echo "# Formabi — Share History"
    echo ""
    echo "Generated: $today"
    echo ""
    echo "| Date | Event | Holder | Class | Qty |"
    echo "|------|-------|--------|-------|----:|"

    while IFS= read -r line; do
      [[ "$line" =~ ^[[:space:]]*#.*$ || -z "$line" ]] && continue
      [[ "$line" =~ ^[[:space:]] ]] && continue

      read -r date event_type holder_id share_class quantity <<< "$line"
      [[ -z "$quantity" ]] && continue
      local name="${HOLDER_NAME[$holder_id]:-$holder_id}"
      echo "| $date | $event_type | $name | $share_class | $quantity |"
    done < "$EVENTS_FILE"
  } | generate_pdf "$output"
}

cmd_pdf_holder() {
  local holder_id="${1:-}"
  [[ -z "$holder_id" ]] && die "usage: shares pdf holder <holder-id>"

  load_classes
  load_holders
  load_events

  [[ -z "${HOLDER_NAME[$holder_id]:-}" ]] && die "unknown holder: $holder_id"

  local name="${HOLDER_NAME[$holder_id]}"
  local today
  today=$(date +%Y-%m-%d)
  local output="${DOWNLOADS_DIR}/${holder_id}-statement-${today}.pdf"

  local total_issued=0
  for key in "${!HOLDINGS[@]}"; do
    total_issued=$((total_issued + ${HOLDINGS[$key]}))
  done

  {
    echo "# Formabi — Holder Statement"
    echo ""
    echo "**Holder:** $name"
    echo ""
    echo "Generated: $today"
    echo ""

    # Summary
    echo "## Current Holdings"
    echo ""
    echo "| Class | Held | % | Vested |"
    echo "|-------|-----:|--:|-------:|"

    local holder_total=0
    for key in $(echo "${!HOLDINGS[@]}" | tr ' ' '\n' | sort); do
      [[ "${key%%:*}" != "$holder_id" ]] && continue
      local count="${HOLDINGS[$key]}"
      (( count == 0 )) && continue
      local class="${key#*:}"
      local pct="0.0"
      if (( total_issued > 0 )); then
        pct=$(awk "BEGIN { printf \"%.1f\", ($count / $total_issued) * 100 }")
      fi
      local vested
      vested=$(compute_vested "$key")
      echo "| $class | $count | ${pct}% | $vested |"
      holder_total=$((holder_total + count))
    done

    echo ""
    echo "**Total shares:** $holder_total"
    echo ""

    # Event history
    echo "## Event History"
    echo ""
    echo "| Date | Event | Class | Qty |"
    echo "|------|-------|-------|----:|"

    while IFS= read -r line; do
      [[ "$line" =~ ^[[:space:]]*#.*$ || -z "$line" ]] && continue
      [[ "$line" =~ ^[[:space:]] ]] && continue

      read -r date event_type ev_holder share_class quantity <<< "$line"
      [[ -z "$quantity" ]] && continue
      [[ "$ev_holder" != "$holder_id" ]] && continue
      echo "| $date | $event_type | $share_class | $quantity |"
    done < "$EVENTS_FILE"
  } | generate_pdf "$output"
}

cmd_pdf() {
  local subcmd="${1:-}"
  shift || true
  case "$subcmd" in
    table)   cmd_pdf_table "$@" ;;
    history) cmd_pdf_history "$@" ;;
    holder)  cmd_pdf_holder "$@" ;;
    *)
      echo "Usage: shares pdf <table|history|holder <id>>"
      echo ""
      echo "Report types:"
      echo "  table              Cap table summary as PDF"
      echo "  history            Full share event history as PDF"
      echo "  holder <id>        Individual holder statement as PDF"
      echo ""
      echo "PDFs are saved to downloads/"
      ;;
  esac
}

cmd_brief() {
  load_classes
  load_holders
  load_events

  echo "# shares context"
  echo ""

  # Classes
  echo "## classes"
  for name in $(echo "${!CLASS_NOMINAL[@]}" | tr ' ' '\n' | sort); do
    echo "  ${name}  nominal=${CLASS_NOMINAL[$name]}  authorised=${CLASS_AUTHORISED[$name]}"
  done
  echo ""

  # Holders
  echo "## holders"
  for id in $(echo "${!HOLDER_NAME[@]}" | tr ' ' '\n' | sort); do
    echo "  ${id}  ${HOLDER_NAME[$id]}"
  done
  echo ""

  # Current holdings + availability
  local total_issued=0
  declare -A CLASS_ISSUED
  for key in "${!HOLDINGS[@]}"; do
    local count="${HOLDINGS[$key]}"
    total_issued=$((total_issued + count))
    local class="${key#*:}"
    CLASS_ISSUED["$class"]=$(( ${CLASS_ISSUED[$class]:-0} + count ))
  done

  echo "## holdings"
  if (( total_issued == 0 )); then
    echo "  (none)"
  else
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
      echo "  ${name}  ${class}  held=${count} (${pct}%)  vested=${vested}"
    done
  fi
  echo ""

  echo "## availability"
  for class in $(echo "${!CLASS_AUTHORISED[@]}" | tr ' ' '\n' | sort); do
    local authorised="${CLASS_AUTHORISED[$class]}"
    local issued="${CLASS_ISSUED[$class]:-0}"
    local available=$((authorised - issued))
    echo "  ${class}  issued=${issued}/${authorised}  available=${available}"
  done
}

cmd_pools() {
  load_classes
  load_holders
  load_events
  load_pools

  if (( ${#POOL_NAMES_LIST[@]} == 0 )); then
    echo "No pools defined. Create cap-table/pools.ledger to define pools."
    return
  fi

  printf "%-16s %-12s %8s %8s %8s  %s\n" "Pool" "Class" "Budget" "Issued" "Avail" "Members"
  printf "%-16s %-12s %8s %8s %8s  %s\n" "----------------" "------------" "--------" "--------" "--------" "----------------------------"

  local total_budget=0 total_issued=0

  for pool in "${POOL_NAMES_LIST[@]}"; do
    local class="${POOL_CLASS[$pool]}"
    local budget="${POOL_BUDGET[$pool]}"
    local members="${POOL_MEMBERS[$pool]}"
    local pool_issued=0
    local member_parts=""

    for member_id in $members; do
      local key="${member_id}:${class}"
      local held="${HOLDINGS[$key]:-0}"
      pool_issued=$((pool_issued + held))
      local name="${HOLDER_NAME[$member_id]:-$member_id}"
      if [[ -n "$member_parts" ]]; then
        member_parts="${member_parts}, ${name} (${held})"
      else
        member_parts="${name} (${held})"
      fi
    done

    local available=$((budget - pool_issued))
    total_budget=$((total_budget + budget))
    total_issued=$((total_issued + pool_issued))

    printf "%-16s %-12s %8d %8d %8d  %s\n" "$pool" "$class" "$budget" "$pool_issued" "$available" "${member_parts:--}"
  done

  echo ""
  printf "%-16s %-12s %8d %8d %8d\n" "Total" "" "$total_budget" "$total_issued" "$((total_budget - total_issued))"
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
  echo "  pools              Show pool budgets and usage"
  echo "  check              Validate ledger consistency"
  echo "  brief              Dump compact context for agent warm-up"
  echo "  pdf <type>         Generate PDF report (table, history, holder)"
  echo "  help               Show this help"
}

# --- Routing ---

case "${1:-help}" in
  table)    cmd_table ;;
  export)   cmd_export ;;
  holders)  cmd_holders ;;
  history)  shift; cmd_history "${1:-}" ;;
  pools)    cmd_pools ;;
  check)    cmd_check ;;
  brief)    cmd_brief ;;
  pdf)      shift; cmd_pdf "$@" ;;
  help|*)   cmd_help ;;
esac
