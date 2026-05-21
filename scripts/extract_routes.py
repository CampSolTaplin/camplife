"""Extract carpool route SVG paths by diffing BASE vs Recorrido.

Strategy:
  1. binary mask = (color within tol) AND (differs from BASE)
  2. keep largest connected component
  3. Zhang-Suen thin to 1-px skeleton
  4. prune short side-branches (skeleton noise from thinning corners)
  5. walk skeleton via DFS with direction continuation preference — handles
     closed loops, U-shapes, and L-shapes without losing parts of the path
  6. order so it starts/ends at the right anchor (gate or drop)
"""
import json
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

CARPOOLS_DIR = Path(__file__).resolve().parent.parent / "Carpools"
OUT_JSON     = Path(__file__).resolve().parent / "routes.json"
DEBUG_DIR    = Path(__file__).resolve().parent / "debug"
DEBUG_DIR.mkdir(exist_ok=True)

# Actual colors discovered from Recorrido images
COLORS = {
    "plaza_blue":   (0, 77, 230),
    "hillel_red":   (230, 27, 27),
    "playground_g": (0, 128, 85),
    "eca_pink":     (255, 128, 255),
    "exit_orange1": (255, 170, 0),
    "exit_orange2": (255, 85, 0),
    "gate_teal":    (0, 170, 204),
    "drop_yellow":  (255, 230, 0),
}

def load_rgb(p):
    return np.array(Image.open(p).convert("RGB"), dtype=np.int16)

def color_diff_mask(base, reco, target, color_tol=70, diff_tol=40):
    tr, tg, tb = target
    d_target = np.sqrt(
        (reco[..., 0] - tr)**2 + (reco[..., 1] - tg)**2 + (reco[..., 2] - tb)**2
    )
    d_base = np.sqrt(((reco - base) ** 2).sum(axis=2))
    return (d_target < color_tol) & (d_base > diff_tol)

def connected_components(mask):
    H, W = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    comps = []
    ys, xs = np.where(mask)
    for y0, x0 in zip(ys, xs):
        if visited[y0, x0]: continue
        comp = []
        q = deque([(y0, x0)])
        visited[y0, x0] = True
        while q:
            y, x = q.popleft()
            comp.append((int(x), int(y)))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0: continue
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        q.append((ny, nx))
        comps.append(comp)
    return comps

def centroid(pixels):
    if not pixels: return None
    xs = [p[0] for p in pixels]; ys = [p[1] for p in pixels]
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

def neighbor_count(skel, y, x):
    H, W = skel.shape
    return sum(1 for ny, nx in neighbors8(y, x, H, W) if skel[ny, nx])

def prune_branches(skel, max_branch_len=12):
    """Remove side branches shorter than max_branch_len pixels."""
    M = skel.copy()
    H, W = M.shape
    changed = True
    while changed:
        changed = False
        # find endpoints
        eps = []
        ys, xs = np.where(M == 1)
        for y, x in zip(ys, xs):
            if neighbor_count(M, y, x) == 1:
                eps.append((y, x))
        for ep in eps:
            # walk from endpoint until we hit a junction (3+ neighbors)
            walk = [ep]
            visited = {ep}
            cur = ep
            while True:
                y, x = cur
                if neighbor_count(M, y, x) >= 3 and len(walk) > 1:
                    # hit a junction — prune this branch if short
                    if len(walk) <= max_branch_len:
                        for py, px in walk[:-1]:
                            M[py, px] = 0
                        changed = True
                    break
                nxt = None
                for ny, nx in neighbors8(y, x, H, W):
                    if M[ny, nx] and (ny, nx) not in visited:
                        nxt = (ny, nx); break
                if nxt is None: break
                visited.add(nxt); walk.append(nxt); cur = nxt
                if len(walk) > max_branch_len + 2: break
    return M

