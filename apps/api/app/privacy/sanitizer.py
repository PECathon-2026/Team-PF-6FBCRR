"""Full PrivacyLens Sanitizer Pipeline."""
import time
from typing import Tuple, List, Dict, Optional
from app.models import (
    RawObservation, SanitizedObservation, SanitizedElement,
    SensitiveSpan, DOMElement
)
from app.privacy.detectors.engine import DetectionEngine
from app.privacy.screenshot import ScreenshotSanitizer

class SanitizerPipeline:
    def __init__(self, detector_engine: Optional[DetectionEngine] = None, screenshot_sanitizer: Optional[ScreenshotSanitizer] = None):
        self.detector = detector_engine or DetectionEngine()
        self.screenshot_sanitizer = screenshot_sanitizer or ScreenshotSanitizer()
        
        # Local in-memory store for before/after preview (TTL cached, discarded on session close)
        # run_id -> { "raw_bytes": ..., "sanitized_bytes": ..., "spans": [...], "created_at": ... }
        self._local_preview_cache: Dict[str, dict] = {}

    def sanitize(
        self,
        raw_obs: RawObservation,
        device_scale_factor: float = 1.0
    ) -> Tuple[SanitizedObservation, List[SensitiveSpan], Optional[bytes]]:
        """
        Executes complete privacy sanitization:
        1. Analyzes DOM structurally and textually
        2. Applies solid opaque pixel masks to screenshot
        3. Reconstructs safe allowlisted SanitizedObservation
        4. Caches local-only original and sanitized previews
        """
        # 1. Run detection engine on DOM elements
        spans, element_sanitized_map = self.detector.analyze_dom(raw_obs.elements)

        # 2. Build sanitized elements allowlist
        sanitized_elements: List[SanitizedElement] = []
        redactions_summary: Dict[str, int] = {}
        for s in spans:
            cat = s.category.value
            redactions_summary[cat] = redactions_summary.get(cat, 0) + 1

        for el in raw_obs.elements:
            clean_text = element_sanitized_map.get(el.id, el.text)
            clean_label = el.label
            # Sanitize label if present
            if clean_label:
                label_spans = self.detector.scan_text(clean_label)
                for ls in label_spans:
                    clean_label = clean_label.replace(ls.text or "", ls.replacement_token)

            sanitized_elements.append(SanitizedElement(
                id=el.id,
                role=el.role,
                label=clean_label,
                sanitized_text=clean_text,
                is_interactive=el.is_interactive,
                bbox=el.bbox,
            ))

        # 3. Screenshot sanitization (solid pixel masks)
        sanitized_screenshot_bytes: Optional[bytes] = None
        provenance_hash = "no_screenshot"
        screenshot_token = None

        if raw_obs.screenshot_bytes:
            sanitized_screenshot_bytes, provenance_hash, _ = self.screenshot_sanitizer.sanitize_screenshot(
                image_bytes=raw_obs.screenshot_bytes,
                spans=spans,
                device_scale_factor=device_scale_factor
            )
            screenshot_token = f"token_{provenance_hash[:16]}"

        # 4. Construct outbound safe observation
        sanitized_obs = SanitizedObservation(
            run_id=raw_obs.run_id,
            page_origin=raw_obs.page_origin,
            page_title=raw_obs.page_title,
            elements=sanitized_elements,
            redactions_summary=redactions_summary,
            sanitized_screenshot_token=screenshot_token,
            provenance_hash=provenance_hash,
        )

        # 5. Store preview strictly in local memory with timestamp
        self._local_preview_cache[raw_obs.run_id] = {
            "raw_bytes": raw_obs.screenshot_bytes,
            "sanitized_bytes": sanitized_screenshot_bytes,
            "spans": spans,
            "created_at": time.time(),
        }

        return sanitized_obs, spans, sanitized_screenshot_bytes

    def get_local_preview(self, run_id: str) -> Optional[dict]:
        """Provides preview exclusively to authenticated local user interface."""
        return self._local_preview_cache.get(run_id)

    def clear_preview(self, run_id: str):
        self._local_preview_cache.pop(run_id, None)
