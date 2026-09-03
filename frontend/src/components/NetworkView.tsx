import type { NetworkEdge, NetworkNode } from "../types";

interface Props {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

const SIZE = 360;
const CENTER = SIZE / 2;
const RADIUS = 128;

export function NetworkView({ nodes, edges }: Props) {
  const positions = new Map(
    nodes.map((node, index) => {
      const angle = (index / Math.max(nodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
      return [
        node.protein,
        {
          x: CENTER + Math.cos(angle) * RADIUS,
          y: CENTER + Math.sin(angle) * RADIUS,
        },
      ] as const;
    }),
  );
  const maxCount = Math.max(...edges.map((edge) => edge.observation_count), 1);

  return (
    <section className="panel network-panel" aria-labelledby="network-title">
      <div className="panel-heading">
        <div>
          <div className="section-kicker">Undirected summary</div>
          <h2 id="network-title">Proximity network</h2>
        </div>
        <span className="analysis-note">Line width = event count</span>
      </div>
      <svg
        className="network-svg"
        viewBox={"0 0 " + SIZE + " " + SIZE}
        role="img"
        aria-labelledby="network-svg-title network-svg-desc"
      >
        <title id="network-svg-title">Aggregated protein-pair proximity network</title>
        <desc id="network-svg-desc">
          {nodes.length} proteins connected by {edges.length} observed pairs.
        </desc>
        {edges.map((edge) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) return null;
          return (
            <line
              key={edge.source + "::" + edge.target}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              strokeWidth={1.5 + (edge.observation_count / maxCount) * 6}
            >
              <title>
                {edge.source} to {edge.target}: {edge.observation_count} observations,
                mean score {edge.mean_score.toFixed(3)}
              </title>
            </line>
          );
        })}
        {nodes.map((node) => {
          const point = positions.get(node.protein)!;
          return (
            <g key={node.protein} transform={"translate(" + point.x + " " + point.y + ")"}>
              <circle r={18 + Math.min(node.degree, 6) * 2} />
              <text y="4" textAnchor="middle">
                {node.protein}
              </text>
              <title>
                {node.protein}: degree {node.degree}, {node.observation_count} observations
              </title>
            </g>
          );
        })}
      </svg>
    </section>
  );
}
