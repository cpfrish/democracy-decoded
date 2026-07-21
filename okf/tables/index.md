---
type: Directory
title: Tables
description: Data files produced or consumed by the democracy-decoded pipeline.
timestamp: 2026-07-20T00:00:00Z
---

# Tables

| Table | Produced by | Rows (approx) |
| --- | --- | --- |
| [congress_individual_members](congress_individual_members.md) | `1_fetch_member_data.py` | ~535 |
| [congress_generational_summary](congress_generational_summary.md) | `1_fetch_member_data.py` | 5 (one per generation) |
| [congress_members_with_photos](congress_members_with_photos.md) | `1_fetch_member_data.py` | ~535 |
| [congress_members_all_chambers](congress_members_all_chambers.md) | `2_fetch_location_data.py` | ~535 |
| [congress_members_districts](congress_members_districts.md) | `2_fetch_location_data.py` | ~435 |
| [congress_bills](congress_bills.md) | `scripts/congress_bill_fetcher_bulk.py` | varies (up to all bills in a Congress) |
| [cb_2024_us_cd119_20m](cb_2024_us_cd119_20m.md) | US Census Bureau (checked into repo) | 435 district features |
