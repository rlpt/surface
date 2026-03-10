#!/usr/bin/env bash
set -euo pipefail

SURFACE_DB="${SURFACE_DB:-$SURFACE_ROOT/.surface-db}"
DOWNLOADS_DIR="${SURFACE_ROOT}/downloads"

die() { echo "error: $1" >&2; exit 1; }

dsql() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt sql -q "$1")
}

dsql_csv() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt sql -r csv -q "$1")
}

# --- Subcommands ---

cmd_table() {
  dsql "
    SELECT
      ct.holder,
      ct.class,
      ct.held,
      CONCAT(ct.pct, '%') AS pct,
      ct.held AS vested
    FROM cap_table ct;
  "

  local total
  total=$(dsql_csv "SELECT COALESCE(SUM(shares_held), 0) FROM holdings;" | tail -1)
  echo ""
  echo "Total issued: $total"
}

cmd_export() {
  dsql_csv "
    SELECT
      ct.holder,
      ct.class AS share_class,
      ct.held AS shares_held,
      ct.pct AS percentage,
      ct.held AS vested,
      ct.held AS total_granted,
      '' AS notes
    FROM cap_table ct;
  "
}

cmd_holders() {
  dsql "
    SELECT
      h.id,
      h.display_name AS name,
      COALESCE(SUM(ho.shares_held), 0) AS total
    FROM holders h
    LEFT JOIN holdings ho ON ho.holder_id = h.id
    GROUP BY h.id, h.display_name
    ORDER BY h.id;
  "
}

cmd_history() {
  local filter="${1:-}"
  local where=""
  if [ -n "$filter" ]; then
    where="WHERE se.holder_id = '${filter}'"
  fi

  dsql "
    SELECT
      se.event_date AS date,
      se.event_type AS event,
      se.holder_id AS holder,
      se.share_class AS class,
      se.quantity AS qty
    FROM share_events se
    ${where}
    ORDER BY se.event_date, se.id;
  "
}

cmd_pools() {
  dsql "
    SELECT
      p.name AS pool,
      p.share_class AS class,
      p.budget,
      COALESCE(issued.total, 0) AS issued,
      p.budget - COALESCE(issued.total, 0) AS avail,
      COALESCE(members.list, '-') AS members
    FROM pools p
    LEFT JOIN (
      SELECT
        pm.pool_name,
        SUM(COALESCE(ho.shares_held, 0)) AS total
      FROM pool_members pm
      LEFT JOIN holdings ho ON ho.holder_id = pm.holder_id
        AND ho.share_class = (SELECT share_class FROM pools WHERE name = pm.pool_name)
      GROUP BY pm.pool_name
    ) issued ON issued.pool_name = p.name
    LEFT JOIN (
      SELECT
        pm.pool_name,
        GROUP_CONCAT(CONCAT(h.display_name, ' (', COALESCE(ho.shares_held, 0), ')') SEPARATOR ', ') AS list
      FROM pool_members pm
      JOIN holders h ON h.id = pm.holder_id
      LEFT JOIN holdings ho ON ho.holder_id = pm.holder_id
        AND ho.share_class = (SELECT share_class FROM pools WHERE name = pm.pool_name)
      GROUP BY pm.pool_name
    ) members ON members.pool_name = p.name
    ORDER BY p.name;
  "
}

