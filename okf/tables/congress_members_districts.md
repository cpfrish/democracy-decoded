---
type: CSV Table
title: congress_members_districts
description: House-only subset of congress_members_all_chambers, one row per district.
resource: data/congress_members_districts.csv
tags: [congress, members, geography, house]
timestamp: 2026-07-20T00:00:00Z
---

# congress_members_districts

Produced by `2_fetch_location_data.py` as `congress_members_all_chambers[Chamber == 'House']`. Same schema as [congress_members_all_chambers](congress_members_all_chambers.md).

## Notes

- ~435 rows, one per House district.
- Joined against [cb_2024_us_cd119_20m](cb_2024_us_cd119_20m.md) (Census district boundaries) to render the House choropleth.
