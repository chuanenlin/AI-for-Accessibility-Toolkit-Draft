"""Tests for the built-in WCAG check tool."""

import pytest

from ai4a11y.models import Issue, PageContext
from ai4a11y.tools.builtin.wcag_check import WCAGCheckTool
from ai4a11y.testing.standard import FIXTURE_HTML, StandardToolTests

pytestmark = pytest.mark.network  # requires CDN access for axe-core


class TestWCAGCheck(StandardToolTests):
    """Standard tool tests for WCAGCheckTool.

    Overrides analyze tests to use a local HTML page via Playwright,
    since WCAGCheckTool needs a real browser to inject axe-core.
    """

    tool_class = WCAGCheckTool

    def _analyze_with_browser(self):
        """Run analyze with a real Playwright browser on local HTML."""
        from playwright.sync_api import sync_playwright

        tool = self._make_tool()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            bp = browser.new_page()
            bp.set_content(FIXTURE_HTML)

            page = PageContext(url=bp.url, html=FIXTURE_HTML)
            page._browser_page = bp
            issues = tool.analyze(page)

            browser.close()
        return issues

    def test_analyze_returns_list_of_issues(self):
        issues = self._analyze_with_browser()
        assert isinstance(issues, list)
        for item in issues:
            assert isinstance(item, Issue)

    def test_issues_have_required_fields(self):
        issues = self._analyze_with_browser()
        for issue in issues:
            assert issue.rule_id
            assert issue.description
            assert issue.severity
