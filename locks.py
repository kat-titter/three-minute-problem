"""Lock-and-key figures: a drug drawn inside its receptor's pocket, contacts drawn to named residues.

Top-down views (looking down on the cell from outside):
- GPCR (mu-opioid, alpha2-adrenergic): seven helices in a ring around the pocket.
- GABA-A: five subunits around the chloride pore; benzodiazepines bind at the alpha1/gamma2 seam.
Side view (Narcan slide): the pocket's two walls (helix 3, helix 6) and its floor (Trp293, the toggle).

Residue positions are schematic; which residue each group touches follows the receptor structures
(mu: Asp147, His297, Trp293; alpha2A: Asp113; GABA-A alpha1: His101).
"""
import math
from mol2svg import load, draw

INK, BODY, MUTE, RED, YEL, YELD = "#1a1517", "#3d3739", "#655e60", "#c8102e", "#ffe36e", "#9a7b00"
YELT = "#6f5900"  # yellow-family text dark enough for 4.5:1 on the panel
HELIX, HELIX_D = "#ddd5d7", "#b9aeb1"


def _angle(p, c):
    return math.atan2(p[1] - c[1], p[0] - c[0])


def orient(name, bond, goals, flips=True):
    """Rotate (and mirror) the molecule so atoms point where `goals` asks.

    goals: list of (atom, target_angle_radians, weight) measured from the molecule's centroid (screen coords).
    Mirroring keeps chirality (flip() swaps wedges and hashes).
    """
    best = None
    for flip in ([False, True] if flips else [False]):
        for deg in range(0, 360, 5):
            m = load(name)
            if flip:
                m.flip()
            m.rotate(deg)
            xs = [a["x"] for a in m.atoms]
            ys = [a["y"] for a in m.atoms]
            c = (sum(xs) / len(xs), sum(ys) / len(ys))
            score = 0.0
            for atom, ang, w in goals:
                a = math.atan2(m.atoms[atom]["y"] - c[1], m.atoms[atom]["x"] - c[0])
                score += w * math.cos(a - ang)
            if best is None or score > best[0]:
                best = (score, flip, deg)
    m = load(name)
    if best[1]:
        m.flip()
    m.rotate(best[2])
    return m


def _place(d, cx, cy):
    """translate a draw() result so its box is centred on (cx, cy); return markup and atom positions."""
    x0, y0, W, H = d["box"]
    tx, ty = cx - (x0 + W / 2), cy - (y0 + H / 2)
    P = [(x + tx, y + ty) for x, y in d["P"]]
    return f'<g transform="translate({tx:.1f} {ty:.1f})">{d["inner"]}</g>', P


def _txt(x, y, s, size=12, fill=MUTE, weight=400, anchor="start"):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>'


def _contact(p, q, kind, gap=None):
    """dashed contact line from atom position p to residue point q."""
    if gap is None:
        gap = 21 if kind == "hbond" else 10  # an O-H contact starts past the H label
    d = math.dist(p, q) or 1
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    sx, sy = p[0] + ux * gap, p[1] + uy * gap
    col = {"salt": RED, "hbond": YELD, "contact": MUTE, "clash": RED}[kind]
    dash = {"salt": "5 4", "hbond": "2 4", "contact": "2 4", "clash": "0"}[kind]
    w = 2.2 if kind in ("salt", "clash") else 2
    return f'<path d="M{sx:.1f} {sy:.1f}L{q[0]:.1f} {q[1]:.1f}" stroke="{col}" stroke-width="{w}" stroke-dasharray="{dash}" stroke-linecap="round" fill="none"/>'


