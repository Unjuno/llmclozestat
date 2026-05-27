# Test Fixtures

This directory contains validation and parser/scorer fixtures.

See:

```text
docs/fixtures.md
```

## Important rule

Files under `invalid/` are intentionally broken.

Do not run repository-wide validation as if every fixture should pass.

Test code should assert that invalid fixtures fail for the expected reason.

## Initial scope

The first fixtures focus on item validation:

```text
tests/fixtures/items/valid/
tests/fixtures/items/invalid/
```

Later fixtures may cover:

```text
results/
summaries/
manifests/
model_repository/
```
