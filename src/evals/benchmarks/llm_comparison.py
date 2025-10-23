"""
LLM Comparison Benchmark

This script compares different LLMs on SQL generation tasks.
Run from repository root:
    PYTHONPATH=. python evals/benchmarks/llm_comparison.py
"""

import asyncio
import os
from pathlib import Path

from vanna import Agent
from vanna.core.evaluation import (
    EvaluationRunner,
    EvaluationDataset,
    AgentVariant,
    TrajectoryEvaluator,
    OutputEvaluator,
    EfficiencyEvaluator,
)
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.local import MemoryConversationStore
from vanna.core.registry import ToolRegistry


def get_sql_tools() -> ToolRegistry:
    """Get SQL-related tools for testing.

    In a real scenario, this would return actual SQL tools.
    For this benchmark, we'll use a placeholder.
    """
    # TODO: Add actual SQL tools
    return ToolRegistry()


async def compare_llms():
    """Compare different LLMs on SQL generation tasks."""

    print("=" * 80)
    print("LLM COMPARISON BENCHMARK - SQL Generation")
    print("=" * 80)
    print()

    # Load test dataset
    dataset_path = Path(__file__).parent.parent / "datasets" / "sql_generation" / "basic.yaml"
    print(f"Loading dataset from: {dataset_path}")
    dataset = EvaluationDataset.from_yaml(str(dataset_path))
    print(f"Loaded dataset: {dataset.name}")
    print(f"Test cases: {len(dataset.test_cases)}")
    print()

    # Get API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("⚠️  ANTHROPIC_API_KEY not set. Using placeholder.")
        anthropic_key = "test-key"

    # Create agent variants
    print("Creating agent variants...")

    tool_registry = get_sql_tools()

    variants = [
        AgentVariant(
            name="claude-sonnet-4",
            agent=Agent(
                llm_service=AnthropicLlmService(
                    api_key=anthropic_key,
                    model="claude-sonnet-4-20250514"
                ),
                tool_registry=tool_registry,
                conversation_store=MemoryConversationStore(),
            ),
            metadata={
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "version": "2025-05-14"
            }
        ),
        AgentVariant(
            name="claude-opus-4",
            agent=Agent(
                llm_service=AnthropicLlmService(
                    api_key=anthropic_key,
                    model="claude-opus-4-20250514"
                ),
                tool_registry=tool_registry,
                conversation_store=MemoryConversationStore(),
            ),
            metadata={
                "provider": "anthropic",
                "model": "claude-opus-4-20250514",
                "version": "2025-05-14"
            }
        ),
    ]

    print(f"Created {len(variants)} variants:")
    for v in variants:
        print(f"  - {v.name}")
    print()

    # Create evaluators
    evaluators = [
        TrajectoryEvaluator(),
        OutputEvaluator(),
        EfficiencyEvaluator(
            max_execution_time_ms=10000,
            max_tokens=5000,
        ),
    ]

    print(f"Using {len(evaluators)} evaluators:")
    for e in evaluators:
        print(f"  - {e.name}")
    print()

    # Create runner with high concurrency for I/O bound tasks
    runner = EvaluationRunner(
        evaluators=evaluators,
        max_concurrency=20,  # Run 20 test cases concurrently
    )

    # Run comparison
    print("Running comparison (all variants in parallel)...")
    print(f"Total executions: {len(variants)} variants × {len(dataset.test_cases)} test cases = {len(variants) * len(dataset.test_cases)}")
    print()

    comparison = await runner.compare_agents(variants, dataset.test_cases)

    # Print results
    print()
    comparison.print_summary()

    # Show winner
    print(f"🏆 Best by score: {comparison.get_best_variant('score')}")
    print(f"⚡ Best by speed: {comparison.get_best_variant('speed')}")
    print(f"✅ Best by pass rate: {comparison.get_best_variant('pass_rate')}")
    print()

    # Save reports
    output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)

    html_path = output_dir / "llm_comparison.html"
    csv_path = output_dir / "llm_comparison.csv"

    comparison.save_html(str(html_path))
    comparison.save_csv(str(csv_path))

    print(f"📊 Reports saved:")
    print(f"  - HTML: {html_path}")
    print(f"  - CSV: {csv_path}")


async def main():
    """Run the LLM comparison benchmark."""
    try:
        await compare_llms()
    except Exception as e:
        print(f"❌ Error running benchmark: {e}")
        import traceback
        traceback.print_stack()
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
