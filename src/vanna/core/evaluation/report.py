"""
Evaluation reporting with HTML, CSV, and console output.

This module provides classes for generating evaluation reports,
including comparison reports for evaluating multiple agent variants.
"""

import csv
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .base import TestCaseResult, AgentVariant, Evaluator, TestCase


@dataclass
class EvaluationReport:
    """Report for a single agent's evaluation results.

    Attributes:
        agent_name: Name of the agent evaluated
        results: List of results for each test case
        evaluators: List of evaluators used
        metadata: Additional metadata about the agent/run
        timestamp: When the evaluation was run
    """

    agent_name: str
    results: List[TestCaseResult]
    evaluators: List[Evaluator]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def pass_rate(self) -> float:
        """Calculate overall pass rate (0.0 to 1.0)."""
        if not self.results:
            return 0.0
        passed = sum(1 for r in self.results if r.overall_passed())
        return passed / len(self.results)

    def average_score(self) -> float:
        """Calculate average score across all test cases."""
        if not self.results:
            return 0.0
        return sum(r.overall_score() for r in self.results) / len(self.results)

    def average_time(self) -> float:
        """Calculate average execution time in milliseconds."""
        if not self.results:
            return 0.0
        return sum(r.execution_time_ms for r in self.results) / len(self.results)

    def total_tokens(self) -> int:
        """Calculate total tokens used across all test cases."""
        return sum(r.agent_result.total_tokens for r in self.results)

    def get_failures(self) -> List[TestCaseResult]:
        """Get all failed test cases."""
        return [r for r in self.results if not r.overall_passed()]

    def print_summary(self) -> None:
        """Print summary to console."""
        print(f"\n{'='*80}")
        print(f"EVALUATION REPORT: {self.agent_name}")
        print(f"{'='*80}")
        print(f"Timestamp: {self.timestamp.isoformat()}")
        print(f"Test Cases: {len(self.results)}")
        print(f"Pass Rate: {self.pass_rate():.1%}")
        print(f"Average Score: {self.average_score():.2f}")
        print(f"Average Time: {self.average_time():.0f}ms")
        print(f"Total Tokens: {self.total_tokens()}")
        print(f"{'='*80}\n")

        failures = self.get_failures()
        if failures:
            print(f"FAILURES ({len(failures)}):")
            for result in failures:
                print(f"\n  Test Case: {result.test_case.id}")
                print(f"  Message: {result.test_case.message}")
                print(f"  Score: {result.overall_score():.2f}")
                for eval_result in result.evaluations:
                    if not eval_result.passed:
                        print(f"    [{eval_result.evaluator_name}] {eval_result.reasoning}")