def gpcr_lock(name, bond, anchor_n, w=360, h=300, pocket_r=72, rh=19, tint=HELIX, hot=HELIX_D,
              contacts=(), o_atom=None, hl=(), hl_rings=(), label="", extra=(), cx=None, cy=None, num_size=12.5, lab_size=12.5):
    """Top-down seven-helix ring with the molecule in the pocket.

    anchor_n: atom pointed at helix 3. o_atom: atom pointed at helix 6 (optional).
    contacts: (atom, helix 1..7, residue, kind) drawn as dashed lines to that helix.
    extra: (helix, residue) lining residues, printed quietly beside their helix.
    """
    goals = [(anchor_n, 0.0, 1.0)]
    if o_atom is not None:
        goals.append((o_atom, math.radians(-150), 0.8))
    m = orient(name, bond, goals)
    d = draw(m, bond, hl_atoms=hl, hl_rings=hl_rings)
    cx = w / 2 if cx is None else cx
    cy = h / 2 + 4 if cy is None else cy
    mol_svg, P = _place(d, cx, cy)
    a3 = _angle(P[anchor_n], (cx, cy))
    a6 = _angle(P[o_atom], (cx, cy)) if o_atom is not None else a3 + math.radians(205)
    ccw = (a3 - a6) % (2 * math.pi)
    ang = {3: a3, 6: a3 - ccw}
    ang[4], ang[5] = a3 - ccw / 3, a3 - 2 * ccw / 3
    rest = 2 * math.pi - ccw
    ang[7], ang[1], ang[2] = ang[6] - rest / 4, ang[6] - rest / 2, ang[6] - 3 * rest / 4
    R = pocket_r + rh + 3
    pos = {k: (cx + R * math.cos(a), cy + R * math.sin(a)) for k, a in ang.items()}
    out = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{pocket_r + 2:.1f}" fill="#fff" data-bg="1"/>']
    contact_helices = {c[1] for c in contacts}
    for k in range(1, 8):
        x, y = pos[k]
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rh}" fill="{hot if k in contact_helices else tint}" stroke="#fff" stroke-width="2" data-bg="1"/>')
        out.append(_txt(x, y + num_size * 0.36, str(k), num_size, INK, 500, "middle"))
    out.append(mol_svg)
    lines = {}
    for atom, hx, res, kind in contacts:
        a = ang[hx]
        q = (cx + (R - rh) * math.cos(a), cy + (R - rh) * math.sin(a))
        out.append(_contact(P[atom], q, kind))
        out.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="4" fill="{RED if kind == "salt" else YELD}"/>')
        lines.setdefault(hx, []).append((res, RED if kind == "salt" else YELT, 600))
    for hx, res in extra:
        lines.setdefault(hx, []).append((res, MUTE, 400))
    for hx, items in lines.items():
        a = ang[hx]
        lx, ly = cx + (R + rh + 7) * math.cos(a), cy + (R + rh + 7) * math.sin(a)
        anchor = "start" if math.cos(a) > 0.35 else "end" if math.cos(a) < -0.35 else "middle"
        n = len(items)
        if math.sin(a) > 0.5:
            y0 = ly + lab_size
        elif math.sin(a) < -0.5:
            y0 = ly - 4 - (n - 1) * (lab_size * 1.55)
        else:
            y0 = ly + lab_size * 0.36 - (n - 1) * (lab_size * 1.55) / 2
        for i, (s, col, wt) in enumerate(items):
            out.append(_txt(lx, y0 + i * (lab_size * 1.55), s, lab_size, col, wt, anchor))
    aria = f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    return f'<svg class="lock" viewBox="0 0 {w} {h}" width="{w}" height="{h}"{aria}>{"".join(out)}</svg>'


def gaba_lock(name, bond, br_atom, w=360, h=300, label=""):
    """Top-down GABA-A pentamer; the benzodiazepine sits in the alpha1/gamma2 seam on the outside."""
    cx, cy, R, r = w / 2 - 54, h / 2 + 40, 64, 33
    names = ["γ2", "α1", "β2", "α1", "β2"]
    angs = [math.radians(-90 + i * 72) for i in range(5)]
    pos = [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in angs]
    out = []
    for i, (x, y) in enumerate(pos):
        fill = "#f3e3a0" if i in (0, 1) else HELIX
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="#fff" stroke-width="2.5" data-bg="1"/>')
        out.append(_txt(x, y + 5, names[i], 13, INK, 600, "middle"))
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="12" fill="{INK}" data-bg="1"/>')
    out.append(_txt(cx, cy + 4, "Cl⁻", 10.5, "#fff", 500, "middle"))
    # GABA's own sites: the two beta/alpha seams
    for i, j in ((1, 2), (3, 4)):
        gx_, gy_ = (pos[i][0] + pos[j][0]) / 2, (pos[i][1] + pos[j][1]) / 2
        out.append(f'<circle cx="{gx_:.1f}" cy="{gy_:.1f}" r="5" fill="#fff" stroke="{BODY}" stroke-width="1.8"/>')
    sx, sy = (pos[0][0] + pos[1][0]) / 2, (pos[0][1] + pos[1][1]) / 2
    out_dir = math.atan2(sy - cy, sx - cx)
    m = orient(name, bond, [(br_atom, out_dir + math.pi, 1.0)])
    d = draw(m, bond)
    x0, y0, W, H = d["box"]
    reach = max(W, H) * 0.5 + 4
    gx, gy = sx + math.cos(out_dir) * reach, sy + math.sin(out_dir) * reach
    mol_svg, P = _place(d, gx, gy)
    out.append(mol_svg)
    a1 = pos[1]
    q = (a1[0] + (sx - a1[0]) * 0.5, a1[1] + (sy - a1[1]) * 0.5)
    out.append(_contact(P[br_atom], q, "hbond", gap=11))
    out.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="4.5" fill="{YELD}"/>')
    # labels: the contact residue, GABA sites, pore
    lx = pos[1][0] + r + 8
    out.append(_txt(lx, pos[1][1] + 4, "α1 His101", 12.5, YELT, 600, "start"))
    out.append(_txt(lx, pos[1][1] + 24, "benzo site", 12, MUTE, 400, "start"))
    out.append(f'<circle cx="{pos[2][0] + r + 12:.1f}" cy="{pos[2][1] + 14:.1f}" r="5" fill="#fff" stroke="{BODY}" stroke-width="1.8"/>')
    out.append(_txt(pos[2][0] + r + 22, pos[2][1] + 18, "GABA sites", 12, MUTE, 400, "start"))
    aria = f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    return f'<svg class="lock" viewBox="0 0 {w} {h}" width="{w}" height="{h}"{aria}>{"".join(out)}</svg>'


