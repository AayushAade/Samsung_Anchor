"""
MEMORA Hierarchical Task Graph Architecture.

Decomposes high-level operational goals into directed acyclic task graphs (DAGs):
Supports:
- Node dependencies
- Serial vs Parallel execution paths
- Topological task ordering
- Dependency satisfaction checking
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from src.executive.executive_models import TaskNode, TaskStatus, TaskType


class TaskGraph:
    """
    Directed Acyclic Graph representing task decomposition for a Goal.
    """

    def __init__(self, parent_goal_id: str) -> None:
        self.parent_goal_id = parent_goal_id
        self._nodes: Dict[str, TaskNode] = {}

    def add_task(
        self,
        title: str,
        task_type: TaskType = TaskType.GENERAL_ACTION,
        dependencies: Optional[List[str]] = None,
        estimated_duration_sec: float = 30.0,
        action_payload: Optional[Dict] = None,
    ) -> TaskNode:
        """
        Add a task node to the graph.
        """
        node = TaskNode(
            title=title,
            task_type=task_type,
            dependencies=dependencies or [],
            parent_goal_id=self.parent_goal_id,
            estimated_duration_sec=estimated_duration_sec,
            action_payload=action_payload or {},
            status=TaskStatus.PENDING,
        )
        self._nodes[node.task_id] = node
        return node

    def is_task_executable(self, task_id: str) -> bool:
        """
        Check if all dependency tasks for the given task are COMPLETED.
        """
        if task_id not in self._nodes:
            return False
        node = self._nodes[task_id]
        if node.status != TaskStatus.PENDING:
            return False

        for dep_id in node.dependencies:
            dep = self._nodes.get(dep_id)
            if not dep or dep.status != TaskStatus.COMPLETED:
                return False
        return True

    def get_executable_tasks(self) -> List[TaskNode]:
        """
        Get all tasks currently ready for execution.
        """
        return [node for t_id, node in self._nodes.items() if self.is_task_executable(t_id)]

    def get_topological_order(self) -> List[TaskNode]:
        """
        Return tasks ordered topologically by dependency sequence.
        """
        ordered: List[TaskNode] = []
        visited: Set[str] = set()

        def visit(node_id: str):
            if node_id in visited or node_id not in self._nodes:
                return
            visited.add(node_id)
            node = self._nodes[node_id]
            for dep_id in node.dependencies:
                visit(dep_id)
            ordered.append(node)

        for n_id in self._nodes:
            visit(n_id)

        return ordered

    def get_all_tasks(self) -> List[TaskNode]:
        return list(self._nodes.values())
