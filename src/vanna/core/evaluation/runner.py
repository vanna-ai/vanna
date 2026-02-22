"""
Evaluation runner with parallel execution support.

This module provides the EvaluationRunner class that executes test cases
against agents with configurable parallelism for efficient evaluation,
especially when comparing multiple LLMs or model versions.
"""

import asyncio
from typing import Any, List, Dict, Optional, AsyncGenerator, TYPE_CHECKING
from datetime import datetime

from .base import (
    TestCase,
    AgentResult,
    TestCaseResult,
    AgentVariant,
    Evaluator,
)
from vanna.core import UiComponent
from vanna.core.llm import LlmRequest, LlmResponse
from vanna.core.middleware import LlmMiddleware
from vanna.core.user.request_context import RequestContext
from vanna.core.observability import ObservabilityProvider

if TYPE_CHECKING:
    from vanna import Agent
    from .report import EvaluationReport, ComparisonReport


class _RecordingLlmMiddleware(LlmMiddleware):
    """Internal middleware that records tool calls and LLM request metadata.

    A fresh instance is created per test-case execution so recordings are
    fully isolated between concurrent runs — no shared mutable state.
    """

    def __init__(self) -> None:
        self.tool_calls: List[Dict[str, Any]] = []
        self.llm_requests: List[Dict[str, Any]] = []
        self.total_tokens: int = 0

    async def before_llm_request(self, request: LlmRequest) -> LlmRequest:
        self.llm_requests.append(
            {
                "message_count": len(request.messages),
                "tool_count": len(request.tools or []),
                "stream": request.stream,
            }
        )
        return request

    async def after_llm_response(
        self, request: LlmRequest, response: LlmResponse
    ) -> LlmResponse:
        if response.tool_calls:
            for tc in response.tool_calls:
                self.tool_calls.append(
                    {"tool_name": tc.name, "arguments": tc.arguments}
                )
        if response.usage:
            self.total_tokens += response.usage.get("total_tokens", 0) or 0
        return response


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
        agent: "Agent",
        test_cases: List[TestCase],
    ) -> "EvaluationReport":
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
    ) -> "ComparisonReport":
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
                },
            )

        # Run all variants in parallel
        tasks = [
            self._run_agent_variant(variant, test_cases) for variant in agent_variants
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
        queue: asyncio.Queue[tuple[str, TestCaseResult]] = asyncio.Queue()

        async def worker(variant: AgentVariant) -> None:
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
    ) -> "EvaluationReport":
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
                },
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
        agent: "Agent",
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
            self._run_single_test_case(agent, test_case) for test_case in test_cases
        ]

        return await asyncio.gather(*tasks)

    async def _run_single_test_case(
        self,
        agent: "Agent",
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
        agent: "Agent",
        test_case: TestCase,
    ) -> AgentResult:
        """Execute agent and capture full trajectory.

        A fresh _RecordingLlmMiddleware and a per-run agent copy are created
        for every test case so concurrent executions never share mutable state.

        Args:
            agent: The agent to execute
            test_case: The test case to run

        Returns:
            AgentResult with all captured data (tool_calls, llm_requests, tokens)
        """
        from vanna.core.agent import Agent as AgentClass
        from vanna.integrations.local import MemoryConversationStore

        recorder = _RecordingLlmMiddleware()
        components: List[UiComponent] = []
        error: Optional[str] = None

        # Build a per-run agent that shares the same services but has its own
        # conversation store (isolation) and the recording middleware appended.
        eval_agent = AgentClass(
            llm_service=agent.llm_service,
            tool_registry=agent.tool_registry,
            user_resolver=agent.user_resolver,
            agent_memory=agent.agent_memory,
            conversation_store=MemoryConversationStore(),
            config=agent.config,
            system_prompt_builder=agent.system_prompt_builder,
            lifecycle_hooks=list(agent.lifecycle_hooks),
            llm_middlewares=[*agent.llm_middlewares, recorder],
            workflow_handler=agent.workflow_handler,
            error_recovery_strategy=agent.error_recovery_strategy,
            context_enrichers=list(agent.context_enrichers),
            llm_context_enhancer=agent.llm_context_enhancer,
            conversation_filters=list(agent.conversation_filters),
            observability_provider=agent.observability_provider,
            audit_logger=agent.audit_logger,
        )

        try:
            request_context = RequestContext(
                cookies={"user_id": test_case.user.id},
                headers={},
                metadata={"test_case_user": test_case.user},
            )

            async for component in eval_agent.send_message(
                request_context=request_context,
                message=test_case.message,
                conversation_id=test_case.conversation_id,
            ):
                components.append(component)

        except Exception as e:
            error = str(e)

        return AgentResult(
            test_case_id=test_case.id,
            components=components,
            tool_calls=recorder.tool_calls,
            llm_requests=recorder.llm_requests,
            total_tokens=recorder.total_tokens,
            error=error,
        )
