"""Browser action executor with secure secret injection."""
import asyncio
from typing import Tuple, Optional
from playwright.async_api import Page
from app.models import ActionProposal, ActionType
from app.privacy.vault import vault

class BrowserExecutor:
    async def execute_action(
        self,
        page: Page,
        action: ActionProposal,
    ) -> Tuple[bool, str]:
        """
        Executes a validated, approved action on the browser page.
        Returns:
            (success: bool, execution_message: str)
        """
        try:
            selector = f'[data-privacylens-id="{action.element_id}"]' if action.element_id else None

            if action.action_type == ActionType.CLICK:
                if not selector:
                    return False, "Click action requires an element_id"
                loc = page.locator(selector).first
                if await loc.count() == 0:
                    return False, f"Element {action.element_id} not found in DOM"
                await loc.click(timeout=4000)
                await asyncio.sleep(0.5)
                return True, f"Clicked element {action.element_id}"

            elif action.action_type == ActionType.TYPE_PLACEHOLDER:
                if not selector:
                    return False, "Type action requires an element_id"
                loc = page.locator(selector).first
                if await loc.count() == 0:
                    return False, f"Element {action.element_id} not found in DOM"
                await loc.fill(action.value or "", timeout=4000)
                await asyncio.sleep(0.2)
                return True, f"Entered text into {action.element_id}"

            elif action.action_type == ActionType.FILL_FROM_VAULT:
                if not selector:
                    return False, "Vault fill action requires an element_id"
                if not action.secret_alias:
                    return False, "Vault fill action requires a secret_alias"
                
                # Fetch secret strictly from local memory vault
                secret_value = vault.get_secret(action.secret_alias)
                if not secret_value:
                    return False, f"Secret alias '{action.secret_alias}' not found in local vault"

                loc = page.locator(selector).first
                if await loc.count() == 0:
                    return False, f"Element {action.element_id} not found in DOM"
                
                # Direct DOM typing: secret value is never serialized into model context or trace
                await loc.fill(secret_value, timeout=4000)
                await asyncio.sleep(0.2)
                return True, f"Securely filled {action.element_id} from vault alias '{action.secret_alias}'"

            elif action.action_type == ActionType.SELECT:
                if not selector:
                    return False, "Select action requires an element_id"
                loc = page.locator(selector).first
                await loc.select_option(action.value or "")
                return True, f"Selected option on {action.element_id}"

            elif action.action_type == ActionType.SCROLL:
                delta_y = int(action.value) if action.value and action.value.isdigit() else 300
                await page.mouse.wheel(0, delta_y)
                await asyncio.sleep(0.2)
                return True, f"Scrolled page by {delta_y}px"

            elif action.action_type == ActionType.NAVIGATE:
                if not action.target_url:
                    return False, "Navigate action requires a target_url"
                await page.goto(action.target_url, wait_until="domcontentloaded")
                await asyncio.sleep(0.5)
                return True, f"Navigated to {action.target_url}"

            elif action.action_type == ActionType.WAIT:
                wait_sec = 1.0
                if action.value:
                    try:
                        wait_sec = float(action.value)
                    except ValueError:
                        pass
                await asyncio.sleep(wait_sec)
                return True, f"Waited {wait_sec}s"

            elif action.action_type == ActionType.FINISH:
                return True, f"Task marked finished: {action.reason}"

            return False, f"Unknown action type: {action.action_type}"

        except Exception as e:
            return False, f"Action execution error: {str(e)}"
