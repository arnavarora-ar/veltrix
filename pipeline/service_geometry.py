"""
VELTRIX service objects — shared geometry.

One source of truth for the six service sculptures. Both exporters use it:
  * export_glb.py      — pure Python, writes models/veltrix-services.glb
  * blender_build.py   — builds the same objects inside Blender for refinement,
                         then exports GLB with Blender's glTF exporter

Every object is a list of "parts". A part = (material_name, positions, normals, uvs, indices).
Material names are the contract with the website: it swaps in physical
materials by name ("accent", "chrome", "glass", "matte", "glow").

Units: metres. Each object sits on y=0 and is roughly 1.6–2.0 tall.
"""
import math
import numpy as np


# --------------------------------------------------------------------------- primitives
def _finish(pos, idx, uvs=None, smooth=True):
    pos = np.asarray(pos, dtype=np.float32)
    idx = np.asarray(idx, dtype=np.uint32).reshape(-1, 3)
    if uvs is None:
        uvs = np.zeros((len(pos), 2), dtype=np.float32)
    uvs = np.asarray(uvs, dtype=np.float32)
    if not smooth:  # un-index so every face gets its own flat normal
        pos = pos[idx.reshape(-1)]
        uvs = uvs[idx.reshape(-1)]
        idx = np.arange(len(pos), dtype=np.uint32).reshape(-1, 3)
    nrm = np.zeros_like(pos)
    a, b, c = pos[idx[:, 0]], pos[idx[:, 1]], pos[idx[:, 2]]
    fn = np.cross(b - a, c - a)
    for k in range(3):
        np.add.at(nrm, idx[:, k], fn)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    ln[ln == 0] = 1
    nrm = (nrm / ln).astype(np.float32)
    return pos, nrm, uvs, idx.reshape(-1)


def lathe(profile, segments=64, smooth=True):
    """profile: list of (radius, y) from bottom to top. Revolved around Y."""
    pos, uvs, idx = [], [], []
    n = len(profile)
    for s in range(segments + 1):
        t = s / segments
        th = t * 2 * math.pi
        for j, (r, y) in enumerate(profile):
            pos.append((r * math.sin(th), y, r * math.cos(th)))
            uvs.append((t, 1 - j / (n - 1)))
    for s in range(segments):
        for j in range(n - 1):
            a = s * n + j
            b = (s + 1) * n + j
            idx += [a, b, a + 1, b, b + 1, a + 1]
    return _finish(pos, idx, uvs, smooth)


def box(sx, sy, sz, cx=0.0, cy=0.0, cz=0.0, rot_y=0.0):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    faces = [  # (normal axis corners) counter-clockwise from outside
        [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)],
        [(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)],
        [(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)],
        [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)],
        [(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)],
        [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)],
    ]
    c, s = math.cos(rot_y), math.sin(rot_y)
    pos, uvs, idx = [], [], []
    for f in faces:
        base = len(pos)
        for (x, y, z), uv in zip(f, [(0, 1), (1, 1), (1, 0), (0, 0)]):
            pos.append((x * c + z * s + cx, y + cy, -x * s + z * c + cz))
            uvs.append(uv)
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]
    return _finish(pos, idx, uvs, smooth=False)


