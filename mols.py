"""Molecule figures for the deck, drawn from PubChem 2D records.

Each slide uses one bond length for all its molecules. Yellow marks the opioid 'key'
(phenol ring + charged nitrogen); red marks the group that changes the drug's action.
"""
from mol2svg import load, svg, ring_bonds
from locks import gpcr_lock, gaba_lock, side_pocket


def key_parts(m):
    """phenol ring (as a ring), the phenol O bond, and the basic N."""
    o, n = m.phenol_O(), m.basic_N()
    rings, bonds, atoms = [], [], []
    if o is not None:
        c = m.nb[o][0][0]
        rings.append(m.aromatic(c))
        bonds.append((o, c))
        atoms.append(o)
    if n is not None:
        atoms.append(n)
    return o, n, rings, bonds, atoms


def n_substituent(m, n):
    """atoms of the N-substituent outside the ring system (methyl, allyl ...), nearest first."""
    for c, _ in m.nb[n]:
        if not any(c in r for r in m.rings):
            out, stack = [c], [c]
            while stack:
                cur = stack.pop()
                for x, _ in m.nb[cur]:
                    if x != n and x not in out:
                        out.append(x)
                        stack.append(x)
            return out
    return []


def build():
    F = {}

    # slide: the shared key (bond 21)
    m = load("leu-enkephalin").rotate(60)
    o, n, R, Bd, A = key_parts(m)
    F["leuenk"] = svg(m, 24, A, Bd, R, callouts=[(o, 0, 42, ["OH → His297"], "middle"), (n, 30, 40, ["N⁺ → Asp147"], "start")],
                      label="Leu-enkephalin; the tyrosine phenol and the N-terminal amine are highlighted")
    m = load("morphine")
    o, n, R, Bd, A = key_parts(m)
    F["morphine"] = svg(m, 24, A, Bd, R, callouts=[(o, 0, -40, ["OH → His297"], "middle"), (n, 44, 10, ["N⁺ → Asp147"], "start")],
                        label="Morphine; phenol and amine highlighted")
    m = load("fentanyl")
    _, n, _, _, _ = key_parts(m)
    F["fentanyl"] = svg(m, 24, [n], [], callouts=[(n, 44, 0, ["N⁺ → Asp147"], "start")],
                        label="Fentanyl; the amine nitrogen highlighted, no phenol")

    # slide: agonist vs antagonist (bond 24)
    for name, lab in (("oxymorphone", ["N–CH₃", "turns mu on"]), ("naloxone", ["N–allyl", "jams mu off"])):
        m = load(name)
        o, n, R, Bd, A = key_parts(m)
        sub = n_substituent(m, n)
        F[name] = svg(m, 27, A, Bd, R, red_atoms=[n] + sub, callouts=[(sub[-1], 30, 26, lab, "start")],
                      label=f"{name}; the nitrogen substituent is highlighted in red")

    # slide: the pill (bond 17)
    m = load("cychlorphine"); n = m.basic_N()
    F["pill_cychlorphine"] = svg(m, 21, [], [], label="Cychlorphine structure")
    m = load("nitazene"); n = m.basic_N()
    F["pill_nitazene"] = svg(m, 20, [], [], label="N-desethyl isotonitazene structure")
    m = load("ethylbromazolam"); seven = next(r for r in m.rings if len(r) == 7)
    F["pill_ethylbromazolam"] = svg(m, 22, [], [], [], label="Ethylbromazolam structure")

    # slide: three locks (bond 17)
    m = load("cychlorphine"); n = m.basic_N()
    F["lock_cychlorphine"] = svg(m, 18, [n], [], callouts=[(n, -40, -6, ["N⁺ → Asp147"], "end")],
                                 label="Cychlorphine; amine nitrogen highlighted")
    m = load("ethylbromazolam"); seven = next(r for r in m.rings if len(r) == 7)
    top = min(seven, key=lambda i: m.atoms[i]["y"])
    F["lock_ethylbromazolam"] = svg(m, 19, [], [], [seven], callouts=[(top, 40, -10, ["diazepine ring"], "start")],
                                    label="Ethylbromazolam; the seven-membered diazepine ring highlighted")
    m = load("medetomidine"); five = next(r for r in m.rings if len(r) == 5)
    n2 = next(i for i in five if m.atoms[i]["el"] == "N" and m.hcount(i) == 0)
    F["lock_medetomidine"] = svg(m, 20, [], [], [five], callouts=[(n2, 40, -10, ["imidazole⁺", "→ Asp113"], "start")],
                                 label="Medetomidine; the imidazole ring highlighted")
    # lock-and-key figures
    m = load("morphine"); o, n = m.phenol_O(), m.basic_N()
    F["lock_mu_big"] = gpcr_lock("morphine", 27, n, w=600, h=460, pocket_r=126, rh=32, o_atom=o, num_size=15, lab_size=14,
                                 contacts=[(n, 3, "Asp147", "salt"), (o, 6, "His297", "hbond")],
                                 extra=[(3, "Tyr148"), (6, "Trp293"), (7, "Tyr326")], hl=[n, o],
                                 label="Morphine in the mu-opioid pocket: its nitrogen bonds Asp147 on helix 3, its OH reaches His297 on helix 6")
    for name in ("oxymorphone", "naloxone"):
        m = load(name); n, o = m.basic_N(), m.phenol_O(); sub = n_substituent(m, n); tip = sub[-1]
        F["pocket_" + name] = side_pocket(name, 21, n, o, tip, blocked=(name == "naloxone"), red_atoms=sub,
                                          label=f"{name} in the mu pocket, side view; the group on the nitrogen is drawn in red")
    m = load("cychlorphine"); n = m.basic_N()
    F["lock_mu"] = gpcr_lock("cychlorphine", 12.5, n, w=360, h=330, pocket_r=92, rh=20, cx=168, contacts=[(n, 3, "Asp147", "salt")], hl=[n],
                             label="Cychlorphine in the mu-opioid pocket, bonded to Asp147")
    F["lock_a2"] = gpcr_lock("medetomidine", 16, 0, w=360, h=330, pocket_r=56, rh=20, cx=168, tint="#dfe3ea", hot="#8a94a6",
                             contacts=[(0, 3, "Asp113", "salt")], hl=[0],
                             label="Medetomidine in the smaller alpha-2 pocket, bonded to Asp113")
    F["lock_gaba"] = gaba_lock("ethylbromazolam", 14, 0, h=330, label="Ethylbromazolam at the alpha1/gamma2 seam of GABA-A, near His101")
    return F


if __name__ == "__main__":
    import sys
    F = build()
    css = (":root{--hlc:#ffe36e;--hlrc:#c8102e;--hlo:.42;--callout:#c8102e;--calloutmute:#6b6466}"
           "body{display:flex;flex-wrap:wrap;gap:24px;padding:20px;color:#1a1517;background:#f6f3f3;font-family:'DM Mono',monospace}"
           "div{border:1px dashed #ccc;padding:6px}svg text{font-family:'DM Mono',monospace}")
    html = ("<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap'>"
            f"<style>{css}</style>" + "".join(f"<div><b>{k}</b><br>{v}</div>" for k, v in F.items()))
    out = sys.argv[1] if len(sys.argv) > 1 else "_mols.html"
    open(out, "w").write(html)
    print({k: len(v) for k, v in F.items()})
