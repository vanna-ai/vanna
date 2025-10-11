"""
Evaluation System Example

This example demonstrates how to use the evaluation framework to test
and compare agents. Shows:
- Creating test cases programmatically
- Running evaluations with multiple evaluators
- Comparing agent variants (e.g., different LLMs)
- Generating reports

Usage:
    PYTHONPATH=. python vanna/examples/evaluation_example.py
"""

import asyncio
from vanna import Agent, MockLlmService, MemoryConversationStore, User
from vanna.core.evaluation import (
    EvaluationRunner,
    EvaluationDataset,
    TestCase,
    ExpectedOutcome,
    AgentVariant,
    TrajectoryEvaluator,
    OutputEvaluator,
    EfficiencyEvaluator,
)
from vanna.core.registry import ToolRegistry


def create_sample_dataset() -> EvaluationDataset:
    """Create a sample dataset for demonstration."""

    eval_user = User(
        id="eval_user",
        username="evaluator",
        email="eval@example.com",
        permissions=[]
    )

    test_cases = [
        TestCase(
            id="test_001",
            user=eval_user,
            message="Hello, how are you?",
            expected_outcome=ExpectedOutcome(
                final_answer_contains=["hello", "hi"],
                max_execution_time_ms=3000,
            ),
            metadata={"category": "greeting", "difficulty": "easy"}
        ),
        TestCase(
            id="test_002",
            user=eval_user,
            message="What can you help me with?",
            expected_outcome=ExpectedOutcome(
                final_answer_contains=["help", "assist"],
                max_execution_time_ms=3000,
            ),
            metadata={"category": "capabilities", "difficulty": "easy"}
        ),
        TestCase(
            id="test_003",
            user=eval_user,
            message="Explain quantum computing",
            expected_outcome=ExpectedOutcome(
                final_answer_contains=["quantum", "computing"],
                min_components=1,
                max_execution_time_ms=5000,
            ),
            metadata={"category": "explanation", "difficulty": "medium"}
        ),
    ]

    return EvaluationDataset(
        name="Demo Test Cases",
        test_cases=test_cases,
        description="Sample test cases for evaluation demo"
    )


def create_test_agent(name: str, response_content: str) -> Agent:
    """Create a test agent with mock LLM."""
    return Agent(
        llm_service=MockLlmService(response_content=response_content),
        tool_registry=ToolRegistry(),
        conversation_store=MemoryConversationStore(),
    )


async def demo_single_agent_evaluation():
    """Demonstrate evaluating a single agent."""
    print("\n" + "="*80)
    print("DEMO 1: Single Agent Evaluation")
    print("="*80 + "\n")

    # Create dataset
    dataset = create_sample_dataset()
    print(f"Loaded dataset: {dataset.name}")
    print(f"Test cases: {len(dataset.test_cases)}\n")

    # Create agent
    agent = create_test_agent(
        "test-agent",
        "Hello! I'm here to help you with various tasks including answering questions about topics like quantum computing."
    )

    # Create evaluators
    evaluators = [
        TrajectoryEvaluator(),
        OutputEvaluator(),
        EfficiencyEvaluator(max_execution_time_ms=5000),
    ]

    # Run evaluation
    runner = EvaluationRunner(evaluators=evaluators, max_concurrency=5)
    print("Running evaluation...")
    report = await runner.run_evaluation(agent, dataset.test_cases)

    # Print results
    report.print_summary()

    # Show failures
    failures = report.get_failures()
    if failures:
        print("\nFailed test cases:")
        for result in failures:
            print(f"  - {result.test_case.id}: {result.test_case.message}")


