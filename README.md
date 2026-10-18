# The Three-Minute Problem

**Read the deck: https://kat-titter.github.io/three-minute-problem/**
PDF: the latest build is attached to the newest [release](https://github.com/kat-titter/three-minute-problem/releases) (or print the web deck: one slide per page).

A case for carrying Narcan (naloxone) at Black Rock City and on every dance floor, in 22 slides:
the problem, the biology of opioids and how naloxone reverses an overdose, what is in counterfeit
pills now, the Black Rock City case study (coverage math for a city of 71,500), and the plan:
two kits and a sober carrier per camp, stage and art car, one in four pockets, say who carries.

Companion site, updated weekly: [Overdose Watch](https://kat-titter.github.io/overdose-watch/),
official overdose death counts and sourced reports for the Bay Area, California and Nevada.

## Build

`index.html` is generated. Edit `index.src.html` and run:

```bash
python3 build.py
```

`build.py` fills each `{{mol:name}}` placeholder with an SVG drawn by `mol2svg.py` (2D structures
from the PubChem SDF files in `mol/sdf/`) and `locks.py` (receptor lock-and-key and pocket figures).
Standard library only; no packages to install.

The web page has print styles: in Chrome, Print → Save as PDF gives one 1280×720 slide per page
plus a sources page.

## Sources

Listed on each slide and on the final sources page. Structures: PubChem 2D coordinates. Receptor
contacts: Manglik et al. 2012 and Huang et al. 2015 (mu-opioid receptor, Nature). Figs 3 and 12 are
illustrative models, not patient data. The effigy glyph is an original drawing, not the Burning Man logo.

This is harm-reduction education, not medical advice. If someone is unresponsive, call 911.

Kat Titterton, San Francisco.
