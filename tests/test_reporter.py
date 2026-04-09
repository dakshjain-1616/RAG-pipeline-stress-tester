#!/usr/bin/env python
"""
Test Reporter Module for RAG Stress Tester.
"""

import pytest
import json
import os
from pathlib import Path
from reporter import Reporter


class TestReporterInit:
    """Test reporter initialization."""
    
    def test_init_with_default_config(self):
        config = {'reporter': {'output_dir': './test_reports'}}
        reporter = Reporter(config)
        assert reporter.output_dir == Path('./test_reports')
        assert reporter.json_filename == 'stress_test_results.json'
        assert reporter.html_filename == 'stress_test_report.html'
    
    def test_init_with_custom_filenames(self):
        config = {
            'reporter': {
                'output_dir': './custom_reports',
                'json_filename': 'custom.json',
                'html_filename': 'custom.html'
            }
        }
        reporter = Reporter(config)
        assert reporter.json_filename == 'custom.json'
        assert reporter.html_filename == 'custom.html'


class TestJSONReport:
    """Test JSON report generation."""
    
    @pytest.fixture
    def reporter(self):
        config = {'reporter': {'output_dir': './test_json_reports'}}
        return Reporter(config)
    
    @pytest.fixture
    def sample_scores(self):
        return {
            'health_score': 75.5,
            'total_requests': 100,
            'successful_requests': 85,
            'failed_requests': 15,
            'error_rate': 0.15,
            'precision_score': 0.82,
            'hallucination_rate': 0.12,
            'refusal_rate': 0.08,
            'consistency_score': 0.88,
            'latency': {'p50': 150, 'p95': 350, 'p99': 500},
            'by_query_type': {'out_of_scope': {'count': 20, 'success_rate': 0.9}},
            'recommendations': ['Test recommendation']
        }
    
    @pytest.fixture
    def sample_results(self):
        return [
            {'query': 'Test query 1', 'success': True, 'latency_ms': 150},
            {'query': 'Test query 2', 'success': False, 'latency_ms': 200}
        ]
    
    @pytest.fixture
    def sample_queries(self):
        return ['Test query 1', 'Test query 2']
    
    def test_generate_json_report_creates_file(self, reporter, sample_scores, sample_results, sample_queries):
        json_path = reporter.generate_json_report(sample_scores, sample_results, sample_queries)
        assert Path(json_path).exists()
        assert json_path.endswith('.json')
    
    def test_json_report_contains_metadata(self, reporter, sample_scores, sample_results, sample_queries):
        json_path = reporter.generate_json_report(sample_scores, sample_results, sample_queries)
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert 'metadata' in data
        assert 'generated_at' in data['metadata']
        assert 'tool_version' in data['metadata']
    
    def test_json_report_contains_summary(self, reporter, sample_scores, sample_results, sample_queries):
        json_path = reporter.generate_json_report(sample_scores, sample_results, sample_queries)
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert 'summary' in data
        assert data['summary']['health_score'] == 75.5
        assert data['summary']['total_requests'] == 100
    
    def test_json_report_contains_raw_results(self, reporter, sample_scores, sample_results, sample_queries):
        json_path = reporter.generate_json_report(sample_scores, sample_results, sample_queries)
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert 'raw_results' in data
        assert len(data['raw_results']) == 2


class TestHTMLReport:
    """Test HTML report generation."""
    
    @pytest.fixture
    def reporter(self):
        config = {'reporter': {'output_dir': './test_html_reports'}}
        return Reporter(config)
    
    @pytest.fixture
    def sample_scores(self):
        return {
            'health_score': 85.0,
            'total_requests': 100,
            'successful_requests': 90,
            'failed_requests': 10,
            'error_rate': 0.10,
            'precision_score': 0.85,
            'hallucination_rate': 0.05,
            'refusal_rate': 0.05,
            'consistency_score': 0.90,
            'latency': {'p50': 100, 'p95': 250, 'p99': 400},
            'by_query_type': {
                'out_of_scope': {'count': 25, 'success_rate': 0.92, 'avg_latency': 120, 'error_rate': 0.08, 'hallucination_rate': 0.04},
                'ambiguous': {'count': 25, 'success_rate': 0.88, 'avg_latency': 140, 'error_rate': 0.12, 'hallucination_rate': 0.06}
            },
            'recommendations': ['Excellent performance', 'Consider optimizing latency']
        }
    
    @pytest.fixture
    def sample_results(self):
        return [
            {'query': 'Test query 1', 'success': True, 'latency_ms': 100},
            {'query': 'Test query 2', 'success': True, 'latency_ms': 150},
            {'query': 'Test query 3', 'success': False, 'latency_ms': 200}
        ]
    
    @pytest.fixture
    def sample_queries(self):
        return ['Test query 1', 'Test query 2', 'Test query 3']
    
    def test_generate_html_report_creates_file(self, reporter, sample_scores, sample_results, sample_queries):
        html_path = reporter.generate_html_report(sample_scores, sample_results, sample_queries)
        assert Path(html_path).exists()
        assert html_path.endswith('.html')
    
    def test_html_report_contains_doctype(self, reporter, sample_scores, sample_results, sample_queries):
        html_path = reporter.generate_html_report(sample_scores, sample_results, sample_queries)
        with open(html_path, 'r') as f:
            content = f.read()
        assert '<!DOCTYPE html>' in content
        assert '<html lang="en">' in content
    
    def test_html_report_contains_health_score(self, reporter, sample_scores, sample_results, sample_queries):
        html_path = reporter.generate_html_report(sample_scores, sample_results, sample_queries)
        with open(html_path, 'r') as f:
            content = f.read()
        assert '85.0' in content
        assert '/100' in content
        assert 'EXCELLENT' in content
    
    def test_html_report_contains_chart_js(self, reporter, sample_scores, sample_results, sample_queries):
        html_path = reporter.generate_html_report(sample_scores, sample_results, sample_queries)
        with open(html_path, 'r') as f:
            content = f.read()
        assert 'chart.js' in content.lower()
        assert '<canvas id="typeChart">' in content
        assert '<canvas id="latencyChart">' in content
    
    def test_html_report_contains_recommendations(self, reporter, sample_scores, sample_results, sample_queries):
        html_path = reporter.generate_html_report(sample_scores, sample_results, sample_queries)
        with open(html_path, 'r') as f:
            content = f.read()
        assert 'Excellent performance' in content
        assert 'Consider optimizing latency' in content
    
    def test_html_report_contains_table(self, reporter, sample_scores, sample_results, sample_queries):
        html_path = reporter.generate_html_report(sample_scores, sample_results, sample_queries)
        with open(html_path, 'r') as f:
            content = f.read()
        assert '<table>' in content
        assert 'Query Type' in content
        assert 'out_of_scope' in content


