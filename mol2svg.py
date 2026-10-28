#!/usr/bin/env python3
"""Draw PubChem 2D SDF records as deck-styled SVG.

- One bond length per figure, passed in px, so molecules on a slide compare honestly.
- Bonds use currentColor; highlights are opaque shapes inside a group with opacity, so overlaps never darken.
- Bonds stop at the edge of each atom label's box, so labels never touch bonds.
"""
import math
from pathlib import Path

SDF = Path(__file__).parent / "mol" / "sdf"
VALENCE = {"N": 3, "O": 2, "S": 2}


def load(name):
    L = (SDF / f"{name}.sdf").read_text().split("\n")
    na, nb = int(L[3][:3]), int(L[3][3:6])
    atoms = []
    for i in range(na):
        l = L[4 + i]
        atoms.append({"x": float(l[0:10]), "y": -float(l[10:20]), "el": l[31:34].strip()})
    bonds = []
    for i in range(nb):
        l = L[4 + na + i]
        a, b, o, st = int(l[0:3]) - 1, int(l[3:6]) - 1, int(l[6:9]), int(l[9:12])
        bonds.append((a, b, o, st))
    for l in L[4 + na + nb:]:
        if l.startswith("M  CHG"):
            f = l.split()[3:]
            for j in range(0, len(f), 2):
                atoms[int(f[j]) - 1]["chg"] = int(f[j + 1])
    keep = [i for i, a in enumerate(atoms) if a["el"] != "H"]
    idx = {o: n for n, o in enumerate(keep)}
    atoms = [atoms[i] for i in keep]
    bonds = [(idx[a], idx[b], o, st) for a, b, o, st in bonds if a in idx and b in idx]
    return Mol(atoms, bonds)


class Mol:
    def __init__(self, atoms, bonds):
        self.atoms, self.bonds = atoms, bonds
        self.nb = {i: [] for i in range(len(atoms))}
        for a, b, o, _ in bonds:
            self.nb[a].append((b, o))
            self.nb[b].append((a, o))
        self.rings = self._rings()

    def _rings(self, maxlen=7):
        rings = set()
        for s in range(len(self.atoms)):
            stack = [(s, [s])]
            while stack:
                cur, path = stack.pop()
                for n, _ in self.nb[cur]:
                    if n == s and len(path) > 2:
                        rings.add(frozenset(path))
                    elif n not in path and len(path) < maxlen and n > s:
                        stack.append((n, path + [n]))
        rings = sorted(rings, key=len)
        out = []
        for r in rings:
            if not any(o < r for o in out):
                out.append(r)
        return out

    def rotate(self, deg):
        a = math.radians(deg)
        for at in self.atoms:
            x, y = at["x"], at["y"]
            at["x"], at["y"] = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        return self

    def flip(self):
        for at in self.atoms:
            at["x"] = -at["x"]
        # wedge/hash meaning is preserved under a mirror only if swapped; we draw stereo marks as given
        self.bonds = [(a, b, o, {1: 6, 6: 1}.get(st, st)) for a, b, o, st in self.bonds]
        return self

    def hcount(self, i):
        el = self.atoms[i]["el"]
        if el not in VALENCE:
            return 0
        chg = self.atoms[i].get("chg", 0)
        val = VALENCE[el] + (chg if el == "N" else chg)  # N+ takes 4 bonds; O- takes 1
        return max(0, val - sum(o for _, o in self.nb[i]))

    def aromatic(self, i):
        for r in self.rings:
            if i in r and len(r) == 6:
                dbl = sum(1 for a, b, o, _ in self.bonds if o == 2 and a in r and b in r)
                if dbl == 3:
                    return r
        return None

    def phenol_O(self):
        for i, a in enumerate(self.atoms):
            if a["el"] == "O" and self.hcount(i) == 1 and len(self.nb[i]) == 1 and self.aromatic(self.nb[i][0][0]):
                return i
        return None

    def basic_N(self):
        """sp3 amine nitrogen not attached to a carbonyl carbon or an aromatic ring."""
        best = None
        for i, a in enumerate(self.atoms):
            if a["el"] != "N" or any(o > 1 for _, o in self.nb[i]):
                continue
            amide = any(
                self.atoms[n]["el"] == "C" and any(self.atoms[m]["el"] == "O" and o == 2 for m, o in self.nb[n])
                for n, _ in self.nb[i]
            )
            arom = any(self.aromatic(n) for n, _ in self.nb[i])
            if not amide and not arom:
                best = i
        return best


