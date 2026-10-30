"""Browser manager supporting Camoufox stealth browser engine."""
import asyncio
import os
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config import settings

# Find playwright firefox executable on system
FIREFOX_PATH = Path("/Users/sagartripathi/Library/Caches/ms-playwright/firefox-1555/firefox/Nightly.app/Contents/MacOS/firefox")
PROPERTIES_PATH = Path("/Users/sagartripathi/Library/Caches/ms-playwright/firefox-1555/firefox/Nightly.app/Contents/MacOS/properties.json")

class BrowserManager:
    def __init__(self, browser_type: str = "camoufox", headless: bool = True):
        self.browser_type = browser_type
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def start(self) -> Page:
        """Launches the anti-detect stealth browser and opens a fresh isolated page."""
        if self._page and not self._page.is_closed():
            return self._page

        self._playwright = await async_playwright().start()

        # Try Camoufox with stealth configuration
        if self.browser_type == "camoufox" and FIREFOX_PATH.exists():
            try:
                from camoufox.async_api import AsyncCamoufox
                # Initialize Camoufox stealth browser with Firefox binary
                camoufox_mgr = AsyncCamoufox(
                    executable_path=str(FIREFOX_PATH),
                    headless=self.headless,
                    block_webgl=True,
                    fingerprint_preset=True,
                    geoip=False,
                    i_know_what_im_doing=True,
                )
                self._browser = await camoufox_mgr.__aenter__()
                self._context = await self._browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    device_scale_factor=1.0
                )
                self._page = await self._context.new_page()
                self._page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))
                return self._page
            except Exception as e:
                print(f"[BrowserManager] Camoufox launch note: {e}, falling back to Playwright Firefox")

        # Fallback to Playwright Firefox / Chromium
        if FIREFOX_PATH.exists():
            self._browser = await self._playwright.firefox.launch(
                executable_path=str(FIREFOX_PATH),
                headless=self.headless
            )
        else:
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )

        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1.0
        )
        self._page = await self._context.new_page()
        # Auto-dismiss dialogs (alerts, confirms) to prevent blocking
        self._page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))
        return self._page

    async def get_page(self) -> Page:
        if not self._page or self._page.is_closed():
            return await self.start()
        return self._page

    async def close(self):
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._page = None
