"""
Tests for Phase 6: Frontend polish and accessibility.

Covers:
- Image alt text, dimensions (width, height, aspect ratio)
- Aria labels on interactive elements (chat launcher, mic, send, close, hero buttons)
- Aria live regions on chat messages
- Teaser bubble elements in chat widget
- Prefers-reduced-motion CSS rules present in custom.css
- Focus-visible styles defined
"""

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())


def test_images_have_dimensions_and_alt():
    """Verify that images in rendered index have width, height, and non-empty alt text."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Hero image checks
    assert 'alt="Sheikh Haseeb"' in html
    assert 'width="320"' in html
    assert 'height="320"' in html

    # Logo checks
    assert 'alt="Logo"' in html
    assert 'width="36"' in html
    assert 'height="36"' in html


def test_accessibility_aria_attributes():
    """Verify that icon buttons and interactive elements have appropriate aria labels."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Chat launcher
    assert 'id="chat-launcher"' in html
    assert 'aria-label="Open Haze"' in html or 'aria-label="Open' in html
    assert 'aria-haspopup="dialog"' in html

    # Chat close button
    assert 'id="chat-close"' in html
    assert 'aria-label="Close chat"' in html

    # Chat send button
    assert 'id="chat-send"' in html
    assert 'aria-label="Send message"' in html

    # Chat mic button
    assert 'id="chat-mic"' in html
    assert 'aria-label="Speak your question"' in html

    # Chat messages aria-live region
    assert 'id="chat-messages"' in html
    assert 'aria-live="polite"' in html


def test_teaser_bubble_present_in_template():
    """Verify that the auto-teaser markup exists with dismiss button."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert 'id="chat-teaser"' in html
    assert "Ask me about Haseeb's projects!" in html
    assert 'id="chat-teaser-close"' in html
    assert 'aria-label="Dismiss message"' in html


def test_css_accessibility_and_motion_rules():
    """Verify custom.css contains prefers-reduced-motion and focus-visible declarations."""
    css_path = Path(__file__).resolve().parent.parent / "app" / "static" / "css" / "custom.css"
    content = css_path.read_text(encoding="utf-8")

    # prefers-reduced-motion media query
    assert "@media (prefers-reduced-motion: reduce)" in content
    assert "animation-duration: 0.01ms !important" in content

    # focus visible rules
    assert ":focus-visible" in content
    assert "outline: 2px solid var(--accent)" in content

    # Teaser styles
    assert ".chat-teaser" in content
    assert ".chat-teaser-bubble" in content
