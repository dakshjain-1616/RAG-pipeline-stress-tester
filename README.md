# RAG Pipeline Stress Tester

> Built autonomously by [NEO](https://heyneo.com) — your fully autonomous AI coding agent. &nbsp; [![NEO for VS Code](https://img.shields.io/badge/VS%20Code-NEO%20Extension-5C2D91?logo=visual-studio-code&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=NeoResearchInc.heyneo)

A battle-testing toolkit for RAG (Retrieval-Augmented Generation) systems. Hammers any HTTP endpoint with 7 categories of adversarial queries under configurable concurrent load, then scores the results across hallucination rate, precision, latency, and consistency.

---

## Why This Exists

Before deploying a RAG system to production, you need to know:

- Does it **hallucinate** when asked about things not in the corpus?
- Does it **refuse appropriately** on out-of-scope questions?
- Does it stay **consistent** when the same question is asked multiple ways?
- Does it **hold up under load** — 10, 25, 50 concurrent users?

Manual testing can't answer these questions at scale. This tool does it automatically.

---

## What It Does

```
Your RAG Endpoint  ◄──  7 adversarial query types  ──  async load driver
                               │
                               ▼
              hallucination rate · precision · latency p95/p99
              refusal rate · consistency score · health score (0–100)
                               │
                               ▼
              HTML report (Chart.js charts) + JSON report
```

---

## Why It Matters

| Without stress testing | With this tool |
|-----------------------|----------------|
| Discover hallucinations in production | Catch them before deployment |
| Users find edge cases | You find them first, in batch |
| Guess at latency under load | Measure p50/p95/p99 at realistic concurrency |
| No audit trail | Timestamped JSON + HTML reports per test run |

---

## Query Categories

The tool ships with 7 pre-built adversarial query banks, each targeting a specific failure mode:

| Category | What it tests |
|----------|---------------|
| `out_of_scope` | Questions with no answer in the corpus — tests hallucination resistance |
| `adversarial` | Trick questions designed to elicit confident wrong answers |
| `ambiguous` | Queries with multiple valid interpretations — tests disambiguation |
| `multilingual` | Non-English queries — tests language handling |
| `temporal` | Time-sensitive questions that depend on stale data |
| `negation` | "What is NOT X" style questions — a common failure mode |
| `compound` | Multi-part questions requiring multiple retrievals |

Add your own by appending lines to any file in `query_bank/`.

---

## Health Score

Every test run produces a composite **Health Score (0–100)**:

```
≥ 80  EXCELLENT   Production-ready
≥ 60  GOOD        Minor issues, review before deploying
≥ 40  FAIR        Significant issues, fix first
 < 40  POOR        Critical failures, do not deploy
```

Calculated from: precision, hallucination rate, refusal rate, consistency, and latency percentiles.

---

## Architecture

```
main.py           Typer CLI — entry point and orchestration
adversarial.py    Query generator — reads and batches from query_bank/
loader.py         Async load driver — aiohttp, configurable concurrency
evaluator.py      Scorer — hallucination, precision, refusal, consistency
reporter.py       Report generator — HTML (Chart.js) + JSON output
query_bank/       7 pre-built adversarial query files (one per line)
tests/            58 pytest tests (no live endpoint needed)
```

---

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Run a stress test

```bash
# Basic test — 10 concurrent users, 60 seconds
python main.py stress-test --endpoint http://localhost:8000/query --concurrency 10 --duration 60

# Use a config file
python main.py stress-test --config config.yaml

# Test specific query types only
python main.py stress-test --endpoint http://localhost:8000/query --query-types out_of_scope,adversarial
```

---

## Configuration

Edit `config.yaml` to customize load levels, thresholds, and reporting:

| Setting | What it controls |
|---------|-----------------|
| `load.concurrency` | Concurrent user levels to test (e.g., `[1, 5, 10, 25]`) |
| `load.duration_seconds` | How long to run at each concurrency level |
| `evaluation.hallucination_threshold` | Score below which a response is flagged |
| `evaluation.refusal_keywords` | Phrases that indicate a refused answer |
| `reporter.output_dir` | Where to save HTML and JSON reports |

---

## Output Reports

Each test run saves two files to `./reports/`:

**`stress_test_results.json`** — machine-readable raw data with per-query latency, success/failure flags, and hallucination scores. Useful for CI/CD integration.

**`stress_test_report.html`** — interactive dashboard with health score badge, bar charts by query type, latency distribution histogram, and a prioritized list of recommended improvements.

---

## Running Tests

```bash
pytest tests/ -v
```

58 tests covering all modules. Uses `aioresponses` to mock HTTP — no live RAG endpoint required.

---

## Project Structure

```
rag-pipeline-stress-tester/
├── main.py           # CLI entry point
├── adversarial.py    # Query generators (7 types)
├── loader.py         # Async load test driver
├── evaluator.py      # Scoring and metrics
├── reporter.py       # HTML + JSON report generator
├── corpus_analyzer.py
├── config.yaml       # Test configuration
├── requirements.txt
├── query_bank/       # 7 adversarial query files
└── tests/            # 58 pytest tests
```

---

## License

MIT
