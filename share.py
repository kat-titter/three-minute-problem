#!/usr/bin/env python3
"""Redraw the touch icon and share card PNGs with headless Chrome: `python3 share.py`.

index.src.html links share/icon.svg as the tab icon; the 180 px touch icon is drawn from the same file.
share/card.html is the 1200 x 630 share card's source.
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
TOUCH_BG = "#ffffff"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CARD_W, CARD_H = 1200, 630  # the og:image size in index.src.html; card.html is laid out at this size
TOUCH_PX = 180  # the apple-touch-icon size
FONT_WAIT_MS = 8000  # virtual time for the card's Google Fonts to load before the screenshot


def screenshot(page, png_path, width_px, height_px):
    """Draw one local HTML page to a PNG with headless Chrome; on failure, show Chrome's own error."""
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        f"--virtual-time-budget={FONT_WAIT_MS}", f"--window-size={width_px},{height_px}",
                        f"--screenshot={png_path}", page.as_uri()], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"Chrome failed on {page.name}:\n{r.stderr}")


def render():
    """Redraw share/apple-touch-icon.png (180 px, opaque, iOS rounds the corners) and share/card.png."""
    tmp = ROOT / "share/.touch.html"
    tmp.write_text(f'<body style="margin:0;background:{TOUCH_BG}">{(ROOT / "share/icon.svg").read_text()}'
                   f'<style>svg{{display:block;width:{TOUCH_PX}px;height:{TOUCH_PX}px}}</style>')
    try:
        screenshot(tmp, ROOT / "share/apple-touch-icon.png", TOUCH_PX, TOUCH_PX)
    finally:
        tmp.unlink()
    screenshot(ROOT / "share/card.html", ROOT / "share/card.png", CARD_W, CARD_H)
    for p in ("apple-touch-icon.png", "card.png"):
        print(f"share/{p}: {(ROOT / 'share' / p).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    render()
