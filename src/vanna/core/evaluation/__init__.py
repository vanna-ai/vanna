"""
Evaluation framework for Vanna Agents.

This module provides a complete evaluation system for testing and comparing
agent variants, with special focus on LLM comparison use cases.

Key Features:
- Parallel execution for efficient I/O-bound operations
- Multiple built-in evaluators (trajectory, output, LLM-as-judge, efficiency)
- Rich reporting (HTML, CSV, console)
- Dataset loaders (YAML, JSON)
- Agent variant comparison

Example:
    >>> from vanna.evaluation import (
    ...     EvaluationRunner,
    ...     EvaluationDataset,
    ...     AgentVariant,
    ...     TrajectoryEvaluator,
    ...     OutputEvaluator,
    ... )
    >>>
    >>> # Load test dataset
    >>> dataset = EvaluationDataset.from_yaml("tests/sql_tasks.yaml")
    >>>
    >>> # Create agent variants
    >>> variants = [
    ...     AgentVariant("claude", claude_agent),
    ...     AgentVariant("gpt", gpt_agent),
    ... ]
    >>>
    >>> # Run comparison
    >>> runner = EvaluationRunner(
    ...     evaluators=[TrajectoryEvaluator(), OutputEvaluator()],
    ...     max_concurrency=20
    ... )
    >>> comparison = await runner.compare_agents(variants, dataset.test_cases)
    >>> comparison.print_summary()
"""

from .base import (
    Evaluator,
    TestCase,
    ExpectedOutcome,
    AgentResult,
    EvaluationResult,
    TestCaseResult,
    AgentVariant,
)
from .runner import EvaluationRunner
from .evaluators import (
    TrajectoryEvaluator,
    OutputEvaluator,
    LLMAsJudgeEvaluator,
    EfficiencyEvaluator,
)
from .report import EvaluationReport, ComparisonReport
from .dataset import EvaluationDataset

__all__ = [
    # Base classes
    "Evaluator",
    "TestCase",
    "ExpectedOutcome",
    "AgentResult",
    "EvaluationResult",
    "TestCaseResult",
    "AgentVariant",
    # Runner
    "EvaluationRunner",
    # Built-in evaluators
    "TrajectoryEvaluator",
    "OutputEvaluator",
    "LLMAsJudgeEvaluator",
    "EfficiencyEvaluator",
    # Reporting
    "EvaluationReport",
    "ComparisonReport",
    # Datasets
    "EvaluationDataset",
]
