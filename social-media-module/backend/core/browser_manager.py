"""
Advanced Browser Management with Retry Logic
Based on proven architecture from successful scraping app
"""

import asyncio
import os
from typing import Any, Callable, Dict, Optional, TypeVar

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

T = TypeVar("T")


class BrowserManager:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def get_browser(self) -> Browser:
        """Get browser instance with remote/local fallback"""
        # Check for remote browser (like Browserless)
        ws_endpoint = os.getenv("BROWSERLESS_WS")

        if ws_endpoint:
            try:
                async with async_playwright() as p:
                    return await p.chromium.connect_over_cdp(ws_endpoint)
            except Exception as e:
                print(f"⚠️  Remote browser failed, using local: {e}")

        # Use local browser
        async with async_playwright() as p:
            return await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--no-first-run",
                    "--disable-default-apps",
                ],
            )

    async def create_context(self, browser: Browser) -> BrowserContext:
        """Create browser context with realistic settings"""
        return await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )

    async def with_browser_page(self, fn: Callable[[Page], T]) -> T:
        """Execute function with managed browser page"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])

            context = await self.create_context(browser)
            page = await context.new_page()

            try:
                return await fn(page)
            finally:
                await context.close()
                await browser.close()

    async def navigate_with_retry(self, page: Page, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with intelligent retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"   🌐 Navigating to: {url} (attempt {attempt + 1})")

                # Try different wait strategies
                if attempt == 0:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                elif attempt == 1:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                else:
                    # Fallback: go to base domain first
                    base_url = "/".join(url.split("/")[:3])
                    await page.goto(base_url, timeout=30000)
                    await asyncio.sleep(2)
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Verify page loaded
                await asyncio.sleep(3)
                title = await page.title()

                if title and len(title) > 0:
                    print(f"   ✅ Successfully loaded: {title[:50]}...")
                    return True

            except Exception as e:
                print(f"   ⚠️  Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        print(f"   ❌ Failed to navigate to {url} after {max_retries} attempts")
        return False

    async def handle_popups_and_overlays(self, page: Page):
        """Handle common popups and overlays"""
        try:
            # Common popup selectors
            popup_selectors = [
                '[data-testid="close-button"]',
                ".modal-close",
                ".popup-close",
                ".overlay-close",
                'button[aria-label="Close"]',
                ".cookie-banner button",
                ".age-gate button",
                ".newsletter-popup .close",
            ]

            for selector in popup_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        await asyncio.sleep(1)
                        print(f"   ✅ Closed popup: {selector}")
                except:
                    continue

        except Exception as e:
            print(f"   ⚠️  Popup handling error: {e}")

    async def smart_scroll(self, page: Page, max_scrolls: int = 5) -> int:
        """Intelligent scrolling with content detection"""
        initial_height = await page.evaluate("document.body.scrollHeight")
        scrolls_performed = 0

        for i in range(max_scrolls):
            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            # Check if new content loaded
            new_height = await page.evaluate("document.body.scrollHeight")

            if new_height > initial_height:
                initial_height = new_height
                scrolls_performed += 1
                print(f"   📜 Scroll {i + 1}: New content loaded")
            else:
                print(f"   📜 Scroll {i + 1}: No new content, stopping")
                break

        return scrolls_performed

    async def extract_page_content(self, page: Page, platform: str) -> str:
        """Extract relevant content based on platform"""

        content_selectors = {
            "linkedin": {
                "posts": ".feed-shared-update-v2, .occludable-update",
                "articles": ".reader-article-content, .article-content",
                "profiles": ".pv-top-card, .profile-section",
            },
            "substack": {
                "articles": ".post-content, .markup, .reader2-post-content",
                "search_results": ".search-result, .post-preview",
                "publications": ".publication-card, .pub-card",
            },
            "reddit": {
                "posts": ".Post, [data-testid='post-container']",
                "comments": ".Comment, [data-testid='comment']",
                "subreddits": ".subreddit-card, .community-card",
            },
        }

        selectors = content_selectors.get(platform, {})

        try:
            # Extract content using multiple selectors
            content_parts = []

            for content_type, selector in selectors.items():
                elements = await page.query_selector_all(selector)
                for element in elements[:20]:  # Limit to prevent huge content
                    try:
                        text = await element.inner_text()
                        if text and len(text.strip()) > 10:
                            content_parts.append(f"[{content_type.upper()}] {text.strip()}")
                    except:
                        continue

            # Fallback: get general page content
            if not content_parts:
                content_parts.append(await page.inner_text("body"))

            return "\n\n".join(content_parts)

        except Exception as e:
            print(f"   ❌ Content extraction error: {e}")
            return ""

    async def detect_total_items(self, page: Page, platform: str) -> int:
        """Detect total number of items available"""
        try:
            # Platform-specific total detection
            if platform == "linkedin":
                total_element = await page.query_selector(".search-results__total, .results-context-header__context")
            elif platform == "substack":
                total_element = await page.query_selector(".search-results-count, .total-results")
            elif platform == "reddit":
                total_element = await page.query_selector(".search-result-meta, .results-count")
            else:
                total_element = None

            if total_element:
                text = await total_element.inner_text()
                # Extract number from text like "1,234 results"
                import re

                numbers = re.findall(r"[\d,]+", text)
                if numbers:
                    return int(numbers[0].replace(",", ""))

            # Fallback: count visible items
            items = await page.query_selector_all("article, .post, .result, .card")
            return len(items)

        except Exception as e:
            print(f"   ⚠️  Total detection error: {e}")
            return 0

    async def wait_for_content_load(self, page: Page, timeout: int = 30000):
        """Wait for dynamic content to load"""
        try:
            # Wait for common loading indicators to disappear
            await page.wait_for_selector(".loading, .spinner, .skeleton", state="detached", timeout=timeout)
        except:
            pass

        try:
            # Wait for content to appear
            await page.wait_for_selector("article, .post, .result, .card", timeout=timeout)
        except:
            print("   ⚠️  Content load timeout, proceeding anyway")

    async def with_retry(self, fn: Callable[[], T], max_retries: int = 3) -> Optional[T]:
        """Execute function with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return await fn()
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"   ❌ Final attempt failed: {e}")
                    return None

                wait_time = 2**attempt
                print(f"   ⚠️  Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

        return None
