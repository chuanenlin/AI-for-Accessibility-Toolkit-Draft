"""Plugin interface for accessibility tools.

This is the core abstraction that teams implement to add new
accessibility capabilities to the toolkit.

Two base classes:
- BaseTool: analyze pages for issues + suggest fixes
- BaseTransform: convert content across modalities (image → text, chart → audio)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai4a11y.models import Adaptation, Element, Issue, PageContext, TransformResult
from ai4a11y.profiles import AbilityProfile


class BaseTool(ABC):
    """Base class for accessibility tools.

    Implement `analyze()` to detect accessibility issues on a page.
    Optionally implement `adapt()` to suggest or apply fixes.

    Example:
        class AltTextTool(BaseTool):
            name = "alt-text"
            description = "Detect and generate missing alt text"
            ability_profiles = ["blv"]
            wcag_criteria = ["1.1.1"]

            def analyze(self, page):
                issues = []
                for el in page.elements:
                    if el.tag == "img" and not el.attributes.get("alt"):
                        issues.append(Issue(
                            rule_id="missing-alt-text",
                            description=f"Image missing alt text: {el.selector}",
                            severity=Severity.CRITICAL,
                            wcag_criteria=["1.1.1"],
                            selector=el.selector,
                        ))
                return issues
    """

    name: str = ""
    description: str = ""
    ability_profiles: list[str] = []
    wcag_criteria: list[str] = []

    @abstractmethod
    def analyze(self, page: PageContext) -> list[Issue]:
        """Find accessibility issues on a page.

        Args:
            page: Parsed page context with elements and HTML.

        Returns:
            List of accessibility issues found.
        """
        ...

    def adapt(
        self, page: PageContext, profile: AbilityProfile
    ) -> list[Adaptation]:
        """Suggest or apply accessibility fixes.

        Override this if your tool can fix the issues it finds.
        The default implementation returns no adaptations.

        Args:
            page: Parsed page context.
            profile: The user's ability profile.

        Returns:
            List of suggested adaptations.
        """
        return []

    def setup(self) -> None:
        """Called once when the tool is loaded. Override for initialization."""
        pass

    def teardown(self) -> None:
        """Called when the tool is unloaded. Override for cleanup."""
        pass

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"


class BaseTransform(ABC):
    """Base class for modality transforms.

    Transforms convert content from one modality to another:
    - image → alt text description
    - chart → sonification (audio)
    - text → plain language
    - video → captions

    Example:
        class ImageToAltText(BaseTransform):
            name = "image-to-alt-text"
            source_modality = "visual"
            target_modality = "text"

            def can_transform(self, element):
                return element.tag == "img"

            def transform(self, element, profile):
                desc = generate_description(element.attributes.get("src", ""))
                return TransformResult(content=desc, content_type="text/plain")
    """

    name: str = ""
    source_modality: str = ""  # "visual", "audio", "text", "data"
    target_modality: str = ""  # "visual", "audio", "text", "haptic"

    @abstractmethod
    def can_transform(self, element: Element) -> bool:
        """Whether this transform can handle the given element.

        Args:
            element: A UI element from the page.

        Returns:
            True if this transform applies to the element.
        """
        ...

    @abstractmethod
    def transform(self, element: Element, profile: AbilityProfile) -> TransformResult:
        """Transform the element's content to a different modality.

        Args:
            element: The element to transform.
            profile: The user's ability profile (affects output style).

        Returns:
            TransformResult with content, MIME type, and metadata.
        """
        ...

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.source_modality}→{self.target_modality}>"
