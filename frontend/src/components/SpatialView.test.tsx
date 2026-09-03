import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SpatialView } from "./SpatialView";

const cells = [
  {
    cell_id: "cell-1",
    condition: "control",
    x: 1,
    y: 2,
    observation_count: 2,
    mean_score: 0.5,
  },
  {
    cell_id: "cell-2",
    condition: "treated",
    x: 3,
    y: 4,
    observation_count: 1,
    mean_score: 0.7,
  },
];

test("exposes plotted cells as keyboard-selectable controls", async () => {
  const user = userEvent.setup();
  const onSelect = vi.fn();
  render(
    <SpatialView
      cells={cells}
      total={2}
      selectedCell={null}
      onSelectCell={onSelect}
    />,
  );

  const cell = screen.getByRole("button", { name: /cell-1/ });
  cell.focus();
  await user.keyboard("{Enter}");
  expect(onSelect).toHaveBeenCalledWith("cell-1");
});

test("renders selected cell proximity details", () => {
  render(
    <SpatialView
      cells={cells}
      total={2}
      onSelectCell={vi.fn()}
      selectedCell={{
        cell_id: "cell-2",
        condition: "treated",
        x: 3,
        y: 4,
        observations: [
          { protein_a: "PD1", protein_b: "PDL1", proximity_score: 0.7 },
        ],
      }}
    />,
  );

  expect(screen.getByText("cell-2", { selector: "strong" })).toBeInTheDocument();
  expect(screen.getByText(/PD1 — PDL1/)).toBeInTheDocument();
});
