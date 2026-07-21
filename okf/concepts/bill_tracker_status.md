---
type: Concept
title: Bill Tracker Status
description: Status classification mirroring the congress.gov bill tracker, derived from a bill's latest action text.
tags: [bills, tracker, classification]
timestamp: 2026-07-20T00:00:00Z
---

# Bill Tracker Status

Defined by `determine_tracker_status()` in `scripts/congress_bill_fetcher_bulk.py`. Rules are checked in order against `latest_action_text` (lowercased); first match wins.

| Status | Trigger |
| --- | --- |
| `Became Law` | Latest action contains "became public law" or "signed by president". |
| `To President` | Contains "presented to president" or "sent to president". |
| `Passed Senate` | Contains "passed senate" and the bill did not originate in the Senate (or vice versa for `Passed House`). |
| `Passed House` | Contains "passed house", accounting for origin chamber (see source for the two-sided check). |
| `Failed` | Contains "failed", "rejected", "defeated", or "withdrawn". |
| `Resolved` | For resolution types (`hres`, `sres`, `hconres`, `sconres`) whose latest action contains "agreed to" or "adopted". |
| `Introduced` | Default when no other rule matches. |

Used by [congress_bills](../tables/congress_bills.md) and the `congress_bill_tracker.html` dashboard.
