"""Contextual and structural DOM PII detectors."""
import re
from typing import List, Tuple
from app.models import DOMElement, SensitiveSpan, SensitiveCategory, BoundingBox

# Password indicators in element attributes
PASSWORD_ATTR_REGEX = re.compile(r'(?i)password|passwd|pwd|passcode|secret')

# Name indicators in form labels / context
NAME_LABELS = ["name", "full name", "first name", "last name", "customer name", "recipient", "cardholder"]
ADDRESS_LABELS = ["address", "street", "city", "zip", "postal code", "pincode", "shipping address", "billing address"]

def detect_dom_context(elements: List[DOMElement]) -> List[SensitiveSpan]:
    """
    Examines DOM elements structurally using tag names, input types, attributes,
    and semantic context to flag sensitive fields.
    """
    spans: List[SensitiveSpan] = []
    
    for el in elements:
        tag = el.tag.lower()
        el_type = (el.type or "").lower()
        name_attr = (el.name or "").lower()
        label = (el.label or "").lower()
        text = el.text.strip()
        val = el.value.strip()
        placeholder = (el.placeholder or "").lower()
        id_attr = (el.attributes.get("id", "") or "").lower()
        class_attr = (el.attributes.get("class", "") or "").lower()
        all_attrs = [name_attr, label, placeholder, id_attr, class_attr]
        
        # 1. CVV check FIRST (even if type=password)
        if any(term in attr for term in ["cvv", "cvc", "security", "card-cvc"] for attr in all_attrs):
            spans.append(SensitiveSpan(
                category=SensitiveCategory.CVV,
                text=val if val else None,
                confidence=0.99,
                detector="DOM_STRUCTURE_CVV",
                reason="Card verification value input field",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 2. OTP / 2FA check BEFORE generic passcode/password check
        if any(term in attr for term in ["otp", "2fa", "verification-code", "verification code", "passcode", "sms-code", "otpcode"] for attr in all_attrs) and "password" not in name_attr:
            spans.append(SensitiveSpan(
                category=SensitiveCategory.OTP,
                text=val if val else None,
                confidence=0.98,
                detector="DOM_STRUCTURE_OTP",
                reason="One-time password or verification input field",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 3. Passwords: input type=password or matching attributes
        if el_type == "password" or any(PASSWORD_ATTR_REGEX.search(attr) for attr in all_attrs):
            spans.append(SensitiveSpan(
                category=SensitiveCategory.PASSWORD,
                text=val if val else "[EMPTY_PASSWORD_FIELD]",
                confidence=1.0,
                detector="DOM_STRUCTURE_PASSWORD",
                reason="Input marked as password field or has password attribute",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 3. Credit Card fields by attribute / label (inputs or card summary)
        if (tag in ["input", "textarea"] or "summarycard" in id_attr or "card" in id_attr) and any(term in attr for term in ["card", "creditcard", "cc-number", "debit", "summarycardend"] for attr in all_attrs):
            spans.append(SensitiveSpan(
                category=SensitiveCategory.CREDIT_CARD,
                text=val if val else text if text else None,
                confidence=0.98,
                detector="DOM_STRUCTURE_CARD",
                reason="Payment card number input field",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 3b. Card Expiry date
        if any(term in attr for term in ["expiry", "expiration", "exp-date", "exp_date", "mm/yy"] for attr in all_attrs):
            spans.append(SensitiveSpan(
                category=SensitiveCategory.CREDIT_CARD,
                text=val if val else text if text else None,
                confidence=0.95,
                detector="DOM_STRUCTURE_EXPIRY",
                reason="Payment card expiration date input field",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 4. Name fields
        if any(term in attr for term in ["full name", "fullname", "recipient", "customer name", "summaryname"] for attr in all_attrs):
            spans.append(SensitiveSpan(
                category=SensitiveCategory.NAME,
                text=val if val else text if text else None,
                confidence=0.95,
                detector="DOM_STRUCTURE_NAME",
                reason="Full name recipient input field",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 5. Address fields
        if any(term in attr for term in ["address", "street", "shipping address", "billing address", "summaryaddress"] for attr in all_attrs):
            spans.append(SensitiveSpan(
                category=SensitiveCategory.ADDRESS,
                text=val if val else text if text else None,
                confidence=0.95,
                detector="DOM_STRUCTURE_ADDRESS",
                reason="Shipping / billing address input field",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 6. OTP / 2FA fields
        if any(term in attr for term in ["otp", "2fa", "verification-code", "passcode", "sms-code", "otpcode"] for attr in [name_attr, label, placeholder]):
            spans.append(SensitiveSpan(
                category=SensitiveCategory.OTP,
                text=val if val else None,
                confidence=0.97,
                detector="DOM_STRUCTURE_OTP",
                reason="One-time password or verification input field",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue

        # 7. Support Chat: private message or user/customer chat transcript
        if "chat-message" in el.attributes.get("class", "").lower() or "chat-bubble" in el.attributes.get("class", "").lower():
            cls_lower = el.attributes.get("class", "").lower()
            if any(k in cls_lower for k in ["private", "user", "customer"]):
                spans.append(SensitiveSpan(
                    category=SensitiveCategory.PRIVATE_MESSAGE,
                    text=text,
                    confidence=0.95,
                    detector="DOM_CONTEXT_CHAT",
                    reason="Customer support transcript private user/customer message",
                    replacement_token="",
                    element_id=el.id,
                    bbox=el.bbox,
                ))
                continue
                
        # 5. Video conference tiles and participant tags
        if "video-tile" in el.attributes.get("class", "").lower() or "video-stream" in el.attributes.get("class", "").lower() or tag == "video":
            spans.append(SensitiveSpan(
                category=SensitiveCategory.FACE,
                text=None,
                confidence=1.0,
                detector="DOM_STRUCTURE_VIDEO_TILE",
                reason="Video conference tile / synthetic camera feed",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue
            
        if "participant-name" in el.attributes.get("class", "").lower() or "user-badge" in el.attributes.get("class", "").lower():
            spans.append(SensitiveSpan(
                category=SensitiveCategory.NAME,
                text=text,
                confidence=0.95,
                detector="DOM_STRUCTURE_PARTICIPANT_NAME",
                reason="Video conference participant identity label",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            continue
            
        # 6. Cross-origin iframes & canvas regions: blanket mask unknown content
        if tag in ["iframe", "canvas"]:
            spans.append(SensitiveSpan(
                category=SensitiveCategory.SENSITIVE_REGION,
                text=None,
                confidence=1.0,
                detector="DOM_STRUCTURE_IFRAME_CANVAS",
                reason=f"Unchecked visual region ({tag}) masked by fail-closed policy",
                replacement_token="",
                element_id=el.id,
                bbox=el.bbox,
            ))
            
    return spans
