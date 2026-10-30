"""Local DOM observation collector."""
import time
import urllib.parse
from typing import List, Tuple
from playwright.async_api import Page
from app.models import DOMElement, BoundingBox, RawObservation

EXTRACT_DOM_SCRIPT = """
() => {
    const elements = [];
    const selector = 'input, button, select, textarea, a, [role="button"], [role="link"], [role="checkbox"], [tabindex], .video-tile, .video-stream, video, .chat-message, .chat-bubble, .participant-name, .user-badge, iframe, canvas, [contenteditable], h1, h2, h3, p, span, td, label, .key-val, code, pre, svg text, .hidden-secret';
    const nodes = document.querySelectorAll(selector);
    
    let counter = 1;
    nodes.forEach(node => {
        const tag = (node.tagName || '').toLowerCase();
        const style = window.getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        const isHidden = (style.display === 'none' || style.visibility === 'hidden' || (rect.width === 0 && rect.height === 0));
        
        const text = (node.innerText || node.textContent || '').trim();
        const value = (node.value !== undefined && typeof node.value === 'string') ? node.value : '';

        // If hidden and has neither text nor value nor special tag, skip
        if (isHidden && !text && !value && tag !== 'canvas' && tag !== 'iframe') {
            return;
        }
        
        const elemId = `elem_${counter++}`;
        node.setAttribute('data-privacylens-id', elemId);
        
        const role = node.getAttribute('role') || '';
        const type = node.getAttribute('type') || '';
        const name = node.getAttribute('name') || '';
        const placeholder = node.getAttribute('placeholder') || '';
        
        // Find associated label if input
        let labelText = node.getAttribute('aria-label') || '';
        if (!labelText && node.id) {
            const labelEl = document.querySelector(`label[for="${node.id}"]`);
            if (labelEl) labelText = labelEl.innerText.trim();
        }
        if (!labelText && node.closest('label')) {
            labelText = node.closest('label').innerText.trim();
        }

        const isInteractive = ['input', 'button', 'select', 'textarea', 'a'].includes(tag) ||
                              role === 'button' || role === 'link' || node.hasAttribute('tabindex');

        const classVal = (typeof node.className === 'string') ? node.className : (node.getAttribute('class') || '');
        const idVal = (typeof node.id === 'string') ? node.id : (node.getAttribute('id') || '');
        const autocompleteVal = node.getAttribute('autocomplete') || '';

        elements.push({
            id: elemId,
            tag: tag,
            role: role || (isInteractive ? tag : null),
            type: type || null,
            name: name || null,
            placeholder: placeholder || null,
            label: labelText || null,
            text: text,
            value: value,
            is_interactive: isInteractive,
            is_sensitive: false,
            bbox: {
                x: isHidden ? 0 : rect.x,
                y: isHidden ? 0 : rect.y,
                width: isHidden ? 0 : rect.width,
                height: isHidden ? 0 : rect.height
            },
            attributes: {
                id: idVal,
                class: classVal,
                autocomplete: autocompleteVal,
                is_hidden: isHidden ? "true" : "false"
            }
        });
    });
    
    return {
        url: window.location.href,
        title: document.title,
        elements: elements
    };
}
"""

class DOMCollector:
    async def collect_observation(self, page: Page, run_id: str) -> RawObservation:
        """
        Collects live DOM elements and screenshot strictly into trusted local memory.
        """
        # Execute DOM element extraction script
        raw_data = await page.evaluate(EXTRACT_DOM_SCRIPT)
        
        page_url = raw_data["url"]
        parsed_url = urllib.parse.urlparse(page_url)
        page_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        page_title = raw_data["title"]
        
        dom_elements: List[DOMElement] = []
        for item in raw_data["elements"]:
            bbox_dict = item.get("bbox")
            bbox = BoundingBox(**bbox_dict) if bbox_dict else None
            dom_elements.append(DOMElement(
                id=item["id"],
                tag=item["tag"],
                role=item.get("role"),
                type=item.get("type"),
                name=item.get("name"),
                label=item.get("label"),
                text=item.get("text", ""),
                value=item.get("value", ""),
                placeholder=item.get("placeholder"),
                is_interactive=item.get("is_interactive", False),
                bbox=bbox,
                attributes=item.get("attributes", {})
            ))

        # Capture screenshot in local memory
        screenshot_bytes = await page.screenshot(type="png", full_page=False)

        return RawObservation(
            run_id=run_id,
            page_url=page_url,
            page_origin=page_origin,
            page_title=page_title,
            elements=dom_elements,
            screenshot_bytes=screenshot_bytes,
            timestamp=time.time(),
        )