def side_pocket(name, bond, n_atom, o_atom, sub_tip, blocked, h=290, label="", red_atoms=()):
    """Side view of the mu pocket: helix 6 wall (left, His297), helix 3 wall (right, Asp147), floor Trp293 (the toggle)."""
    m = orient(name, bond, [(n_atom, 0.0, 1.0), (o_atom, math.radians(-150), 0.7), (sub_tip, math.radians(70), 0.9)])
    d = draw(m, bond, hl_atoms=[n_atom, o_atom], red_atoms=red_atoms)
    x0, y0, W, H = d["box"]
    margin, wall, gap = 64, 24, 22
    w = W + 2 * (margin + wall + gap)
    cx, cy = w / 2, 40 + H / 2
    mol_svg, P = _place(d, cx, cy)
    left, right = cx - W / 2 - gap, cx + W / 2 + gap
    floor = cy + H / 2 + 18
    out = []
    out.append(f'<rect x="{left - wall:.1f}" y="30" width="{wall}" height="{floor - 18:.1f}" rx="12" fill="{HELIX_D}" data-bg="1"/>')
    out.append(f'<rect x="{right:.1f}" y="30" width="{wall}" height="{floor - 18:.1f}" rx="12" fill="{HELIX_D}" data-bg="1"/>')
    out.append(_txt(left - wall / 2, 20, "helix 6", 11.5, MUTE, 500, "middle"))
    out.append(_txt(right + wall / 2, 20, "helix 3", 11.5, MUTE, 500, "middle"))
    tip = P[sub_tip]
    fx = min(max(tip[0], left + 40), right - 40)
    out.append(f'<ellipse cx="{fx:.1f}" cy="{floor + 12:.1f}" rx="40" ry="13" fill="{RED if blocked else HELIX_D}" data-bg="1"/>')
    out.append(_txt(fx, floor + 16.5, "Trp293", 11.5, "#fff" if blocked else INK, 600, "middle"))
    out.append(mol_svg)
    qn = (right, P[n_atom][1])
    qo = (left, P[o_atom][1])
    out.append(_contact(P[n_atom], qn, "salt"))
    out.append(f'<circle cx="{qn[0]:.1f}" cy="{qn[1]:.1f}" r="4.5" fill="{RED}"/>')
    out.append(_contact(P[o_atom], qo, "hbond"))
    out.append(f'<circle cx="{qo[0]:.1f}" cy="{qo[1]:.1f}" r="4.5" fill="{YELD}"/>')
    out.append(_txt(right + wall + 6, qn[1] + 4, "Asp147", 12, RED, 600, "start"))
    out.append(_txt(left - wall - 6, qo[1] + 4, "His297", 12, YELT, 600, "end"))
    if blocked:
        mx, my = tip[0], (tip[1] + floor) / 2 + 2
        out.append(f'<path d="M{mx-6:.1f} {my-6:.1f}L{mx+6:.1f} {my+6:.1f}M{mx+6:.1f} {my-6:.1f}L{mx-6:.1f} {my+6:.1f}" stroke="{RED}" stroke-width="3" stroke-linecap="round"/>')
        out.append(_txt(fx, floor + 46, "the red tail jams the toggle", 12.5, RED, 600, "middle"))
    else:
        out.append(f'<path d="M{left - wall - 4:.1f} {floor - 4:.1f}L{left - wall - 30:.1f} {floor + 10:.1f}" stroke="{INK}" stroke-width="2" marker-end="url(#arK)" fill="none"/>')
        out.append(_txt(fx, floor + 46, "toggle free: helix 6 swings out", 12.5, INK, 600, "middle"))
    hh = floor + 58
    aria = f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    return f'<svg class="lock" viewBox="0 0 {w:.0f} {hh:.0f}" width="{w:.0f}" height="{hh:.0f}"{aria}>{"".join(out)}</svg>'
