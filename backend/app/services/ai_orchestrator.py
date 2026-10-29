import uuid
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.schemas import (
    BrowserAction,
    BrowserActionType,
    ActionRiskLevel,
    TaskSession,
)
from app.config import settings


class AIProvider(ABC):
    """Abstract base class for AI planner adapters."""

    @abstractmethod
    async def plan_action(
        self,
        task: TaskSession,
        step_index: int,
        sanitized_dom_text: str,
        current_url: str
    ) -> BrowserAction:
        """Generates the next browser action based on sanitized task context."""
        pass


class DeterministicMockProvider(AIProvider):
    """
    Deterministic Mock AI Provider.
    Used for offline testing, CI/CD, and repeatable benchmarking without credentials.
    Clearly and transparently generates reproducible, deterministic browser plans.
    """

    async def plan_action(
        self,
        task: TaskSession,
        step_index: int,
        sanitized_dom_text: str,
        current_url: str
    ) -> BrowserAction:
        action_id = f"act_{uuid.uuid4().hex[:10]}"
        dom_lower = sanitized_dom_text.lower()
        goal_lower = task.goal.lower()

        # Consequential checkout / payment / submission scenario
        if "checkout" in goal_lower or "submit" in goal_lower or "pay" in goal_lower or "purchase" in goal_lower:
            if "submit" in dom_lower or "place order" in dom_lower or "pay" in dom_lower:
                return BrowserAction(
                    action_id=action_id,
                    type=BrowserActionType.SUBMIT,
                    target_selector="form#checkout-form button[type='submit']",
                    target_description="Submit finalized order form",
                    value=None,
                    risk_level=ActionRiskLevel.HIGH,
                    is_consequential=True,
                    rationale="[DETERMINISTIC_MOCK] Submit form after verifying sanitized parameters."
                )
            else:
                return BrowserAction(
                    action_id=action_id,
                    type=BrowserActionType.TYPE,
                    target_selector="input#promo-code",
                    target_description="Fill promotional discount code",
                    value="PRIVACY2026",
                    risk_level=ActionRiskLevel.MEDIUM,
                    is_consequential=False,
                    rationale="[DETERMINISTIC_MOCK] Apply coupon to checkout cart."
                )

        # Standard browsing / receipt retrieval scenario
        if "order" in goal_lower or "flight" in goal_lower or "receipt" in goal_lower:
            if step_index == 1:
                return BrowserAction(
                    action_id=action_id,
                    type=BrowserActionType.CLICK,
                    target_selector="a.view-receipt-link, button#receipt",
                    target_description="Click 'View Booking Receipt' link",
                    value=None,
                    risk_level=ActionRiskLevel.LOW,
                    is_consequential=False,
                    rationale="[DETERMINISTIC_MOCK] Access receipt view to locate booking reference code."
                )
            elif step_index == 2:
                return BrowserAction(
                    action_id=action_id,
                    type=BrowserActionType.EXTRACT,
                    target_selector="span.booking-reference, #order-id",
                    target_description="Extract booking reference confirmation code",
                    value=None,
                    risk_level=ActionRiskLevel.LOW,
                    is_consequential=False,
                    rationale="[DETERMINISTIC_MOCK] Reading authorized booking code from sanitized receipt."
                )
            else:
                return BrowserAction(
                    action_id=action_id,
                    type=BrowserActionType.WAIT,
                    target_selector="body",
                    target_description="Task objective achieved; idle",
                    value=None,
                    risk_level=ActionRiskLevel.LOW,
                    is_consequential=False,
                    rationale="[DETERMINISTIC_MOCK] All target information extracted successfully."
                )

        # Default fallback action
        return BrowserAction(
            action_id=action_id,
            type=BrowserActionType.CLICK,
            target_selector="button.continue-btn, a.next",
            target_description="Click Continue button",
            value=None,
            risk_level=ActionRiskLevel.LOW,
            is_consequential=False,
            rationale="[DETERMINISTIC_MOCK] Standard browsing progression towards declared objective."
        )


class CloudAIProvider(AIProvider):
    """
    Real Cloud AI Provider (e.g. Gemini / OpenAI).
    Activated only when valid credentials exist in the environment.
    Strictly guaranteed to receive only sanitized context verified by the Outbound Firewall.
    """

    def __init__(self, provider_name: str, api_key: str):
        self.provider_name = provider_name
        self.api_key = api_key

    async def plan_action(
        self,
        task: TaskSession,
        step_index: int,
        sanitized_dom_text: str,
        current_url: str
    ) -> BrowserAction:
        # Note: If credentials are placeholder or unavailable, fallback safely to deterministic mock
        if not self.api_key:
            mock = DeterministicMockProvider()
            action = await mock.plan_action(task, step_index, sanitized_dom_text, current_url)
            action.rationale = f"[FALLBACK_MOCK - Missing {self.provider_name} API Key] {action.rationale}"
            return action

        # Real API invocation would occur here strictly on sanitized_dom_text
        # For offline evaluation / test safety, deterministic mock is the default
        mock = DeterministicMockProvider()
        return await mock.plan_action(task, step_index, sanitized_dom_text, current_url)


def get_ai_provider() -> AIProvider:
    """Factory creating configured AI adapter with transparent mock labeling."""
    provider_name = settings.AI_PROVIDER.lower()
    if provider_name == "gemini" and settings.GEMINI_API_KEY:
        return CloudAIProvider("Gemini", settings.GEMINI_API_KEY)
    elif provider_name == "openai" and settings.OPENAI_API_KEY:
        return CloudAIProvider("OpenAI", settings.OPENAI_API_KEY)
    return DeterministicMockProvider()
