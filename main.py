#!/usr/bin/env python3
"""
RAG Pipeline Stress Tester CLI

A production-quality tool for stress testing RAG HTTP endpoints with adversarial,
edge-case, and load queries. Outputs structured HTML + JSON reports.
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import typer
import yaml

from adversarial import QueryGenerator
from loader import LoadTester
from evaluator import Evaluator
from reporter import Reporter
from corpus_analyzer import CorpusAnalyzer

app = typer.Typer(
    name="rag-stress-tester",
    help="Stress test RAG pipeline endpoints with adversarial queries",
    add_completion=False
)


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        return {
            "endpoint": {"base_url": "http://localhost:8000", "query_path": "/query", "timeout_seconds": 30},
            "load": {"concurrency_levels": [1, 5, 10, 25, 50], "ramp_mode": False, "duration_seconds": 60, "rate_limit_per_second": 100},
            "retry": {"max_attempts": 3, "exponential_backoff": True, "base_delay_seconds": 1.0},
            "reporter": {"output_dir": "./reports"}
        }
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


@app.command()
def stress_test(
    endpoint: str = typer.Option("http://localhost:8000/query", "--endpoint", "-e", help="RAG endpoint URL to test"),
    config: str = typer.Option("config.yaml", "--config", "-c", help="Path to configuration file"),
    concurrency: int = typer.Option(10, "--concurrency", "-n", help="Number of concurrent requests", min=1, max=100),
    duration: int = typer.Option(60, "--duration", "-d", help="Test duration in seconds", min=1),
    query_types: Optional[str] = typer.Option(None, "--query-types", "-t", help="Comma-separated list of query types"),
    output_dir: str = typer.Option("./reports", "--output", "-o", help="Output directory for reports"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Run stress test against a RAG endpoint."""
    typer.echo(f"🚀 Starting RAG Stress Test\n   Endpoint: {endpoint}\n   Concurrency: {concurrency}\n   Duration: {duration}s")
    
    config = load_config(config)
    config["endpoint"]["base_url"] = endpoint.rsplit('/', 1)[0] if '/' in endpoint else endpoint
    config["endpoint"]["query_path"] = "/" + endpoint.rsplit('/', 1)[1] if '/' in endpoint else "/query"
    config["load"]["concurrency_levels"] = [concurrency]
    config["load"]["duration_seconds"] = duration
    config["reporter"]["output_dir"] = output_dir
    
    query_generator = QueryGenerator(config)
    load_tester = LoadTester(config)
    evaluator = Evaluator(config)
    reporter = Reporter(config)
    
    os.makedirs(output_dir, exist_ok=True)
    
    typer.echo("\n📊 Generating test queries...")
    typed_queries = query_generator.generate_all_with_types(query_types.split(',') if query_types else None)
    queries = [q for q, _ in typed_queries]
    qtypes = [t for _, t in typed_queries]
    typer.echo(f"   Generated {len(queries)} test queries")

    typer.echo("\n⚡ Running load tests...")
    results = asyncio.run(load_tester.run_tests(endpoint, queries, qtypes))
    
    typer.echo("\n📈 Evaluating results...")
    scores = evaluator.evaluate(results)
    
    typer.echo("\n📝 Generating reports...")
    report_paths = reporter.generate_reports(scores, results, queries)
    
    typer.echo(f"\n✅ Stress test complete!\n   JSON Report: {report_paths['json']}\n   HTML Report: {report_paths['html']}")

    health_score = scores.get('health_score', 0)
    typer.echo(f"\n{'='*55}")
    typer.echo(f"  Overall Health Score : {health_score:.1f}/100")
    if health_score >= 80:
        typer.echo("  Status               : EXCELLENT - System is robust")
    elif health_score >= 60:
        typer.echo("  Status               : GOOD - Some improvements needed")
    elif health_score >= 40:
        typer.echo("  Status               : FAIR - Significant issues detected")
    else:
        typer.echo("  Status               : POOR - Critical vulnerabilities found")

    typer.echo(f"  Total requests       : {scores.get('total_requests', 0)}")
    typer.echo(f"  Error rate           : {scores.get('error_rate', 0)*100:.1f}%")
    typer.echo(f"  Precision score      : {scores.get('precision_score', 0)*100:.1f}%")
    typer.echo(f"  Hallucination rate   : {scores.get('hallucination_rate', 0)*100:.1f}%")
    typer.echo(f"  Refusal rate         : {scores.get('refusal_rate', 0)*100:.1f}%")
    typer.echo(f"  Consistency score    : {scores.get('consistency_score', 0)*100:.1f}%")
    lat = scores.get('latency_metrics', scores.get('latency', {}))
    typer.echo(f"  Latency p50/p95/p99  : {lat.get('p50',0):.1f} / {lat.get('p95',0):.1f} / {lat.get('p99',0):.1f} ms")

    by_type = scores.get('by_query_type', {})
    if by_type and list(by_type.keys()) != ['unknown']:
        typer.echo(f"\n  {'Query Type':<18} {'Count':>6}  {'Halluc%':>8}  {'Refusal%':>9}  {'AvgLat':>8}")
        typer.echo(f"  {'-'*18} {'-'*6}  {'-'*8}  {'-'*9}  {'-'*8}")
        for qtype, stats in sorted(by_type.items()):
            typer.echo(
                f"  {qtype:<18} {stats.get('count',0):>6}  "
                f"{stats.get('hallucination_rate',0)*100:>7.1f}%  "
                f"{stats.get('refusal_rate',0)*100:>8.1f}%  "
                f"{stats.get('avg_latency',0):>7.1f}ms"
            )

    recs = scores.get('recommendations', [])
    if recs:
        typer.echo(f"\n  Recommendations:")
        for rec in recs:
            typer.echo(f"    - {rec}")
    typer.echo(f"{'='*55}")


