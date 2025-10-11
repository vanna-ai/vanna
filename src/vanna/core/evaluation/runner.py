"""
Evaluation runner with parallel execution support.

This module provides the EvaluationRunner class that executes test cases
against agents with configurable parallelism for efficient evaluation,
especially when comparing multiple LLMs or model versions.
"""

import asyncio
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime

from .base import (
    TestCase,
    AgentResult,
    TestCaseResult,
    AgentVariant,
    Evaluator,
)
from vanna.core import UiComponent
from vanna.core.observability import ObservabilityProvider


class EvaluationRunner:
    """Run evaluations with parallel execution support.

    The primary use case is comparing multiple agent variants (e.g., different LLMs)
    on the same set of test cases. The runner executes test cases in parallel with
    configurable concurrency to handle I/O-bound LLM operations efficiently.

    Example:
        >>> runner = EvaluationRunner(
        ...     evaluators=[TrajectoryEvaluator(), OutputEvaluator()],
        ...     max_concurrency=20
        ... )
        >>> comparison = await runner.compare_agents(
        ...     agent_variants=[claude_variant, gpt_variant],
        ...     test_cases=dataset.test_cases
        ... )
    """

    def __init__(
        self,
        evaluators: List[Evaluator],
        max_concurrency: int = 10,
        observability_provider: Optional[ObservabilityProvider] = None,
    ):
        """Initialize the evaluation runner.

        Args:
            evaluators: List of evaluators to apply to each test case
            max_concurrency: Maximum number of concurrent test case executions
            observability_provider: Optional observability for tracking eval runs
        """
        self.evaluators = evaluators
        self.max_concurrency = max_concurrency
        self.observability = observability_provider
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def run_evaluation(
        self,
        agent: "Agent",  # type: ignore
        test_cases: List[TestCase],
    ) -> "EvaluationReport":  # type: ignore
        """Run evaluation on a single agent.

        Args:
            agent: The agent to evaluate
            test_cases: List of test cases to run

        Returns:
            EvaluationReport with results for all test cases
        """
        from .report import EvaluationReport

        results = await self._run_test_cases_parallel(agent, test_cases)
        return EvaluationReport(
            agent_name="agent",
            results=results,
            evaluators=self.evaluators,
            timestamp=datetime.now(),
        )

    async def compare_agents(
        self,
        agent_variants: List[AgentVariant],
        test_cases: List[TestCase],
    ) -> "ComparisonReport":  # type: ignore
        """Compare multiple agent variants on same test cases.

        This is the PRIMARY use case for LLM comparison. Runs all variants
        in parallel for maximum efficiency with I/O-bound LLM calls.

        Args:
            agent_variants: List of agent variants to compare
            test_cases: Test cases to run on each variant

        Returns:
            ComparisonReport with results for all variants
        """
        from .report import ComparisonReport

        # Create span for overall comparison
        if self.observability:
            span = await self.observability.create_span(
                "agent_comparison",
                attributes={
                    "num_variants": len(agent_variants),
                    "num_test_cases": len(test_cases),
                }
            )

        # Run all variants in parallel
        tasks = [
            self._run_agent_variant(variant, test_cases)
            for variant in agent_variants
        ]

        variant_reports = await asyncio.gather(*tasks)

        if self.observability:
            await self.observability.end_span(span)

        return ComparisonReport(
            variants=agent_variants,
            reports=dict(zip([v.name for v in agent_variants], variant_reports)),
            test_cases=test_cases,
            timestamp=datetime.now(),
        )

    async def compare_agents_streaming(
        self,
        agent_variants: List[AgentVariant],
        test_cases: List[TestCase],
    ) -> AsyncGenerator[tuple[str, TestCaseResult, int, int], None]:
        """Stream comparison results as they complete.

        Useful for long-running evaluations where you want to see
        progress updates in real-time (e.g., for UI display).

        Args:
            agent_variants: Agent variants to compare
            test_cases: Test cases to run

        Yields:
            Tuples of (variant_name, result, completed_count, total_count)
        """
        queue: asyncio.Queue = asyncio.Queue()

        async def worker(variant: AgentVariant):
            """Worker that runs test cases for one variant."""
            results = await self._run_test_cases_parallel(variant.agent, test_cases)
            for result in results:
                await queue.put((variant.name, result))

        # Start all workers
        workers = [asyncio.create_task(worker(v)) for v in agent_variants]

        # Yield results as they arrive
        completed = 0
        total = len(agent_variants) * len(test_cases)

        while completed < total:
            variant_name, result = await queue.get()
            completed += 1
            yield variant_name, result, completed, total

        # Wait for all workers to complete
        await asyncio.gather(*workers)

    async def _run_agent_variant(
        self,
        variant: AgentVariant,
        test_cases: List[TestCase],
    ) -> "EvaluationReport":  # type: ignore
        """Run a single agent variant on all test cases.

        Args:
            variant: The agent variant to evaluate
            test_cases: Test cases to run

        Returns:
            EvaluationReport for this variant
        """
        from .report import EvaluationReport

        if self.observability:
            span = await self.observability.create_span(
                f"variant_{variant.name}",
                attributes={
                    "variant": variant.name,
                    "num_test_cases": len(test_cases),
                    **variant.metadata,
                }
            )

        results = await self._run_test_cases_parallel(variant.agent, test_cases)

        if self.observability:
            await self.observability.end_span(span)

        return EvaluationReport(
            agent_name=variant.name,
            results=results,
            evaluators=self.evaluators,
            metadata=variant.metadata,
            timestamp=datetime.now(),
        )

    async def _run_test_cases_parallel(
        self,
        agent: "Agent",  # type: ignore
        test_cases: List[TestCase],
    ) -> List[TestCaseResult]:
        """Run test cases in parallel with concurrency limit.

        Args:
            agent: The agent to run test cases on
            test_cases: Test cases to execute

        Returns:
            List of TestCaseResult, one per test case
        """
        tasks = [
            self._run_single_test_case(agent, test_case)
            for test_case in test_cases
        ]

        return await asyncio.gather(*tasks)

    async def _run_single_test_case(
        self,
        agent: "Agent",  # type: ignore
        test_case: TestCase,
    ) -> TestCaseResult:
        """Run a single test case with semaphore to limit concurrency.

        Args:
            agent: The agent to execute
            test_case: The test case to run

        Returns:
            TestCaseResult with agent execution and evaluations
        """
        async with self._semaphore:
            # Execute agent
            start_time = asyncio.get_event_loop().time()
            agent_result = await self._execute_agent(agent, test_case)
            execution_time = asyncio.get_event_loop().time() - start_time

            # Run evaluators
            eval_results = []
            for evaluator in self.evaluators:
                eval_result = await evaluator.evaluate(test_case, agent_result)
                eval_results.append(eval_result)

            return TestCaseResult(
                test_case=test_case,
                agent_result=agent_result,
                evaluations=eval_results,
                execution_time_ms=execution_time * 1000,
            )

    async def _execute_agent(
        self,
        agent: "Agent",  # type: ignore
        test_case: TestCase,
    ) -> AgentResult:  # type: ignore
        """Execute agent and capture full trajectory.

        Args:
            agent: The agent to execute
            test_case: The test case to run

        Returns:
            AgentResult with all captured data
        """
        components: List[UiComponent] = []
        tool_calls: List[Dict] = []
        error: Optional[str] = None

        try:
            async for component in agent.send_message(
                user=test_case.user,
                message=test_case.message,
                conversation_id=test_case.conversation_id,
            ):
                components.append(component)

        except Exception as e:
            error = str(e)

        # TODO: Extract tool calls and LLM requests from observability
        # For now, these will be empty unless we hook into observability

        return AgentResult(
            test_case_id=test_case.id,
            components=components,
            tool_calls=tool_calls,
            llm_requests=[],
            error=error,
        )
