---
type: CSV Table
title: congress_members_with_photos
description: congress_individual_members with capitalized column names and an added official photo URL per member.
resource: data/congress_members_with_photos.csv
tags: [congress, members, photos]
timestamp: 2026-07-20T00:00:00Z
---

# congress_members_with_photos

Produced by `1_fetch_member_data.py` via `scripts/congress_photo_fetcher.py::CongressPhotoFetcher`. Input is [congress_individual_members](congress_individual_members.md) with columns renamed to capitalized form for the photo fetcher.

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `BioguideID` | STRING | Unique Bioguide ID (join key; was `bioguide_id`). |
| `Name` | STRING | Member's full name (was `name`). |
| `Party` | STRING | Party affiliation (was `party`). |
| `BirthYear` | INTEGER | Birth year (was `birth_year`). |
| `Generation` | STRING | See [generations](../concepts/generations.md) (was `generation`). |
| `BillCount` | INTEGER | Bills sponsored (was `bill_count`). |
| `PhotoURL` | STRING | Official member photo URL from bioguide.congress.gov. Some members may lack a photo. |

## Notes

- This is the intermediate table `2_fetch_location_data.py` reads as input to add state/district/chamber — see [congress_members_all_chambers](congress_members_all_chambers.md).
