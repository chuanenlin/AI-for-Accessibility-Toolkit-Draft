"""Core data models for the AI for Accessibility Toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


@dataclass
class Element:
    """A UI element on a page."""

    tag: str
    selector: str
    attributes: dict = field(default_factory=dict)
    text: str = ""
    html: str = ""


@dataclass
class Issue:
    """An accessibility issue found on a page."""

    rule_id: str
    description: str
    severity: Severity
    wcag_criteria: list[str] = field(default_factory=list)
    selector: str = ""
    html: str = ""
    help_url: str = ""
    tool_name: str = ""


@dataclass
class Adaptation:
    """A suggested or applied accessibility fix."""

    element: Element
    action: str  # "add_alt_text", "simplify_text", "add_caption", etc.
    original: str = ""
    replacement: str = ""
    tool_name: str = ""


@dataclass
class PageContext:
    """Parsed representation of a web page."""

    url: str
    title: str = ""
    html: str = ""
    elements: list[Element] = field(default_factory=list)
    analysis: dict = field(default_factory=dict)  # LLM semantic analysis
    _browser_page: Any = field(default=None, repr=False)


@dataclass
class TransformResult:
    """Output of a modality transform.

    Wraps the transformed content with its MIME type and metadata,
    so transforms can return text, audio bytes, structured data, etc.
    """

    content: str | bytes
    content_type: str = "text/plain"  # MIME type
    metadata: dict = field(default_factory=dict)


@dataclass
class AuditResult:
    """Result of running an accessibility audit."""

    url: str
    page: PageContext
    issues: list[Issue] = field(default_factory=list)
    adaptations: list[Adaptation] = field(default_factory=list)
    tools_run: list[str] = field(default_factory=list)
    plan: dict = field(default_factory=dict)  # LLM orchestrator plan and reasoning

    @property
    def critical(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.CRITICAL]

    @property
    def serious(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.SERIOUS]

    @property
    def moderate(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.MODERATE]

    @property
    def minor(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.MINOR]
