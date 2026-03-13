# Board Module — LLM Context

Board governance: meetings, minutes, attendees, and resolutions. Stored in Dolt alongside other company data.

## Tables

- `board_meetings` — meetings (id, meeting_date, title, location, status, called_by, created_at)
- `board_attendees` — who attended (meeting_id, person_name, role)
- `board_minutes` — numbered minute items (meeting_id, seq, item_text)
- `board_resolutions` — formal resolutions (id, meeting_id, resolution_text, status, proposed_by, voted_date)

## Statuses

Meeting: `scheduled` → `in-progress` → `completed` | `cancelled`

Attendee roles: `chair`, `secretary`, `director`, `observer`

Resolution: `pending` → `passed` | `failed` | `withdrawn`

## Workflow: run a board meeting

```bash
# 1. Schedule
board new 2026-03-15 "Q1 Board Meeting"

# 2. Add attendees
board attend bm-2026-03-15 "Alice Smith" chair
board attend bm-2026-03-15 "Bob Chen" secretary
board attend bm-2026-03-15 "Carol Davis" director

# 3. Record minutes
board minute bm-2026-03-15 1 "Meeting called to order at 10:00"
board minute bm-2026-03-15 2 "Review of Q1 financials presented by Alice"
board minute bm-2026-03-15 3 "Discussion of expansion plans"

# 4. Propose and vote on resolutions
board resolve bm-2026-03-15 "Approve Q1 financial statements as presented"
board vote bm-2026-03-15-r1 passed

# 5. Generate board pack HTML
board html
```

## Commands

Read:
- `board meetings` — list all meetings with attendee/resolution counts
- `board meeting <id>` — full meeting detail
- `board resolutions [pending|passed|all]` — list resolutions
- `board minutes <id>` — show minutes for a meeting

Write:
- `board new <date> <title>` — create meeting (id: bm-<date>)
- `board attend <id> <person> [role]` — add attendee
- `board minute <id> <seq> "text"` — add minute item
- `board resolve <id> "text"` — propose resolution
- `board vote <resolution-id> passed|failed` — record outcome

Output:
- `board html [dir]` — generate HTML board pack (default: out/board/)
- `board pdf pack` — full board pack as PDF (→ downloads/)
- `board pdf meeting <id>` — single meeting as PDF (→ downloads/)
- `board pdf resolutions` — all resolutions as PDF (→ downloads/)
- `board serve [dir]` — build and serve on localhost:8001
