"""Discover what colored regions actually exist in each Recorrido by
finding all highly-saturated pixels and grouping by hue."""
import numpy as np
from PIL import Image
from pathlib import Path
import colorsys

CARPOOLS = Path(__file__).resolve().parent.parent / "Carpools"

def analyze(name, recordPath):
    arr = np.array(Image.open(recordPath).convert("RGB"))
    H, W, _ = arr.shape
    R = arr[..., 0].astype(np.float32) / 255
    G = arr[..., 1].astype(np.float32) / 255
    B = arr[..., 2].astype(np.float32) / 255
    mx = np.max(arr, axis=2).astype(np.float32) / 255
    mn = np.min(arr, axis=2).astype(np.float32) / 255
    # saturation
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # value (brightness)
    val = mx
    # hue (degrees 0-360)
    hue = np.zeros_like(mx)
    delta = mx - mn
    mask = delta > 0
    # red dominant
    rmax = (arr[..., 0] == np.max(arr, axis=2)) & mask
    gmax = (arr[..., 1] == np.max(arr, axis=2)) & mask & ~rmax
    bmax = (arr[..., 2] == np.max(arr, axis=2)) & mask & ~rmax & ~gmax
    hue[rmax] = ((G[rmax] - B[rmax]) / delta[rmax]) % 6
    hue[gmax] = ((B[gmax] - R[gmax]) / delta[gmax]) + 2
    hue[bmax] = ((R[bmax] - G[bmax]) / delta[bmax]) + 4
    hue = hue * 60

    # Saturated, bright pixels
    keep = (sat > 0.45) & (val > 0.40)
    print(f"\n=== {name} ({W}x{H}) ===")
    print(f"  saturated bright pixels: {int(keep.sum())}")

    # Bin by hue ranges
    bins = [
        ("red",    [(0, 15), (340, 360)]),
        ("orange", [(15, 40)]),
        ("yellow", [(40, 65)]),
        ("green",  [(80, 165)]),
        ("teal",   [(165, 200)]),
        ("blue",   [(200, 250)]),
        ("pink",   [(290, 340)]),
    ]
    for label, ranges in bins:
        mask = keep.copy() & False
        for lo, hi in ranges:
            mask |= (hue >= lo) & (hue < hi) & keep
        if mask.sum() < 50:
            print(f"  {label:7}: {int(mask.sum())} pixels")
            continue
        ys, xs = np.where(mask)
        xmin, xmax = xs.min(), xs.max()
        ymin, ymax = ys.min(), ys.max()
        cx = int(xs.mean()); cy = int(ys.mean())
        # Take sample colors
        samp = arr[ys[0], xs[0]]
        print(f"  {label:7}: {len(xs):>5} px  bbox x[{xmin}-{xmax}] y[{ymin}-{ymax}]  centroid({cx},{cy})  sample #{samp[0]:02X}{samp[1]:02X}{samp[2]:02X}")

for name, f in [
    ("Scheck", "Scheck Family Plaza Recorrido.png"),
    ("Hillel", "Hillel Carpool Recorrido.png"),
    ("Savage", "Savage Playground Recorrido.png"),
    ("ECA",    "ECA CARPOOL Recorrido.png"),
]:
    analyze(name, CARPOOLS / f)
