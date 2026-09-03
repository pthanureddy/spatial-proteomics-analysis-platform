import { useRef, useState } from "react";

interface Props {
  disabled: boolean;
  onUpload: (name: string, filename: string, csv: string) => Promise<void>;
  onUseSample: () => Promise<void>;
}

function readFileAsText(file: File): Promise<string> {
  if (typeof file.text === "function") return file.text();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("The selected file could not be read."));
    reader.onload = () => resolve(String(reader.result || ""));
    reader.readAsText(file);
  });
}

export function UploadPanel({ disabled, onUpload, onUseSample }: Props) {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLocalError("");
    if (!file) {
      setLocalError("Choose a CSV file before uploading.");
      inputRef.current?.focus();
      return;
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setLocalError("Choose a file with a .csv extension.");
      return;
    }
    const resolvedName = name.trim() || file.name.replace(/\.csv$/i, "");
    await onUpload(resolvedName, file.name, await readFileAsText(file));
    setName("");
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <section className="upload-panel" aria-labelledby="upload-title">
      <div className="section-kicker">New analysis</div>
      <h2 id="upload-title">Import an edge list</h2>
      <p className="supporting-copy">
        UTF-8 CSV · synthetic or de-identified test data only
      </p>
      <form onSubmit={submit}>
        <label htmlFor="dataset-name">Dataset label</label>
        <input
          id="dataset-name"
          value={name}
          maxLength={120}
          placeholder="e.g. treatment pilot"
          onChange={(event) => setName(event.target.value)}
          disabled={disabled}
        />
        <label htmlFor="dataset-file">Proximity edge-list CSV</label>
        <input
          id="dataset-file"
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
          disabled={disabled}
        />
        {localError && (
          <p className="field-error" role="alert">
            {localError}
          </p>
        )}
        <button className="primary-button" type="submit" disabled={disabled}>
          Validate &amp; import
        </button>
      </form>
      <div className="sample-divider">
        <span>or</span>
      </div>
      <button
        className="secondary-button"
        type="button"
        onClick={() => void onUseSample()}
        disabled={disabled}
      >
        Load bundled synthetic sample
      </button>
    </section>
  );
}
