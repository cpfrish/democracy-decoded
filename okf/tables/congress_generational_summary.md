---
type: CSV Table
title: congress_generational_summary
description: Aggregate bill-sponsorship stats grouped by generation.
resource: data/congress_generational_summary.csv
tags: [congress, members, generations]
timestamp: 2026-07-20T00:00:00Z
---

# congress_generational_summary

Produced by `1_fetch_member_data.py`, one row per [generation](../concepts/generations.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `generation` | STRING | Generation bucket name. See [generations](../concepts/generations.md). |
| `member_count` | INTEGER | Number of members in this generation. |
| `total_bills` | INTEGER | Sum of bills sponsored by members in this generation. |
| `avg_bills_per_member` | FLOAT | `total_bills / member_count`, rounded to 2 decimals. |

## Notes

- Derived from the same fetch pass as [congress_individual_members](congress_individual_members.md); not re-derivable from it alone since it isn't checked in (git-ignored).
