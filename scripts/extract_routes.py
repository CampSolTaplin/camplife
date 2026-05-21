"""Extract carpool route SVG paths by diffing BASE vs Recorrido images.

Uses ACTUAL median colors discovered by discover_v2.py:
  blue  #004DE6   (Plaza entry)
  red   #E61B1B   (Hillel entry)
  green #008055   (Playground entry)
  pink  #FF80FF   (ECA entry)
  orange #FFAA00  (Plaza/Savage/ECA exit; Hillel uses #FF5500)
  yellow #FFE600  (drop-off circles)
  teal  #00AACC   (gate circles)

Strategy per category:
  1. binary mask = (color within tolerance) AND (differs from BASE)
  2. keep only the largest connected component
  3. for circles, return centroid
  4. for paths, Zhang-Suen thin then BFS-trace the skeleton
"""
import json
import sys
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

CARPOOLS_DIR = Path(__file__).resolve().parent.parent / "Carpools"
OUT_JSON     = Path(__file__).resolve().parent / "routes.json"
DEBUG_DIR    = Path(__file__).resolve().parent / "debug"
DEBUG_DIR.mkdir(exist_ok=True)

COLORS = {
    "plaza_blue":   (0, 77, 230),
    "hillel_red":   (230, 27, 27),
    "playground_g": (0, 128, 85),
    "eca_pink":     (255, 128, 255),
    "exit_orange1": (255, 170, 0),   # Plaza/Savage/ECA
    "exit_orange2": (255, 85, 0),    # Hillel
    "gate_teal":    (0, 170, 204),
    "drop_yellow":  (255, 230, 0),
}

def load_rgb(p):
    return np.array(Image.open(p).convert("RGB"), dtype=np.int16)

def color_diff_mask(base, reco, target, color_tol=60, diff_tol=40):
    tr, tg, tb = target
    d_target = np.sqrt(
        (reco[..., 0] - tr)**2 + (reco[..., 1] - tg)**2 + (reco[..., 2] - tb)**2
    )
    d_base = np.sqrt(
        ((reco - base) ** 2).sum(axis=2)
    )
    return (d_target < color_tol) & (d_base > diff_tol)

def connected_components(mask):
    H, W = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    comps = []
    ys, xs = np.where(mask)
    seed_set = set(zip(ys.tolist(), xs.tolist()))
    for y0, x0 in zip(ys, xs):
        if visited[y0, x0]: continue
        comp = []
        q = deque([(y0, x0)])
        visited[y0, x0] = True
        while q:
            y, x = q.popleft()
            comp.append((int(x), int(y)))
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                ny, nx = y+dy, x+dx
                if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    q.append((ny, nx))
        comps.append(comp)
    return comps

def centroid(pixels):
    if not pixels: return None
    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]
    return (int(round(sum(xs)/len(xs))), int(round(sum(ys)/len(ys))))

def zhang_suen_thin(mask):
    M = mask.copy().astype(np.uint8)
    changing = True
    while changing:
        changing = False
        for step in (0, 1):
            H, W = M.shape
            to_remove = []
            for y in range(1, H-1):
                for x in range(1, W-1):
                    if M[y, x] != 1: continue
                    p2,p3,p4,p5,p6,p7,p8,p9 = (
                        M[y-1,x], M[y-1,x+1], M[y,x+1], M[y+1,x+1],
                        M[y+1,x], M[y+1,x-1], M[y,x-1], M[y-1,x-1])
                    B = p2+p3+p4+p5+p6+p7+p8+p9
                    if not (2 <= B <= 6): continue
                    seq = (p2,p3,p4,p5,p6,p7,p8,p9,p2)
                    A = sum((seq[i]==0 and seq[i+1]==1) for i in range(8))
                    if A != 1: continue
                    if step == 0:
                        if p2*p4*p6: continue
                        if p4*p6*p8: continue
                    else:
                        if p2*p4*p8: continue
                        if p2*p6*p8: continue
                    to_remove.append((y, x))
            for y, x in to_remove: M[y, x] = 0
            if to_remove: changing = True
    return M

def neighbors8(y, x, H, W):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0: continue
            ny, nx = y+dy, x+dx
            if 0 <= ny < H and 0 <= nx < W:
                yield ny, nx

def bfs_farthest(skel, start_yx):
    H, W = skel.shape
    visited = {start_yx: None}
    q = deque([start_yx])
    last = start_yx
    while q:
        cur = q.popleft()
        last = cur
        y, x = cur
        for ny, nx in neighbors8(y, x, H, W):
            if skel[ny, nx] and (ny, nx) not in visited:
                visited[(ny, nx)] = cur
                q.append((ny, nx))
    return last, visited

def trace_skeleton(skel):
    ys, xs = np.where(skel == 1)
    if len(ys) == 0: return []
    start = (int(ys[0]), int(xs[0]))
    end1, _ = bfs_farthest(skel, start)
    end2, parents = bfs_farthest(skel, end1)
    path = []
    cur = end2
    while cur is not None:
        path.append((cur[1], cur[0]))
        cur = parents.get(cur)
    return path

def resample_path(path, target_count=20):
    if len(path) <= target_count:
        return path
    step = (len(path) - 1) / (target_count - 1)
    out = []
    for i in range(target_count):
        idx = int(round(i * step))
        out.append(path[min(idx, len(path)-1)])
    return out

