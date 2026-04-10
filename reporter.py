#!/usr/bin/env python
"""
Reporter - JSON and HTML Report Generator with Chart.js visualizations.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class Reporter:
    """Generate stress test reports in JSON and HTML formats."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.reporter_config = config.get('reporter', {})
        self.output_dir = Path(self.reporter_config.get('output_dir', './reports'))
        self.json_filename = self.reporter_config.get('json_filename', 'stress_test_results.json')
        self.html_filename = self.reporter_config.get('html_filename', 'stress_test_report.html')
        
    def generate_json_report(self, scores: Dict, results: List[Dict], queries: List[str]) -> str:
        """Generate JSON report with raw data."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'tool_version': '1.0.0',
                'test_duration_seconds': self.config.get('load', {}).get('duration_seconds', 60),
                'concurrency': self.config.get('load', {}).get('concurrency_levels', [10])[0]
            },
            'summary': {
                'health_score': scores.get('health_score', 0),
                'total_requests': scores.get('total_requests', 0),
                'successful_requests': scores.get('successful_requests', 0),
                'failed_requests': scores.get('failed_requests', 0),
                'error_rate': scores.get('error_rate', 0),
                'precision_score': scores.get('precision_score', 0),
                'hallucination_rate': scores.get('hallucination_rate', 0),
                'refusal_rate': scores.get('refusal_rate', 0),
                'consistency_score': scores.get('consistency_score', 0)
            },
            'latency': scores.get('latency', {}),
            'by_query_type': scores.get('by_query_type', {}),
            'recommendations': scores.get('recommendations', []),
            'raw_results': results,
            'queries': queries
        }
        json_path = self.output_dir / self.json_filename
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return str(json_path)
    
    def generate_html_report(self, scores: Dict, results: List[Dict], queries: List[str]) -> str:
        """Generate HTML report with Chart.js visualizations."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        health_score = scores.get('health_score', 0)
        latency = scores.get('latency', {})
        by_type = scores.get('by_query_type', {})
        recommendations = scores.get('recommendations', [])

        if health_score >= 80:
            health_status, health_color = "EXCELLENT", "#28a745"
        elif health_score >= 60:
            health_status, health_color = "GOOD", "#17a2b8"
        elif health_score >= 40:
            health_status, health_color = "FAIR", "#ffc107"
        else:
            health_status, health_color = "POOR", "#dc3545"

        type_names = list(by_type.keys()) if by_type else ['unknown']
        type_success_rates = [by_type.get(t, {}).get('success_rate', 0) * 100 for t in type_names]
        latencies = [r['latency_ms'] for r in results if r.get('latency_ms')]

        recommendations_html = ''.join(f'<li>{rec}</li>' for rec in recommendations)

        table_rows_html = ''
        for tn in type_names:
            td = by_type.get(tn, {})
            success_css = "success" if td.get("success_rate", 0) > 0.8 else "error"
            hall_rate = td.get("hallucination_rate", 0)
            hall_css = "error" if hall_rate > 0.5 else ("warning" if hall_rate > 0.2 else "success")
            ref_rate = td.get("refusal_rate", 0)
            ref_css = "success" if (tn == "out_of_scope" and ref_rate > 0.5) else ("error" if ref_rate > 0.5 and tn != "out_of_scope" else "")
            table_rows_html += (
                f'<tr><td>{tn}</td>'
                f'<td>{td.get("count", 0)}</td>'
                f'<td class="{success_css}">{td.get("success_rate", 0) * 100:.1f}%</td>'
                f'<td>{td.get("avg_latency", 0):.1f}ms</td>'
                f'<td>{td.get("error_rate", 0) * 100:.1f}%</td>'
                f'<td class="{hall_css}">{hall_rate * 100:.1f}%</td>'
                f'<td class="{ref_css}">{ref_rate * 100:.1f}%</td></tr>'
            )

        type_hallucination_rates = [by_type.get(t, {}).get('hallucination_rate', 0) * 100 for t in type_names]
        type_refusal_rates = [by_type.get(t, {}).get('refusal_rate', 0) * 100 for t in type_names]
        type_labels_json = json.dumps(type_names)
        type_data_json = json.dumps(type_success_rates)
        type_hallucination_json = json.dumps(type_hallucination_rates)
        type_refusal_json = json.dumps(type_refusal_rates)
        latencies_json = json.dumps(latencies if latencies else [0])

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_requests = scores.get('total_requests', 0)
        success_rate = (1 - scores.get('error_rate', 0)) * 100
        precision_val = scores.get('precision_score', 0) * 100
        hallucination_val = scores.get('hallucination_rate', 0) * 100
        p95_val = latency.get('p95', 0)
        consistency_val = scores.get('consistency_score', 0) * 100

        # CSS kept as a plain string so curly braces need no escaping
        css = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 30px; margin-bottom: 20px; border-radius: 8px; }
        .header h1 { margin-bottom: 10px; }
        .health-score { background: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        """ + f".health-score .score {{ font-size: 48px; font-weight: bold; color: {health_color}; }}" + """
        """ + f".health-score .status {{ font-size: 24px; color: {health_color}; margin-top: 10px; }}" + """
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-card h3 { color: #2c3e50; margin-bottom: 15px; font-size: 14px; text-transform: uppercase; }
        .metric-value { font-size: 32px; font-weight: bold; color: #333; }
        .metric-label { color: #666; font-size: 14px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .chart-container h3 { color: #2c3e50; margin-bottom: 15px; }
        .recommendations { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .recommendations h3 { color: #2c3e50; margin-bottom: 15px; }
        .recommendations li { padding: 10px; border-left: 4px solid #ffc107; margin-bottom: 10px; background: #fff9e6; list-style: none; }
        .table-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #2c3e50; color: white; }
        tr:hover { background: #f5f5f5; }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .warning { color: #e67e00; }
        """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Stress Test Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RAG Pipeline Stress Test Report</h1>
            <div class="timestamp">Generated: {timestamp}</div>
        </div>
        <div class="health-score">
            <div class="score">{health_score:.1f}/100</div>
            <div class="status">{health_status}</div>
        </div>
        <div class="metrics-grid">
            <div class="metric-card"><h3>Total Requests</h3><div class="metric-value">{total_requests}</div><div class="metric-label">queries tested</div></div>
            <div class="metric-card"><h3>Success Rate</h3><div class="metric-value">{success_rate:.1f}%</div><div class="metric-label">successful responses</div></div>
            <div class="metric-card"><h3>Precision Score</h3><div class="metric-value">{precision_val:.1f}%</div><div class="metric-label">relevant responses</div></div>
            <div class="metric-card"><h3>Hallucination Rate</h3><div class="metric-value">{hallucination_val:.1f}%</div><div class="metric-label">potential hallucinations</div></div>
            <div class="metric-card"><h3>P95 Latency</h3><div class="metric-value">{p95_val:.1f}ms</div><div class="metric-label">response time</div></div>
            <div class="metric-card"><h3>Consistency</h3><div class="metric-value">{consistency_val:.1f}%</div><div class="metric-label">uniform quality</div></div>
        </div>
        <div class="chart-container"><h3>Success Rate by Query Type</h3><canvas id="typeChart"></canvas></div>
        <div class="chart-container"><h3>Hallucination &amp; Refusal Rate by Query Type</h3><canvas id="hallucChart"></canvas></div>
        <div class="chart-container"><h3>Latency Distribution</h3><canvas id="latencyChart"></canvas></div>
        <div class="recommendations"><h3>Recommendations</h3><ul>{recommendations_html}</ul></div>
        <div class="table-container"><h3>Query Type Breakdown</h3>
            <table>
                <thead><tr><th>Query Type</th><th>Count</th><th>Success Rate</th><th>Avg Latency</th><th>Error Rate</th><th>Hallucination Rate</th><th>Refusal Rate</th></tr></thead>
                <tbody>{table_rows_html}</tbody>
            </table>
        </div>
    </div>
    <script>
        const typeCtx = document.getElementById('typeChart').getContext('2d');
        new Chart(typeCtx, {{
            type: 'bar',
            data: {{
                labels: {type_labels_json},
                datasets: [{{
                    label: 'Success Rate (%)',
                    data: {type_data_json},
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{ beginAtZero: true, max: 100 }}
                }}
            }}
        }});

        const hallucCtx = document.getElementById('hallucChart').getContext('2d');
        new Chart(hallucCtx, {{
            type: 'bar',
            data: {{
                labels: {type_labels_json},
                datasets: [
                    {{
                        label: 'Hallucination Rate (%)',
                        data: {type_hallucination_json},
                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Refusal Rate (%)',
                        data: {type_refusal_json},
                        backgroundColor: 'rgba(255, 205, 86, 0.6)',
                        borderColor: 'rgba(255, 205, 86, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
            }}
        }});

        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        const binSize = 100;
        const latData = {latencies_json};
        const maxLat = latData.length > 0 ? Math.max(...latData) : 0;
        const bins = {{}};
        for (let i = 0; i <= maxLat; i += binSize) bins[i] = 0;
        latData.forEach(function(lat) {{
            const bin = Math.floor(lat / binSize) * binSize;
            if (bins[bin] !== undefined) bins[bin]++;
        }});
        new Chart(latencyCtx, {{
            type: 'bar',
            data: {{
                labels: Object.keys(bins).map(function(k) {{ return k + 'ms'; }}),
                datasets: [{{
                    label: 'Requests',
                    data: Object.values(bins),
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{ responsive: true }}
        }});
    </script>
</body>
</html>"""

        html_path = self.output_dir / self.html_filename
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(html_path)
    
    def generate_reports(self, scores: Dict, results: List[Dict], queries: List[str]) -> Dict[str, str]:
        """Generate both JSON and HTML reports."""
        json_path = self.generate_json_report(scores, results, queries)
        html_path = self.generate_html_report(scores, results, queries)
        return {'json': json_path, 'html': html_path}


if __name__ == "__main__":
    config = {'reporter': {'output_dir': './reports', 'json_filename': 'test_results.json', 'html_filename': 'test_report.html'}}
    reporter = Reporter(config)
    scores = {'health_score': 75.5, 'total_requests': 100, 'successful_requests': 85, 'failed_requests': 15, 'error_rate': 0.15,
              'precision_score': 0.82, 'hallucination_rate': 0.12, 'refusal_rate': 0.08, 'consistency_score': 0.88,
              'latency': {'p50': 150, 'p95': 350, 'p99': 500},
              'by_query_type': {'out_of_scope': {'count': 20, 'success_rate': 0.9, 'avg_latency': 140}},
              'recommendations': ['High error rate detected.', 'System is performing well across most metrics.']}
    results = [{'query': 'Test query', 'success': True, 'latency_ms': 150}, {'query': 'Another query', 'success': False, 'latency_ms': 200}]
    queries = ['Test query', 'Another query']
    paths = reporter.generate_reports(scores, results, queries)
    print("Generated reports:\n  JSON: " + paths['json'] + "\n  HTML: " + paths['html'])