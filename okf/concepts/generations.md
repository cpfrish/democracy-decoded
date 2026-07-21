---
type: Concept
title: Generations
description: Birth-year buckets used to classify members of Congress into generational cohorts.
tags: [generations, classification]
timestamp: 2026-07-20T00:00:00Z
---

# Generations

Defined by `get_generation()` in `scripts/congress_member_fetcher.py`.

| Generation | Birth years |
| --- | --- |
| Silent Generation | 1928–1945 |
| Baby Boomer | 1946–1964 |
| Gen X | 1965–1980 |
| Millennial | 1981–1996 |
| Gen Z | 1997+ |
| Unknown | Birth year missing or before 1928 |

Used by [congress_individual_members](../tables/congress_individual_members.md), [congress_generational_summary](../tables/congress_generational_summary.md), and downstream member tables.
