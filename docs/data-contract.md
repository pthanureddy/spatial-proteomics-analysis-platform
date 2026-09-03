# Generic proximity edge-list contract

## Boundary

This is a project-defined normalized CSV contract for synthetic test data. It is
not the PXL format and does not claim compatibility with Pixelator or any assay
export. A row records a protein-pair proximity observation; it does not prove a
biochemical interaction.

## Transport

- UTF-8 or UTF-8 with BOM.
- Header row required.
- Comma-delimited and parseable by Python's RFC-style CSV reader.
- Sent as a raw request body with <code>Content-Type: text/csv</code>.
- Default maximum: 5 MiB and 100,000 data rows.
- Unknown columns are ignored and reported as warnings.
- Duplicate column names are rejected.

## Columns

| Column | Type | Constraints | Meaning in this project |
| --- | --- | --- | --- |
| <code>cell_id</code> | string | required, trimmed, 1–128 characters | Stable identifier within this dataset |
| <code>condition</code> | string | required, trimmed, 1–64 characters | Group used for descriptive comparison |
| <code>protein_a</code> | string | required, trimmed, 1–64 characters | First marker in the normalized pair |
| <code>protein_b</code> | string | required, trimmed, 1–64 characters; not equal to A ignoring case | Second marker in the normalized pair |
| <code>proximity_score</code> | finite float | inclusive range [0, 1] | Synthetic normalized closeness strength |
| <code>x</code> | finite float | at least 0 | Caller-supplied synthetic cell coordinate |
| <code>y</code> | finite float | at least 0 | Caller-supplied synthetic cell coordinate |

All rows with the same <code>cell_id</code> must have identical
<code>condition</code>, <code>x</code>, and <code>y</code>. Protein pairs are
canonicalized case-insensitively so a <code>CD4,CD3</code> row is stored as
<code>CD3,CD4</code>. Original marker spelling is otherwise preserved.

Example:

~~~csv
cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell_001,control,CD3,CD4,0.62,12.0,18.4
cell_001,control,CD3,CD8,0.31,12.0,18.4
cell_005,treated,CD3,CD4,0.49,15.7,44.1
~~~

## Analysis contract v1.0

### Dataset summary

- <code>observation_count</code>: number of accepted CSV rows.
- <code>unique_cell_count</code>: cardinality of <code>cell_id</code>.
- <code>unique_protein_count</code>: marker names across both pair positions.
- <code>conditions</code>: unique conditions in ascending lexical order.

### Protein-pair metric

For each canonical pair:

- observation count;
- unique-cell count; and
- arithmetic mean of <code>proximity_score</code>, rounded to six decimals.

Rows are observations, not necessarily independent replicates. The arithmetic
mean is descriptive and has no uncertainty or significance attached.

### Condition comparison

If the request does not select conditions, the first two lexically sorted
conditions are used when at least two exist. For every pair present in either
condition:

- <code>count_delta = count(condition_b) - count(condition_a)</code>;
- <code>mean_score_delta = mean(condition_b) - mean(condition_a)</code> when the
  pair exists in both; otherwise it is JSON <code>null</code>.

Changing condition order changes delta direction. These are raw descriptive
deltas—not differential-expression/proximity statistics.

### Undirected network summary

Each marker becomes one node and each observed canonical pair one edge:

- node degree is the number of unique neighbouring markers;
- node observation count is the sum of incident edge observations;
- node mean score is the observation-weighted mean across incident edges;
- edge observation count and mean score match the pair aggregate.

No direction, causality, binding, enrichment, or biological significance is
implied.

### Cell endpoints

The cell-page endpoint returns at most 500 points per request with supplied x/y,
condition, observation count, and mean score. The detail endpoint returns every
accepted protein-pair proximity observation for one cell. The UI uses these
coordinates directly and does not infer a layout.

## Determinism and versioning

Pair keys, conditions, nodes, and edges are sorted. API aggregates are rounded
to six decimal places. Any future semantic change should increment
<code>analysis_version</code>; additive transport fields alone need not.

