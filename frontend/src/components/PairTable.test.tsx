import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PairTable } from "./PairTable";

const pairs = [
  {
    protein_a: "CD3",
    protein_b: "CD4",
    observation_count: 4,
    unique_cell_count: 3,
    mean_score: 0.55,
  },
  {
    protein_a: "PD1",
    protein_b: "PDL1",
    observation_count: 2,
    unique_cell_count: 2,
    mean_score: 0.62,
  },
];

test("renders pair metrics and filters by marker", async () => {
  const user = userEvent.setup();
  render(<PairTable pairs={pairs} />);

  expect(screen.getByRole("rowheader", { name: /CD3/ })).toBeInTheDocument();
  await user.type(screen.getByRole("searchbox"), "PDL1");

  expect(screen.queryByRole("rowheader", { name: /CD3/ })).not.toBeInTheDocument();
  expect(screen.getByRole("rowheader", { name: /PD1/ })).toBeInTheDocument();
});

test("reports an empty filtered result", async () => {
  const user = userEvent.setup();
  render(<PairTable pairs={pairs} />);

  await user.type(screen.getByRole("searchbox"), "NOT-A-MARKER");
  expect(screen.getByText(/No pairs match/)).toBeInTheDocument();
});
