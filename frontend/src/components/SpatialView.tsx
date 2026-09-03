import type { CellDetail, CellPoint } from "../types";

interface Props {
  cells: CellPoint[];
  total: number;
  selectedCell: CellDetail | null;
  onSelectCell: (cellId: string) => void;
}

const WIDTH = 560;
const HEIGHT = 330;
const PADDING = 28;
const CONDITION_COLORS = ["#0e7c73", "#e05f4e", "#6b5dd3", "#bb7a11"];

function extent(values: number[]): [number, number] {
  return [Math.min(...values), Math.max(...values)];
}

function scale(value: number, domain: [number, number], range: [number, number]) {
  if (domain[0] === domain[1]) return (range[0] + range[1]) / 2;
  return (
    range[0] +
    ((value - domain[0]) / (domain[1] - domain[0])) * (range[1] - range[0])
  );
}

export function SpatialView({
  cells,
  total,
  selectedCell,
  onSelectCell,
}: Props) {
  const conditions = [...new Set(cells.map((cell) => cell.condition))].sort();
  const colors = new Map(
    conditions.map((condition, index) => [
      condition,
      CONDITION_COLORS[index % CONDITION_COLORS.length],
    ]),
  );
  const xDomain = extent(cells.map((cell) => cell.x));
  const yDomain = extent(cells.map((cell) => cell.y));

  return (
    <section className="panel spatial-panel" aria-labelledby="spatial-title">
      <div className="panel-heading">
        <div>
          <div className="section-kicker">Synthetic coordinates</div>
          <h2 id="spatial-title">Cell field</h2>
        </div>
        <span className="analysis-note">
          Showing {cells.length} of {total}
        </span>
      </div>
      <p className="panel-intro">
        Each point is one cell from the uploaded x/y fields. This is a test-data
        view, not a reconstructed assay layout.
      </p>
      <div className="condition-key" aria-label="Condition color key">
        {conditions.map((condition) => (
          <span key={condition}>
            <i style={{ background: colors.get(condition) }} />
            {condition}
          </span>
        ))}
      </div>
      <div className="spatial-layout">
        <svg
          className="spatial-svg"
          viewBox={"0 0 " + WIDTH + " " + HEIGHT}
          role="group"
          aria-label="Selectable cell coordinate plot"
        >
          <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="8" />
          <line x1={PADDING} y1={HEIGHT - PADDING} x2={WIDTH - PADDING} y2={HEIGHT - PADDING} />
          <line x1={PADDING} y1={PADDING} x2={PADDING} y2={HEIGHT - PADDING} />
          <text x={WIDTH - PADDING} y={HEIGHT - 8} textAnchor="end">x</text>
          <text x="10" y={PADDING} textAnchor="start">y</text>
          {cells.map((cell) => {
            const selected = selectedCell?.cell_id === cell.cell_id;
            return (
              <circle
                key={cell.cell_id}
                role="button"
                tabIndex={0}
                aria-label={
                  cell.cell_id +
                  ", " +
                  cell.condition +
                  ", mean score " +
                  cell.mean_score.toFixed(3)
                }
                aria-pressed={selected}
                cx={scale(cell.x, xDomain, [PADDING + 8, WIDTH - PADDING - 8])}
                cy={scale(cell.y, yDomain, [HEIGHT - PADDING - 8, PADDING + 8])}
                r={selected ? 9 : 5 + Math.min(cell.observation_count, 6) * 0.65}
                fill={colors.get(cell.condition)}
                onClick={() => onSelectCell(cell.cell_id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelectCell(cell.cell_id);
                  }
                }}
              >
                <title>
                  {cell.cell_id} · {cell.condition} · ({cell.x}, {cell.y})
                </title>
              </circle>
            );
          })}
        </svg>
        <div className="cell-detail" aria-live="polite">
          {selectedCell ? (
            <>
              <div className="cell-detail-title">
                <span>Selected cell</span>
                <strong>{selectedCell.cell_id}</strong>
              </div>
              <dl>
                <div>
                  <dt>Condition</dt>
                  <dd>{selectedCell.condition}</dd>
                </div>
                <div>
                  <dt>Position</dt>
                  <dd>
                    {selectedCell.x}, {selectedCell.y}
                  </dd>
                </div>
              </dl>
              <h3>Proximity observations</h3>
              <ul>
                {selectedCell.observations.map((observation, index) => (
                  <li
                    key={
                      observation.protein_a +
                      observation.protein_b +
                      String(index)
                    }
                  >
                    <span>
                      {observation.protein_a} — {observation.protein_b}
                    </span>
                    <strong>{observation.proximity_score.toFixed(3)}</strong>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p>Select a cell point to inspect its proximity observations.</p>
          )}
        </div>
      </div>
    </section>
  );
}
