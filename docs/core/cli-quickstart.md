# CLI Quickstart

## Commands

The product command surface is intentionally small:

```bash
chase open --project <dir> [--chapter <n> | --target-chapter <n>]
chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]
chase write --project <dir> [--chapter <n> | --target-chapter <n>] [--steps <csv>]
chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]
chase check --project <dir> [--chapter <n> | --target-chapter <n>]
```

## Common flows

```bash
# Prepare launch or next chapter context
chase open --project my-book
chase open --project my-book --chapter 12

# Run quality gate
chase quality --project my-book --chapter-no 12

# Run the main writing pipeline
chase write --project my-book --chapter 12

# Check book health
chase status --project my-book

# Dry-run health sweep
chase check --project my-book --chapter 12
```

## Default chains

- `write`: `open,runtime,quality,status`
- `check`: `open,quality,status` and never enters runtime prose generation.

## Chapter semantics

- `--chapter <n>` means the current drafted reference chapter.
- `open` uses that reference chapter to prepare `target_chapter = n + 1` by default, and now builds planning review plus next-context readiness in-process.
- Use `--target-chapter <m>` when the planning target is not simply reference + 1.
- `status`, `quality`, and `runtime` consume the reference chapter directly.

