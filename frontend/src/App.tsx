import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  getAnalysis,
  getCell,
  getCells,
  getDataset,
  listDatasets,
  loadBundledSample,
  uploadDataset,
} from "./api";
import { ComparisonTable } from "./components/ComparisonTable";
import { NetworkView } from "./components/NetworkView";
import { PairTable } from "./components/PairTable";
import { SpatialView } from "./components/SpatialView";
import { UploadPanel } from "./components/UploadPanel";
import type { Analysis, CellDetail, CellPage, Dataset } from "./types";

function readableError(error: unknown) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [cellPage, setCellPage] = useState<CellPage | null>(null);
  const [selectedCell, setSelectedCell] = useState<CellDetail | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const requestSequence = useRef(0);

  const refreshDatasets = useCallback(async (preferredId?: string) => {
    const items = await listDatasets();
    setDatasets(items);
    setSelectedId((current) => preferredId || current || items[0]?.id || null);
  }, []);

  useEffect(() => {
    refreshDatasets()
      .catch((caught) => setError(readableError(caught)))
      .finally(() => setBusy(false));
  }, [refreshDatasets]);

  useEffect(() => {
    if (!selectedId) {
      setDataset(null);
      setAnalysis(null);
      setCellPage(null);
      return;
    }
    const sequence = ++requestSequence.current;
    setBusy(true);
    setError("");
    Promise.all([
      getDataset(selectedId),
      getAnalysis(selectedId),
      getCells(selectedId),
    ])
      .then(([nextDataset, nextAnalysis, nextCells]) => {
        if (sequence !== requestSequence.current) return;
        setDataset(nextDataset);
        setAnalysis(nextAnalysis);
        setCellPage(nextCells);
        setSelectedCell(null);
      })
      .catch((caught) => {
        if (sequence === requestSequence.current) {
          setError(readableError(caught));
        }
      })
      .finally(() => {
        if (sequence === requestSequence.current) setBusy(false);
      });
  }, [selectedId]);

  async function handleUpload(
    name: string,
    filename: string,
    csv: string,
  ) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await uploadDataset(name, filename, csv);
      await refreshDatasets(result.dataset.id);
      setNotice(
        result.warnings.length
          ? "Imported with note: " + result.warnings.join(" ")
          : "Dataset validated and imported.",
      );
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setBusy(false);
    }
  }

  async function handleSample() {
    setBusy(true);
    setError("");
    try {
      const csv = await loadBundledSample();
      await handleUpload(
        "Bundled synthetic example",
        "synthetic-sample.csv",
        csv,
      );
    } catch (caught) {
      setError(readableError(caught));
      setBusy(false);
    }
  }

  async function handleCompare(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;
    const values = new FormData(event.currentTarget);
    const conditionA = String(values.get("condition-a"));
    const conditionB = String(values.get("condition-b"));
    setBusy(true);
    setError("");
    try {
      setAnalysis(await getAnalysis(selectedId, conditionA, conditionB));
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setBusy(false);
    }
  }

  async function handleCellSelection(cellId: string) {
    if (!selectedId) return;
    try {
      setSelectedCell(await getCell(selectedId, cellId));
    } catch (caught) {
      setError(readableError(caught));
    }
  }

  return (
    <>
      <a className="skip-link" href="#analysis-workspace">
        Skip to analysis
      </a>
      <header className="app-header">
        <div className="brand-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div>
          <p className="eyebrow">Independent engineering sample</p>
          <h1>Spatial Proteomics Analysis</h1>
        </div>
        <div className="boundary-badge">
          <span aria-hidden="true">●</span>
          Synthetic / exploratory
        </div>
      </header>
      <div className="truth-banner">
        Descriptive software demonstration only. Do not use this workspace for
        biological conclusions, clinical decisions, or real patient data.
      </div>

      <div className="app-shell">
        <aside className="sidebar">
          <UploadPanel
            disabled={busy}
            onUpload={handleUpload}
            onUseSample={handleSample}
          />
          <nav aria-labelledby="datasets-title" className="dataset-nav">
            <div className="section-kicker">Workspace</div>
            <h2 id="datasets-title">Datasets</h2>
            {!datasets.length ? (
              <p className="empty-sidebar">No local datasets yet.</p>
            ) : (
              <ul>
                {datasets.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={item.id === selectedId ? "selected" : ""}
                      aria-current={item.id === selectedId ? "page" : undefined}
                      onClick={() => setSelectedId(item.id)}
                    >
                      <span>{item.name}</span>
                      <small>{item.row_count.toLocaleString()} events</small>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </nav>
        </aside>

        <main id="analysis-workspace" tabIndex={-1} aria-busy={busy}>
          <div className="status-region" aria-live="polite">
            {busy && <p className="loading-message">Updating workspace…</p>}
            {error && (
              <p className="error-message" role="alert">
                {error}
              </p>
            )}
            {notice && <p className="notice-message">{notice}</p>}
          </div>

          {!dataset || !analysis || !cellPage ? (
            <section className="empty-state">
              <div className="empty-glyph" aria-hidden="true">
                <i />
                <i />
                <i />
                <i />
              </div>
              <p className="eyebrow">Analysis workspace</p>
              <h2>Start with a validated protein-pair proximity edge list.</h2>
              <p>
                Import your own synthetic CSV or load the bundled example to
                inspect pair counts, mean scores, condition deltas, and network
                structure.
              </p>
            </section>
          ) : (
            <div className="analysis-stack">
              <section className="dataset-heading" aria-labelledby="dataset-title">
                <div>
                  <p className="eyebrow">Active dataset</p>
                  <h2 id="dataset-title">{dataset.name}</h2>
                  <p>
                    {dataset.original_filename} · imported{" "}
                    {formatDate(dataset.created_at)}
                  </p>
                </div>
                <span className="version-chip">
                  Analysis contract v{analysis.analysis_version}
                </span>
              </section>

              <section className="metric-grid" aria-label="Dataset summary">
                <article>
                  <span>Proximity observations</span>
                  <strong>{analysis.summary.observation_count.toLocaleString()}</strong>
                </article>
                <article>
                  <span>Unique cells</span>
                  <strong>{analysis.summary.unique_cell_count.toLocaleString()}</strong>
                </article>
                <article>
                  <span>Protein markers</span>
                  <strong>{analysis.summary.unique_protein_count}</strong>
                </article>
                <article>
                  <span>Conditions</span>
                  <strong>{analysis.summary.conditions.length}</strong>
                </article>
              </section>

              {analysis.summary.conditions.length >= 2 && (
                <form className="condition-controls" onSubmit={handleCompare}>
                  <span>Compare</span>
                  <label>
                    <span className="sr-only">Baseline condition</span>
                    <select
                      name="condition-a"
                      defaultValue={analysis.comparison?.condition_a}
                    >
                      {analysis.summary.conditions.map((condition) => (
                        <option key={condition}>{condition}</option>
                      ))}
                    </select>
                  </label>
                  <span aria-hidden="true">→</span>
                  <label>
                    <span className="sr-only">Comparison condition</span>
                    <select
                      name="condition-b"
                      defaultValue={analysis.comparison?.condition_b}
                    >
                      {analysis.summary.conditions.map((condition) => (
                        <option key={condition}>{condition}</option>
                      ))}
                    </select>
                  </label>
                  <button type="submit" disabled={busy}>
                    Apply
                  </button>
                </form>
              )}

              <SpatialView
                cells={cellPage.items}
                total={cellPage.total}
                selectedCell={selectedCell}
                onSelectCell={(cellId) => void handleCellSelection(cellId)}
              />

              <div className="two-column-grid">
                <PairTable pairs={analysis.pair_metrics} />
                <NetworkView
                  nodes={analysis.network_nodes}
                  edges={analysis.network_edges}
                />
              </div>

              {analysis.comparison && (
                <ComparisonTable comparison={analysis.comparison} />
              )}
            </div>
          )}
        </main>
      </div>
      <footer>
        Local SQLite persistence · Generic normalized CSV · No PXL ingestion
      </footer>
    </>
  );
}
