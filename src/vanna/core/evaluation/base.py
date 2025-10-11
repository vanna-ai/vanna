"""
Core evaluation abstractions for the Vanna Agents framework.

This module provides the base classes and models for evaluating agent behavior,
including test cases, expected outcomes, and evaluation results.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel

from vanna.core import User, UiComponent


class ExpectedOutcome(BaseModel):
    """Defines what we expect from the agent for a test case.

    Provides multiple ways to specify expectations:
    - tools_called: List of tool names that should be called
    - tools_not_called: List of tool names that should NOT be called
    - final_answer_contains: Keywords/phrases that should appear in output
    - final_answer_not_contains: Keywords/phrases that should NOT appear
    - min_components: Minimum number of UI components expected
    - max_execution_time_ms: Maximum allowed execution time
    - custom_validators: Custom validation functions
    """

    tools_called: Optional[List[str]] = None
    tools_not_called: Optional[List[str]] = None
    final_answer_contains: Optional[List[str]] = None
    final_answer_not_contains: Optional[List[str]] = None
    min_components: Optional[int] = None
    max_components: Optional[int] = None
    max_execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = {}


class TestCase(BaseModel):
    """A single evaluation test case.

    Attributes:
        id: Unique identifier for the test case
        user: User context for the test
        message: The message to send to the agent
        conversation_id: Optional conversation ID for multi-turn tests
        expected_outcome: What we expect the agent to do/produce
        metadata: Additional metadata for categorization/filtering
    """

    id: str
    user: User
    message: str
    conversation_id: Optional[str] = None
    expected_outcome: Optional[ExpectedOutcome] = None
    metadata: Dict[str, Any] = {}


@dataclass
class AgentResult:
    """The result of running an agent on a test case.

    Captures everything that happened during agent execution
    for later evaluation.
    """

    test_case_id: str
    components: List[UiComponent]
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    llm_requests: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    total_tokens: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_final_answer(self) -> str:
        """Extract the final answer from components."""
        # Find text components and concatenate
        texts = []
        for component in self.components:
            if hasattr(component, 'rich_component'):
                rich_comp = component.rich_component
                if hasattr(rich_comp, 'type') and rich_comp.type.value == 'text':
                    content = rich_comp.data.get('content') or getattr(rich_comp, 'content', '')
                    if content:
                        texts.append(content)
        return '\n'.join(texts)

    def get_tool_names_called(self) -> List[str]:
        """Get list of tool names that were called."""
        return [call.get('tool_name', '') for call in self.tool_calls]


class EvaluationResult(BaseModel):
    """Result of evaluating a single test case.

    Attributes:
        test_case_id: ID of the test case evaluated
        evaluator_name: Name of the evaluator that produced this result
        passed: Whether the test case passed
        score: Score from 0.0 to 1.0
        reasoning: Explanation of the evaluation
        metrics: Additional metrics captured during evaluation
        timestamp: When the evaluation was performed
    """

    test_case_id: str
    evaluator_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    reasoning: str
    metrics: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()


@dataclass
class TestCaseResult:
    """Complete result for a single test case including all evaluations."""

    test_case: TestCase
    agent_result: AgentResult
    evaluations: List[EvaluationResult]
    execution_time_ms: float

    def overall_passed(self) -> bool:
        """Check if all evaluations passed."""
        return all(e.passed for e in self.evaluations)

    def overall_score(self) -> float:
        """Calculate average score across all evaluations."""
        if not self.evaluations:
            return 0.0
        return sum(e.score for e in self.evaluations) / len(self.evaluations)


@dataclass
class AgentVariant:
    """A variant of an agent to evaluate (different LLM, config, etc).

    Used for comparing different agent configurations, especially
    different LLMs or model versions.

    Attributes:
        name: Human-readable name for this variant
        agent: The agent instance to evaluate
        metadata: Additional info (model name, provider, config, etc)
    """

    name: str
    agent: Any  # Agent type - avoiding circular import
    metadata: Dict[str, Any] = field(default_factory=dict)


class Evaluator(ABC):
    """Base class for evaluating agent behavior.

    Evaluators examine the agent's execution and determine if it
    met expectations. Multiple evaluators can be composed to check
    different aspects (trajectory, output quality, efficiency, etc).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this evaluator."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        test_case: TestCase,
        agent_result: AgentResult,
    ) -> EvaluationResult:
        """Evaluate a single test case execution.

        Args:
            test_case: The test case that was executed
            agent_result: The result from running the agent

        Returns:
            EvaluationResult with pass/fail, score, and reasoning
        """
        pass
