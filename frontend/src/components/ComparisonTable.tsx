import type { Analysis } from "../types";

interface Props {
  comparison: NonNullable<Analysis["comparison"]>;
}

function signed(value: number, digits = 0) {
  const formatted = value.toFixed(digits);
  return value > 0 ? "+" + formatted : formatted;
}

export function ComparisonTable({ comparison }: Props) {
  return (
    <section className="panel comparison-panel" aria-labelledby="comparison-title">
      <div className="panel-heading">
        <div>
          <div className="section-kicker">Descriptive comparison</div>
          <h2 id="comparison-title">Condition deltas</h2>
        </div>
        <span className="analysis-note">No significance testing</span>
      </div>
      <div className="comparison-legend" aria-hidden="true">
        <span>{comparison.condition_a}</span>
        <span className="arrow">→</span>
        <span>{comparison.condition_b}</span>
      </div>
      <div className="table-scroll">
        <table>
          <caption className="sr-only">
            Changes from {comparison.condition_a} to {comparison.condition_b}
          </caption>
          <thead>
            <tr>
              <th scope="col">Pair</th>
              <th scope="col" className="number-cell">
                Event Δ
              </th>
              <th scope="col" className="number-cell">
                Mean score Δ
              </th>
            </tr>
          </thead>
          <tbody>
            {comparison.pairs.map((pair) => (
              <tr key={pair.protein_a + "::" + pair.protein_b}>
                <th scope="row">
                  {pair.protein_a} — {pair.protein_b}
                </th>
                <td className="number-cell delta">
                  {signed(pair.count_delta)}
                </td>
                <td className="number-cell delta">
                  {pair.mean_score_delta === null
                    ? "n/a"
                    : signed(pair.mean_score_delta, 3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

