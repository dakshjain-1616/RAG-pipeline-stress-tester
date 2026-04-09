#!/usr/bin/env python3
"""
Load Tester - Async Concurrent Request Runner with aiohttp.
Features: configurable concurrency, ramp mode, duration mode, rate limiting, retry with exponential backoff.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import aiohttp
from aiohttp import ClientTimeout, ClientError


class LoadTester:
    """Async concurrent request runner for RAG stress testing."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.load_config = config.get('load', {})
        self.retry_config = config.get('retry', {})
        self.endpoint_config = config.get('endpoint', {})
        
        self.concurrency_levels = self.load_config.get('concurrency_levels', [1, 5, 10, 25, 50])
        self.ramp_mode = self.load_config.get('ramp_mode', False)
        self.duration_seconds = self.load_config.get('duration_seconds', 60)
        self.rate_limit = self.load_config.get('rate_limit_per_second', 100)
        self.max_attempts = self.retry_config.get('max_attempts', 3)
        self.exponential_backoff = self.retry_config.get('exponential_backoff', True)
        self.base_delay = self.retry_config.get('base_delay_seconds', 1.0)
        self.timeout_seconds = self.endpoint_config.get('timeout_seconds', 30)
        self.results: List[Dict] = []
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, query: str, query_type: str = 'unknown') -> Dict:
        """Make a single request with retry logic."""
        start_time = time.perf_counter()
        result = {
            'query': query, 'query_type': query_type, 'timestamp': datetime.now().isoformat(),
            'attempt': 0, 'success': False, 'status_code': None, 'latency_ms': None,
            'response': None, 'error': None, 'retry_count': 0
        }
        
        for attempt in range(1, self.max_attempts + 1):
            result['attempt'] = attempt
            try:
                payload = {'query': query}
                async with session.post(endpoint, json=payload, timeout=ClientTimeout(total=self.timeout_seconds)) as response:
                    result['status_code'] = response.status
                    result['latency_ms'] = (time.perf_counter() - start_time) * 1000
                    try:
                        result['response'] = await response.json()
                    except:
                        result['response'] = await response.text()
                    result['success'] = response.status == 200
                    if result['success']:
                        break
            except asyncio.TimeoutError:
                result['error'] = f"Timeout after {self.timeout_seconds}s"
                result['latency_ms'] = (time.perf_counter() - start_time) * 1000
            except ClientError as e:
                result['error'] = str(e)
                result['latency_ms'] = (time.perf_counter() - start_time) * 1000
            except Exception as e:
                result['error'] = f"Unexpected error: {str(e)}"
                result['latency_ms'] = (time.perf_counter() - start_time) * 1000
            
            if attempt < self.max_attempts:
                result['retry_count'] = attempt
                delay = self.base_delay * (2 ** (attempt - 1)) if self.exponential_backoff else self.base_delay
                await asyncio.sleep(delay)
        
        return result
    
    async def run_concurrent_batch(self, endpoint: str, queries: List[Tuple[str, str]], concurrency: int) -> List[Dict]:
        """Run a batch of queries with specified concurrency."""
        results = []
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(concurrency)
            async def limited_request(query: str, query_type: str):
                async with semaphore:
                    return await self.make_request(session, endpoint, query, query_type)
            tasks = [limited_request(query, query_type) for query, query_type in queries]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({'query': 'unknown', 'query_type': 'error', 'timestamp': datetime.now().isoformat(),
                                    'success': False, 'status_code': None, 'latency_ms': None, 'response': None,
                                    'error': str(result), 'retry_count': 0})
                else:
                    results.append(result)
        return results
    
    async def run_ramp_test(self, endpoint: str, queries: List[Tuple[str, str]]) -> List[Dict]:
        """Run ramp mode test - gradually increase concurrency."""
        all_results = []
        for concurrency in self.concurrency_levels:
            print(f"  Ramp: Testing with concurrency={concurrency}")
            subset = queries[:min(len(queries), 100)]
            results = await self.run_concurrent_batch(endpoint, subset, concurrency)
            all_results.extend(results)
            await asyncio.sleep(1)
        return all_results
    
    async def run_duration_test(self, endpoint: str, queries: List[Tuple[str, str]], concurrency: int) -> List[Dict]:
        """Run duration mode test - fixed time testing."""
        all_results = []
        start_time = time.time()
        end_time = start_time + self.duration_seconds
        rate_limit_delay = 1.0 / self.rate_limit if self.rate_limit > 0 else 0
        
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(concurrency)
            async def limited_request(query: str, query_type: str):
                async with semaphore:
                    return await self.make_request(session, endpoint, query, query_type)
            
            query_index = 0
            while time.time() < end_time:
                tasks = []
                for _ in range(concurrency):
                    query, query_type = queries[query_index % len(queries)]
                    tasks.append(limited_request(query, query_type))
                    query_index += 1
                if tasks:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in batch_results:
                        if isinstance(result, Exception):
                            all_results.append({'query': 'unknown', 'query_type': 'error', 'timestamp': datetime.now().isoformat(),
                                                'success': False, 'status_code': None, 'latency_ms': None, 'response': None,
                                                'error': str(result), 'retry_count': 0})
                        else:
                            all_results.append(result)
                if rate_limit_delay > 0:
                    await asyncio.sleep(rate_limit_delay)
        return all_results
    
    async def run_tests(self, endpoint: str, queries: List[str], query_types: Optional[List[str]] = None) -> List[Dict]:
        """Run stress tests against endpoint."""
        query_with_types = [(q, qt) for q, qt in zip(queries, query_types)] if query_types else [(q, 'unknown') for q in queries]
        print(f"  Starting stress test with {len(query_with_types)} queries")
        
        if self.ramp_mode:
            results = await self.run_ramp_test(endpoint, query_with_types)
        else:
            concurrency = self.concurrency_levels[0] if self.concurrency_levels else 10
            results = await self.run_duration_test(endpoint, query_with_types, concurrency)
        
        self.results = results
        return results
    
    def get_statistics(self) -> Dict:
        """Get basic statistics about test results."""
        if not self.results:
            return {'total_requests': 0}
        successful = sum(1 for r in self.results if r.get('success', False))
        failed = len(self.results) - successful
        latencies = [r['latency_ms'] for r in self.results if r.get('latency_ms') is not None]
        return {
            'total_requests': len(self.results), 'successful': successful, 'failed': failed,
            'success_rate': successful / len(self.results) if self.results else 0,
            'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
        }


if __name__ == "__main__":
    config = {
        'endpoint': {'base_url': 'http://localhost:8000', 'query_path': '/query', 'timeout_seconds': 30},
        'load': {'concurrency_levels': [1, 5, 10], 'ramp_mode': False, 'duration_seconds': 10, 'rate_limit_per_second': 10},
        'retry': {'max_attempts': 2, 'exponential_backoff': True, 'base_delay_seconds': 0.5}
    }
    tester = LoadTester(config)
    queries = ["What is machine learning?", "How does AI work?", "Explain neural networks"]
    endpoint = "http://localhost:8000/query"
    print("Running load test...")
    results = asyncio.run(tester.run_tests(endpoint, queries))
    print(f"\nTest Results:")
    stats = tester.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")