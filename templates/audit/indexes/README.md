# Audit Indexes

This directory contains purpose-built category index files. Each index covers one cross-cutting query category. Index entries are summary pointers — not full event dumps.

Full event detail lives in per-work-item logs at `work-items/WORK-NNN.jsonl`.

---

## Index Files

| File | One entry per | Links to |
|------|--------------|----------|
| `update-history.jsonl` | `/update` session | session log |
| `rescan-history.jsonl` | `/rescan` session | session log |
| `clarity-items.jsonl` | Clarity Assessment item identified | work-item log |
| `delegations.jsonl` | Agent delegation decision | work-item log |
| `reclassifications.jsonl` | Severity reclassification | work-item log |
| `drift-detections.jsonl` | Drift flag at verification | work-item log |
| `human-gates.jsonl` | Human gate decision | work-item log |
| `backlog-activity.jsonl` | Backlog event (activation, fetch, transition, elaboration, completion check) | work-item log or session log |

---

## Entry Format

Every index entry is a summary pointer. It contains only the fields needed for the cross-cutting query plus a `work_item_id` and `session_id` reference back to the full log.

**Never** copy full payloads into index entries. Index files exist for fast lookup; full detail is always retrieved from the work-item log.

---

## Growth Model

Each index file grows at **one line per event of that category** — never one line per session or per work item. Indexes are inherently bounded by event category frequency and never require rotation.
