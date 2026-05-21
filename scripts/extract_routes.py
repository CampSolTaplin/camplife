"""Extract carpool route SVG paths by walking the THICK colored line.

Approach:
  1. Build binary mask of pixels matching route color AND differing from BASE.
  2. Keep largest connected component.
  3. Walk the mask: start at the pixel nearest the anchor (gate or drop), then
     repeatedly step to the nearest *available* pixel inside a search radius
     while clearing a corridor behind us. This traces the centerline of the
     thick line without zigzagging.
  4. Resample to a manageable number of waypoints.
"""
import json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

CARPOOLS_DIR = Path(__file__).resolve().parent.parent / "Carpools"
OUT_JSON     = Path(__file__).resolve().parent / "routes.json"
DEBUG_DIR    = Path(__file__).resolve().parent / "debug"
DEBUG_DIR.mkdir(exist_ok=True)

# Median colors discovered by inspecting the Recorrido images
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

def color_diff_mask(base, reco, target, color_tol=80, diff_tol=40):
    tr, tg, tb = target
    dt = np.sqrt((reco[..., 0] - tr)**2 + (reco[..., 1] - tg)**2 + (reco[..., 2] - tb)**2)
    db = np.sqrt(((reco - base) ** 2).sum(axis=2))
    return (dt < color_tol) & (db > diff_tol)

def dilate(mask, iters=1):
    """Binary dilation: expand mask by iters pixels (8-connectivity)."""
    M = mask.copy().astype(bool)
    for _ in range(iters):
        new_M = M.copy()
        new_M[1:-1, 1:-1] |= M[:-2, 1:-1] | M[2:, 1:-1] | M[1:-1, :-2] | M[1:-1, 2:]
        new_M[1:-1, 1:-1] |= M[:-2, :-2] | M[:-2, 2:] | M[2:, :-2] | M[2:, 2:]
        M = new_M
    return M

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
    xs = [p[0] for p in pixels]; ys = [p[1] for p in pixels]
    return (int(round(sum(xs)/len(xs))), int(round(sum(ys)/len(ys))))

def walk_thick_line(mask, anchor, step=6, clear_radius=8):
    """Walk along a thick line. clear_radius clears a corridor so the walker
    doesn't re-traverse the same segment, but small enough to leave the line
    walkable forward."""
    H, W = mask.shape
    avail = mask.copy()
    ys, xs = np.where(avail)
    if len(ys) == 0: return []

    ax, ay = anchor
    d2 = (xs - ax) ** 2 + (ys - ay) ** 2
    i = int(np.argmin(d2))
    cur = (int(xs[i]), int(ys[i]))

    path = [cur]
    # Clear initial corridor
    cx, cy = cur
    y0, y1 = max(0, cy-clear_radius), min(H, cy+clear_radius+1)
    x0, x1 = max(0, cx-clear_radius), min(W, cx+clear_radius+1)
    avail[y0:y1, x0:x1] = False
    prev_dy, prev_dx = 0, 0

    while True:
        cx, cy = cur
        # Search window slightly larger than step
        sw = step + clear_radius
        y0, y1 = max(0, cy-sw), min(H, cy+sw+1)
        x0, x1 = max(0, cx-sw), min(W, cx+sw+1)
        block = avail[y0:y1, x0:x1]
        ly, lx = np.where(block)
        if len(ly) == 0: break
        gy = ly + y0; gx = lx + x0
        dy = gy - cy; dx = gx - cx
        dmag2 = dy*dy + dx*dx
        # Within step distance
        within = dmag2 <= sw*sw
        if not within.any(): break
        gy = gy[within]; gx = gx[within]
        dy = dy[within]; dx = dx[within]
        dmag2 = dmag2[within]

        if prev_dy == 0 and prev_dx == 0:
            idx = int(np.argmin(dmag2))
        else:
            mag = np.sqrt(dmag2)
            pmag = (prev_dy*prev_dy + prev_dx*prev_dx) ** 0.5
            cos_sim = (dy*prev_dy + dx*prev_dx) / (mag * pmag + 1e-9)
            # Strong direction preference, slight bias toward closer
            score = cos_sim * 200 - mag
            idx = int(np.argmax(score))
        nx, ny = int(gx[idx]), int(gy[idx])
        prev_dy, prev_dx = ny - cy, nx - cx
        cur = (nx, ny)
        path.append(cur)
        # Clear corridor around new pos
        y0, y1 = max(0, ny-clear_radius), min(H, ny+clear_radius+1)
        x0, x1 = max(0, nx-clear_radius), min(W, nx+clear_radius+1)
        avail[y0:y1, x0:x1] = False

    return path

def resample_path(path, every_px=20):
    if not path: return path
    out = [path[0]]
    last = path[0]
    for p in path[1:-1]:
        if (p[0]-last[0])**2 + (p[1]-last[1])**2 >= every_px*every_px:
            out.append(p); last = p
    if out[-1] != path[-1]:
        out.append(path[-1])
    return out

