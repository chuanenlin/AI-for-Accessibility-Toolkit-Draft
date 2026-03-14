"""AI for Accessibility Toolkit — AI agents that adapt the web to each user's abilities."""

from ai4a11y.agents.adapt import AdaptAgent
from ai4a11y.agents.app import AppAgent
from ai4a11y.agents.user import UserAgent
from ai4a11y.llm import LLMClient
from ai4a11y.models import Adaptation, AuditResult, Element, Issue, PageContext, Severity, TransformResult
from ai4a11y.tools.base import BaseTool, BaseTransform
from ai4a11y.orchestrator import Orchestrator, adapt, check
from ai4a11y.profiles import AbilityProfile, combine_profiles, get_profile

__all__ = [
    "AdaptAgent",
    "AppAgent",
    "UserAgent",
    "LLMClient",
    "Orchestrator",
    "adapt",
    "check",
    "BaseTool",
    "BaseTransform",
    "AbilityProfile",
    "combine_profiles",
    "get_profile",
    "Adaptation",
    "AuditResult",
    "Element",
    "Issue",
    "PageContext",
    "Severity",
    "TransformResult",
]
