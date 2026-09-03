import { useMemo, useState } from "react";
import type { PairMetric } from "../types";

interface Props {
  pairs: PairMetric[];
}

export function PairTable({ pairs }: Props) {
  const [query, setQuery] = useState("");
  const visiblePairs = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return [...pairs]
      .filter((pair) =>
        (pair.protein_a + " " + pair.protein_b)
          .toLowerCase()
          .includes(normalized),
      )
      .sort(
        (left, right) =>
          right.observation_count - left.observation_count ||
          left.protein_a.localeCompare(right.protein_a) ||
          left.protein_b.localeCompare(right.protein_b),
      );
  }, [pairs, query]);

  return (
    <section className="panel pair-panel" aria-labelledby="pair-title">
      <div className="panel-heading">
        <div>
          <div className="section-kicker">Edge aggregation</div>
          <h2 id="pair-title">Protein pairs</h2>
        </div>
        <label className="compact-search">
          <span className="sr-only">Filter protein pairs</span>
          <input
            type="search"
            value={query}
            placeholder="Filter markers"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>
      <div className="table-scroll">
        <table>
          <caption className="sr-only">
            Descriptive proximity metrics aggregated by canonical protein pair
          </caption>
          <thead>
            <tr>
              <th scope="col">Pair</th>
              <th scope="col" className="number-cell">
                Events
              </th>
              <th scope="col" className="number-cell">
                Cells
              </th>
              <th scope="col" className="number-cell">
                Mean score
              </th>
            </tr>
          </thead>
          <tbody>
            {visiblePairs.map((pair) => (
              <tr key={pair.protein_a + "::" + pair.protein_b}>
                <th scope="row">
                  <span className="pair-name">{pair.protein_a}</span>
                  <span className="pair-link">—</span>
                  <span className="pair-name">{pair.protein_b}</span>
                </th>
                <td className="number-cell">{pair.observation_count}</td>
                <td className="number-cell">{pair.unique_cell_count}</td>
                <td className="number-cell">{pair.mean_score.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!visiblePairs.length && (
          <p className="empty-inline">No pairs match “{query}”.</p>
        )}
      </div>
    </section>
  );
}