@app.command()
def analyze_corpus(
    corpus_path: str = typer.Option(..., "--corpus", "-p", help="Path to corpus directory or file"),
    output_dir: str = typer.Option("./query_bank", "--output", "-o", help="Output directory for generated queries"),
    num_queries: int = typer.Option(50, "--num-queries", "-n", help="Number of queries to generate per type", min=1, max=200),
    min_word_freq: int = typer.Option(2, "--min-word-freq", help="Minimum word frequency to count as a domain keyword", min=1),
):
    """Analyze a corpus to generate in-scope and out-of-scope queries."""
    typer.echo(f"📚 Analyzing corpus: {corpus_path}")
    config = load_config()
    config.setdefault('corpus_analyzer', {})['min_word_freq'] = min_word_freq
    analyzer = CorpusAnalyzer(config)
    results = analyzer.analyze(corpus_path, num_queries)
    os.makedirs(output_dir, exist_ok=True)
    for query_type, queries in results.items():
        output_file = Path(output_dir) / f"{query_type}_generated.txt"
        with open(output_file, 'w') as f:
            f.write(f"# Generated {query_type} queries\n")
            for query in queries:
                f.write(f"{query}\n")
        typer.echo(f"   Generated {len(queries)} {query_type} queries → {output_file}")
    typer.echo("\n✅ Corpus analysis complete!")


@app.command()
def quick_test(endpoint: str = typer.Option("http://localhost:8000/query", "--endpoint", "-e", help="RAG endpoint URL to test")):
    """Run a quick sanity test with minimal queries."""
    typer.echo(f"🔍 Running quick sanity test...")
    config = load_config()
    config["load"]["concurrency_levels"] = [1]
    config["load"]["duration_seconds"] = 10
    query_generator = QueryGenerator(config)
    load_tester = LoadTester(config)
    evaluator = Evaluator(config)
    queries = query_generator.generate_sample()
    typer.echo(f"   Testing with {len(queries)} sample queries")
    results = asyncio.run(load_tester.run_tests(endpoint, queries))
    scores = evaluator.evaluate(results)
    health_score = scores.get('health_score', 0)
    typer.echo(f"\n🎯 Quick Test Health Score: {health_score:.1f}/100")
    typer.echo("   ✅ Endpoint appears functional" if health_score >= 60 else "   ⚠️  Endpoint may have issues")


@app.command()
def version():
    """Show version information."""
    typer.echo("RAG Pipeline Stress Tester v1.0.0")


if __name__ == "__main__":
    app()