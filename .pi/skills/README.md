---
name: kib-e-skill-index
description: Human-readable index of this project's skill packages. Contains no task instructions.
disable-model-invocation: true
---

# Project skills — inventarisasi-kib-e

Load-on-demand skill packages for this repository (Flask + SQLite KIB-E asset
inventory app). Each skill is a directory with a `SKILL.md`.

| Skill                   | When to use                                                    |
|-------------------------|----------------------------------------------------------------|
| `kib-e-domain`          | Any inventory field, validation, default, or data-semantics task |
| `kib-e-data-workflow`   | Seeding, backfill, migrations, DB reset, data integrity checks  |
| `kib-e-frontend`        | Any UI change: templates, Tabulator grids, forms, photo upload  |
| `kib-e-testing`         | Writing or running tests                                        |

Companion docs: `inventarisasi-docs/` in the repo root is the human-readable
vault. Skills reference it instead of duplicating it.
