"""Adapt Agent — decides how to adapt a page for a user.

Without LLM: runs every tool's adapt() and collects results.
With LLM: reasons about which adaptations matter most, resolves
conflicts when multiple tools target the same element, and
evaluates whether the adaptations actually help.
"""

from __future__ import annotations

import json

from ai4a11y.models import Adaptation, Element, Issue, PageContext, TransformResult
from ai4a11y.tools.base import BaseTool, BaseTransform
from ai4a11y.tools.registry import get_registry
from ai4a11y.profiles import AbilityProfile


class AdaptAgent:
    """Generates and prioritizes adaptations for a user's ability profile.

    Without LLM: collects all adaptations from tools (fast, deterministic).
    With LLM: prioritizes by impact, resolves conflicts, explains reasoning.

    Args:
        llm: Optional LLMClient for intelligent adaptation planning.
    """

    def __init__(self, llm=None):
        self.llm = llm

    def adapt_with_tools(
        self,
        page: PageContext,
        profile: AbilityProfile,
        tools: list[BaseTool],
        issues: list[Issue] | None = None,
    ) -> list[Adaptation]:
        """Run adapt() on each tool, then prioritize results.

        Args:
            page: The parsed page context.
            profile: The user's ability profile.
            tools: Tools to run adapt() on.
            issues: Issues found during analysis (used for LLM reasoning).
        """
        # Collect raw adaptations from all tools
        all_adaptations = []
        for tool in tools:
            all_adaptations.extend(tool.adapt(page, profile))

        if not all_adaptations:
            return all_adaptations

        # With LLM: prioritize and resolve conflicts
        if self.llm:
            return self._prioritize(all_adaptations, issues or [], profile, page)

        return all_adaptations

    def _prioritize(
        self,
        adaptations: list[Adaptation],
        issues: list[Issue],
        profile: AbilityProfile,
        page: PageContext,
    ) -> list[Adaptation]:
        """Use LLM to prioritize adaptations and resolve conflicts."""
        # Build adaptation descriptions for the prompt
        adaptation_info = []
        for i, a in enumerate(adaptations):
            adaptation_info.append({
                "index": i,
                "action": a.action,
                "element": a.element.selector,
                "element_tag": a.element.tag,
                "original": (a.original or "")[:100],
                "replacement": (a.replacement or "")[:100],
                "tool": a.tool_name,
            })

        issue_summary = []
        for issue in issues[:20]:
            issue_summary.append({
                "rule": issue.rule_id,
                "severity": issue.severity.value,
                "description": issue.description[:100],
            })

        result = self.llm.complete_json(
            system=(
                "You are an accessibility adaptation specialist. Given a set of "
                "suggested adaptations and the user's ability profile, decide which "
                "adaptations to keep, which to drop, and in what order to apply them.\n\n"
                "Consider:\n"
                "- Impact: which adaptations help this specific user most?\n"
                "- Conflicts: do any adaptations target the same element? Pick the best one.\n"
                "- Dependencies: should some adaptations happen before others?\n"
                "- Completeness: are there obvious gaps not addressed?"
            ),
            prompt=(
                f"User profile: {profile.name} — {profile.description}\n"
                f"User needs: {', '.join(profile.needs)}\n"
                f"Page: {page.url}\n\n"
                f"Issues found ({len(issues)} total):\n"
                + json.dumps(issue_summary, indent=2)
                + f"\n\nAdaptations suggested ({len(adaptations)} total):\n"
                + json.dumps(adaptation_info, indent=2)
                + "\n\nReturn JSON:\n"
                "{\n"
                '  "ordered_indices": [0, 2, 1, ...],\n'
                '  "dropped_indices": [3, ...],\n'
                '  "reasoning": "Why this ordering and which conflicts were resolved"\n'
                "}"
            ),
        )

        # Reorder adaptations based on LLM reasoning
        ordered = []
        dropped = set(result.get("dropped_indices", []))
        for idx in result.get("ordered_indices", range(len(adaptations))):
            if idx not in dropped and 0 <= idx < len(adaptations):
                ordered.append(adaptations[idx])

        # Include any that weren't mentioned (don't silently drop)
        mentioned = set(result.get("ordered_indices", [])) | dropped
        for i, a in enumerate(adaptations):
            if i not in mentioned:
                ordered.append(a)

        return ordered

    def find_transforms(
        self, element: Element, profile: AbilityProfile
    ) -> list[BaseTransform]:
        """Find transforms applicable to an element for a given profile."""
        registry = get_registry()
        applicable = []
        for transform in registry.transforms.values():
            if transform.target_modality in profile.preferred_modalities:
                if transform.can_transform(element):
                    applicable.append(transform)
        return applicable

    def transform(
        self, element: Element, profile: AbilityProfile
    ) -> list[tuple[BaseTransform, TransformResult]]:
        """Apply all applicable modality transforms to an element.

        Returns:
            List of (transform, result) tuples.
        """
        results = []
        for transform in self.find_transforms(element, profile):
            result = transform.transform(element, profile)
            results.append((transform, result))
        return results

    def __repr__(self) -> str:
        llm_info = f" llm={self.llm.provider}" if self.llm else ""
        return f"<AdaptAgent{llm_info}>"
