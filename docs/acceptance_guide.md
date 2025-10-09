# Acceptance Verification Guide

This guide walks non-developers through running the acceptance pipeline with
mocked services and producing a structured report for sign-off.

## 1. Run the pipeline with mock adapters

Use the built-in mock adapters to avoid calling external services. The command
also saves spec-formatted logs that can be parsed by the reporting script.

```bash
python main.py --use-mock --emit-spec-log
```

Key flags:

- `--use-mock` creates deterministic outputs so the run finishes quickly and
  consistently.
- `--emit-spec-log` writes the log lines (tagged with `[Spec-...]`) to the path
  specified by `--spec-log-path` (`artifacts/spec_pipeline.log` by default).

If you would like to store artifacts in a different folder, add
`--artifacts-dir path/to/folder` when invoking the command above.

## 2. Generate the acceptance report

Once the pipeline completes, feed the saved log into the reporting script:

```bash
python scripts/generate_acceptance_report.py --log-file artifacts/spec_pipeline.log
```

Example text output:

```
Acceptance Summary
==================
Overall Status: PASS

Tasks:
 - [PASS] Step 1: Generating strategic blueprint (using Gemini)...
     • Generated 2 strategies.
 - [PASS] Step 2: Embedding generated strategies using Ollama...
     • Strategies embedded successfully.
 - [PASS] Step 3: Calculating cosine similarity matrix...
     • Similarity matrix calculated.
 - [PASS] Step 4: Generating SoC summaries for downstream agents...
     • FILE: Summary updated for strategy-01 (stored at artifacts/mock_run/strategy-01/summary.md)
 - [PASS] Step 5: Evaluating whether to persist long-term reflections...
     • INFO: No reflection agents were triggered in this run.

Key Files:
 - artifacts/spec_pipeline.log
 - artifacts/mock_run/strategy-01/summary.md
 - artifacts/mock_run/strategy-02/summary.md
```

To generate JSON instead, add `--format json`.

With these two steps you can hand over both the raw logs and a summarised
report for acceptance review without touching any source code.
