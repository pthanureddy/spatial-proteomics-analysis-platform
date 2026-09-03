# Recorded 100,000-row scale check

This record is included for reproducibility, not as a performance claim or
service-level target.

## Conditions

- Date: 2026-09-03
- Command: <code>python -m scripts.scale_check --rows 100000 --seed 2026</code>
- Execution: one local CPython process, no API server, temporary on-disk SQLite
  database, cold command invocation, one observed run
- Python: 3.11.9
- Platform reported by Python: Windows-10-10.0.26200-SP0
- Processor reported by Python: AMD64 Family 25 Model 117 Stepping 2,
  AuthenticAMD
- Generated CSV: 4,706,587 bytes
- Rows: 100,000

## Observed wall-clock timings

| Stage | Seconds |
| --- | ---: |
| Generate and serialize deterministic CSV | 0.5745 |
| Decode and validate CSV | 0.4911 |
| Insert all rows in one SQLite transaction | 0.8873 |
| Read rows and compute descriptive analysis | 0.3723 |

The command asserted that the final summary contained exactly 100,000
observations. These figures capture one machine and one run; filesystem cache,
CPU scheduling, Python/SQLite builds, and hardware will change them. The script
does not measure HTTP transfer, concurrent users, memory high-water mark,
container overhead, or production persistence.

