---
type: CSV Table
title: congress_members_all_chambers
description: All members of both chambers with state, district (House only), and chamber added.
resource: data/congress_members_all_chambers.csv
tags: [congress, members, geography]
timestamp: 2026-07-20T00:00:00Z
---

# congress_members_all_chambers

Produced by `2_fetch_location_data.py`, calling `GET https://api.congress.gov/v3/member/{bioguide_id}` per member.

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `Name` | STRING | Member's full name. |
| `Party` | STRING | Party affiliation. |
| `BirthYear` | INTEGER | Birth year. |
| `BillCount` | INTEGER | Bills sponsored. |
| `BioguideID` | STRING | Unique Bioguide ID (join key). |
| `PhotoURL` | STRING | Official member photo URL. |
| `State` | STRING | Two-letter state code. |
| `District` | INTEGER (nullable) | Congressional district number; null for Senate members. |
| `Chamber` | STRING | `House` or `Senate`, derived from the member's latest term. |
| `Generation` | STRING | See [generations](../concepts/generations.md). |

## Notes

- Superset of [congress_members_districts](congress_members_districts.md) — that table is `Chamber == 'House'` only.
- Powers the dual-chamber choropleth map (`congress_map_dual_chamber.html`).