class TestReportGeneration:
    """Test combined report generation."""
    
    @pytest.fixture
    def reporter(self):
        config = {'reporter': {'output_dir': './test_combined_reports'}}
        return Reporter(config)
    
    @pytest.fixture
    def sample_data(self):
        scores = {
            'health_score': 70.0,
            'total_requests': 50,
            'successful_requests': 40,
            'failed_requests': 10,
            'error_rate': 0.20,
            'precision_score': 0.75,
            'hallucination_rate': 0.15,
            'refusal_rate': 0.10,
            'consistency_score': 0.80,
            'latency': {'p50': 120, 'p95': 300, 'p99': 450},
            'by_query_type': {'test': {'count': 10, 'success_rate': 0.8}},
            'recommendations': ['Test recommendation']
        }
        results = [{'query': 'Q1', 'success': True, 'latency_ms': 100}]
        queries = ['Q1']
        return scores, results, queries
    
    def test_generate_reports_returns_both_paths(self, reporter, sample_data):
        scores, results, queries = sample_data
        paths = reporter.generate_reports(scores, results, queries)
        assert 'json' in paths
        assert 'html' in paths
        assert Path(paths['json']).exists()
        assert Path(paths['html']).exists()


class TestHealthScoreStatus:
    """Test health score status determination."""
    
    @pytest.fixture
    def reporter(self):
        config = {'reporter': {'output_dir': './test_health_reports'}}
        return Reporter(config)
    
    def test_excellent_health_score(self, reporter):
        scores = {'health_score': 90, 'total_requests': 10, 'successful_requests': 10, 'failed_requests': 0,
                  'error_rate': 0, 'precision_score': 0.9, 'hallucination_rate': 0.05, 'refusal_rate': 0.05,
                  'consistency_score': 0.95, 'latency': {'p95': 100}, 'by_query_type': {}, 'recommendations': []}
        html_path = reporter.generate_html_report(scores, [{'success': True, 'latency_ms': 50}], ['test'])
        with open(html_path, 'r') as f:
            content = f.read()
        assert 'EXCELLENT' in content
    
    def test_good_health_score(self, reporter):
        scores = {'health_score': 70, 'total_requests': 10, 'successful_requests': 8, 'failed_requests': 2,
                  'error_rate': 0.2, 'precision_score': 0.75, 'hallucination_rate': 0.1, 'refusal_rate': 0.1,
                  'consistency_score': 0.8, 'latency': {'p95': 200}, 'by_query_type': {}, 'recommendations': []}
        html_path = reporter.generate_html_report(scores, [{'success': True, 'latency_ms': 100}], ['test'])
        with open(html_path, 'r') as f:
            content = f.read()
        assert 'GOOD' in content
    
    def test_fair_health_score(self, reporter):
        scores = {'health_score': 50, 'total_requests': 10, 'successful_requests': 6, 'failed_requests': 4,
                  'error_rate': 0.4, 'precision_score': 0.6, 'hallucination_rate': 0.2, 'refusal_rate': 0.2,
                  'consistency_score': 0.6, 'latency': {'p95': 300}, 'by_query_type': {}, 'recommendations': []}
        html_path = reporter.generate_html_report(scores, [{'success': True, 'latency_ms': 150}], ['test'])
        with open(html_path, 'r') as f:
            content = f.read()
        assert 'FAIR' in content
    
    def test_poor_health_score(self, reporter):
        scores = {'health_score': 30, 'total_requests': 10, 'successful_requests': 4, 'failed_requests': 6,
                  'error_rate': 0.6, 'precision_score': 0.4, 'hallucination_rate': 0.3, 'refusal_rate': 0.3,
                  'consistency_score': 0.4, 'latency': {'p95': 500}, 'by_query_type': {}, 'recommendations': []}
        html_path = reporter.generate_html_report(scores, [{'success': False, 'latency_ms': 300}], ['test'])
        with open(html_path, 'r') as f:
            content = f.read()
        assert 'POOR' in content