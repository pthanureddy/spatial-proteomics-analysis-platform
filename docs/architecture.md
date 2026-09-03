# Architecture

## Design goals

This reference implementation optimizes for inspectability:

1. reject malformed data before persistence;
2. keep descriptive calculations deterministic and testable without HTTP or a
   database;
3. expose operational bounds instead of accepting unbounded uploads/results;
4. make the synthetic-data and non-inference boundary visible at both API and
   UI layers; and
5. provide a credible local-to-cloud evolution path without pretending the
   blueprint has been deployed.

## Runtime components

### React client

The Vite-built React application is a working analysis surface rather than a
marketing page. <code>src/api.ts</code> owns the JSON/text boundary and converts
non-success responses into typed <code>ApiError</code> instances. The main
application guards against stale dataset loads with a monotonically increasing
request sequence.

Tables remain the accessible source of exact pair values. SVG views are
supplementary: the network has a title/description, and every cell point is
keyboard focusable, labelled, and selectable with Enter or Space.

### FastAPI service

Routes handle transport concerns only: content type, stream size, query bounds,
status codes, and response schemas. A request middleware attaches or propagates
an <code>X-Request-ID</code> and emits structured JSON completion logs.

CSV validation returns immutable domain records. It reports at most 25 row
errors in one response, preventing an invalid large file from producing an
unbounded error payload.

### Analysis service

<code>analyse_observations</code> is a pure deterministic transformation over
plain records. Pair ordering, condition ordering, network nodes, and edges are
sorted. Floating-point output is rounded to six decimals at the API boundary.
That contract makes test snapshots and downstream caching practical.

### SQLite repository

Each operation opens a short-lived connection with foreign keys and a busy
timeout enabled. Dataset metadata and all proximity rows are inserted within
one <code>BEGIN IMMEDIATE</code> transaction. A failed insert cannot leave a
metadata-only dataset.

Indexes support the dominant access paths: dataset lookup, condition grouping,
and canonical protein-pair grouping. The service currently performs aggregation
in Python to keep its domain logic independently testable; SQL or an analytical
engine becomes preferable as volume grows.

## Request flow

~~~mermaid
sequenceDiagram
    participant U as Browser
    participant A as FastAPI route
    participant V as CSV validator
    participant D as SQLite repository
    participant S as Analysis service

    U->>A: POST text/csv stream
    A->>A: enforce byte limit
    A->>V: UTF-8 bytes + row limit
    V-->>A: canonical records or structured errors
    A->>D: atomic dataset insert
    D-->>A: dataset metadata
    A-->>U: 201 Created

    U->>A: GET dataset analysis
    A->>D: read dataset observations
    D-->>A: normalized records
    A->>S: deterministic aggregation
    S-->>A: pair, delta, and graph summaries
    A-->>U: versioned JSON contract
~~~

## Failure behavior

| Boundary | Behavior |
| --- | --- |
| Unsupported content type | 415 with <code>unsupported_media_type</code> |
| Body beyond configured bytes | streaming stops; 413 with <code>upload_too_large</code> |
| Invalid CSV/schema/row | no database write; 422 with row/field details |
| Invalid comparison selection | 422 with a stable condition error code |
| Missing dataset or cell | 404 with a resource-specific code |
| Unexpected exception | framework 500 plus request-correlated server log |

The application never logs uploaded row contents.

## Deployment shape

Docker Compose uses a named volume and a same-origin nginx proxy. The Kubernetes
blueprint preserves the same boundary:

~~~text
Ingress ─┬─ /api/* ─► backend Service ─► one FastAPI pod ─► RWO PVC / SQLite
         └─ /*     ─► frontend Service ─► two static nginx pods
~~~

One backend replica plus a <code>Recreate</code> strategy is intentional. It
avoids suggesting that a file-backed database on a ReadWriteOnce volume is safe
for horizontal writes.

## Production evolution

A production design would likely:

- put original uploads in immutable object storage and enqueue validation;
- persist metadata in managed PostgreSQL and high-volume observations in a
  partitioned relational or columnar analytical store;
- perform aggregation asynchronously and version materialized results;
- paginate pair/cell result sets with stable cursors;
- add workload identity, authorization, per-tenant isolation, retention, and
  immutable audit events;
- add OpenTelemetry traces/metrics and request/body-rate controls at ingress;
- qualify vendor-specific ingestion against fixtures and published schemas; and
- develop statistical methods with domain experts, explicit assumptions, and
  validation datasets.

Those are scaling directions, not capabilities claimed by this repository.