def sphere(r, cx=0.0, cy=0.0, cz=0.0, seg=40, rings=24):
    profile = [(r * math.sin(math.pi * i / rings), -r * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    p, n, u, i = lathe(profile, seg)
    p = p + np.array([cx, cy, cz], dtype=np.float32)
    return p, n, u, i


def torus(R, r, cx=0.0, cy=0.0, cz=0.0, seg=72, tube=18, axis="y"):
    pos, uvs, idx = [], [], []
    for i in range(seg + 1):
        u = i / seg * 2 * math.pi
        for j in range(tube + 1):
            v = j / tube * 2 * math.pi
            x = (R + r * math.cos(v)) * math.cos(u)
            z = (R + r * math.cos(v)) * math.sin(u)
            y = r * math.sin(v)
            if axis == "z":  # ring standing up, facing the camera
                x, y, z = x, z, y
            pos.append((x + cx, y + cy, z + cz))
            uvs.append((i / seg, j / tube))
    for i in range(seg):
        for j in range(tube):
            a = i * (tube + 1) + j
            b = (i + 1) * (tube + 1) + j
            if axis == "z":  # swapping y/z mirrors the shape, so flip winding
                idx += [a, b, a + 1, b, b + 1, a + 1]
            else:
                idx += [a, a + 1, b, b, a + 1, b + 1]
    return _finish(pos, idx, uvs)


def rounded_slab(w, h, d, radius, cx=0.0, cy=0.0, cz=0.0, tilt=0.0, corner_seg=8):
    """Thin pane with rounded corners in its XY plane, extruded along Z."""
    outline = []
    for k, (ox, oy) in enumerate([(w / 2 - radius, h / 2 - radius), (-w / 2 + radius, h / 2 - radius),
                                   (-w / 2 + radius, -h / 2 + radius), (w / 2 - radius, -h / 2 + radius)]):
        for s in range(corner_seg + 1):
            a = (k * 90 + s * 90 / corner_seg) * math.pi / 180
            outline.append((ox + radius * math.cos(a), oy + radius * math.sin(a)))
    n = len(outline)
    pos, uvs, idx = [], [], []
    ct, st = math.cos(tilt), math.sin(tilt)

    def put(x, y, z):
        # tilt around X, then translate
        y2, z2 = y * ct - z * st, y * st + z * ct
        pos.append((x + cx, y2 + cy, z2 + cz))
        uvs.append((x / w + 0.5, 0.5 - y / h))

    # caps
    for zsign in (1, -1):
        base = len(pos)
        put(0, 0, zsign * d / 2)
        for x, y in outline:
            put(x, y, zsign * d / 2)
        for k in range(n):
            a, b = base + 1 + k, base + 1 + (k + 1) % n
            idx += [base, a, b] if zsign > 0 else [base, b, a]
    # side wall (own vertices → crisp edge)
    base = len(pos)
    for x, y in outline:
        put(x, y, d / 2)
        put(x, y, -d / 2)
    for k in range(n):
        a, b = base + 2 * k, base + 2 * ((k + 1) % n)
        idx += [a, a + 1, b, b, a + 1, b + 1]
    p, nn, u, i = _finish(pos, idx, uvs, smooth=False)
    return p, nn, u, i


def mobius(R=0.62, width=0.42, thick=0.05, seg=180, cross=6, cy=1.0):
    """Thick Möbius ribbon — the 'one continuous story' of content."""
    pos, uvs, idx = [], [], []
    # rectangular cross-section, walked around the strip
    hw, ht = width / 2, thick / 2
    sec = [(-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht), (-hw, -ht)]
    for i in range(seg + 1):
        t = i / seg * 2 * math.pi
        half = t / 2
        for j, (a, b) in enumerate(sec):
            # rotate cross-section by half-angle (the twist)
            ca, sa = math.cos(half), math.sin(half)
            rr = a * ca - b * sa
            yy = a * sa + b * ca
            x = (R + rr) * math.cos(t)
            z = (R + rr) * math.sin(t)
            pos.append((x, yy + cy, z))
            uvs.append((i / seg, j / 4))
    m = len(sec)
    for i in range(seg):
        for j in range(m - 1):
            a = i * m + j
            b = (i + 1) * m + j
            idx += [a, a + 1, b, b, a + 1, b + 1]
    return _finish(pos, idx, uvs)


def merge(*parts):
    P, N, U, I, off = [], [], [], [], 0
    for p, n, u, i in parts:
        P.append(p); N.append(n); U.append(u); I.append(i + off); off += len(p)
    return np.concatenate(P), np.concatenate(N), np.concatenate(U), np.concatenate(I)


def plinth(r=0.42, h=0.08):
    return lathe([(0, 0), (r, 0), (r, h * 0.7), (r * 0.96, h), (0, h)], 64, smooth=False)


# --------------------------------------------------------------------------- the six objects
def brand_identity():
    """Faceted gem — a brand is the sum of its facets."""
    prof = [(0.0, 0.18), (0.62, 0.95), (0.66, 1.02), (0.44, 1.30), (0.0, 1.34)]
    gem = lathe(prof, segments=12, smooth=False)
    return [("accent", *gem), ("chrome", *plinth())]


def social_media():
    """Cluster of conversation bubbles orbiting a ring."""
    bubbles = merge(
        sphere(0.36, 0.0, 1.05, 0.0),
        sphere(0.22, 0.42, 1.42, 0.12),
        sphere(0.17, -0.40, 0.72, 0.22),
        sphere(0.12, -0.28, 1.55, -0.18),
        sphere(0.09, 0.50, 0.80, -0.20),
    )
    ring = torus(0.72, 0.025, 0, 1.08, 0, axis="y")
    return [("accent", *bubbles), ("chrome", *ring), ("chrome", *plinth())]


def content_copy():
    """Twisted Möbius ribbon — one continuous story."""
    return [("accent", *mobius(cy=1.0)), ("chrome", *plinth())]


def web_design():
    """Three floating interface panes, layered like a live site."""
    panes = merge(
        rounded_slab(1.05, 0.72, 0.04, 0.06, 0.00, 0.78, -0.18, tilt=-0.12),
        rounded_slab(1.05, 0.72, 0.04, 0.06, 0.10, 1.02, 0.02, tilt=-0.12),
    )
    top = rounded_slab(1.05, 0.72, 0.04, 0.06, 0.20, 1.26, 0.22, tilt=-0.12)
    dots = merge(*[sphere(0.022, 0.20 - 0.42 + k * 0.07, 1.26 + 0.29, 0.22 + 0.06, seg=16, rings=10) for k in range(3)])
    return [("glass", *panes), ("accent", *top), ("glow", *dots), ("chrome", *plinth())]


def performance_ads():
    """Rising columns on a curve — measurable growth."""
    cols = []
    for k in range(5):
        a = -0.9 + k * 0.45
        x, z = 0.48 * math.sin(a), 0.48 * math.cos(a) - 0.25
        h = 0.35 + k * 0.30
        cols.append(lathe([(0, 0.08), (0.11, 0.08), (0.11, 0.08 + h), (0, 0.08 + h)], 32, smooth=False))
        cols[-1] = (cols[-1][0] + np.array([x, 0, z], dtype=np.float32), *cols[-1][1:])
    peak = sphere(0.09, 0.48 * math.sin(0.9), 0.08 + 0.35 + 4 * 0.30 + 0.16, 0.48 * math.cos(0.9) - 0.25, seg=32, rings=20)
    return [("accent", *merge(*cols[:4])), ("glow", *merge(cols[4], peak)), ("chrome", *plinth(0.55))]


def strategy():
    """Gyroscope — orientation, balance and a fixed north."""
    outer = torus(0.62, 0.035, 0, 1.0, 0, axis="z")
    inner = torus(0.46, 0.03, 0, 1.0, 0, axis="y")
    core = sphere(0.16, 0, 1.0, 0)
    needle = lathe([(0, 0.0), (0.05, 0.0), (0, 0.55)], 24, smooth=False)
    needle = (needle[0] + np.array([0, 1.0, 0], dtype=np.float32), *needle[1:])
    stand = lathe([(0.03, 0.08), (0.03, 0.38)], 16)
    return [("chrome", *merge(outer, inner, stand)), ("accent", *core), ("glow", *needle), ("chrome", *plinth())]


SERVICES = [
    ("brand_identity", brand_identity),
    ("social_media", social_media),
    ("content_copy", content_copy),
    ("web_design", web_design),
    ("performance_ads", performance_ads),
    ("strategy", strategy),
]

# Base colours stored in the GLB (the site re-tints "accent" per service).
MATERIALS = {
    "accent": ((0.95, 0.35, 0.18, 1.0), 0.1, 0.35),
    "chrome": ((0.85, 0.85, 0.88, 1.0), 1.0, 0.18),
    "glass":  ((0.9, 0.92, 1.0, 0.35), 0.0, 0.05),
    "matte":  ((0.12, 0.12, 0.14, 1.0), 0.0, 0.8),
    "glow":   ((1.0, 0.9, 0.7, 1.0), 0.0, 0.3),
}
