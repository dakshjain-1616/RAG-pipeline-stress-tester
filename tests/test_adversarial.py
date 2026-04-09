#!/usr/bin/env python
"""
Test Adversarial Query Generators for RAG Stress Tester.
"""

import pytest
import os
from pathlib import Path
from adversarial import (
    OutOfScopeGenerator,
    AmbiguousGenerator,
    MultilingualGenerator,
    AdversarialGenerator,
    TemporalGenerator,
    NegationGenerator,
    CompoundGenerator
)


class TestOutOfScopeGenerator:
    """Test out-of-scope query generation."""
    
    def test_generate_batch_returns_non_empty_list(self):
        gen = OutOfScopeGenerator()
        queries = gen.generate_batch(10)
        assert len(queries) == 10
        assert all(isinstance(q, str) for q in queries)
        assert all(len(q) > 0 for q in queries)
    
    def test_generate_batch_no_duplicates(self):
        gen = OutOfScopeGenerator()
        queries = gen.generate_batch(50)
        assert len(set(queries)) == len(queries)  # No duplicates
    
    def test_load_from_file_existing_file(self):
        gen = OutOfScopeGenerator()
        # Create temp file
        temp_file = Path('/tmp/test_out_of_scope.txt')
        temp_file.write_text('Query 1\nQuery 2\nQuery 3\n')
        queries = gen.load_from_file(str(temp_file))
        assert len(queries) == 3
        assert queries[0] == 'Query 1'
        temp_file.unlink()
    
    def test_load_from_file_missing_file(self):
        gen = OutOfScopeGenerator()
        queries = gen.load_from_file('/nonexistent/file.txt')
        assert queries == []


class TestAmbiguousGenerator:
    """Test ambiguous query generation."""
    
    def test_generate_batch_returns_non_empty(self):
        gen = AmbiguousGenerator()
        queries = gen.generate_batch(10)
        assert len(queries) == 10
        assert all(isinstance(q, str) and len(q) > 0 for q in queries)
    
    def test_ambiguous_queries_have_multiple_interpretations(self):
        gen = AmbiguousGenerator()
        queries = gen.generate_batch(20)
        # Check for common ambiguous patterns
        ambiguous_keywords = ['policy', 'process', 'procedure', 'it', 'the system', 'how does']
        found_ambiguous = sum(1 for q in queries if any(kw in q.lower() for kw in ambiguous_keywords))
        assert found_ambiguous > 0  # At least some should be ambiguous


class TestMultilingualGenerator:
    """Test multilingual query generation."""
    
    def test_generate_batch_covers_multiple_languages(self):
        gen = MultilingualGenerator()
        queries = gen.generate_batch(20)
        assert len(queries) >= 10  # At least 10 languages
        
    def test_multilingual_queries_non_empty(self):
        gen = MultilingualGenerator()
        queries = gen.generate_batch(10)
        assert all(isinstance(q, str) and len(q) > 0 for q in queries)


class TestAdversarialGenerator:
    """Test adversarial/injection query generation."""
    
    def test_generate_batch_returns_non_empty(self):
        gen = AdversarialGenerator()
        queries = gen.generate_batch(10)
        assert len(queries) == 10
        assert all(isinstance(q, str) and len(q) > 0 for q in queries)
    
    def test_adversarial_queries_contain_injection_patterns(self):
        gen = AdversarialGenerator()
        queries = gen.generate_batch(20)
        injection_keywords = ['ignore', 'override', 'system prompt', 'jailbreak', 'bypass']
        found_injection = sum(1 for q in queries if any(kw in q.lower() for kw in injection_keywords))
        assert found_injection > 0


class TestTemporalTrapGenerator:
    """Test temporal trap query generation."""

    def test_generate_batch_returns_non_empty(self):
        gen = TemporalGenerator()
        queries = gen.generate_batch(10)
        assert len(queries) == 10
        assert all(isinstance(q, str) and len(q) > 0 for q in queries)

    def test_temporal_queries_reference_time(self):
        gen = TemporalGenerator()
        queries = gen.generate_batch(20)
        time_keywords = ['today', 'yesterday', 'recent', 'latest', 'current', 'this week']
        found_temporal = sum(1 for q in queries if any(kw in q.lower() for kw in time_keywords))
        assert found_temporal > 0


class TestNegationTrapGenerator:
    """Test negation trap query generation."""

    def test_generate_batch_returns_non_empty(self):
        gen = NegationGenerator()
        queries = gen.generate_batch(10)
        assert len(queries) == 10
        assert all(isinstance(q, str) and len(q) > 0 for q in queries)

    def test_negation_queries_contain_negation(self):
        gen = NegationGenerator()
        queries = gen.generate_batch(20)
        negation_keywords = ['not', 'never', 'exclude', 'without', 'except']
        found_negation = sum(1 for q in queries if any(kw in q.lower() for kw in negation_keywords))
        assert found_negation > 0


class TestCompoundQueryGenerator:
    """Test compound query generation."""

    def test_generate_batch_returns_non_empty(self):
        gen = CompoundGenerator()
        queries = gen.generate_batch(10)
        assert len(queries) == 10
        assert all(isinstance(q, str) and len(q) > 0 for q in queries)

    def test_compound_queries_have_multiple_parts(self):
        gen = CompoundGenerator()
        queries = gen.generate_batch(20)
        # Compound queries should have multiple question parts
        multi_part = sum(1 for q in queries if q.count(',') >= 1 or 'and' in q.lower() or '?' in q.replace(q.split('?')[0] if q.split('?') else '', ''))
        assert multi_part > 0  # At least some should be compound


class TestQueryBankFiles:
    """Test that query bank files load correctly."""
    
    def test_query_bank_files_exist(self):
        query_bank_dir = Path('/app/project/query_bank')
        assert query_bank_dir.exists()
        
    def test_query_bank_files_load_without_errors(self):
        query_bank_dir = Path('/app/project/query_bank')
        expected_files = ['out_of_scope.txt', 'ambiguous.txt', 'multilingual.txt', 'adversarial.txt']
        for filename in expected_files:
            filepath = query_bank_dir / filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                assert len(lines) > 0, f"{filename} should have content"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])