@dataclass
class ComparisonReport:
    """Report comparing multiple agent variants.

    This is the primary report type for LLM comparison use cases.

    Attributes:
        variants: List of agent variants compared
        reports: Dict mapping variant name to EvaluationReport
        test_cases: Test cases used for comparison
        timestamp: When the comparison was run
    """

    variants: List[AgentVariant]
    reports: Dict[str, EvaluationReport]
    test_cases: List[TestCase]
    timestamp: datetime = field(default_factory=datetime.now)

    def print_summary(self) -> None:
        """Print comparison summary to console."""
        print("\n" + "="*80)
        print("AGENT COMPARISON SUMMARY")
        print("="*80)
        print(f"Timestamp: {self.timestamp.isoformat()}")
        print(f"Variants: {len(self.variants)}")
        print(f"Test Cases: {len(self.test_cases)}")

        # Table of results
        print(f"\n{'Agent':<25} {'Pass Rate':<12} {'Avg Score':<12} {'Avg Time':<12} {'Tokens':<12}")
        print("-"*80)

        for variant_name, report in self.reports.items():
            print(
                f"{variant_name:<25} "
                f"{report.pass_rate():<12.1%} "
                f"{report.average_score():<12.2f} "
                f"{report.average_time():<12.0f} "
                f"{report.total_tokens():<12,}"
            )

        print("="*80 + "\n")

    def get_best_variant(self, metric: str = "score") -> str:
        """Get the best performing variant by metric.

        Args:
            metric: Metric to optimize ('score', 'speed', 'pass_rate')

        Returns:
            Name of the best variant
        """
        if metric == "score":
            return max(self.reports.items(), key=lambda x: x[1].average_score())[0]
        elif metric == "speed":
            return min(self.reports.items(), key=lambda x: x[1].average_time())[0]
        elif metric == "pass_rate":
            return max(self.reports.items(), key=lambda x: x[1].pass_rate())[0]
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def save_csv(self, path: str) -> None:
        """Save detailed CSV for further analysis.

        Each row represents one test case × one variant combination.
        """
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'variant',
                'test_case_id',
                'test_message',
                'passed',
                'score',
                'execution_time_ms',
                'tokens',
                'error',
                'evaluator_scores',
            ])

            # Data rows
            for variant_name, report in self.reports.items():
                for result in report.results:
                    evaluator_scores = {
                        e.evaluator_name: e.score
                        for e in result.evaluations
                    }

                    writer.writerow([
                        variant_name,
                        result.test_case.id,
                        result.test_case.message[:50],  # Truncate
                        result.overall_passed(),
                        result.overall_score(),
                        result.execution_time_ms,
                        result.agent_result.total_tokens,
                        result.agent_result.error or '',
                        str(evaluator_scores),
                    ])

    def save_html(self, path: str) -> None:
        """Save interactive HTML comparison report.

        Generates a rich HTML report with:
        - Summary statistics
        - Charts comparing variants
        - Side-by-side test case results
        """
        html = self._generate_html()
        with open(path, 'w') as f:
            f.write(html)

    def _generate_html(self) -> str:
        """Generate HTML content for report."""
        # Build HTML report
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Agent Comparison Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #333; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            ".passed { color: green; font-weight: bold; }",
            ".failed { color: red; font-weight: bold; }",
            ".best { background-color: #d4edda !important; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>Agent Comparison Report</h1>",
            f"<p>Generated: {self.timestamp.isoformat()}</p>",
            f"<p>Variants: {len(self.variants)} | Test Cases: {len(self.test_cases)}</p>",
        ]

        # Summary table
        html_parts.append("<h2>Summary</h2>")
        html_parts.append("<table>")
        html_parts.append("<tr><th>Agent</th><th>Pass Rate</th><th>Avg Score</th><th>Avg Time (ms)</th><th>Total Tokens</th></tr>")

        best_by_score = self.get_best_variant("score")

        for variant_name, report in self.reports.items():
            row_class = "best" if variant_name == best_by_score else ""
            html_parts.append(
                f"<tr class='{row_class}'>"
                f"<td>{variant_name}</td>"
                f"<td>{report.pass_rate():.1%}</td>"
                f"<td>{report.average_score():.2f}</td>"
                f"<td>{report.average_time():.0f}</td>"
                f"<td>{report.total_tokens():,}</td>"
                f"</tr>"
            )

        html_parts.append("</table>")

        # Test case details
        html_parts.append("<h2>Test Case Details</h2>")

        for i, test_case in enumerate(self.test_cases):
            html_parts.append(f"<h3>Test Case {i+1}: {test_case.id}</h3>")
            html_parts.append(f"<p><strong>Message:</strong> {test_case.message}</p>")

            html_parts.append("<table>")
            html_parts.append("<tr><th>Variant</th><th>Result</th><th>Score</th><th>Time (ms)</th></tr>")

            for variant_name, report in self.reports.items():
                result = next((r for r in report.results if r.test_case.id == test_case.id), None)
                if result:
                    passed_class = "passed" if result.overall_passed() else "failed"
                    passed_text = "PASS" if result.overall_passed() else "FAIL"

                    html_parts.append(
                        f"<tr>"
                        f"<td>{variant_name}</td>"
                        f"<td class='{passed_class}'>{passed_text}</td>"
                        f"<td>{result.overall_score():.2f}</td>"
                        f"<td>{result.execution_time_ms:.0f}</td>"
                        f"</tr>"
                    )

            html_parts.append("</table>")

        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)