async def demo_agent_comparison():
    """Demonstrate comparing multiple agent variants."""
    print("\n" + "="*80)
    print("DEMO 2: Agent Comparison (LLM Comparison Use Case)")
    print("="*80 + "\n")

    # Create dataset
    dataset = create_sample_dataset()
    print(f"Loaded dataset: {dataset.name}")
    print(f"Test cases: {len(dataset.test_cases)}\n")

    # Create agent variants
    variants = [
        AgentVariant(
            name="agent-v1",
            agent=create_test_agent(
                "v1",
                "Hi there! I can help you with many things including explaining complex topics like quantum computing."
            ),
            metadata={"version": "1.0", "model": "mock-v1"}
        ),
        AgentVariant(
            name="agent-v2",
            agent=create_test_agent(
                "v2",
                "Hello! I'm your helpful assistant. I can assist with various tasks and explain topics like quantum computing in detail."
            ),
            metadata={"version": "2.0", "model": "mock-v2"}
        ),
        AgentVariant(
            name="agent-v3",
            agent=create_test_agent(
                "v3",
                "Greetings! I'm designed to help you with a wide range of tasks, from simple questions to complex explanations about quantum computing and more."
            ),
            metadata={"version": "3.0", "model": "mock-v3"}
        ),
    ]

    print(f"Created {len(variants)} agent variants:")
    for v in variants:
        print(f"  - {v.name}")
    print()

    # Create evaluators
    evaluators = [
        OutputEvaluator(),
        EfficiencyEvaluator(max_execution_time_ms=5000),
    ]

    # Run comparison
    runner = EvaluationRunner(evaluators=evaluators, max_concurrency=10)
    print(f"Running comparison ({len(variants)} variants × {len(dataset.test_cases)} test cases)...")
    print("All variants running in parallel for maximum efficiency...\n")

    comparison = await runner.compare_agents(variants, dataset.test_cases)

    # Print results
    comparison.print_summary()

    # Show best variants
    print("Best Performing Variants:")
    print(f"  🏆 Best score: {comparison.get_best_variant('score')}")
    print(f"  ⚡ Fastest: {comparison.get_best_variant('speed')}")
    print(f"  ✅ Best pass rate: {comparison.get_best_variant('pass_rate')}")


async def demo_dataset_operations():
    """Demonstrate dataset creation and manipulation."""
    print("\n" + "="*80)
    print("DEMO 3: Dataset Operations")
    print("="*80 + "\n")

    # Create dataset
    dataset = create_sample_dataset()

    # Show dataset info
    print(f"Dataset: {dataset.name}")
    print(f"Description: {dataset.description}")
    print(f"Total test cases: {len(dataset)}\n")

    # Filter by metadata
    easy_tests = dataset.filter_by_metadata(difficulty="easy")
    medium_tests = dataset.filter_by_metadata(difficulty="medium")

    print(f"Easy test cases: {len(easy_tests)}")
    print(f"Medium test cases: {len(medium_tests)}\n")

    # Save to file (for demonstration)
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = os.path.join(tmpdir, "dataset.yaml")
        json_path = os.path.join(tmpdir, "dataset.json")

        dataset.save_yaml(yaml_path)
        dataset.save_json(json_path)

        print("Dataset saved to temporary files:")
        print(f"  - YAML: {yaml_path}")
        print(f"  - JSON: {json_path}\n")

        # Load back
        loaded_yaml = EvaluationDataset.from_yaml(yaml_path)
        loaded_json = EvaluationDataset.from_json(json_path)

        print("Loaded datasets:")
        print(f"  - From YAML: {len(loaded_yaml)} test cases")
        print(f"  - From JSON: {len(loaded_json)} test cases")


async def main():
    """Run all evaluation demos."""
    print("\n🚀 Vanna Agents Evaluation System Demo")
    print("="*80)

    # Demo 1: Single agent evaluation
    await demo_single_agent_evaluation()

    # Demo 2: Agent comparison (main use case)
    await demo_agent_comparison()

    # Demo 3: Dataset operations
    await demo_dataset_operations()

    print("\n" + "="*80)
    print("✅ All demos completed!")
    print("="*80)
    print("\nKey Takeaways:")
    print("  1. Evaluations are integral to the Vanna package")
    print("  2. Parallel execution handles I/O-bound LLM calls efficiently")
    print("  3. Agent comparison is a first-class use case")
    print("  4. Multiple evaluators can be composed for comprehensive testing")
    print("  5. Reports can be exported to HTML, CSV, or printed to console")
    print("\nFor LLM comparison, see: evals/benchmarks/llm_comparison.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
