from __future__ import annotations
from pathlib import Path
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from .models import LocatorStrategy

class BrowserSurface:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.pw: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def __enter__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()

    def start_trace(self):
        assert self.context
        self.context.tracing.start(screenshots=True, snapshots=True, sources=False)

    def stop_trace(self, path: Path):
        assert self.context
        self.context.tracing.stop(path=str(path))

    def goto(self, url: str):
        assert self.page
        self.page.goto(url, wait_until="domcontentloaded")

    def observe(self) -> str:
        assert self.page
        try:
            return self.page.aria_snapshot(mode="ai", depth=8)
        except TypeError:
            return self.page.locator("body").aria_snapshot()

    def screenshot(self, path: Path):
        assert self.page
        self.page.screenshot(path=str(path), full_page=True)

    def locator(self, spec: LocatorStrategy):
        assert self.page
        if spec.kind == "role_name":
            return self.page.get_by_role(spec.role, name=spec.name, exact=spec.exact)
        if spec.kind == "label":
            return self.page.get_by_label(spec.value, exact=spec.exact)
        if spec.kind == "text":
            return self.page.get_by_text(spec.value, exact=spec.exact)
        if spec.kind == "css":
            return self.page.locator(spec.value)
        raise ValueError(spec.kind)

    def click(self, spec: LocatorStrategy, timeout_ms: int = 5000):
        self.locator(spec).click(timeout=timeout_ms)

    def fill(self, spec: LocatorStrategy, value: str, timeout_ms: int = 5000):
        self.locator(spec).fill(value, timeout=timeout_ms)

    def read(self, spec: LocatorStrategy, timeout_ms: int = 5000) -> str:
        loc = self.locator(spec)
        loc.wait_for(state="visible", timeout=timeout_ms)
        return loc.inner_text().strip()

    def body_text(self) -> str:
        assert self.page
        return self.page.locator("body").inner_text()
