# Spatial Proteomics Analysis Platform

An independent portfolio project demonstrating an end-to-end analysis workflow
for a **generic, normalized protein-pair proximity edge list**. It combines a
FastAPI service, SQLite persistence, deterministic descriptive analysis, and an
accessible React/TypeScript exploration UI.

> **Scope and truth boundary**
>
> All bundled data are synthetic. A proximity observation does not establish a
> biochemical interaction. This project is not affiliated with, commissioned by,
> or endorsed by Pixelgen Technologies. It is not a PXL/Pixelator parser, has not
> been tested for compatibility with those formats, and must not be used for
> biological conclusions, clinical decisions, or patient data.

## What it demonstrates

- Bounded CSV streaming with a 5 MiB default upload limit and 100,000-row cap.
- Row-level validation with structured errors, UTF-8 enforcement, canonical
  undirected protein pairs, and consistent condition/coordinates per cell.
- Atomic dataset persistence in SQLite with foreign keys and query indexes.
- Deterministic pair counts, mean proximity scores, descriptive condition
  deltas, and undirected network summaries.
- Bounded cell pagination plus per-cell proximity detail, so supplied synthetic
  x/y coordinates are explored rather than discarded.
- A responsive UI with upload/sample flows, filterable tables, condition
  controls, an accessible SVG network, and a keyboard-operable cell map.
- Backend and frontend tests, container builds, CI, and Kubernetes manifests as
  deployment blueprints.

