"""Find ONLY the added route markings (pixels that differ from BASE)."""
import numpy as np
from PIL import Image
from pathlib import Path

CARPOOLS = Path(__file__).resolve().parent.parent / "Carpools"

def analyze(name, basePath, recoPath):
    base = np.array(Image.open(basePath).convert("RGB"), dtype=np.int16)
    reco = np.array(Image.open(recoPath).convert("RGB"), dtype=np.int16)
    H, W, _ = reco.shape
    diff = np.sqrt(((reco - base) ** 2).sum(axis=2))
    changed = diff > 60  # pixels meaningfully different from base
    print(f"\n=== {name} ({W}x{H}) — {int(changed.sum())} changed pixels ===")

    # Bin changed pixels by approximate hue
    rgb = reco[changed]
    coords_y, coords_x = np.where(changed)
    R, G, B = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    mx = np.maximum(np.maximum(R, G), B)
    mn = np.minimum(np.minimum(R, G), B)
    delta = mx - mn
    sat = np.where(mx > 0, delta / np.maximum(mx, 1), 0)
    val = mx / 255

    # Hue computation
    hue = np.zeros(len(R), dtype=np.float32)
    nz = delta > 0
    r_dom = (R == mx) & nz
    g_dom = (G == mx) & nz & ~r_dom
    b_dom = (B == mx) & nz & ~r_dom & ~g_dom
    hue[r_dom] = ((G[r_dom] - B[r_dom]) / np.maximum(delta[r_dom], 1)) % 6
    hue[g_dom] = ((B[g_dom] - R[g_dom]) / np.maximum(delta[g_dom], 1)) + 2
    hue[b_dom] = ((R[b_dom] - G[b_dom]) / np.maximum(delta[b_dom], 1)) + 4
    hue = hue * 60

    bins = [
        ("red",    [(0, 15), (340, 360)]),
        ("orange", [(15, 45)]),
        ("yellow", [(45, 65)]),
        ("green",  [(80, 165)]),
        ("teal",   [(165, 200)]),
        ("blue",   [(200, 250)]),
        ("purple", [(250, 290)]),
        ("pink",   [(290, 340)]),
    ]
    for label, ranges in bins:
        m = np.zeros(len(R), dtype=bool)
        for lo, hi in ranges:
            m |= (hue >= lo) & (hue < hi)
        m &= (sat > 0.35) & (val > 0.35)
        cnt = int(m.sum())
        if cnt < 80:
            print(f"  {label:7}: {cnt}")
            continue
        xs = coords_x[m]; ys = coords_y[m]
        xmin, xmax = int(xs.min()), int(xs.max())
        ymin, ymax = int(ys.min()), int(ys.max())
        cx = int(xs.mean()); cy = int(ys.mean())
        # median color
        idxs = np.where(m)[0]
        med_r = int(np.median(R[idxs]))
        med_g = int(np.median(G[idxs]))
        med_b = int(np.median(B[idxs]))
        print(f"  {label:7}: {cnt:>5}  bbox x[{xmin}-{xmax}] y[{ymin}-{ymax}]  centroid({cx},{cy})  median #{med_r:02X}{med_g:02X}{med_b:02X}")

for name, b, r in [
    ("Scheck", "Scheck Family Plaza BASE.png", "Scheck Family Plaza Recorrido.png"),
    ("Hillel", "Hillel Carpool Base.png", "Hillel Carpool Recorrido.png"),
    ("Savage", "Savage Playground BASE.png", "Savage Playground Recorrido.png"),
    ("ECA",    "ECA CARPOOL BASE.png", "ECA CARPOOL Recorrido.png"),
]:
    analyze(name, CARPOOLS / b, CARPOOLS / r)
