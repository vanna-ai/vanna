"""
Built-in evaluators for common evaluation tasks.

This module provides ready-to-use evaluators for:
- Trajectory evaluation (tools called, order, efficiency)
- Output evaluation (content matching, quality)
- LLM-as-judge evaluation (custom criteria)
- Efficiency evaluation (time, tokens, cost)
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import Evaluator, TestCase, AgentResult, EvaluationResult
from vanna.core import LlmService


class TrajectoryEvaluator(Evaluator):
    """Evaluate the path the agent took (tools called, order, etc).

    Checks if the agent called the expected tools and didn't call
    unexpected ones. Useful for verifying agent reasoning and planning.
    """

    @property
    def name(self) -> str:
        return "trajectory"

    async def evaluate(
        self, test_case: TestCase, agent_result: AgentResult
    ) -> EvaluationResult:
        """Evaluate tool call trajectory."""
        if agent_result.error:
            return EvaluationResult(
                test_case_id=test_case.id,
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reasoning=f"Agent execution failed: {agent_result.error}",
            )

        expected = test_case.expected_outcome
        if not expected:
            return EvaluationResult(
                test_case_id=test_case.id,
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reasoning="No expected outcome specified, passing by default",
            )

        tools_called = agent_result.get_tool_names_called()
        issues = []
        score = 1.0

        # Check expected tools were called
        if expected.tools_called:
            for expected_tool in expected.tools_called:
                if expected_tool not in tools_called:
                    issues.append(f"Expected tool '{expected_tool}' was not called")
                    score -= 0.5 / len(expected.tools_called)

        # Check unexpected tools were not called
        if expected.tools_not_called:
            for unexpected_tool in expected.tools_not_called:
                if unexpected_tool in tools_called:
                    issues.append(f"Unexpected tool '{unexpected_tool}' was called")
                    score -= 0.5 / len(expected.tools_not_called)

        score = max(0.0, min(1.0, score))
        passed = score >= 0.7  # 70% threshold

        reasoning = "Trajectory evaluation: "
        if issues:
            reasoning += "; ".join(issues)
        else:
            reasoning += "All expected tools called, no unexpected tools"

        return EvaluationResult(
            test_case_id=test_case.id,
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reasoning=reasoning,
            metrics={
                "tools_called": tools_called,
                "num_tools_called": len(tools_called),
                "issues": issues,
            },
        )


class OutputEvaluator(Evaluator):
    """Evaluate the final output quality.

    Checks if the output contains expected content and doesn't
    contain forbidden content. Case-insensitive substring matching.
    """

    @property
    def name(self) -> str:
        return "output"

    async def evaluate(
        self, test_case: TestCase, agent_result: AgentResult
    ) -> EvaluationResult:
        """Evaluate output content."""
        if agent_result.error:
            return EvaluationResult(
                test_case_id=test_case.id,
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reasoning=f"Agent execution failed: {agent_result.error}",
            )

        expected = test_case.expected_outcome
        if not expected:
            return EvaluationResult(
                test_case_id=test_case.id,
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reasoning="No expected outcome specified, passing by default",
            )

        final_answer = agent_result.get_final_answer().lower()
        issues = []
        score = 1.0

        # Check expected content is present
        if expected.final_answer_contains:
            for expected_content in expected.final_answer_contains:
                if expected_content.lower() not in final_answer:
                    issues.append(f"Expected content '{expected_content}' not found in output")
                    score -= 0.5 / len(expected.final_answer_contains)

        # Check forbidden content is absent
        if expected.final_answer_not_contains:
            for forbidden_content in expected.final_answer_not_contains:
                if forbidden_content.lower() in final_answer:
                    issues.append(f"Forbidden content '{forbidden_content}' found in output")
                    score -= 0.5 / len(expected.final_answer_not_contains)

        score = max(0.0, min(1.0, score))
        passed = score >= 0.7  # 70% threshold

        reasoning = "Output evaluation: "
        if issues:
            reasoning += "; ".join(issues)
        else:
            reasoning += "All expected content present, no forbidden content"

        return EvaluationResult(
            test_case_id=test_case.id,
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reasoning=reasoning,
            metrics={
                "output_length": len(final_answer),
                "issues": issues,
            },
        )


class LLMAsJudgeEvaluator(Evaluator):
    """Use an LLM to judge agent performance based on custom criteria.

    This evaluator uses a separate LLM to assess the quality of the
    agent's output based on natural language criteria.
    """

    def __init__(self, judge_llm: LlmService, criteria: str):
        """Initialize LLM-as-judge evaluator.

        Args:
            judge_llm: The LLM service to use for judging
            criteria: Natural language description of what to evaluate
        """
        self.judge_llm = judge_llm
        self.criteria = criteria

    @property
    def name(self) -> str:
        return "llm_judge"

    async def evaluate(
        self, test_case: TestCase, agent_result: AgentResult
    ) -> EvaluationResult:
        """Evaluate using LLM as judge."""
        if agent_result.error:
            return EvaluationResult(
                test_case_id=test_case.id,
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reasoning=f"Agent execution failed: {agent_result.error}",
            )

        final_answer = agent_result.get_final_answer()

        # Build prompt for judge
        judge_prompt = f"""You are evaluating an AI agent's response to a user query.

