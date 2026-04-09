"""
Tests for evaluator.py - Scoring and Metrics module.
"""

import pytest
import sys
import numpy as np

sys.path.insert(0, '/app/project')

from evaluator import Evaluator


class TestEvaluator:
    """Test Evaluator class."""

    def test_evaluator_initialization(self):
        """Test that Evaluator initializes correctly."""
        evaluator = Evaluator()
        assert evaluator is not None
        assert hasattr(evaluator, 'detect_refusal')
        assert hasattr(evaluator, 'calculate_keyword_overlap')
        assert hasattr(evaluator, 'detect_hallucination')
        assert hasattr(evaluator, 'evaluate')

    def test_detect_refusal_positive(self):
        """Test refusal detection with clear refusal phrases."""
        evaluator = Evaluator()
        responses = [
            "I cannot answer that question",
            "I don't know the answer",
            "Unable to provide that information",
            "Not enough information to answer"
        ]
        for response in responses:
            assert evaluator.detect_refusal(response) is True

    def test_detect_refusal_negative(self):
        """Test refusal detection with non-refusal responses."""
        evaluator = Evaluator()
        responses = [
            "The answer is 42",
            "According to the document, it works like this",
            "Here is the information you requested"
        ]
        for response in responses:
            assert evaluator.detect_refusal(response) is False

    def test_calculate_keyword_overlap(self):
        """Test keyword overlap calculation."""
        evaluator = Evaluator()
        query = "What is the weather forecast for New York?"
        response = "The weather in New York is sunny with a forecast of rain tomorrow"
        overlap = evaluator.calculate_keyword_overlap(query, response)
        assert overlap > 0
        assert overlap <= 1.0

    def test_calculate_keyword_overlap_low(self):
        """Test keyword overlap with low similarity."""
        evaluator = Evaluator()
        query = "What is the weather forecast?"
        response = "The stock price is increasing"
        overlap = evaluator.calculate_keyword_overlap(query, response)
        assert overlap < 0.5

    def test_detect_hallucination_high_overlap(self):
        """Test hallucination detection with high overlap (not hallucination)."""
        evaluator = Evaluator()
        query = "What is the capital of France?"
        response = "The capital of France is Paris"
        is_hallucination = evaluator.detect_hallucination(query, response, threshold=0.5)
        assert is_hallucination is False

    def test_detect_hallucination_low_overlap(self):
        """Test hallucination detection with low overlap (hallucination)."""
        evaluator = Evaluator()
        query = "What is the capital of France?"
        response = "The weather is sunny today"
        is_hallucination = evaluator.detect_hallucination(query, response, threshold=0.5)
        assert is_hallucination is True

    def test_calculate_latency_metrics(self):
        """Test latency metrics calculation."""
        evaluator = Evaluator()
        latencies = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        metrics = evaluator.calculate_latency_metrics(latencies)
        assert 'p50' in metrics
        assert 'p95' in metrics
        assert 'p99' in metrics
        assert 'mean' in metrics
        assert 'std' in metrics
        assert metrics['p50'] > 0
        assert metrics['p95'] > metrics['p50']
        assert metrics['p99'] >= metrics['p95']

    def test_calculate_error_rate(self):
        """Test error rate calculation."""
        evaluator = Evaluator()
        results = [
            {'error': None},
            {'error': None},
            {'error': 'timeout'},
            {'error': None},
            {'error': 'connection_error'}
        ]
        error_rate = evaluator.calculate_error_rate(results)
        assert error_rate == 0.4  # 2 errors out of 5

    def test_calculate_consistency_score(self):
        """Test consistency score calculation."""
        evaluator = Evaluator()
        responses = [
            "The answer is 42",
            "The answer is 42",
            "The answer is 42",
            "The answer is 43",
            "The answer is 42"
        ]
        consistency = evaluator.calculate_consistency_score(responses)
        assert consistency > 0.5  # Most responses are consistent

    def test_calculate_precision_score(self):
        """Test precision score calculation."""
        evaluator = Evaluator()
        queries = ["What is X?", "How does Y work?"]
        responses = ["X is defined as...", "Y works by..."]
        precision = evaluator.calculate_precision_score(queries, responses)
        assert precision >= 0
        assert precision <= 1.0

    def test_calculate_hallucination_rate(self):
        """Test hallucination rate calculation."""
        evaluator = Evaluator()
        queries = ["What is A?", "What is B?", "What is C?"]
        responses = ["A is...", "Random unrelated text", "C is..."]
        rate = evaluator.calculate_hallucination_rate(queries, responses)
        assert rate >= 0
        assert rate <= 1.0

    def test_calculate_refusal_rate(self):
        """Test refusal rate calculation."""
        evaluator = Evaluator()
        responses = [
            "I cannot answer",
            "Here is the answer",
            "I don't know",
            "The answer is 42"
        ]
        rate = evaluator.calculate_refusal_rate(responses)
        assert rate == 0.5  # 2 refusals out of 4

    def test_evaluate_full(self):
        """Test full evaluation pipeline."""
        evaluator = Evaluator()
        queries = ["What is X?", "Tell me about Y"]
        responses = ["X is...", "Y works by..."]
        latencies = [0.1, 0.2]
        errors = [None, None]
        
        results = evaluator.evaluate(queries, responses, latencies, errors)
        
        assert 'hallucination_rate' in results
        assert 'refusal_rate' in results
        assert 'precision_score' in results
        assert 'latency_metrics' in results
        assert 'error_rate' in results
        assert 'consistency_score' in results
        assert 'health_score' in results

    def test_evaluate_with_errors(self):
        """Test evaluation with some errors."""
        evaluator = Evaluator()
        queries = ["Query 1", "Query 2", "Query 3"]
        responses = ["Response 1", "Response 2", "Response 3"]
        latencies = [0.1, 0.2, 0.3]
        errors = [None, 'timeout', None]
        
        results = evaluator.evaluate(queries, responses, latencies, errors)
        assert results['error_rate'] > 0

    def test_evaluate_with_refusals(self):
        """Test evaluation with refusal responses."""
        evaluator = Evaluator()
        queries = ["Query 1", "Query 2"]
        responses = ["I cannot answer", "Here is the answer"]
        latencies = [0.1, 0.2]
        errors = [None, None]
        
        results = evaluator.evaluate(queries, responses, latencies, errors)
        assert results['refusal_rate'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])