cmd_check() {
  local errors=0

  # Check events reference valid holders
  local bad_holders
  bad_holders=$(dsql_csv "
    SELECT DISTINCT se.holder_id
    FROM share_events se
    LEFT JOIN holders h ON h.id = se.holder_id
    WHERE h.id IS NULL;
  " | tail -n +2)

  if [ -n "$bad_holders" ]; then
    echo "error: events reference unknown holders: $bad_holders"
    errors=$((errors + 1))
  fi

  # Check events reference valid classes
  local bad_classes
  bad_classes=$(dsql_csv "
    SELECT DISTINCT se.share_class
    FROM share_events se
    LEFT JOIN share_classes sc ON sc.name = se.share_class
    WHERE sc.name IS NULL;
  " | tail -n +2)

  if [ -n "$bad_classes" ]; then
    echo "error: events reference unknown share classes: $bad_classes"
    errors=$((errors + 1))
  fi

  # Check no negative holdings
  local negative
  negative=$(dsql_csv "
    SELECT holder_id, share_class,
      SUM(CASE
        WHEN event_type IN ('grant', 'transfer-in') THEN quantity
        ELSE -quantity
      END) AS net
    FROM share_events
    GROUP BY holder_id, share_class
    HAVING net < 0;
  " | tail -n +2)

  if [ -n "$negative" ]; then
    echo "error: negative holdings found:"
    echo "$negative"
    errors=$((errors + 1))
  fi

  # Check total issued does not exceed authorised
  local over
  over=$(dsql_csv "
    SELECT class, authorised, issued
    FROM class_availability
    WHERE issued > authorised;
  " | tail -n +2)

  if [ -n "$over" ]; then
    echo "error: issued exceeds authorised:"
    echo "$over"
    errors=$((errors + 1))
  fi

  if (( errors > 0 )); then
    echo ""
    echo "$errors error(s) found"
    exit 1
  fi

  echo "OK"
}

cmd_brief() {
  echo "# shares context"
  echo ""

  echo "## classes"
  dsql_csv "SELECT name, nominal_value, nominal_currency, authorised FROM share_classes;" | tail -n +2 | while IFS=, read -r name val cur auth; do
    echo "  ${name}  nominal=${cur}${val}  authorised=${auth}"
  done
  echo ""

  echo "## holders"
  dsql_csv "SELECT id, display_name FROM holders ORDER BY id;" | tail -n +2 | while IFS=, read -r id name; do
    echo "  ${id}  ${name}"
  done
  echo ""

  echo "## holdings"
  dsql_csv "SELECT holder, class, held, pct FROM cap_table;" | tail -n +2 | while IFS=, read -r holder class held pct; do
    echo "  ${holder}  ${class}  held=${held} (${pct}%)  vested=${held}"
  done
  echo ""

  echo "## availability"
  dsql_csv "SELECT class, issued, authorised, available FROM class_availability;" | tail -n +2 | while IFS=, read -r class issued auth avail; do
    echo "  ${class}  issued=${issued}/${auth}  available=${avail}"
  done
}

# --- Mutation commands ---

cmd_grant() {
  local holder="${1:-}" class="${2:-}" qty="${3:-}"
  [ -z "$holder" ] || [ -z "$class" ] || [ -z "$qty" ] && die "usage: shares grant <holder-id> <class> <quantity>"

  # Validate holder exists
  local hname
  hname=$(dsql_csv "SELECT display_name FROM holders WHERE id = '${holder}';" | tail -n +2)
  [ -z "$hname" ] && die "unknown holder: $holder"

  # Validate class exists
  local cauth
  cauth=$(dsql_csv "SELECT authorised FROM share_classes WHERE name = '${class}';" | tail -n +2)
  [ -z "$cauth" ] && die "unknown share class: $class"

  # Check availability
  local avail
  avail=$(dsql_csv "SELECT available FROM class_availability WHERE class = '${class}';" | tail -n +2)
  if [ "$qty" -gt "$avail" ]; then
    die "insufficient shares: requested $qty but only $avail available in class '$class'"
  fi

  local today
  today=$(date +%Y-%m-%d)
  dsql "INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity) VALUES ('${today}', 'grant', '${holder}', '${class}', ${qty});"
  (cd "$SURFACE_DB" && dolt add . && dolt commit -m "grant ${qty} ${class} to ${holder}")

  echo "Granted ${qty} ${class} shares to ${hname}"
  echo ""
  cmd_table
}

cmd_transfer() {
  local from="${1:-}" to="${2:-}" class="${3:-}" qty="${4:-}"
  [ -z "$from" ] || [ -z "$to" ] || [ -z "$class" ] || [ -z "$qty" ] && die "usage: shares transfer <from-id> <to-id> <class> <quantity>"

  # Validate both holders exist
  local fname
  fname=$(dsql_csv "SELECT display_name FROM holders WHERE id = '${from}';" | tail -n +2)
  [ -z "$fname" ] && die "unknown holder: $from"

  local tname
  tname=$(dsql_csv "SELECT display_name FROM holders WHERE id = '${to}';" | tail -n +2)
  [ -z "$tname" ] && die "unknown holder: $to"

  # Check sender has enough
  local held
  held=$(dsql_csv "SELECT COALESCE(shares_held, 0) FROM holdings WHERE holder_id = '${from}' AND share_class = '${class}';" | tail -n +2)
  held="${held:-0}"
  if [ "$qty" -gt "$held" ]; then
    die "${fname} only holds ${held} ${class} shares, cannot transfer ${qty}"
  fi

  local today
  today=$(date +%Y-%m-%d)
  dsql "
    INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity) VALUES
      ('${today}', 'transfer-out', '${from}', '${class}', ${qty}),
      ('${today}', 'transfer-in',  '${to}',   '${class}', ${qty});
  "
  (cd "$SURFACE_DB" && dolt add . && dolt commit -m "transfer ${qty} ${class} from ${from} to ${to}")

  echo "Transferred ${qty} ${class} shares: ${fname} -> ${tname}"
  echo ""
  cmd_table
}

cmd_add_holder() {
  local id="${1:-}" name="${2:-}"
  [ -z "$id" ] || [ -z "$name" ] && die "usage: shares add-holder <id> \"Display Name\""

  # Check not duplicate
  local existing
  existing=$(dsql_csv "SELECT id FROM holders WHERE id = '${id}';" | tail -n +2)
  [ -n "$existing" ] && die "holder '$id' already exists"

  dsql "INSERT INTO holders (id, display_name) VALUES ('${id}', '${name}');"
  (cd "$SURFACE_DB" && dolt add . && dolt commit -m "add holder: ${name} (${id})")

  echo "Added holder: ${name} (${id})"
}

cmd_add_pool() {
  local name="${1:-}" class="${2:-}" budget="${3:-}"
  [ -z "$name" ] || [ -z "$class" ] || [ -z "$budget" ] && die "usage: shares add-pool <name> <class> <budget>"

  local cauth
  cauth=$(dsql_csv "SELECT authorised FROM share_classes WHERE name = '${class}';" | tail -n +2)
  [ -z "$cauth" ] && die "unknown share class: $class"

  dsql "INSERT INTO pools (name, share_class, budget) VALUES ('${name}', '${class}', ${budget});"
  (cd "$SURFACE_DB" && dolt add . && dolt commit -m "add pool: ${name} (${budget} ${class})")

  echo "Added pool: ${name} — ${budget} ${class} shares"
}

cmd_pool_add() {
  local pool="${1:-}" holder="${2:-}"
  [ -z "$pool" ] || [ -z "$holder" ] && die "usage: shares pool-add <pool> <holder-id>"

  local pname
  pname=$(dsql_csv "SELECT name FROM pools WHERE name = '${pool}';" | tail -n +2)
  [ -z "$pname" ] && die "unknown pool: $pool"

  local hname
  hname=$(dsql_csv "SELECT display_name FROM holders WHERE id = '${holder}';" | tail -n +2)
  [ -z "$hname" ] && die "unknown holder: $holder"

  dsql "INSERT INTO pool_members (pool_name, holder_id) VALUES ('${pool}', '${holder}');"
  (cd "$SURFACE_DB" && dolt add . && dolt commit -m "add ${holder} to pool ${pool}")

  echo "Added ${hname} to pool ${pool}"
}

cmd_push() {
  local subcmd="${1:-}"
  shift || true
  PYTHONPATH="" python3 "$SURFACE_ROOT/modules/shares/scripts/push.py" "$subcmd" "$@"
}

# --- PDF helpers ---

generate_pdf() {
  local output_file="$1"
  mkdir -p "$DOWNLOADS_DIR"
  local pdf_args=(--pdf-engine=typst -V mainfont="Helvetica" -V margin-top=2cm -V margin-bottom=2cm -V margin-left=2cm -V margin-right=2cm)
  pandoc "${pdf_args[@]}" -o "$output_file"
  echo "$output_file"
}

cmd_pdf_table() {
  local today
  today=$(date +%Y-%m-%d)
  local output="${DOWNLOADS_DIR}/cap-table-${today}.pdf"
  local total
  total=$(dsql_csv "SELECT COALESCE(SUM(shares_held), 0) FROM holdings;" | tail -1)

  {
    echo "# Formabi — Cap Table"
    echo ""
    echo "Generated: $today"
    echo ""

    if [ "$total" = "0" ]; then
      echo "No shares issued."
    else
      echo "| Holder | Class | Held | % | Vested |"
      echo "|--------|-------|-----:|--:|-------:|"

      dsql_csv "SELECT holder, class, held, pct FROM cap_table;" | tail -n +2 | while IFS=, read -r holder class held pct; do
        echo "| $holder | $class | $held | ${pct}% | $held |"
      done

      echo ""
      echo "**Total issued:** $total"
    fi
  } | generate_pdf "$output"
}

cmd_pdf_history() {
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

    dsql_csv "
      SELECT se.event_date, se.event_type, h.display_name, se.share_class, se.quantity
      FROM share_events se
      JOIN holders h ON h.id = se.holder_id
      ORDER BY se.event_date, se.id;
    " | tail -n +2 | while IFS=, read -r date etype name class qty; do
      echo "| $date | $etype | $name | $class | $qty |"
    done
  } | generate_pdf "$output"
}

cmd_pdf_holder() {
  local holder_id="${1:-}"
  [ -z "$holder_id" ] && die "usage: shares pdf holder <holder-id>"

  local name
  name=$(dsql_csv "SELECT display_name FROM holders WHERE id = '${holder_id}';" | tail -1)
  [ -z "$name" ] && die "unknown holder: $holder_id"

  local today
  today=$(date +%Y-%m-%d)
  local output="${DOWNLOADS_DIR}/${holder_id}-statement-${today}.pdf"
  local total
  total=$(dsql_csv "SELECT COALESCE(SUM(shares_held), 0) FROM holdings;" | tail -1)

  {
    echo "# Formabi — Holder Statement"
    echo ""
    echo "**Holder:** $name"
    echo ""
    echo "Generated: $today"
    echo ""
    echo "## Current Holdings"
    echo ""
    echo "| Class | Held | % | Vested |"
    echo "|-------|-----:|--:|-------:|"

    local holder_total=0
    dsql_csv "SELECT class, held, pct FROM cap_table WHERE holder_id = '${holder_id}';" | tail -n +2 | while IFS=, read -r class held pct; do
      echo "| $class | $held | ${pct}% | $held |"
    done

    local htotal
    htotal=$(dsql_csv "SELECT COALESCE(SUM(shares_held), 0) FROM holdings WHERE holder_id = '${holder_id}';" | tail -1)
    echo ""
    echo "**Total shares:** $htotal"
    echo ""

    echo "## Event History"
    echo ""
    echo "| Date | Event | Class | Qty |"
    echo "|------|-------|-------|----:|"

    dsql_csv "
      SELECT event_date, event_type, share_class, quantity
      FROM share_events
      WHERE holder_id = '${holder_id}'
      ORDER BY event_date, id;
    " | tail -n +2 | while IFS=, read -r date etype class qty; do
      echo "| $date | $etype | $class | $qty |"
    done
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

cmd_help() {
  echo "shares — cap table management (dolt)"
  echo ""
  echo "Usage: shares <command> [args]"
  echo ""
  echo "Read:"
  echo "  table                              Cap table with percentages"
  echo "  export                             Cap table as CSV"
  echo "  holders                            List all shareholders"
  echo "  history [holder]                   Share events (optionally filtered)"
  echo "  pools                              Pool budgets and usage"
  echo "  check                              Validate consistency"
  echo "  brief                              Context dump for agent warm-up"
  echo ""
  echo "Write:"
  echo "  grant <holder> <class> <qty>       Grant shares"
  echo "  transfer <from> <to> <class> <qty> Transfer shares"
  echo "  add-holder <id> \"Name\"             Add a shareholder"
  echo "  add-pool <name> <class> <budget>   Create a share pool"
  echo "  pool-add <pool> <holder>           Add holder to pool"
  echo ""
  echo "Export:"
  echo "  pdf <table|history|holder <id>>    Generate PDF"
  echo "  push <table|history|holders|pools|all>  Push to Google Sheets"
  echo ""
  echo "  push requires: GOOGLE_SERVICE_ACCOUNT_KEY, SHARES_SHEET_ID"
}

# --- Routing ---

case "${1:-help}" in
  table)      cmd_table ;;
  export)     cmd_export ;;
  holders)    cmd_holders ;;
  history)    shift; cmd_history "${1:-}" ;;
  pools)      cmd_pools ;;
  check)      cmd_check ;;
  brief)      cmd_brief ;;
  grant)      shift; cmd_grant "$@" ;;
  transfer)   shift; cmd_transfer "$@" ;;
  add-holder) shift; cmd_add_holder "$1" "$2" ;;
  add-pool)   shift; cmd_add_pool "$@" ;;
  pool-add)   shift; cmd_pool_add "$@" ;;
  push)       shift; cmd_push "$@" ;;
  pdf)        shift; cmd_pdf "$@" ;;
  help|*)     cmd_help ;;
esac