def ring_bonds(mol, ring):
    return [(a, b) for a, b, _, _ in mol.bonds if a in ring and b in ring]


def draw(mol, bond=22, hl_atoms=(), hl_bonds=(), hl_rings=(), red_atoms=(), callouts=(), pad=10):
    """Return an inline SVG string.

    hl_*: yellow highlight (rings drawn as filled polygons); red_atoms: red highlight (atoms + bonds between them).
    callouts: (atom, dx, dy, [lines], anchor) in px relative to the atom; first line bold red, rest muted.
    """
    lens = [math.dist((mol.atoms[a]["x"], mol.atoms[a]["y"]), (mol.atoms[b]["x"], mol.atoms[b]["y"])) for a, b, _, _ in mol.bonds]
    unit = sorted(lens)[len(lens) // 2]
    k = bond / unit
    xs = [a["x"] for a in mol.atoms]
    ys = [a["y"] for a in mol.atoms]
    P = [((a["x"] - min(xs)) * k, (a["y"] - min(ys)) * k) for a in mol.atoms]
    fs = max(10.0, min(13.0, bond * 0.56))
    cw = fs * 0.62  # DM Mono advance width

    labels = {}
    for i, a in enumerate(mol.atoms):
        if a["el"] != "C":
            h = mol.hcount(i)
            chg = a.get("chg", 0)
            el = a["el"] + ("⁺" if chg == 1 else "⁻" if chg == -1 else "")
            labels[i] = (el, "H" if h == 1 else "H₂" if h == 2 else "H₃" if h == 3 else "")

    # text boxes are taller below the atom centre than above it (descender space in the em box)
    up_h, down_h = fs * 0.64 + 1.0, fs * 0.86 + 1.0

    def trim_pt(i, dx, dy):
        """distance from atom i along (dx, dy) to the edge of its label box (0 for unlabelled carbons)."""
        if i not in labels:
            return 0.0
        hw = cw * len(labels[i][0]) / 2 + 1.5
        hh = down_h if dy > 0 else up_h
        tx = hw / abs(dx) if abs(dx) > 1e-6 else 1e9
        ty = hh / abs(dy) if abs(dy) > 1e-6 else 1e9
        return min(tx, ty)

    hl, red, bonds_svg, text, call = [], [], [], [], []
    bx = [p[0] for p in P]
    by = [p[1] for p in P]

    # --- highlights
    r_hl = bond * 0.36
    for ring in hl_rings:
        order = sorted(ring, key=lambda i: math.atan2(P[i][1] - sum(P[j][1] for j in ring) / len(ring), P[i][0] - sum(P[j][0] for j in ring) / len(ring)))
        pts = " ".join(f"{P[i][0]:.1f},{P[i][1]:.1f}" for i in order)
        hl.append(f'<polygon points="{pts}" stroke="var(--hlc)" stroke-width="{r_hl*2:.1f}" stroke-linejoin="round"/>')
    for a, b in hl_bonds:
        hl.append(f'<path d="M{P[a][0]:.1f} {P[a][1]:.1f}L{P[b][0]:.1f} {P[b][1]:.1f}" stroke="var(--hlc)" stroke-width="{r_hl*2:.1f}" stroke-linecap="round"/>')
    for i in hl_atoms:
        hl.append(f'<circle cx="{P[i][0]:.1f}" cy="{P[i][1]:.1f}" r="{r_hl*1.25:.1f}"/>')
    rs = set(red_atoms)
    for a, b, _, _ in mol.bonds:
        if a in rs and b in rs:
            red.append(f'<path d="M{P[a][0]:.1f} {P[a][1]:.1f}L{P[b][0]:.1f} {P[b][1]:.1f}" stroke="var(--hlrc)" stroke-width="{r_hl*2:.1f}" stroke-linecap="round"/>')
    for i in rs:
        red.append(f'<circle cx="{P[i][0]:.1f}" cy="{P[i][1]:.1f}" r="{r_hl*1.1:.1f}"/>')

    # --- bonds: every drawn line is trimmed where it leaves an atom label's box
    def exit_dist(i, sx, sy, ux, uy):
        if i not in labels:
            return 0.0
        cx, cy = P[i]
        hw = cw * len(labels[i][0]) / 2 + 1.5
        left, right, top_, bot = cx - hw, cx + hw, cy - up_h, cy + down_h
        if not (left < sx < right and top_ < sy < bot):
            return 0.0
        tx = ((right - sx) / ux if ux > 0 else (left - sx) / ux) if abs(ux) > 1e-9 else 1e9
        ty = ((bot - sy) / uy if uy > 0 else (top_ - sy) / uy) if abs(uy) > 1e-9 else 1e9
        return min(tx, ty)

    def seg(a, b, x1, y1, x2, y2):
        L = math.dist((x1, y1), (x2, y2)) or 1
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        t1 = exit_dist(a, x1, y1, ux, uy)
        t2 = exit_dist(b, x2, y2, -ux, -uy)
        if t1 + t2 >= L - 1:
            return None
        return x1 + ux * t1, y1 + uy * t1, x2 - ux * t2, y2 - uy * t2

    def line(a, b, x1, y1, x2, y2, extra=""):
        s = seg(a, b, x1, y1, x2, y2)
        if s:
            bonds_svg.append(f'<path d="M{s[0]:.1f} {s[1]:.1f}L{s[2]:.1f} {s[3]:.1f}"{extra}/>')

    for a, b, o, st in mol.bonds:
        (x1, y1), (x2, y2) = P[a], P[b]
        d = math.dist(P[a], P[b]) or 1
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        nx, ny = -uy, ux
        if o == 1 and st in (1, 6):
            s = seg(a, b, x1, y1, x2, y2)
            if not s:
                continue
            sx, sy, ex, ey = s
            w = bond * 0.13
            if st == 1:  # wedge
                bonds_svg.append(f'<path d="M{sx:.1f} {sy:.1f}L{ex+nx*w:.1f} {ey+ny*w:.1f}L{ex-nx*w:.1f} {ey-ny*w:.1f}Z" fill="currentColor" stroke="none"/>')
            else:  # hash
                for n in range(1, 7):
                    tt = n / 6
                    cx, cy = sx + (ex - sx) * tt, sy + (ey - sy) * tt
                    bonds_svg.append(f'<path d="M{cx+nx*w*tt:.1f} {cy+ny*w*tt:.1f}L{cx-nx*w*tt:.1f} {cy-ny*w*tt:.1f}" stroke-width="1.1"/>')
            continue
        if o == 1:
            line(a, b, x1, y1, x2, y2)
            continue
        if o == 3:
            off = bond * 0.14
            for s in (-1, 0, 1):
                line(a, b, x1 + nx * off * s, y1 + ny * off * s, x2 + nx * off * s, y2 + ny * off * s)
            continue
        # double bond
        ring = next((r for r in mol.rings if a in r and b in r), None)
        off = bond * 0.17
        if ring:
            cx = sum(P[i][0] for i in ring) / len(ring)
            cy = sum(P[i][1] for i in ring) / len(ring)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            side = 1 if (cx - mx) * nx + (cy - my) * ny > 0 else -1
            sh = 0.15 * d
            line(a, b, x1, y1, x2, y2)
            line(a, b, x1 + ux * sh + nx * off * side, y1 + uy * sh + ny * off * side, x2 - ux * sh + nx * off * side, y2 - uy * sh + ny * off * side)
        elif a in labels or b in labels or len(mol.nb[a]) == 1 or len(mol.nb[b]) == 1:
            for s in (-0.5, 0.5):
                line(a, b, x1 + nx * off * s, y1 + ny * off * s, x2 + nx * off * s, y2 + ny * off * s)
        else:
            side = 1
            subs = [P[n] for n, _ in mol.nb[a] + mol.nb[b] if n not in (a, b)]
            if subs:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                side = 1 if sum((px - mx) * nx + (py - my) * ny for px, py in subs) > 0 else -1
            sh = 0.12 * d
            line(a, b, x1, y1, x2, y2)
            line(a, b, x1 + ux * sh + nx * off * side, y1 + uy * sh + ny * off * side, x2 - ux * sh + nx * off * side, y2 - uy * sh + ny * off * side)

    # --- atom labels: element centred on the atom, H on the side away from the neighbours
    for i, (el, hs) in labels.items():
        x, y = P[i]
        base = y + fs * 0.36
        text.append(f'<text x="{x:.1f}" y="{base:.1f}" text-anchor="middle" font-size="{fs:.1f}" font-weight="500" fill="currentColor">{el}</text>')
        bx += [x - cw * len(el) / 2, x + cw * len(el) / 2]
        by += [y - fs * 0.64, y + fs * 0.86]
        if hs:
            dirs = [(-(P[n][0] - x), -(P[n][1] - y)) for n, _ in mol.nb[i]]
            angs = [math.atan2(-dy_, -dx_) for dx_, dy_ in dirs]  # angles of the bonds leaving the atom

            def clearance(a):
                return min((abs((a - b + math.pi) % (2 * math.pi) - math.pi) for b in angs), default=math.pi)
            cands = [(0.0, "right"), (math.pi, "left"), (-math.pi / 2, "up"), (math.pi / 2, "down")]
            best = max(cands, key=lambda c: (round(clearance(c[0]), 2), c[1] == "right", c[1] == "left"))[1]
            w_el = cw * len(el) / 2
            if best in ("right", "left"):
                hx = x + w_el if best == "right" else x - w_el
                anchor = "start" if best == "right" else "end"
                text.append(f'<text x="{hx:.1f}" y="{base:.1f}" text-anchor="{anchor}" font-size="{fs:.1f}" font-weight="500" fill="currentColor">{hs}</text>')
                wh = cw * len(hs)
                bx += [hx - wh, hx + wh]
            else:
                hy = base + (fs * 1.56 if best == "down" else -fs * 1.56)
                text.append(f'<text x="{x:.1f}" y="{hy:.1f}" text-anchor="middle" font-size="{fs:.1f}" font-weight="500" fill="currentColor">{hs}</text>')
                by += [hy - fs * 1.0, hy + fs * 0.5]

    # --- callouts
    for atom, dx, dy, lines, anchor in callouts:
        x, y = P[atom]
        ex, ey = x + dx, y + dy
        d = math.dist((x, y), (ex, ey)) or 1
        start = bond * 0.5
        sx, sy = x + (ex - x) / d * start, y + (ey - y) / d * start
        call.append(f'<path d="M{sx:.1f} {sy:.1f}L{ex:.1f} {ey:.1f}" stroke="var(--callout)" stroke-width="1.4" fill="none"/>')
        call.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="2.6" fill="var(--callout)"/>')
        gap = 7
        tx = ex + (gap if anchor == "start" else -gap if anchor == "end" else 0)
        if anchor == "middle":
            ty0 = ey - 9 - 20 * (len(lines) - 1) if dy < 0 else ey + 19
        else:
            ty0 = ey + 4.5
        for n, line in enumerate(lines):
            w = "600" if n == 0 else "400"
            col = "var(--callout)" if n == 0 else "var(--calloutmute)"
            fsz = 13 if n == 0 else 12
            call.append(f'<text x="{tx:.1f}" y="{ty0 + n*20:.1f}" text-anchor="{anchor}" font-size="{fsz}" font-weight="{w}" fill="{col}">{line}</text>')
            width = len(line) * fsz * 0.62
            x0 = tx if anchor == "start" else tx - width if anchor == "end" else tx - width / 2
            bx += [x0, x0 + width]
            by += [ty0 + n * 20 - 13, ty0 + n * 20 + 7]
        bx.append(ex)
        by.append(ey)

    x0, y0 = min(bx) - pad, min(by) - pad
    W, H = max(bx) - x0 + pad, max(by) - y0 + pad
    inner = (
        f'<g class="hl" fill="var(--hlc)" style="opacity:var(--hlo)" data-bg="1">{"".join(hl)}</g>'
        f'<g class="hl" fill="var(--hlrc)" style="opacity:var(--hlo)" data-bg="1">{"".join(red)}</g>'
        f'<g stroke="currentColor" stroke-width="1.6" stroke-linecap="round" fill="none">{"".join(bonds_svg)}</g>'
        f'<g>{"".join(text)}{"".join(call)}</g>'
    )
    return {"inner": inner, "box": (x0, y0, W, H), "P": P, "fs": fs}


def svg(mol, bond=22, hl_atoms=(), hl_bonds=(), hl_rings=(), red_atoms=(), callouts=(), pad=10, cls="mol", label=None):
    d = draw(mol, bond, hl_atoms, hl_bonds, hl_rings, red_atoms, callouts, pad)
    x0, y0, W, H = d["box"]
    aria = f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    return (f'<svg class="{cls}" xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {W:.0f} {H:.0f}" '
            f'width="{W:.0f}" height="{H:.0f}"{aria}>{d["inner"]}</svg>')
