#!/usr/bin/env python3
"""Inline molecule figures (mols.py, drawn from PubChem 2D records) and the share tags (share.py) into index.html."""
import re
from pathlib import Path
from mols import build
from share import head

root = Path(__file__).parent
F = build()
src = (root / "index.src.html").read_text()
out = re.sub(r"\{\{mol:(\w+)\}\}", lambda m: F[m.group(1)], src)
out = out.replace("<!-- share --><!-- /share -->", head())
assert "{{" not in out and "<!-- share -->" not in out, "unfilled placeholder"
(root / "index.html").write_text(out)
print(f"index.html: {len(out):,} bytes")