def to_svg_d(poly):
    if not poly: return ""
    parts = [f"M {poly[0][0]} {poly[0][1]}"]
    for p in poly[1:]:
        parts.append(f"L {p[0]} {p[1]}")
    return " ".join(parts)

def best_path(base, reco, color_targets, color_tol=70, diff_tol=40, debug_name=None, basePath=None):
    """Try each target color; return path data for the one with largest result."""
    best = None
    for tgt in color_targets:
        mask = color_diff_mask(base, reco, tgt, color_tol, diff_tol)
        if mask.sum() < 50: continue
        comps = connected_components(mask)
        comps.sort(key=len, reverse=True)
        big = comps[0]
        if best is None or len(big) > best[0]:
            best = (len(big), big, mask)
    if best is None: return None
    _, big, mask = best
    print(f"    largest comp: {len(big)} px")
    # Build skeleton mask
    H, W = mask.shape
    big_mask = np.zeros_like(mask, dtype=np.uint8)
    for x, y in big: big_mask[y, x] = 1
    skel = zhang_suen_thin(big_mask)
    print(f"    skeleton: {int(skel.sum())} px")
    path = trace_skeleton(skel)
    poly = resample_path(path, 22)
    print(f"    waypoints: {len(poly)}")
    if debug_name and basePath:
        save_debug(basePath, big_mask, poly, debug_name)
    return poly

def best_circle(base, reco, target, color_tol=55, diff_tol=40):
    mask = color_diff_mask(base, reco, target, color_tol, diff_tol)
    if mask.sum() < 30: return None
    comps = connected_components(mask)
    comps.sort(key=len, reverse=True)
    big = comps[0]
    print(f"    circle largest comp: {len(big)} px")
    return centroid(big)

def save_debug(basePath, mask, poly, name):
    img = Image.open(basePath).convert("RGB").copy()
    arr = np.array(img)
    if mask is not None:
        arr[mask > 0] = (255, 0, 255)
    img2 = Image.fromarray(arr)
    draw = ImageDraw.Draw(img2)
    if poly and len(poly) >= 2:
        draw.line(poly, fill=(255, 255, 0), width=4)
    for i, (x, y) in enumerate(poly or []):
        r = 6
        draw.ellipse([x-r,y-r,x+r,y+r], fill=(255,165,0), outline=(0,0,0))
    img2.save(DEBUG_DIR / name)

def process(name, basePath, recoPath, entry_key, exit_keys=("exit_orange1","exit_orange2")):
    print(f"\n=== {name} ===")
    base = load_rgb(basePath)
    reco = load_rgb(recoPath)

    print("  drop:")
    drop = best_circle(base, reco, COLORS["drop_yellow"], color_tol=55, diff_tol=35)
    print(f"    centroid: {drop}")
    print("  gate:")
    gate = best_circle(base, reco, COLORS["gate_teal"], color_tol=55, diff_tol=35)
    print(f"    centroid: {gate}")

    print("  entry:")
    entryPoly = best_path(base, reco, [COLORS[entry_key]], color_tol=80, diff_tol=40,
                          debug_name=f"{name}_entry.png", basePath=basePath)

    print("  exit:")
    exitPoly = best_path(base, reco, [COLORS[k] for k in exit_keys], color_tol=80, diff_tol=40,
                         debug_name=f"{name}_exit.png", basePath=basePath)

    # Orient: entry ends at drop, exit starts at drop and ends at gate
    if entryPoly and drop:
        d0 = (entryPoly[0][0]-drop[0])**2 + (entryPoly[0][1]-drop[1])**2
        d1 = (entryPoly[-1][0]-drop[0])**2 + (entryPoly[-1][1]-drop[1])**2
        if d0 < d1:
            entryPoly = list(reversed(entryPoly))
            print("    reversed entry")
    if exitPoly and drop and gate:
        d0_drop = (exitPoly[0][0]-drop[0])**2 + (exitPoly[0][1]-drop[1])**2
        d1_drop = (exitPoly[-1][0]-drop[0])**2 + (exitPoly[-1][1]-drop[1])**2
        if d1_drop < d0_drop:
            exitPoly = list(reversed(exitPoly))
            print("    reversed exit")

    return {
        "drop": list(drop) if drop else None,
        "gate": list(gate) if gate else None,
        "entryD": to_svg_d(entryPoly) if entryPoly else "",
        "exitD":  to_svg_d(exitPoly)  if exitPoly  else "",
    }

def main():
    results = {}
    results["scheck"] = process("scheck",
        CARPOOLS_DIR/"Scheck Family Plaza BASE.png",
        CARPOOLS_DIR/"Scheck Family Plaza Recorrido.png",
        "plaza_blue")
    results["hillel"] = process("hillel",
        CARPOOLS_DIR/"Hillel Carpool Base.png",
        CARPOOLS_DIR/"Hillel Carpool Recorrido.png",
        "hillel_red")
    results["savage"] = process("savage",
        CARPOOLS_DIR/"Savage Playground BASE.png",
        CARPOOLS_DIR/"Savage Playground Recorrido.png",
        "playground_g")
    results["eca"] = process("eca",
        CARPOOLS_DIR/"ECA CARPOOL BASE.png",
        CARPOOLS_DIR/"ECA CARPOOL Recorrido.png",
        "eca_pink")
    OUT_JSON.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT_JSON}")
    print(f"Debug renders: {DEBUG_DIR}")

if __name__ == "__main__":
    main()
