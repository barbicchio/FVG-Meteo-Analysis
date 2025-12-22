# Data Quality Report

## Scope and reference schema

All data quality checks described in this document are **derived directly from the canonical schema** defined in:

👉 [`docs/schema.md`](schema.md)

Specifically, this report evaluates:
- missing values according to the schema `Nullable` specification
- range violations based on documented `Allowed range / domain`
- duplicate records according to declared dataset invariants
- temporal coverage and gaps relative to the expected daily granularity

Schema version referenced: **v1.1**