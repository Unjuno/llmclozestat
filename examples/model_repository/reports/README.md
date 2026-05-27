# Reports

Derived reports for this model repository should go here.

Recommended outputs:

```text
reports/run_index.csv
reports/blank_fills.csv
reports/fill_distribution.csv
reports/position_pass_rate.csv
reports/metadata.json
```

## Derived, not source of truth

Reports are generated from raw submission JSONL files.

Source of truth:

```text
submissions/**/run.jsonl
submissions/**/run-shards/*.jsonl
```

Reports may be regenerated after merge by CI or manually.

## Do not edit reports in result PRs

A result PR should only add:

```text
submissions/<submitter_id>/<run_id>/**
```

Report updates should happen separately after the result submission is accepted.
