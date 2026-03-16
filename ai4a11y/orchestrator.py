"""Orchestrator — coordinates agents and tools.

Uses an LLM to analyze the page, plan which tools to activate,
and reason about the best adaptation strategy for each user.
"""

from __future__ import annotations

import json
import logging

from ai4a11y.agents.adapt import AdaptAgent
from ai4a11y.agents.app import AppAgent
from ai4a11y.agents.user import UserAgent
from ai4a11y.llm import LLMClient
from ai4a11y.models import Adaptation, AuditResult, PageContext
from ai4a11y.tools.builtin.wcag_check import WCAGCheckTool
from ai4a11y.tools.registry import get_registry

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates agents and tools to produce accessibility adaptations.

    Uses an LLM to analyze the page and plan which tools to run.
    Falls back to rule-based filtering if the LLM call fails.

    Args:
        agents: List of agents (UserAgent, AppAgent, AdaptAgent).
        llm: LLMClient instance. Defaults to Gemini if not provided.
    """

    def __init__(self, agents: list | None = None, llm: LLMClient | None = None):
        self.user_agent: UserAgent | None = None
        self.app_agent: AppAgent | None = None
        self.adapt_agent: AdaptAgent | None = None
        self.llm = llm or LLMClient()

        for agent in agents or []:
            if isinstance(agent, UserAgent):
                self.user_agent = agent
            elif isinstance(agent, AppAgent):
                self.app_agent = agent
            elif isinstance(agent, AdaptAgent):
                self.adapt_agent = agent

    def run(self) -> AuditResult:
        """Run the full pipeline: understand → plan → analyze → adapt.

        Uses a single shared Playwright browser session for all tools.

        Returns:
            AuditResult with issues, adaptations, and plan.
        """
        if not self.app_agent:
            raise ValueError("AppAgent is required — pass AppAgent(url=...) to Orchestrator")

        from playwright.sync_api import sync_playwright

        plan = {}
        page = None
        all_issues = []
        all_adaptations = []
        tools_run = []

        registry = get_registry()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    browser_page = browser.new_page()
                    browser_page.goto(self.app_agent.url, wait_until="domcontentloaded")

                    # 1. Understand the page (AppAgent parses + LLM analysis)
                    page = self.app_agent.parse(browser_page=browser_page)
                    page._browser_page = browser_page

                    # 2. Discover available tools
                    wcag = WCAGCheckTool()

                    registry.discover()
                    profile = self.user_agent.profile if self.user_agent else None

                    # Collect all available tools (excluding built-in wcag which always runs)
                    available_tools = [
                        t for t in registry.tools.values() if t.name != wcag.name
                    ]

                    # 3. Plan — LLM decides which tools to run
                    if profile and available_tools:
                        try:
                            plan = self._plan(page, profile, available_tools)
                            selected_names = set(plan.get("tools_to_run", []))
                            tools_to_run = [
                                t for t in available_tools
                                if t.name in selected_names
                                or (not t.ability_profiles and t.name not in selected_names)
                            ]
                        except Exception as e:
                            logger.warning("LLM planning failed, falling back to rule-based: %s", e)
                            tools_to_run = self._filter_by_profile(available_tools, profile)
                    else:
                        tools_to_run = self._filter_by_profile(available_tools, profile)

                    # 4. Run built-in WCAG check (always)
                    issues = wcag.analyze(page)
                    all_issues.extend(issues)
                    tools_run.append(wcag.name)

                    # 5. Run selected tools
                    active_tools = []
                    for tool in tools_to_run:
                        issues = tool.analyze(page)
                        all_issues.extend(issues)
                        tools_run.append(tool.name)
                        active_tools.append(tool)

                    # 6. Generate adaptations via AdaptAgent
                    if profile:
                        adapt_agent = self.adapt_agent or AdaptAgent(llm=self.llm)
                        try:
                            adaptations = adapt_agent.adapt_with_tools(
                                page, profile, active_tools, issues=all_issues,
                            )
                        except Exception as e:
                            logger.warning("Adaptation failed, continuing with empty adaptations: %s", e)
                            adaptations = []
                        all_adaptations.extend(adaptations)

                        # 7. Run modality transforms on page elements
                        for element in page.elements:
                            for transform, result in adapt_agent.transform(element, profile):
                                all_adaptations.append(Adaptation(
                                    element=element,
                                    action=f"transform:{transform.name}",
                                    original=transform.source_modality,
                                    replacement=result.content if isinstance(result.content, str) else f"[{result.content_type}]",
                                    tool_name=transform.name,
                                ))
                finally:
                    browser.close()

            # Clean up browser page reference
            if page is not None:
                page._browser_page = None
        finally:
            registry.teardown_all()

        if page is None:
            raise RuntimeError(f"Failed to load page: {self.app_agent.url}")

        # Sort issues by severity
        severity_order = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}
        all_issues.sort(key=lambda i: severity_order.get(i.severity.value, 99))

        return AuditResult(
            url=page.url,
            page=page,
            issues=all_issues,
            adaptations=all_adaptations,
            tools_run=tools_run,
            plan=plan,
        )

    def _plan(self, page: PageContext, profile, available_tools: list) -> dict:
        """Use LLM to plan which tools to run and why."""
        tool_info = "\n".join(
            f"- {t.name}: {t.description} "
            f"(profiles: {', '.join(t.ability_profiles) or 'all'})"
            for t in available_tools
        )

        # Include page analysis if AppAgent produced one
        page_context = f"URL: {page.url}\nTitle: {page.title}"
        if page.analysis:
            page_context += f"\n\nPage analysis:\n{json.dumps(page.analysis, indent=2)}"
        else:
            page_context += f"\n\nPage HTML (first 3000 chars):\n{page.html[:3000]}"

        return self.llm.complete_json(
            system=(
                "You are an accessibility expert planning how to adapt a web page "
                "for a specific user. Given the page content and the user's ability "
                "profile, decide which tools to activate.\n\n"
                "Consider:\n"
                "- What does this page contain? (images, charts, forms, text, etc.)\n"
                "- What are this user's specific needs?\n"
                "- Which tools will actually help for this page + this user?\n"
                "- Don't run tools that won't find anything useful."
            ),
            prompt=(
                f"{page_context}\n\n"
                f"User profile: {profile.name} — {profile.description}\n"
                f"User needs: {', '.join(profile.needs)}\n"
                f"Preferred modalities: {', '.join(profile.preferred_modalities)}\n\n"
                f"Available tools:\n{tool_info}\n\n"
                "Return JSON:\n"
                "{\n"
                '  "analysis": "Brief analysis of this page\'s accessibility landscape",\n'
                '  "tools_to_run": ["tool-name", ...],\n'
                '  "reasoning": "Why these tools for this user on this page",\n'
                '  "priority_areas": ["What to focus on first"]\n'
                "}"
            ),
        )

    def _filter_by_profile(self, tools: list, profile) -> list:
        """Rule-based tool filtering by ability profile (fallback)."""
        if not profile:
            return list(tools)
        profile_names = profile.name.split("+")
        return [
            t for t in tools
            if not t.ability_profiles
            or any(p in t.ability_profiles for p in profile_names)
        ]


def check(url: str, profile: str | list[str] | None = None, llm: LLMClient | None = None) -> AuditResult:
    """Check a web page for accessibility issues.

    Args:
        url: URL to check.
        profile: Optional ability profile to filter tools.
        llm: Optional LLMClient override. Defaults to Gemini.

    Returns:
        AuditResult with issues found.

    Example:
        result = check("https://example.com")
        result = check("https://example.com", profile="blv")
    """
    llm_client = llm or LLMClient()
    agents = [AppAgent(url, llm=llm_client)]
    if profile:
        agents.append(UserAgent(profile=profile))
    orchestrator = Orchestrator(agents=agents, llm=llm_client)
    return orchestrator.run()


def adapt(url: str, profile: str | list[str], llm: LLMClient | None = None) -> AuditResult:
    """Adapt a web page for a specific ability profile.

    Args:
        url: URL to adapt.
        profile: Ability profile name or list of names.
        llm: Optional LLMClient override. Defaults to Gemini.

    Returns:
        AuditResult with issues and adaptations.

    Example:
        result = adapt("https://example.com", profile="blv")
        result.plan          # LLM's reasoning about what to adapt
        result.adaptations   # prioritized adaptations
    """
    llm_client = llm or LLMClient()
    agents = [AppAgent(url, llm=llm_client), UserAgent(profile=profile)]
    orchestrator = Orchestrator(agents=agents, llm=llm_client)
    return orchestrator.run()
