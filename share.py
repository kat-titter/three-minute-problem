#!/usr/bin/env python3
"""Tab icon and share card. build.py stamps head() into index.html; `python3 share.py` redraws the two PNGs.

share/icon.svg is the one home of the icon: the tab icon is inlined from it and the 180 px touch icon drawn from it.
share/card.html is the 1200 x 630 share card's source. Redrawing needs Google Chrome; building does not.
"""
import subprocess, urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://kat-titter.github.io/three-minute-problem/"
ALT = "Breathing stops. You have three minutes. The Three-Minute Problem, a case for carrying Narcan."
TOUCH_BG = "#ffffff"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def head():
    """The icon, touch-icon and share-card tags for the page head."""
    svg = (ROOT / "share/icon.svg").read_text().strip().replace('"', "'")
    icon = "data:image/svg+xml," + urllib.parse.quote(svg, safe=" ='/:;,.-()")
    card = SITE + "share/card.png"
    return "\n".join([
        f'<link rel="icon" href="{icon}">',
        '<link rel="apple-touch-icon" href="share/apple-touch-icon.png">',
        f'<meta property="og:image" content="{card}">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{ALT}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image" content="{card}">',
    ])


def shot(page, png, w, h):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--virtual-time-budget=8000", f"--window-size={w},{h}", f"--screenshot={png}", page.as_uri()],
                   check=True, capture_output=True)


def render():
    """Redraw share/apple-touch-icon.png (180 px, opaque, iOS rounds the corners) and share/card.png."""
    tmp = ROOT / "share/.touch.html"
    tmp.write_text(f'<body style="margin:0;background:{TOUCH_BG}">{(ROOT / "share/icon.svg").read_text()}'
                   '<style>svg{display:block;width:180px;height:180px}</style>')
    try:
        shot(tmp, ROOT / "share/apple-touch-icon.png", 180, 180)
    finally:
        tmp.unlink()
    shot(ROOT / "share/card.html", ROOT / "share/card.png", 1200, 630)
    for p in ("apple-touch-icon.png", "card.png"):
        print(f"share/{p}: {(ROOT / 'share' / p).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    render()