def to_svg_d(poly):
    if not poly: return ""
    parts = [f"M {poly[0][0]} {poly[0][1]}"]
    for p in poly[1:]:
        parts.append(f"L {p[0]} {p[1]}")
    return " ".join(parts)

def best_circle(base, reco, target, color_tol=55, diff_tol=35):
    mask = color_diff_mask(base, reco, target, color_tol, diff_tol)
    if mask.sum() < 30: return None
    comps = connected_components(mask)
    comps.sort(key=len, reverse=True)
    return centroid(comps[0])

def best_route(base, reco, targets, anchor, color_tol=80, diff_tol=40):
    """Build mask, close gaps via dilation, walk the result."""
    # Union of all target colors (orange has 2 variants)
    union = None
    for tgt in targets:
        m = color_diff_mask(base, reco, tgt, color_tol, diff_tol)
        union = m if union is None else (union | m)
    if union is None or union.sum() < 50:
        return None, 0
    # Close gaps so the whole route is one component
    closed = dilate(union, iters=5)
    comps = connected_components(closed)
    comps.sort(key=len, reverse=True)
    # The closed comp may include extra pixels from dilation;
    # restrict to those that were originally in the union.
    big_set = set(comps[0])
    comp_mask = np.zeros_like(union, dtype=bool)
    for x, y in comps[0]:
        comp_mask[y, x] = True
    walk = walk_thick_line(comp_mask, anchor, step=10, clear_radius=4)
    return walk, len(comps[0])

def save_debug(basePath, entry, exitP, drop, gate, name):
    img = Image.open(basePath).convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    if entry and len(entry) >= 2:
        draw.line(entry, fill=(0, 60, 220), width=5)
    if exitP and len(exitP) >= 2:
        draw.line(exitP, fill=(255, 140, 0), width=5)
    if drop:
        x, y = drop
        draw.ellipse([x-15,y-15,x+15,y+15], fill=(255, 230, 0), outline=(0,0,0), width=2)
    if gate:
        x, y = gate
        draw.ellipse([x-15,y-15,x+15,y+15], fill=(0, 200, 220), outline=(0,0,0), width=2)
    for i, p in enumerate(entry or []):
        r = 2
        draw.ellipse([p[0]-r,p[1]-r,p[0]+r,p[1]+r], fill=(255, 0, 255))
    for i, p in enumerate(exitP or []):
        r = 2
        draw.ellipse([p[0]-r,p[1]-r,p[0]+r,p[1]+r], fill=(255, 0, 0))
    img.save(DEBUG_DIR / name)

def process(name, basePath, recoPath, entry_color_key, entry_tol=80):
    print(f"\n=== {name} ===")
    base = load_rgb(basePath)
    reco = load_rgb(recoPath)

    drop = best_circle(base, reco, COLORS["drop_yellow"])
    gate = best_circle(base, reco, COLORS["gate_teal"])
    print(f"  drop {drop}  gate {gate}")

    # Entry: walk starting from the pixel nearest the gate
    entry, n_e = best_route(base, reco, [COLORS[entry_color_key]], anchor=gate, color_tol=entry_tol)
    print(f"  entry: comp={n_e}  walked={len(entry) if entry else 0}")
    # Exit: walk starting from the pixel nearest the drop
    exitP, n_x = best_route(base, reco, [COLORS["exit_orange1"], COLORS["exit_orange2"]], anchor=drop)
    print(f"  exit:  comp={n_x}  walked={len(exitP) if exitP else 0}")

    # Anchor with exact gate/drop at the endpoints
    if entry and gate and drop:
        entry = [tuple(gate)] + entry + [tuple(drop)]
    if exitP and gate and drop:
        exitP = [tuple(drop)] + exitP + [tuple(gate)]

    entry_rs = resample_path(entry, every_px=14)
    exit_rs  = resample_path(exitP, every_px=14)
    print(f"  entry waypoints: {len(entry_rs)}, exit waypoints: {len(exit_rs)}")

    save_debug(basePath, entry_rs, exit_rs, drop, gate, f"{name}.png")

    return {
        "drop": list(drop) if drop else None,
        "gate": list(gate) if gate else None,
        "entryD": to_svg_d(entry_rs) if entry_rs else "",
        "exitD":  to_svg_d(exit_rs)  if exit_rs  else "",
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
        CARPOOLS_DIR/"Savage Playground Recorrido.png", "playground_g", entry_tol=45)
    r["eca"] = process("eca",
        CARPOOLS_DIR/"ECA CARPOOL BASE.png",
        CARPOOLS_DIR/"ECA CARPOOL Recorrido.png", "eca_pink")
    OUT_JSON.write_text(json.dumps(r, indent=2))
    print(f"\nWrote {OUT_JSON}")

if __name__ == "__main__":
    main()
