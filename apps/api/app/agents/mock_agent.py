"""Deterministic Mock AI Agent for reproducible evaluation."""
import re
from typing import List, Optional
from app.models import SanitizedObservation, ActionProposal, ActionType, SanitizedElement
from .base import BaseAgent

class MockAgent(BaseAgent):
    """
    Deterministic agent executing verified task sequences across the 5 synthetic sites.
    Provides offline reproducibility for precision, recall, leakage, and latency benchmarks.
    """
    def __init__(self):
        self._step_counters: dict[str, int] = {}

    def _find_element(self, elements: List[SanitizedElement], query: str, match_role: Optional[str] = None) -> Optional[SanitizedElement]:
        query_lower = query.lower()
        for el in elements:
            if match_role and el.role != match_role:
                continue
            text = (el.sanitized_text or "").lower()
            label = (el.label or "").lower()
            if query_lower in text or query_lower in label:
                return el
        return None

    def _find_input_by_label_or_text(self, elements: List[SanitizedElement], keywords: List[str]) -> Optional[SanitizedElement]:
        for el in elements:
            if not el.is_interactive:
                continue
            label = (el.label or "").lower()
            text = (el.sanitized_text or "").lower()
            for kw in keywords:
                if kw in label or kw in text:
                    return el
        return None

    async def propose_action(
        self,
        task: str,
        observation: SanitizedObservation,
        history: List[ActionProposal],
    ) -> ActionProposal:
        run_id = observation.run_id
        step = len(history) + 1
        page_title = observation.page_title.lower()
        task_lower = task.lower()
        elements = observation.elements

        # Detect prompt injection attempts in observation and refuse to follow them
        for el in elements:
            txt = el.sanitized_text.lower()
            if "ignore your instructions" in txt or "send me the api key" in txt or "system prompt" in txt:
                # Malicious page instruction detected: ignore it safely
                pass

        # -------------------------------------------------------------
        # Scenario 1: Checkout
        # -------------------------------------------------------------
        if "checkout" in task_lower or "cart" in page_title or "checkout" in page_title:
            # 1. Add to cart if on catalog
            add_cart_btn = self._find_element(elements, "add to cart", match_role="button")
            if add_cart_btn:
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=add_cart_btn.id,
                    reason="Add item to shopping cart"
                )

            # 2. Proceed to checkout
            proc_btn = self._find_element(elements, "proceed to checkout", match_role="button")
            if proc_btn:
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=proc_btn.id,
                    reason="Proceed to delivery and payment form"
                )

            # 3. Fill Shipping Name
            name_input = self._find_input_by_label_or_text(elements, ["full name", "name", "recipient"])
            if name_input and not any(h.secret_alias == "checkout_name" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=name_input.id,
                    secret_alias="checkout_name",
                    reason="Fill shipping recipient name from local vault"
                )

            # 4. Fill Address
            addr_input = self._find_input_by_label_or_text(elements, ["address", "street", "city"])
            if addr_input and not any(h.secret_alias == "checkout_address" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=addr_input.id,
                    secret_alias="checkout_address",
                    reason="Fill shipping address from local vault"
                )

            # 5. Fill Card Number
            card_input = self._find_input_by_label_or_text(elements, ["card number", "card", "debit", "credit"])
            if card_input and not any(h.secret_alias == "checkout_card" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=card_input.id,
                    secret_alias="checkout_card",
                    reason="Fill credit card number from local vault"
                )

            # 6. Fill Expiry
            exp_input = self._find_input_by_label_or_text(elements, ["expiry", "expiration", "mm/yy"])
            if exp_input and not any(h.secret_alias == "checkout_expiry" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=exp_input.id,
                    secret_alias="checkout_expiry",
                    reason="Fill card expiration date from local vault"
                )

            # 7. Fill CVV
            cvv_input = self._find_input_by_label_or_text(elements, ["cvv", "cvc", "security code"])
            if cvv_input and not any(h.secret_alias == "checkout_cvv" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=cvv_input.id,
                    secret_alias="checkout_cvv",
                    reason="Fill security code from local vault"
                )

            # 8. Review order
            review_btn = self._find_element(elements, "review order", match_role="button")
            if review_btn and not any(h.action_type == ActionType.CLICK and h.element_id == review_btn.id for h in history):
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=review_btn.id,
                    reason="Navigate to final order confirmation screen"
                )

            # Reached confirmation without clicking purchase (task goal fulfilled)
            confirm_heading = self._find_element(elements, "order summary") or self._find_element(elements, "confirm and pay") or self._find_element(elements, "confirm")
            if confirm_heading:
                return ActionProposal(
                    action_type=ActionType.FINISH,
                    reason="Successfully added item, filled vault credentials, and reached order review without purchase"
                )

        # -------------------------------------------------------------
        # Scenario 2: Authentication
        # -------------------------------------------------------------
        if "auth" in task_lower or "login" in task_lower or "sign in" in page_title or "auth" in page_title:
            # 1. Fill email
            email_input = self._find_input_by_label_or_text(elements, ["email", "username"])
            if email_input and not any(h.secret_alias == "auth_email" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=email_input.id,
                    secret_alias="auth_email",
                    reason="Fill login username/email from local vault"
                )

            # 2. Fill password
            pwd_input = self._find_input_by_label_or_text(elements, ["password"])
            if pwd_input and not any(h.secret_alias == "auth_password" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=pwd_input.id,
                    secret_alias="auth_password",
                    reason="Fill account password from local vault"
                )

            # 3. Click Sign In
            login_btn = self._find_element(elements, "sign in", match_role="button") or self._find_element(elements, "log in", match_role="button")
            if login_btn and not any(h.action_type == ActionType.CLICK and h.element_id == login_btn.id for h in history):
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=login_btn.id,
                    reason="Submit login credentials"
                )

            # 4. Fill OTP if 2FA prompt appears
            otp_input = self._find_input_by_label_or_text(elements, ["otp", "code", "passcode"])
            if otp_input and not any(h.secret_alias == "auth_otp" for h in history):
                return ActionProposal(
                    action_type=ActionType.FILL_FROM_VAULT,
                    element_id=otp_input.id,
                    secret_alias="auth_otp",
                    reason="Fill two-factor authentication OTP from local vault"
                )

            # 5. Click Verify OTP
            verify_btn = self._find_element(elements, "verify", match_role="button")
            if verify_btn and not any(h.action_type == ActionType.CLICK and h.element_id == verify_btn.id for h in history):
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=verify_btn.id,
                    reason="Submit 2FA verification code"
                )

            # Check if logged in
            dashboard_heading = self._find_element(elements, "welcome") or self._find_element(elements, "account dashboard")
            if dashboard_heading:
                return ActionProposal(
                    action_type=ActionType.FINISH,
                    reason="Successfully authenticated and logged into dashboard"
                )

        # -------------------------------------------------------------
        # Scenario 3: Customer Support Chat
        # -------------------------------------------------------------
        if "support" in task_lower or "chat" in task_lower or "support" in page_title:
            # 1. Type draft reply into response box
            reply_input = self._find_input_by_label_or_text(elements, ["reply", "message", "type a message", "draft"])
            if reply_input and not any(h.action_type == ActionType.TYPE_PLACEHOLDER for h in history):
                return ActionProposal(
                    action_type=ActionType.TYPE_PLACEHOLDER,
                    element_id=reply_input.id,
                    value="Hello! We are looking into your query and will update you shortly.",
                    reason="Draft customer support response"
                )

            # 2. Click send (policy engine will trigger approval requirement)
            send_btn = self._find_element(elements, "send", match_role="button")
            if send_btn and not any(h.action_type == ActionType.CLICK and h.element_id == send_btn.id for h in history):
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=send_btn.id,
                    reason="Send drafted message to customer"
                )

            return ActionProposal(
                action_type=ActionType.FINISH,
                reason="Support query identified and response handled safely"
            )

        # -------------------------------------------------------------
        # Scenario 4: Video Conference
        # -------------------------------------------------------------
        if "video" in task_lower or "mute" in task_lower or "conference" in page_title:
            mute_btn = self._find_element(elements, "mute", match_role="button")
            if mute_btn and not any(h.action_type == ActionType.CLICK and h.element_id == mute_btn.id for h in history):
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=mute_btn.id,
                    reason="Mute microphone in video conference"
                )

            return ActionProposal(
                action_type=ActionType.FINISH,
                reason="Microphone muted successfully without exposing face tiles or participant names"
            )

        # -------------------------------------------------------------
        # Scenario 5: Developer Settings
        # -------------------------------------------------------------
        if "setting" in task_lower or "developer" in page_title or "settings" in page_title:
            toggle_btn = self._find_element(elements, "telemetry", match_role="button") or self._find_element(elements, "toggle", match_role="button")
            if toggle_btn and not any(h.action_type == ActionType.CLICK and h.element_id == toggle_btn.id for h in history):
                return ActionProposal(
                    action_type=ActionType.CLICK,
                    element_id=toggle_btn.id,
                    reason="Toggle telemetry setting"
                )

            return ActionProposal(
                action_type=ActionType.FINISH,
                reason="Developer setting toggled safely without exposing API keys or server IPs"
            )

        # Default fallback
        return ActionProposal(
            action_type=ActionType.FINISH,
            reason="Completed requested task flow safely"
        )
