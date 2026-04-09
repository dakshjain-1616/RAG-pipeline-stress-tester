#!/usr/bin/env python
"""
Test Load Tester Module for RAG Stress Tester.
"""

import pytest
import asyncio
from aiohttp import ClientSession
from loader import LoadTester


class TestLoadTester:
    """Test load tester functionality."""
    
    @pytest.fixture
    def load_tester(self):
        config = {
            'load': {
                'concurrency_levels': [1, 5, 10],
                'ramp_mode': False,
                'duration_seconds': 60,
                'rate_limit_per_second': 100
            },
            'retry': {
                'max_attempts': 3,
                'exponential_backoff': True,
                'base_delay_seconds': 0.1
            },
            'endpoint': {
                'timeout_seconds': 30
            }
        }
        return LoadTester(config)
    
    def test_init_sets_config_correctly(self, load_tester):
        assert load_tester.concurrency_levels == [1, 5, 10]
        assert load_tester.ramp_mode is False
        assert load_tester.duration_seconds == 60
        assert load_tester.max_attempts == 3
    
    def test_make_request_structure(self, load_tester):
        """Test that make_request returns correct structure."""
        async def test_request():
            async with ClientSession() as session:
                # Mock endpoint that doesn't exist - should fail
                result = await load_tester.make_request(
                    session, 
                    'http://localhost:9999/nonexistent',
                    'test query',
                    'test_type'
                )
                assert 'query' in result
                assert 'query_type' in result
                assert 'success' in result
                assert 'latency_ms' in result
                assert result['query'] == 'test query'
                assert result['query_type'] == 'test_type'
        
        asyncio.run(test_request())
    
    def test_retry_config_applied(self, load_tester):
        """Test retry configuration is applied."""
        assert load_tester.exponential_backoff is True
        assert load_tester.base_delay == 0.1
        assert load_tester.max_attempts == 3
    
    def test_concurrency_levels_set(self, load_tester):
        """Test concurrency levels are configured."""
        assert len(load_tester.concurrency_levels) > 0
        assert all(isinstance(c, int) for c in load_tester.concurrency_levels)
        assert min(load_tester.concurrency_levels) >= 1


class TestLoadTesterWithMockServer:
    """Test load tester with mock server responses."""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'load': {
                'concurrency_levels': [1, 5],
                'ramp_mode': False,
                'duration_seconds': 10,
                'rate_limit_per_second': 100
            },
            'retry': {
                'max_attempts': 2,
                'exponential_backoff': False,
                'base_delay_seconds': 0.05
            },
            'endpoint': {
                'timeout_seconds': 5
            }
        }
    
    def test_run_concurrent_batch_with_invalid_endpoint(self, mock_config):
        """Test batch run with invalid endpoint returns failures."""
        load_tester = LoadTester(mock_config)
        queries = [('test query 1', 'test'), ('test query 2', 'test')]
        
        async def run_test():
            results = await load_tester.run_concurrent_batch(
                'http://localhost:9999/invalid',
                queries,
                concurrency=1
            )
            assert len(results) == 2
            assert all(isinstance(r, dict) for r in results)
            # All should fail since endpoint doesn't exist
            assert all(r['success'] is False for r in results)
        
        asyncio.run(run_test())


class TestLoadTesterRampMode:
    """Test ramp mode functionality."""
    
    @pytest.fixture
    def ramp_config(self):
        return {
            'load': {
                'concurrency_levels': [1, 5, 10],
                'ramp_mode': True,
                'duration_seconds': 30,
                'rate_limit_per_second': 50
            },
            'retry': {
                'max_attempts': 1,
                'exponential_backoff': False,
                'base_delay_seconds': 0.1
            },
            'endpoint': {
                'timeout_seconds': 5
            }
        }
    
    def test_ramp_mode_enabled(self, ramp_config):
        """Test ramp mode configuration."""
        load_tester = LoadTester(ramp_config)
        assert load_tester.ramp_mode is True
        assert len(load_tester.concurrency_levels) > 1
    
    def test_ramp_test_with_invalid_endpoint(self, ramp_config):
        """Test ramp test returns results for each concurrency level."""
        load_tester = LoadTester(ramp_config)
        queries = [('query ' + str(i), 'test') for i in range(5)]
        
        async def run_test():
            results = await load_tester.run_ramp_test(
                'http://localhost:9999/invalid',
                queries
            )
            assert len(results) > 0
            assert all(isinstance(r, dict) for r in results)
        
        asyncio.run(run_test())