The terminology is informed by public descriptions of graph-shaped proximity
data and differential proximity workflows in the
[PXL file documentation](https://software.pixelgen.com/pixelator/pxl-file/) and
[spatial-analysis tutorial](https://software.pixelgen.com/pna-analysis/python/tutorials/spatial_analyses/).
Those sources provide domain context only; this repository implements its own
small generic export contract.

## Architecture

~~~text
Browser
  │  raw text/csv + JSON
  ▼
React / TypeScript ── same-origin /api proxy ──► FastAPI
  │                                             │
  ├─ summary cards                              ├─ bounded stream + validation
  ├─ pair / delta tables                        ├─ analysis service (pure Python)
  ├─ proximity network                          └─ SQLite repository
  └─ synthetic x/y cell field                              │
                                                          ▼
                                                  persistent volume
~~~

The API separates transport, validation, persistence, and analysis. The
analysis service accepts plain records and returns sorted, rounded output, which
makes it independently testable and reproducible. See
[docs/architecture.md](docs/architecture.md) for request flow, decisions, and a
production scaling path.

## Quick start

Prerequisites: Python 3.11 or newer and Node.js 20 or newer.

### Backend

From the repository root:

~~~bash
cd backend
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install -e ".[test]"
uvicorn app.main:app --reload
~~~

The API is available at http://localhost:8000 and its OpenAPI UI at
http://localhost:8000/docs.

### Frontend

In a second terminal:

~~~bash
cd frontend
npm ci
npm run dev
~~~

Open http://localhost:5173. Choose **Load bundled synthetic sample** for the
shortest path through the application.

### Docker Compose

~~~bash
docker compose up --build
~~~

The UI is served at http://localhost:5173 and proxies API calls to the backend.
SQLite state is retained in the named <code>spatial-data</code> volume.

## Sample workflow

1. Load the bundled sample or choose a UTF-8 CSV.
2. The API validates the complete file before opening a database transaction.
3. Select the imported dataset to inspect summary and pair metrics.
4. Choose two conditions and apply the comparison. Deltas are always
   comparison minus baseline.
5. Select a point in the synthetic coordinate field to inspect that cell's
   proximity observations.

The bundled file contains 16 observations across eight cells, two conditions,
five protein markers, and seven unique protein pairs. The default alphabetical
comparison is <code>control → treated</code>.

To call the ingestion API directly:

~~~bash
curl -X POST \
  "http://localhost:8000/api/v1/datasets?name=Synthetic%20example" \
  -H "Content-Type: text/csv" \
  -H "X-Filename: synthetic_proximity_edges.csv" \
  --data-binary "@sample_data/synthetic_proximity_edges.csv"
~~~

## API surface

| Method | Path | Purpose |
| --- | --- | --- |
| GET | <code>/api/v1/health</code> | Process and database readiness |
| GET | <code>/api/v1/sample.csv</code> | Bundled 16-row synthetic CSV |
| POST | <code>/api/v1/datasets?name=…</code> | Validate and atomically ingest a raw CSV body |
| GET | <code>/api/v1/datasets</code> | List locally persisted datasets |
| GET | <code>/api/v1/datasets/{id}</code> | Read dataset metadata |
| GET | <code>/api/v1/datasets/{id}/analysis</code> | Read descriptive pair, comparison, and network output |
| GET | <code>/api/v1/datasets/{id}/cells</code> | Page through cell coordinate summaries (maximum 500) |
| GET | <code>/api/v1/datasets/{id}/cells/{cell_id}</code> | Read one cell and its proximity observations |

Errors use one stable envelope:

~~~json
{
  "error": {
    "code": "invalid_csv",
    "message": "The CSV contains invalid rows.",
    "details": [
      {"row": 2, "field": "proximity_score", "message": "Must be a finite number."}
    ]
  }
}
~~~

See [docs/data-contract.md](docs/data-contract.md) for all field constraints and
analysis definitions.

## Tests and verification

~~~bash
# backend (from backend/)
python -m pytest
python -m pytest --cov=app --cov-report=term-missing

# frontend (from frontend/)
npm test
npm run build
npm audit --audit-level=high

# infrastructure syntax / local images (from repository root)
docker compose config
docker compose build
kubectl kustomize deploy/kubernetes
~~~

The GitHub Actions workflow runs backend tests with an 80% coverage floor,
frontend unit tests and production compilation, a production-dependency audit,
and both Docker builds. It intentionally contains no publish or deployment
step.

## Deterministic scale check

The optional command generates exactly 100,000 synthetic rows with a fixed
seed, validates them, inserts them into a temporary SQLite database, reads them
back, and computes the analysis:

~~~bash
cd backend
python -m scripts.scale_check --rows 100000 --seed 2026
~~~

It prints the Python/platform details, CSV byte size, and per-stage wall-clock
timings for that run. This is a single-process diagnostic, not a throughput,
capacity, or production benchmark. Results are intentionally not generalized
across hardware. A documented local run is in
[docs/scale-check.md](docs/scale-check.md).

## Deployment blueprint

<code>deploy/kubernetes</code> provides a Kustomize-compatible namespace,
ConfigMap, single-replica backend, persistent volume claim, two-replica static
frontend, services, probes, resource requests/limits, and an example ingress.
Image names and hostname are placeholders. Nothing in this repository has been
deployed by this project.

The backend is deliberately constrained to one replica because SQLite on a
ReadWriteOnce volume is the local-reference persistence choice. A real
multi-replica service should first move datasets and observations to a managed
relational or analytical store.

## Limitations and tradeoffs

- No PXL, Pixelator, or vendor-specific ingestion is implemented or tested.
- Metrics are descriptive only. There is no normalization, abundance
  filtering, batch correction, multiple-testing correction, uncertainty
  estimate, or statistical significance testing.
- x/y values are caller-supplied synthetic coordinates. The service does not
  infer or reconstruct spatial layouts.
- The server validates an upload in memory after enforcing the byte bound, then
  inserts it in one transaction. This keeps failure behavior clear but is not a
  streaming analytics design.
- SQLite is appropriate for local demonstration, not concurrent analytical
  workloads or horizontally scaled writes.
- Authentication, authorization, audit retention, malware scanning, object
  storage, and sensitive-data controls are outside this local project.
- Network metrics are intentionally basic: unique-neighbor degree, observation
  count, and mean score. No causal or biological meaning is assigned.
- Pair analysis is returned as one response and the UI displays at most 500
  cell points. Large production result sets need server-side pagination or
  columnar delivery.

## Repository map

~~~text
backend/
  app/api/             HTTP routes and request bounds
  app/services/        CSV validation and deterministic analysis
  app/database.py      SQLite schema and repository
  scripts/             sample generator and 100k-row scale check
  tests/               pytest unit and API tests
frontend/
  src/components/      upload, tables, network, and cell field
  src/api.ts           typed HTTP boundary
  src/types.ts         API response contracts
deploy/kubernetes/     non-deployed Kustomize blueprint
docs/                  architecture and data-contract notes
sample_data/           synthetic normalized edge list
~~~