def walk_skeleton(skel, anchor_xy=None):
    """Walk the skeleton, preferring straight continuation at junctions.
    If anchor_xy is given, start from the skeleton pixel nearest to it."""
    H, W = skel.shape
    ys, xs = np.where(skel == 1)
    if len(ys) == 0: return []

    # Find endpoints (1-neighbor pixels)
    endpoints = []
    for y, x in zip(ys, xs):
        if neighbor_count(skel, y, x) == 1:
            endpoints.append((int(y), int(x)))

    # Choose start
    if anchor_xy is not None and endpoints:
        ax, ay = anchor_xy
        start = min(endpoints, key=lambda yx: (yx[1]-ax)**2 + (yx[0]-ay)**2)
    elif endpoints:
        start = endpoints[0]
    else:
        # Closed loop — pick anchor-nearest skeleton pixel or any
        if anchor_xy is not None:
            ax, ay = anchor_xy
            best = (int(ys[0]), int(xs[0]))
            bd = (best[1]-ax)**2 + (best[0]-ay)**2
            for y, x in zip(ys, xs):
                d = (x-ax)**2 + (y-ay)**2
                if d < bd: bd = d; best = (int(y), int(x))
            start = best
        else:
            start = (int(ys[0]), int(xs[0]))

    visited = {start}
    path = [(start[1], start[0])]
    prev_dy, prev_dx = 0, 0

    while True:
        y, x = path[-1][1], path[-1][0]
        cands = []
        for ny, nx in neighbors8(y, x, H, W):
            if skel[ny, nx] and (ny, nx) not in visited:
                cands.append((ny, nx))
        if not cands: break
        if len(cands) == 1:
            ny, nx = cands[0]
        else:
            best = cands[0]
            best_score = -2
            for cy, cx in cands:
                dy, dx = cy - y, cx - x
                if prev_dy == 0 and prev_dx == 0:
                    score = 0
                else:
                    dmag = (dy*dy + dx*dx) ** 0.5
                    pmag = (prev_dy*prev_dy + prev_dx*prev_dx) ** 0.5
                    score = (dy*prev_dy + dx*prev_dx) / (dmag * pmag + 1e-9)
                if score > best_score:
                    best_score = score; best = (cy, cx)
            ny, nx = best
        visited.add((ny, nx))
        path.append((nx, ny))
        prev_dy, prev_dx = ny - y, nx - x

    return path

def resample_path(path, every=4):
    """Take every Nth pixel to reduce density without losing shape."""
    if not path: return path
    out = [path[0]]
    last_kept = path[0]
    for p in path[1:-1]:
        dx = p[0] - last_kept[0]; dy = p[1] - last_kept[1]
        if dx*dx + dy*dy >= every*every:
            out.append(p)
            last_kept = p
    if path[-1] != out[-1]:
        out.append(path[-1])
    return out

def to_svg_d(poly):
    if not poly: return ""
    parts = [f"M {poly[0][0]} {poly[0][1]}"]
    for p in poly[1:]:
        parts.append(f"L {p[0]} {p[1]}")
    return " ".join(parts)

def best_path(base, reco, color_targets, anchor=None, color_tol=70, diff_tol=40):
    """Extract path for the largest-component color among the targets."""
    best_mask = None; best_pixels = None; best_len = 0
    for tgt in color_targets:
        mask = color_diff_mask(base, reco, tgt, color_tol, diff_tol)
        if mask.sum() < 50: continue
        comps = connected_components(mask)
        comps.sort(key=len, reverse=True)
        if len(comps[0]) > best_len:
            best_len = len(comps[0])
            best_pixels = comps[0]
            best_mask = mask
    if not best_pixels: return None
    # Rebuild a mask with only the largest component
    H, W = best_mask.shape
    comp_mask = np.zeros_like(best_mask, dtype=np.uint8)
    for x, y in best_pixels: comp_mask[y, x] = 1
    # Thin then prune
    skel = zhang_suen_thin(comp_mask)
    skel = prune_branches(skel, max_branch_len=15)
    print(f"    component={len(best_pixels)} skel={int(skel.sum())}")
    # Walk
    path = walk_skeleton(skel, anchor_xy=anchor)
    print(f"    walked={len(path)} px")
    return resample_path(path, every=5)

def best_circle(base, reco, target, color_tol=55, diff_tol=35):
    mask = color_diff_mask(base, reco, target, color_tol, diff_tol)
    if mask.sum() < 30: return None
    comps = connected_components(mask)
    comps.sort(key=len, reverse=True)
    return centroid(comps[0])

