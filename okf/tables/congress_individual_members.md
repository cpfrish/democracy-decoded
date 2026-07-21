---
type: CSV Table
title: congress_individual_members
description: One row per current member of Congress, with party, birth year, generation, and bill count.
resource: data/congress_individual_members.csv
tags: [congress, members]
timestamp: 2026-07-20T00:00:00Z
---

# congress_individual_members

Produced by `1_fetch_member_data.py`, sourced via `scripts/congress_member_fetcher.py::fetch_congress_members_json()`.

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `bioguide_id` | STRING | Unique Bioguide ID for the member (join key across all member tables). |
| `name` | STRING | Member's full name. |
| `party` | STRING | Party affiliation (`D`, `R`, `I`). |
| `birth_year` | INTEGER | Birth year, used to derive [generation](../concepts/generations.md). |
| `generation` | STRING | See [generations](../concepts/generations.md) for bucket definitions. |
| `bill_count` | INTEGER | Number of bills sponsored by this member. |

## Notes

- Git-ignored; regenerate with `python 1_fetch_member_data.py` (requires `CONGRESS_API_KEY`).
- Feeds into [congress_generational_summary](congress_generational_summary.md) and, after renaming to capitalized columns, [congress_members_with_photos](congress_members_with_photos.md).
