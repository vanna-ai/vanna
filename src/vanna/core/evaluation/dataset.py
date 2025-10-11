"""
Dataset loaders for evaluation test cases.

This module provides utilities for loading test case datasets from
YAML and JSON files.
"""

import json
import yaml
from typing import List
from pathlib import Path

from .base import TestCase, ExpectedOutcome
from vanna.core import User


class EvaluationDataset:
    """Collection of test cases with metadata.

    Example YAML format:
        dataset:
          name: "SQL Generation Tasks"
          description: "Test cases for SQL generation"
          test_cases:
            - id: "sql_001"
              user_id: "test_user"
              message: "Show me total sales by region"
              expected_outcome:
                tools_called: ["generate_sql", "execute_query"]
                final_answer_contains: ["SELECT", "GROUP BY", "region"]
    """

    def __init__(self, name: str, test_cases: List[TestCase], description: str = ""):
        """Initialize evaluation dataset.

        Args:
            name: Name of the dataset
            test_cases: List of test cases
            description: Optional description
        """
        self.name = name
        self.test_cases = test_cases
        self.description = description

    @classmethod
    def from_yaml(cls, path: str) -> "EvaluationDataset":
        """Load dataset from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            EvaluationDataset instance
        """
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        return cls._from_dict(data)

    @classmethod
    def from_json(cls, path: str) -> "EvaluationDataset":
        """Load dataset from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            EvaluationDataset instance
        """
        with open(path, 'r') as f:
            data = json.load(f)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> "EvaluationDataset":
        """Create dataset from dictionary.

        Args:
            data: Dictionary with dataset structure

        Returns:
            EvaluationDataset instance
        """
        dataset_config = data.get('dataset', data)
        name = dataset_config.get('name', 'Unnamed Dataset')
        description = dataset_config.get('description', '')

        test_cases = []
        for tc_data in dataset_config.get('test_cases', []):
            test_case = cls._parse_test_case(tc_data)
            test_cases.append(test_case)

        return cls(name=name, test_cases=test_cases, description=description)

    @classmethod
    def _parse_test_case(cls, data: dict) -> TestCase:
        """Parse a single test case from dictionary.

        Args:
            data: Test case dictionary

        Returns:
            TestCase instance
        """
        # Create user
        user_id = data.get('user_id', 'test_user')
        user = User(
            id=user_id,
            username=data.get('username', user_id),
            email=data.get('email', f'{user_id}@example.com'),
            permissions=data.get('permissions', []),
        )

        # Parse expected outcome if present
        expected_outcome = None
        if 'expected_outcome' in data:
            outcome_data = data['expected_outcome']
            expected_outcome = ExpectedOutcome(
                tools_called=outcome_data.get('tools_called'),
                tools_not_called=outcome_data.get('tools_not_called'),
                final_answer_contains=outcome_data.get('final_answer_contains'),
                final_answer_not_contains=outcome_data.get('final_answer_not_contains'),
                min_components=outcome_data.get('min_components'),
                max_components=outcome_data.get('max_components'),
                max_execution_time_ms=outcome_data.get('max_execution_time_ms'),
                metadata=outcome_data.get('metadata', {}),
            )

        return TestCase(
            id=data['id'],
            user=user,
            message=data['message'],
            conversation_id=data.get('conversation_id'),
            expected_outcome=expected_outcome,
            metadata=data.get('metadata', {}),
        )

    def save_yaml(self, path: str) -> None:
        """Save dataset to YAML file.

        Args:
            path: Path to save YAML file
        """
        data = self._to_dict()
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def save_json(self, path: str) -> None:
        """Save dataset to JSON file.

        Args:
            path: Path to save JSON file
        """
        data = self._to_dict()
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _to_dict(self) -> dict:
        """Convert dataset to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'dataset': {
                'name': self.name,
                'description': self.description,
                'test_cases': [
                    self._test_case_to_dict(tc) for tc in self.test_cases
                ]
            }
        }

    def _test_case_to_dict(self, test_case: TestCase) -> dict:
        """Convert test case to dictionary.

        Args:
            test_case: TestCase to convert

        Returns:
            Dictionary representation
        """
        data = {
            'id': test_case.id,
            'user_id': test_case.user.id,
            'username': test_case.user.username,
            'email': test_case.user.email,
            'message': test_case.message,
        }

        if test_case.conversation_id:
            data['conversation_id'] = test_case.conversation_id

        if test_case.expected_outcome:
            outcome = test_case.expected_outcome
            outcome_dict = {}

            if outcome.tools_called:
                outcome_dict['tools_called'] = outcome.tools_called
            if outcome.tools_not_called:
                outcome_dict['tools_not_called'] = outcome.tools_not_called
            if outcome.final_answer_contains:
                outcome_dict['final_answer_contains'] = outcome.final_answer_contains
            if outcome.final_answer_not_contains:
                outcome_dict['final_answer_not_contains'] = outcome.final_answer_not_contains
            if outcome.min_components is not None:
                outcome_dict['min_components'] = outcome.min_components
            if outcome.max_components is not None:
                outcome_dict['max_components'] = outcome.max_components
            if outcome.max_execution_time_ms is not None:
                outcome_dict['max_execution_time_ms'] = outcome.max_execution_time_ms
            if outcome.metadata:
                outcome_dict['metadata'] = outcome.metadata

            if outcome_dict:
                data['expected_outcome'] = outcome_dict

        if test_case.metadata:
            data['metadata'] = test_case.metadata

        return data

    def filter_by_metadata(self, **kwargs) -> "EvaluationDataset":
        """Filter test cases by metadata fields.

        Args:
            **kwargs: Metadata fields to match

        Returns:
            New EvaluationDataset with filtered test cases
        """
        filtered = [
            tc for tc in self.test_cases
            if all(tc.metadata.get(k) == v for k, v in kwargs.items())
        ]

        return EvaluationDataset(
            name=f"{self.name} (filtered)",
            test_cases=filtered,
            description=f"Filtered from: {self.description}",
        )

    def __len__(self) -> int:
        """Get number of test cases."""
        return len(self.test_cases)

    def __repr__(self) -> str:
        """String representation."""
        return f"EvaluationDataset(name='{self.name}', test_cases={len(self.test_cases)})"
