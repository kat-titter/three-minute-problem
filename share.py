#!/usr/bin/env python3
"""Redraw the touch icon and share card PNGs with headless Chrome: `python3 share.py`.

index.src.html links share/icon.svg as the tab icon; the 180 px touch icon is drawn from the same file.
share/card.html is the 1200 x 630 share card's source. Needs Google Chrome and a network connection (the card loads Google Fonts).
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).parent
TOUCH_BG = "#ffffff"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CARD_W, CARD_H = 1200, 630  # must match card.html's CSS and the og:image size tags
TOUCH_PX = 180  # the apple-touch-icon size
FONT_WAIT_MS = 8000  # virtual time for the card's Google Fonts to load; offline, the card falls back to system fonts


def screenshot(page, png_path, width_px, height_px):
    """Draw one local HTML page to a PNG with headless Chrome, or stop with Chrome's own error and keep the old PNG.

    Chrome can exit 0 without writing a file, so it draws to a fresh temp path that must exist before it replaces png_path.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / png_path.name
        r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            f"--virtual-time-budget={FONT_WAIT_MS}", f"--window-size={width_px},{height_px}",
                            f"--screenshot={tmp}", page.as_uri()], capture_output=True, text=True)
        if r.returncode or not tmp.exists():
            sys.exit(f"Chrome drew no {png_path.name} from {page.name} (exit {r.returncode}):\n{r.stderr}")
        shutil.move(tmp, png_path)
    print(f"{png_path.relative_to(ROOT)}: {png_path.stat().st_size / 1024:.0f} KB")


def render():
    """Redraw share/apple-touch-icon.png (180 px, opaque, iOS rounds the corners) and share/card.png."""
    with tempfile.TemporaryDirectory() as d:  # the touch page inlines the icon, so it can live outside the repo
        tmp = Path(d) / "touch.html"
        tmp.write_text(f'<body style="margin:0;background:{TOUCH_BG}">{(ROOT / "share/icon.svg").read_text()}'
                       f'<style>svg{{display:block;width:{TOUCH_PX}px;height:{TOUCH_PX}px}}</style>')
        screenshot(tmp, ROOT / "share/apple-touch-icon.png", TOUCH_PX, TOUCH_PX)
    screenshot(ROOT / "share/card.html", ROOT / "share/card.png", CARD_W, CARD_H)


if __name__ == "__main__":
    render()
