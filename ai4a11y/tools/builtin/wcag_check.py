"""Built-in WCAG check tool using axe-core.

Injects axe-core into a Playwright page to detect WCAG 2.2 violations.
No Node.js dependency — axe-core runs directly in the browser.
"""

from __future__ import annotations

from ai4a11y.models import Adaptation, Issue, PageContext, Severity
from ai4a11y.tools.base import BaseTool
from ai4a11y.profiles import AbilityProfile

AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"

SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "serious": Severity.SERIOUS,
    "moderate": Severity.MODERATE,
    "minor": Severity.MINOR,
}


class WCAGCheckTool(BaseTool):
    """WCAG 2.2 violation detection using axe-core."""

    name = "wcag-check"
    description = "Detect WCAG 2.2 accessibility violations using axe-core"
    ability_profiles = ["blv", "dhh", "motor", "cognitive", "speech", "aging"]
    wcag_criteria = []  # axe-core covers all criteria

    def analyze(self, page: PageContext) -> list[Issue]:
        """Run axe-core on a page and return violations as Issues.

        If page has a ``_browser_page`` attribute (set by the Orchestrator),
        reuses that browser session. Otherwise launches its own browser.
        """
        browser_page = getattr(page, "_browser_page", None)

        if browser_page:
            return self._run_axe(browser_page)

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                bp = browser.new_page()
                bp.goto(page.url, wait_until="domcontentloaded")
                issues = self._run_axe(bp)
            finally:
                browser.close()

        return issues

    def _run_axe(self, browser_page) -> list[Issue]:
        """Inject axe-core and parse violations."""
        browser_page.add_script_tag(url=AXE_CDN)
        browser_page.wait_for_function("typeof axe !== 'undefined'")
        results = browser_page.evaluate("axe.run()")

        issues = []
        for violation in results.get("violations", []):
            severity = SEVERITY_MAP.get(
                violation.get("impact", "minor"), Severity.MINOR
            )
            wcag_tags = [
                t for t in violation.get("tags", [])
                if t.startswith("wcag")
            ]
            for node in violation.get("nodes", []):
                issues.append(Issue(
                    rule_id=violation["id"],
                    description=violation.get("description", ""),
                    severity=severity,
                    wcag_criteria=wcag_tags,
                    selector=", ".join(node.get("target", [])),
                    html=node.get("html", ""),
                    help_url=violation.get("helpUrl", ""),
                    tool_name=self.name,
                ))
        return issues

    def adapt(
        self, page: PageContext, profile: AbilityProfile
    ) -> list[Adaptation]:
        """axe-core detects but doesn't fix — return empty.

        Fix generation is handled by other tools (e.g., alt-text, caption).
        """
        return []
