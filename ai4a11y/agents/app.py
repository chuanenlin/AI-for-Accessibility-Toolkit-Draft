"""App Agent — understands what the web app can do.

Parses the DOM to discover UI elements and interactive capabilities.
When an LLM is available, also reasons about page semantics — what
the page is for, what accessibility challenges it presents, and
what areas need the most attention.
"""

from __future__ import annotations

from ai4a11y.models import Element, PageContext


class AppAgent:
    """Understands a web app's structure and accessibility landscape.

    Without LLM: extracts elements via Playwright (fast, deterministic).
    With LLM: also analyzes page semantics — purpose, challenges, focus areas.

    Args:
        url: The URL of the web app to analyze.
        llm: Optional LLMClient for semantic page analysis.
    """

    def __init__(self, url: str, llm=None):
        self.url = url
        self.llm = llm
        self._page_context: PageContext | None = None

    def parse(self, browser_page=None) -> PageContext:
        """Load the page and extract its structure.

        Args:
            browser_page: Optional Playwright page to reuse. If not provided,
                launches a new browser (standalone usage).
        """
        if browser_page:
            return self._extract(browser_page)

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="domcontentloaded")
            result = self._extract(page)
            browser.close()

        return result

    def _extract(self, page) -> PageContext:
        """Extract page structure from a Playwright page."""
        title = page.title()
        html = page.content()

        elements = page.evaluate("""() => {
            const selectors = [
                'img', 'a', 'button', 'input', 'select', 'textarea',
                'video', 'audio', 'canvas', 'svg',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'table', 'form', 'nav', 'main', 'aside',
                '[role]', '[aria-label]', '[aria-describedby]',
            ];
            const seen = new Set();
            const results = [];
            for (const sel of selectors) {
                for (const el of document.querySelectorAll(sel)) {
                    if (seen.has(el)) continue;
                    seen.add(el);
                    const attrs = {};
                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    let path = el.tagName.toLowerCase();
                    if (el.id) path += '#' + el.id;
                    else if (el.className && typeof el.className === 'string')
                        path += '.' + el.className.trim().split(/\\s+/).join('.');
                    results.push({
                        tag: el.tagName.toLowerCase(),
                        selector: path,
                        attributes: attrs,
                        text: (el.textContent || '').trim().substring(0, 200),
                        html: el.outerHTML.substring(0, 500),
                    });
                }
            }
            return results;
        }""")

        parsed_elements = [
            Element(
                tag=el["tag"],
                selector=el["selector"],
                attributes=el.get("attributes", {}),
                text=el.get("text", ""),
                html=el.get("html", ""),
            )
            for el in elements
        ]

        # Build the base page context
        self._page_context = PageContext(
            url=self.url,
            title=title,
            html=html,
            elements=parsed_elements,
        )

        # LLM-powered semantic analysis
        if self.llm:
            self._page_context.analysis = self._analyze_semantics(
                self._page_context
            )

        return self._page_context

    def _analyze_semantics(self, page: PageContext) -> dict:
        """Use LLM to understand what this page is and what challenges it has."""
        # Summarize elements for the prompt
        element_summary = []
        for el in page.elements[:50]:  # cap to avoid token overflow
            desc = f"{el.tag}"
            if el.attributes.get("role"):
                desc += f' role="{el.attributes["role"]}"'
            if el.attributes.get("alt"):
                desc += f' alt="{el.attributes["alt"][:50]}"'
            elif el.tag == "img":
                desc += " (no alt text)"
            if el.text:
                desc += f' "{el.text[:60]}"'
            element_summary.append(desc)

        return self.llm.complete_json(
            system=(
                "You are a web accessibility analyst. Analyze this page's "
                "structure and identify accessibility challenges.\n\n"
                "Focus on what matters: What is this page for? What interactive "
                "patterns does it use? Where are the biggest accessibility gaps?"
            ),
            prompt=(
                f"URL: {page.url}\n"
                f"Title: {page.title}\n\n"
                f"Elements found ({len(page.elements)} total):\n"
                + "\n".join(f"  - {e}" for e in element_summary)
                + "\n\nReturn JSON:\n"
                "{\n"
                '  "purpose": "What this page does in one sentence",\n'
                '  "content_types": ["text", "images", "charts", "forms", ...],\n'
                '  "accessibility_challenges": [\n'
                '    {"area": "...", "severity": "high|medium|low", "description": "..."}\n'
                "  ],\n"
                '  "recommended_focus": ["what to prioritize for adaptation"]\n'
                "}"
            ),
        )

    @property
    def page(self) -> PageContext:
        if self._page_context is None:
            return self.parse()
        return self._page_context

    def __repr__(self) -> str:
        return f"<AppAgent url={self.url!r}>"
