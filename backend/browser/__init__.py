"""Browser automation for auto-filling job application forms using Playwright."""
from __future__ import annotations

import asyncio
import os
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from backend.config import get_settings


@dataclass
class ApplicationForm:
    """Detected form fields on an application page."""
    url: str = ""
    company: str = ""
    job_title: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)
    has_upload: bool = False
    has_cover_letter: bool = False
    submit_button_selector: str = ""
    detected_platform: str = ""  # greenhouse, lever, workday, ashby, other


@dataclass
class ApplyResult:
    """Result of an auto-apply attempt."""
    success: bool = False
    url: str = ""
    fields_filled: int = 0
    fields_total: int = 0
    resume_uploaded: bool = False
    cover_letter_filled: bool = False
    blocked_by: str = ""  # CAPTCHA, LOGIN, AUTH, etc.
    error: str = ""
    screenshot_path: str = ""
    form_snapshot: Dict[str, Any] = field(default_factory=dict)


class AutoApplyEngine:
    """Playwright-based engine for automatically filling job application forms."""

    # Common form field selectors for different platforms
    PLATFORM_SELECTORS = {
        "greenhouse": {
            "name": ["#first_name", "#last_name", "[name='first_name']", "[name='last_name']"],
            "email": ["#email", "[name='email']"],
            "phone": ["#phone", "[name='phone']"],
            "resume": ["input[type='file'][name*='resume']", "input[type='file'][accept*='pdf']"],
            "cover_letter": ["textarea[name*='cover']", "#cover_letter", "[data-testid='cover-letter']"],
            "linkedin": ["input[name*='linkedin']", "[name*='linked_in']"],
            "github": ["input[name*='github']"],
            "website": ["input[name*='website']", "input[name*='portfolio']"],
            "submit": ["input[type='submit']", "button[type='submit']", ".submit-button"],
            "captcha": [".g-recaptcha", "#captcha", "[data-sitekey]"],
            "login_required": ["#login", ".login-form", "[data-testid='login']"],
        },
        "lever": {
            "name": ["input[name='name']", "#name"],
            "email": ["input[name='email']", "#email"],
            "phone": ["input[name='phone']", "#phone"],
            "resume": ["input[type='file'][name*='resume']", "input[accept*='pdf']"],
            "cover_letter": ["textarea[name='comments']", ".application-question textarea"],
            "linkedin": ["input[name*='urls[LinkedIn]']", "input[name*='linkedin']"],
            "github": ["input[name*='urls[GitHub]']", "input[name*='github']"],
            "website": ["input[name*='urls[Portfolio]']", "input[name*='website']"],
            "submit": ["button[data-qa='btn-submit']", "button[type='submit']"],
            "captcha": [".g-recaptcha", "#captcha"],
            "login_required": [".auth-page", "#login"],
        },
        "workday": {
            "name": ["[data-automation-id='legalNameSection_firstName']", "[data-automation-id='legalNameSection_lastName']"],
            "email": ["[data-automation-id='email']"],
            "phone": ["[data-automation-id='phone-number']"],
            "resume": ["input[type='file'][data-automation-id*='resume']"],
            "cover_letter": ["[data-automation-id*='coverLetter'] textarea"],
            "submit": ["[data-automation-id='bottom-navigation-next-button']"],
            "captcha": [".g-recaptcha", "[data-automation-id='captcha']"],
            "login_required": ["[data-automation-id='login']"],
        },
        "ashby": {
            "name": ["[name='name']", "#name"],
            "email": ["[name='email']", "#email"],
            "phone": ["[name='phone']", "#phone"],
            "resume": ["input[type='file']"],
            "cover_letter": ["textarea[name*='cover']", "[name='applicationQuestion']"],
            "submit": ["button[type='submit']"],
            "captcha": [".g-recaptcha"],
            "login_required": [".auth-page"],
        },
    }

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.settings = get_settings()
        self._browser = None
        self._context = None

    async def _ensure_browser(self):
        """Ensure Playwright browser is running."""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
                self._pw = await async_playwright().start()
                self._browser = await self._pw.chromium.launch(
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                self._context = await self._browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                )
            except ImportError:
                raise RuntimeError("Playwright is not installed. Run: pip install playwright && playwright install chromium")
            except Exception as e:
                raise RuntimeError(f"Failed to start browser: {e}")

    async def close(self):
        """Close the browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if hasattr(self, '_pw') and self._pw:
            await self._pw.stop()

    async def detect_form(self, url: str) -> ApplicationForm:
        """Navigate to a URL and detect the application form structure."""
        await self._ensure_browser()
        page = await self._context.new_page()

        form = ApplicationForm(url=url)

        try:
            # Check for bot detection / CAPTCHA
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # Detect platform
            form.detected_platform = await self._detect_platform(page)

            # Check for blocking conditions
            if await self._check_captcha(page):
                form.fields = [{"type": "blocked", "reason": "CAPTCHA detected"}]
                return form

            if await self._check_login_required(page):
                form.fields = [{"type": "blocked", "reason": "Login required"}]
                return form

            # Detect form fields
            selectors = self.PLATFORM_SELECTORS.get(form.detected_platform, self.PLATFORM_SELECTORS["greenhouse"])

            for field_name, selector_list in selectors.items():
                if field_name in ("captcha", "login_required"):
                    continue
                for selector in selector_list:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            form.fields.append({
                                "name": field_name,
                                "selector": selector,
                                "visible": is_visible,
                                "tag": await element.evaluate("el => el.tagName.toLowerCase()"),
                                "type": await element.evaluate("el => el.type || ''"),
                            })
                            if field_name == "resume":
                                form.has_upload = True
                            if field_name == "cover_letter":
                                form.has_cover_letter = True
                            break
                    except Exception:
                        continue

            # Find submit button
            for selector in selectors.get("submit", []):
                try:
                    btn = await page.query_selector(selector)
                    if btn and await btn.is_visible():
                        form.submit_button_selector = selector
                        break
                except Exception:
                    continue

            # Extract job info from page
            try:
                title_el = await page.query_selector("h1, [data-testid='job-title'], .job-title")
                if title_el:
                    form.job_title = (await title_el.inner_text()).strip()
                company_el = await page.query_selector("[data-testid='company-name'], .company-name, h2")
                if company_el:
                    form.company = (await company_el.inner_text()).strip()
            except Exception:
                pass

        except Exception as e:
            form.fields = [{"type": "error", "reason": str(e)}]
        finally:
            await page.close()

        return form

    async def auto_fill(
        self,
        url: str,
        user_data: Dict[str, str],
        resume_path: Optional[str] = None,
        cover_letter: Optional[str] = None,
        dry_run: bool = True,
    ) -> ApplyResult:
        """
        Navigate to application URL and auto-fill the form.

        Args:
            url: Application URL
            user_data: Dict with keys like name, email, phone, linkedin, github, website
            resume_path: Path to resume PDF file
            cover_letter: Cover letter text
            dry_run: If True, fill but don't submit

        Returns:
            ApplyResult with details of what was filled
        """
        await self._ensure_browser()
        page = await self._context.new_page()
        result = ApplyResult(url=url)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # Check blocking conditions
            if await self._check_captcha(page):
                result.blocked_by = "CAPTCHA"
                return result

            if await self._check_login_required(page):
                result.blocked_by = "LOGIN_REQUIRED"
                return result

            # Detect platform and fill fields
            platform = await self._detect_platform(page)
            selectors = self.PLATFORM_SELECTORS.get(platform, self.PLATFORM_SELECTORS["greenhouse"])

            fields_filled = 0
            fields_total = 0

            # Fill name fields
            name_parts = user_data.get("name", "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            for selector in selectors.get("name", []):
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        fields_total += 1
                        if "first" in selector.lower():
                            await el.fill(first_name)
                            fields_filled += 1
                        elif "last" in selector.lower():
                            await el.fill(last_name)
                            fields_filled += 1
                        elif not fields_filled:
                            await el.fill(user_data.get("name", ""))
                            fields_filled += 1
                except Exception:
                    continue

            # Fill email
            for selector in selectors.get("email", []):
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        fields_total += 1
                        await el.fill(user_data.get("email", ""))
                        fields_filled += 1
                        break
                except Exception:
                    continue

            # Fill phone
            for selector in selectors.get("phone", []):
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        fields_total += 1
                        await el.fill(user_data.get("phone", ""))
                        fields_filled += 1
                        break
                except Exception:
                    continue

            # Fill LinkedIn
            for selector in selectors.get("linkedin", []):
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        fields_total += 1
                        await el.fill(user_data.get("linkedin_url", ""))
                        fields_filled += 1
                        break
                except Exception:
                    continue

            # Fill GitHub
            for selector in selectors.get("github", []):
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        fields_total += 1
                        await el.fill(user_data.get("github_url", ""))
                        fields_filled += 1
                        break
                except Exception:
                    continue

            # Fill website/portfolio
            for selector in selectors.get("website", []):
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        fields_total += 1
                        await el.fill(user_data.get("portfolio_url", ""))
                        fields_filled += 1
                        break
                except Exception:
                    continue

            # Upload resume
            if resume_path and os.path.exists(resume_path):
                for selector in selectors.get("resume", []):
                    try:
                        el = await page.query_selector(selector)
                        if el:
                            await el.set_input_files(resume_path)
                            result.resume_uploaded = True
                            fields_total += 1
                            fields_filled += 1
                            break
                    except Exception:
                        continue

            # Fill cover letter
            if cover_letter:
                for selector in selectors.get("cover_letter", []):
                    try:
                        el = await page.query_selector(selector)
                        if el and await el.is_visible():
                            fields_total += 1
                            await el.fill(cover_letter)
                            result.cover_letter_filled = True
                            fields_filled += 1
                            break
                    except Exception:
                        continue

            result.fields_filled = fields_filled
            result.fields_total = fields_total

            # Take screenshot
            screenshot_dir = os.path.join(self.settings.uploads_dir, "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"apply_{int(time.time())}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            result.screenshot_path = screenshot_path

            if not dry_run:
                # Submit the form
                for selector in selectors.get("submit", []):
                    try:
                        btn = await page.query_selector(selector)
                        if btn and await btn.is_visible():
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            result.success = True
                            break
                    except Exception:
                        continue

        except Exception as e:
            result.error = str(e)
        finally:
            await page.close()

        return result

    async def _detect_platform(self, page) -> str:
        """Detect which ATS platform the page uses."""
        url = page.url.lower()
        html = ""

        try:
            html = await page.evaluate("document.documentElement.outerHTML.substring(0, 5000)")
        except Exception:
            pass

        if "greenhouse" in url or "greenhouse" in html.lower():
            return "greenhouse"
        if "lever" in url or "lever" in html.lower():
            return "lever"
        if "workday" in url or "myworkdayjobs" in url:
            return "workday"
        if "ashby" in url or "ashbyhq" in url:
            return "ashby"
        if "icims" in url:
            return "icims"
        return "other"

    async def _check_captcha(self, page) -> bool:
        """Check if page has CAPTCHA."""
        try:
            captcha = await page.query_selector(".g-recaptcha, #captcha, [data-sitekey], iframe[src*='captcha']")
            if captcha:
                return True
            # Check text content
            text = await page.inner_text("body")
            captcha_words = ["verify you are human", "prove you're not a robot", "captcha", "recaptcha"]
            return any(w in text.lower() for w in captcha_words)
        except Exception:
            return False

    async def _check_login_required(self, page) -> bool:
        """Check if page requires login."""
        try:
            login = await page.query_selector("input[type='password'], #login-form, .login-page")
            if login:
                return True
            text = await page.inner_text("body")
            return "sign in" in text.lower()[:1000] or "log in" in text.lower()[:1000]
        except Exception:
            return False


async def batch_auto_apply(
    applications: List[Dict[str, Any]],
    user_data: Dict[str, str],
    resume_path: Optional[str] = None,
    dry_run: bool = True,
) -> List[ApplyResult]:
    """
    Batch auto-apply to multiple jobs.

    Args:
        applications: List of dicts with 'url', 'job_title', 'company', 'cover_letter'
        user_data: User profile data for form filling
        resume_path: Path to resume PDF
        dry_run: If True, fill but don't submit

    Returns:
        List of ApplyResult
    """
    engine = AutoApplyEngine(headless=True)
    results = []

    try:
        for app in applications:
            url = app.get("url", "")
            if not url:
                results.append(ApplyResult(
                    url="",
                    error="No application URL provided",
                ))
                continue

            print(f"Auto-filling: {app.get('job_title', 'Unknown')} at {app.get('company', 'Unknown')}")

            result = await engine.auto_fill(
                url=url,
                user_data=user_data,
                resume_path=resume_path,
                cover_letter=app.get("cover_letter", ""),
                dry_run=dry_run,
            )
            results.append(result)

            # Respectful delay between applications
            await asyncio.sleep(2)

    finally:
        await engine.close()

    return results
