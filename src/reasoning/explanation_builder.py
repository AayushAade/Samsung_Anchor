"""
MEMORA Explanation Builder & Reasoning Graph Constructor.

Generates an explainable reasoning graph trace mapping high-level conclusions:
Conclusion -> Hypotheses -> Supporting Evidence -> Subsystem Sources -> Raw Observations

Ensures every automated decision and cognitive state conclusion is transparent and auditable.
"""

from __future__ import annotations

import uuid
from typing import List, Tuple

from src.reasoning.reasoning_models import (
    CognitiveStateMode,
    Hypothesis,
    Observation,
    ReasoningGraphNode,
    ReasoningNodeType,
)


class ExplanationBuilder:
    """
    Constructs explainable reasoning graph trees and human-readable narratives.
    """

    @classmethod
    def build_reasoning_graph(
        cls,
        estimated_state: CognitiveStateMode,
        top_hypothesis: Hypothesis,
        supporting_observations: List[Observation],
    ) -> Tuple[List[ReasoningGraphNode], str]:
        """
        Build causal graph nodes and textual narrative summary.
        """
        nodes: List[ReasoningGraphNode] = []

        # 1. Root Node: Conclusion
        c_node = ReasoningGraphNode(
            node_type=ReasoningNodeType.CONCLUSION,
            label=f"State Conclusion: {estimated_state.value}",
            confidence=top_hypothesis.confidence,
        )
        nodes.append(c_node)

        # 2. Hypothesis Node
        h_node = ReasoningGraphNode(
            node_type=ReasoningNodeType.HYPOTHESIS,
            label=top_hypothesis.title,
            confidence=top_hypothesis.confidence,
            parent_ids=[c_node.node_id],
        )
        c_node.child_ids.append(h_node.node_id)
        nodes.append(h_node)

        # 3. Supporting Evidence & Observation Nodes
        narrative_parts = [
            f"Conclusion: '{estimated_state.value}' (Confidence: {top_hypothesis.confidence:.0%}).",
            f"Primary Hypothesis: '{top_hypothesis.title}'.",
        ]

        if supporting_observations:
            narrative_parts.append("Supporting Evidence:")

        for obs in supporting_observations[:4]:
            o_node = ReasoningGraphNode(
                node_type=ReasoningNodeType.OBSERVATION,
                label=f"Source [{obs.source}]: Category {obs.category.value}",
                confidence=obs.confidence,
                parent_ids=[h_node.node_id],
            )
            h_node.child_ids.append(o_node.node_id)
            nodes.append(o_node)
            narrative_parts.append(
                f"  - [{obs.source}] {obs.category.value} (Confidence: {obs.confidence:.0%})"
            )

        narrative = "\n".join(narrative_parts)
        return nodes, narrative