User Query: {test_case.message}

Agent's Response:
{final_answer}

Evaluation Criteria:
{self.criteria}

Please evaluate the response and provide:
1. A score from 0.0 to 1.0 (where 1.0 is perfect)
2. Whether it passes (score >= 0.7)
3. Brief reasoning for your evaluation

Respond in this format:
SCORE: <number>
PASSED: <yes/no>
REASONING: <your explanation>
"""

        try:
            # Call judge LLM
            from vanna.core.llm import LlmRequest, LlmMessage

            request = LlmRequest(
                user_id=test_case.user.id,
                messages=[LlmMessage(role="user", content=judge_prompt)],
                temperature=0.0,  # Deterministic judging
            )

            response = await self.judge_llm.send_message(request)
            judgment = response.content

            # Parse response
            score = self._parse_score(judgment)
            passed = self._parse_passed(judgment)
            reasoning = self._parse_reasoning(judgment)

            return EvaluationResult(
                test_case_id=test_case.id,
                evaluator_name=self.name,
                passed=passed,
                score=score,
                reasoning=reasoning,
                metrics={"judge_response": judgment},
            )

        except Exception as e:
            return EvaluationResult(
                test_case_id=test_case.id,
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reasoning=f"LLM judge evaluation failed: {str(e)}",
            )

    def _parse_score(self, judgment: str) -> float:
        """Parse score from judge response."""
        try:
            for line in judgment.split('\n'):
                if line.startswith('SCORE:'):
                    score_str = line.replace('SCORE:', '').strip()
                    return float(score_str)
        except:
            pass
        return 0.5  # Default if parsing fails

    def _parse_passed(self, judgment: str) -> bool:
        """Parse pass/fail from judge response."""
        for line in judgment.split('\n'):
            if line.startswith('PASSED:'):
                passed_str = line.replace('PASSED:', '').strip().lower()
                return passed_str in ['yes', 'true', 'pass']
        return False

    def _parse_reasoning(self, judgment: str) -> str:
        """Parse reasoning from judge response."""
        for line in judgment.split('\n'):
            if line.startswith('REASONING:'):
                return line.replace('REASONING:', '').strip()
        return judgment  # Return full judgment if no reasoning line found


class EfficiencyEvaluator(Evaluator):
    """Evaluate resource usage (time, tokens, cost).

    Checks if the agent completed within acceptable resource limits.
    """

    def __init__(
        self,
        max_execution_time_ms: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
    ):
        """Initialize efficiency evaluator.

        Args:
            max_execution_time_ms: Maximum allowed execution time in milliseconds
            max_tokens: Maximum allowed token usage
            max_cost_usd: Maximum allowed cost in USD
        """
        self.max_execution_time_ms = max_execution_time_ms
        self.max_tokens = max_tokens
        self.max_cost_usd = max_cost_usd

    @property
    def name(self) -> str:
        return "efficiency"

    async def evaluate(
        self, test_case: TestCase, agent_result: AgentResult
    ) -> EvaluationResult:
        """Evaluate resource efficiency."""
        issues = []
        score = 1.0

        # Check execution time
        if self.max_execution_time_ms:
            if agent_result.execution_time_ms > self.max_execution_time_ms:
                issues.append(
                    f"Execution time {agent_result.execution_time_ms:.0f}ms "
                    f"exceeded limit {self.max_execution_time_ms:.0f}ms"
                )
                score -= 0.33

        # Check token usage
        if self.max_tokens:
            if agent_result.total_tokens > self.max_tokens:
                issues.append(
                    f"Token usage {agent_result.total_tokens} exceeded limit {self.max_tokens}"
                )
                score -= 0.33

        # Check cost (would need cost calculation from metadata)
        # For now, skip cost evaluation

        # Check from expected outcome if specified
        expected = test_case.expected_outcome
        if expected and expected.max_execution_time_ms:
            if agent_result.execution_time_ms > expected.max_execution_time_ms:
                issues.append(
                    f"Execution time {agent_result.execution_time_ms:.0f}ms "
                    f"exceeded test case limit {expected.max_execution_time_ms:.0f}ms"
                )
                score -= 0.34

        score = max(0.0, min(1.0, score))
        passed = score >= 0.7

        reasoning = "Efficiency evaluation: "
        if issues:
            reasoning += "; ".join(issues)
        else:
            reasoning += "Within resource limits"

        return EvaluationResult(
            test_case_id=test_case.id,
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reasoning=reasoning,
            metrics={
                "execution_time_ms": agent_result.execution_time_ms,
                "total_tokens": agent_result.total_tokens,
                "issues": issues,
            },
        )
