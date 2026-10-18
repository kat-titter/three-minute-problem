#!/usr/bin/env python3
"""Inline molecule figures (mols.py, drawn from PubChem 2D records) into index.html."""
import re
from pathlib import Path
from mols import build

root = Path(__file__).parent
F = build()
src = (root / "index.src.html").read_text()
out = re.sub(r"\{\{mol:(\w+)\}\}", lambda m: F[m.group(1)], src)
assert "{{" not in out, "unfilled placeholder"
(root / "index.html").write_text(out)
print(f"index.html: {len(out):,} bytes")