def save_debug(basePath, polyEntry, polyExit, drop, gate, name):
    img = Image.open(basePath).convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    if polyEntry and len(polyEntry) >= 2:
        draw.line(polyEntry, fill=(0, 128, 255), width=5)
    if polyExit and len(polyExit) >= 2:
        draw.line(polyExit, fill=(255, 140, 0), width=5)
    if drop:
        x, y = drop
        draw.ellipse([x-15,y-15,x+15,y+15], fill=(255, 230, 0), outline=(0,0,0), width=2)
    if gate:
        x, y = gate
        draw.ellipse([x-15,y-15,x+15,y+15], fill=(0, 200, 220), outline=(0,0,0), width=2)
    img.save(DEBUG_DIR / name)

def process(name, basePath, recoPath, entry_key, exit_keys=("exit_orange1","exit_orange2")):
    print(f"\n=== {name} ===")
    base = load_rgb(basePath); reco = load_rgb(recoPath)

    drop = best_circle(base, reco, COLORS["drop_yellow"])
    gate = best_circle(base, reco, COLORS["gate_teal"])
    print(f"  drop {drop}  gate {gate}")

    # Entry: walk starting near gate (so first waypoint = gate-anchor)
    print("  entry path:")
    entryPoly = best_path(base, reco, [COLORS[entry_key]], anchor=gate)
    # Exit: walk starting near drop
    print("  exit path:")
    exitPoly = best_path(base, reco, [COLORS[k] for k in exit_keys], anchor=drop)

    # Orient entry: starts near gate, ends near drop
    if entryPoly and gate and drop:
        d0 = (entryPoly[0][0]-gate[0])**2 + (entryPoly[0][1]-gate[1])**2
        d1 = (entryPoly[-1][0]-gate[0])**2 + (entryPoly[-1][1]-gate[1])**2
        if d1 < d0:
            entryPoly = list(reversed(entryPoly)); print("    reversed entry to start at gate")
    # Orient exit: starts near drop, ends near gate
    if exitPoly and drop and gate:
        d0d = (exitPoly[0][0]-drop[0])**2 + (exitPoly[0][1]-drop[1])**2
        d1d = (exitPoly[-1][0]-drop[0])**2 + (exitPoly[-1][1]-drop[1])**2
        if d1d < d0d:
            exitPoly = list(reversed(exitPoly)); print("    reversed exit to start at drop")

    # Anchor with exact gate/drop coords at endpoints (so the loop closes)
    if entryPoly and gate and drop:
        entryPoly = [tuple(gate)] + entryPoly + [tuple(drop)]
    if exitPoly and gate and drop:
        exitPoly = [tuple(drop)] + exitPoly + [tuple(gate)]

    save_debug(basePath, entryPoly, exitPoly, drop, gate, f"{name}.png")

    return {
        "drop": list(drop) if drop else None,
        "gate": list(gate) if gate else None,
        "entryD": to_svg_d(entryPoly) if entryPoly else "",
        "exitD":  to_svg_d(exitPoly)  if exitPoly  else "",
    }

def main():
    r = {}
    r["scheck"] = process("scheck",
        CARPOOLS_DIR/"Scheck Family Plaza BASE.png",
        CARPOOLS_DIR/"Scheck Family Plaza Recorrido.png", "plaza_blue")
    r["hillel"] = process("hillel",
        CARPOOLS_DIR/"Hillel Carpool Base.png",
        CARPOOLS_DIR/"Hillel Carpool Recorrido.png", "hillel_red")
    r["savage"] = process("savage",
        CARPOOLS_DIR/"Savage Playground BASE.png",
        CARPOOLS_DIR/"Savage Playground Recorrido.png", "playground_g")
    r["eca"] = process("eca",
        CARPOOLS_DIR/"ECA CARPOOL BASE.png",
        CARPOOLS_DIR/"ECA CARPOOL Recorrido.png", "eca_pink")
    OUT_JSON.write_text(json.dumps(r, indent=2))
    print(f"\nWrote {OUT_JSON}")
    print(f"Debug renders: {DEBUG_DIR}")

if __name__ == "__main__":
    main()
