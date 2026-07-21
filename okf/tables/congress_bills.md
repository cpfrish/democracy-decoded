---
type: CSV Table
title: congress_bills
description: Bill-level metadata, sponsor info, and tracker status for a given Congress, used to build the bill tracker dashboard.
resource: data/congress_119_bills_2.csv
tags: [congress, bills, tracker]
timestamp: 2026-07-20T00:00:00Z
---

# congress_bills

Produced by `scripts/congress_bill_fetcher_bulk.py::fetch_bills_data_bulk()`, saved as `data/congress_{congress}_bills_2.csv` (default `congress_119_bills_2.csv`), then read by `4_create_bill_tracker.py`.

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `congress` | INTEGER | Congress number (e.g., 119). |
| `bill_type` | STRING | Bill type prefix (`hr`, `s`, `hjres`, etc.) — see [legislative document codes](../concepts/legislative_document_codes.md). |
| `bill_number` | STRING | Bill number within its type/congress. |
| `bill_id` | STRING | `{bill_type}{bill_number}`, e.g. `hr263`. |
| `title` | STRING | Bill title. |
| `introduced_date` | DATE | Date the bill was introduced. |
| `latest_action_date` | DATE | Date of the most recent recorded action. |
| `latest_action_text` | STRING | Free-text description of the most recent action. |
| `tracker_status` | STRING | One of the [bill tracker statuses](../concepts/bill_tracker_status.md). |
| `origin_chamber` | STRING | `House` or `Senate` — chamber where the bill originated. |
| `policy_area` | STRING | Primary policy area, falling back to the first legislative subject if unset. |
| `sponsor` | STRING | Primary sponsor's full name. |
| `sponsor_party` | STRING | Primary sponsor's party. |
| `sponsor_state` | STRING | Primary sponsor's state. |
| `cosponsors_count` | INTEGER | Number of cosponsors. |
| `congress_url` | STRING | Link to the bill on Congress.gov. |
| `summary` | STRING | Currently always empty — `fetch_bill_summary()` exists but isn't wired in. |
| `actions` | STRING (JSON) | Full action history, JSON-encoded as a string for CSV storage. Parse with `json.loads()`. |

## Notes

- Fetching all bills for a Congress can take 5 minutes to several hours depending on `max_bills`; see `README.md` API rate limit notes.
- `tracker_status` is derived by `determine_tracker_status()` from `latest_action_text` — see [bill tracker status](../concepts/bill_tracker_status.md) for the exact rules.
