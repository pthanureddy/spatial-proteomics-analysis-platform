import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UploadPanel } from "./UploadPanel";

test("requires a selected file before submission", async () => {
  const user = userEvent.setup();
  render(
    <UploadPanel
      disabled={false}
      onUpload={vi.fn()}
      onUseSample={vi.fn()}
    />,
  );

  await user.click(screen.getByRole("button", { name: /validate/i }));
  expect(screen.getByRole("alert")).toHaveTextContent("Choose a CSV");
});

test("uploads CSV text with a default label", async () => {
  const user = userEvent.setup();
  const onUpload = vi.fn().mockResolvedValue(undefined);
  render(
    <UploadPanel
      disabled={false}
      onUpload={onUpload}
      onUseSample={vi.fn()}
    />,
  );
  const file = new File(["cell_id,condition\n"], "pilot.csv", {
    type: "text/csv",
  });

  await user.upload(screen.getByLabelText("Proximity edge-list CSV"), file);
  await user.click(screen.getByRole("button", { name: /validate/i }));

  expect(onUpload).toHaveBeenCalledWith(
    "pilot",
    "pilot.csv",
    "cell_id,condition\n",
  );
});
