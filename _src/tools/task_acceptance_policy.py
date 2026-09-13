#!/usr/bin/env python3
"""Machine-enforced Task/Feature acceptance policy algorithms and batch expansion.

Usage:
    from task_acceptance_policy import expand_batch, validate_feature_acceptance
"""
from typing import Dict, List, Set, Any, Optional


def expand_batch(tasks: Dict[str, Dict[str, Any]], assigned: List[str], accepted: List[str]) -> List[str]:
    """Expand induced prerequisite-closed batch for integration checkpoints.

    Args:
        tasks: Dictionary mapping task_id to task attributes (e.g. {'prereq': [...], 'checkpoint': bool}).
        assigned: List of assigned target task IDs.
        accepted: List of already accepted task IDs.

    Returns:
        Deterministically ordered list of task IDs in topological order (leaves to targets)
        that must be included in the review batch.

    Raises:
        ValueError: On missing endpoints, unassigned predecessor checkpoints, or dependency cycles.
    """
    assigned_set = set(assigned)
    accepted_set = set(accepted)
    included = set()
    visiting = set()
    visited = set()

    def visit(task_id: str):
        if task_id not in tasks:
            raise ValueError(f"missing endpoint {task_id}")
        if task_id in accepted_set:
            return
        if task_id in visiting:
            raise ValueError("cycle")
        if task_id in visited:
            return
        if tasks[task_id].get("checkpoint") and task_id not in assigned_set:
            raise ValueError(f"unassigned checkpoint {task_id}")
        visiting.add(task_id)
        for prereq in sorted(tasks[task_id].get("prereq", [])):
            visit(prereq)
        visiting.remove(task_id)
        visited.add(task_id)
        included.add(task_id)

    for task_id in sorted(assigned_set):
        visit(task_id)

    indegree = {task_id: 0 for task_id in included}
    successors = {task_id: [] for task_id in included}
    for task_id in included:
        for prereq in tasks[task_id].get("prereq", []):
            if prereq in included:
                indegree[task_id] += 1
                successors[prereq].append(task_id)
    ready = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    ordered = []
    while ready:
        task_id = ready.pop(0)
        ordered.append(task_id)
        for successor in sorted(successors[task_id]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
                ready.sort()
    if len(ordered) != len(included):
        raise ValueError("cycle")
    return ordered


def validate_feature_acceptance(feature_tasks: Dict[str, Dict[str, Any]], terminal_integrating_task: str) -> bool:
    """Verify that a Feature has full graph coverage to its terminal integrating task."""
    if terminal_integrating_task not in feature_tasks:
        return False
    visited = set()
    def visit(task_id: str):
        if task_id in visited:
            return
        visited.add(task_id)
        for prereq in feature_tasks.get(task_id, {}).get("prereq", []):
            if prereq in feature_tasks:
                visit(prereq)
    visit(terminal_integrating_task)
    return visited == set(feature_tasks.keys())
