"""Render PNG views and the SVG/PDF exploded technical drawing from the CAD model."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

import build_model as bm

OUT = bm.OUT
DISCLAIMER = ("APPROXIMATE REVERSE-ENGINEERED MODEL from a single photograph - "
              "not a manufacturer-authorised design. Dimensions in mm are estimates.")

# Camera: pen axis (Z) runs left->right, clip side (+X) is up.
AZ, EL = np.radians(72), np.radians(22)
FWD = np.array([np.sin(EL), np.cos(EL) * np.sin(AZ), np.cos(EL) * np.cos(AZ)])  # toward viewer-ish
RIGHT = np.cross(np.array([1.0, 0, 0]), FWD); RIGHT /= np.linalg.norm(RIGHT)
UP = np.cross(FWD, RIGHT)
LIGHT = np.array([0.8, 0.5, 0.4]); LIGHT /= np.linalg.norm(LIGHT)


def proj(p):
    return np.c_[p @ RIGHT, p @ UP], p @ FWD


def render(ms, fname, title, labels=False, parts=None):
    xs = np.vstack([m.vertices for _, m, *_ in ms])
    floor = xs[:, 0].min() - 3.0
    polys, cols, depth = [], [], []
    for n, m, rgb, a in ms:
        tri = m.vertices[m.faces]
        sh = tri.copy(); sh[..., 0] = floor          # drop shadow on floor plane
        sh[..., 2] += (tri[..., 0] - floor) * 0.35
        s2, _ = proj(sh.reshape(-1, 3))
        polys += list(s2.reshape(-1, 3, 2)); cols += [(0.55, 0.56, 0.6, 0.06 * a)] * len(tri)
        depth += [-1e9] * len(tri)
    for n, m, rgb, a in ms:
        tri = m.vertices[m.faces]; nrm = m.face_normals
        if a < 1:  # translucent: back faces only add murk, so drop them
            keep = nrm @ FWD > 0
            tri, nrm = tri[keep], nrm[keep]
        if a < 1:  # glossy translucent: keep only a light fresnel-ish tint
            lam = 0.75 + 0.25 * np.abs(nrm @ LIGHT)
        else:
            lam = 0.35 + 0.65 * np.clip(nrm @ LIGHT, 0, 1) + 0.25 * np.clip(nrm @ FWD, 0, 1) ** 8
        s2, d = proj(tri.reshape(-1, 3))
        polys += list(s2.reshape(-1, 3, 2)); depth += list(d.reshape(-1, 3).mean(1))
        c = np.clip(np.outer(lam, rgb), 0, 1)
        cols += [tuple(ci) + (a,) for ci in c]
    order = np.argsort(depth)
    fig, ax = plt.subplots(figsize=(26, 7.5), dpi=160)
    fig.patch.set_facecolor("#f4f5f7"); ax.set_facecolor("#f4f5f7")
    ax.add_collection(PolyCollection([polys[i] for i in order], facecolors=[cols[i] for i in order],
                                     edgecolors="none", antialiased=False))
    allp = np.vstack(polys); ax.set_xlim(allp[:, 0].min() - 8, allp[:, 0].max() + 8)
    ymin, ymax = allp[:, 1].min(), allp[:, 1].max()
    ax.set_ylim(ymin - (30 if labels else 6), ymax + (30 if labels else 6))
    if labels:
        for i, (n, m, *_r) in enumerate(ms, 1):
            c = m.vertices.mean(0)
            if n == "Ink_Column":
                c = m.vertices[m.vertices[:, 2] > np.percentile(m.vertices[:, 2], 30)].mean(0)
            pp, _ = proj(c[None]); px, py = pp[0]
            up = i % 2 == 1
            ly = (ymax + 10 + 9 * (i % 4 == 1)) if up else (ymin - 10 - 9 * (i % 4 == 0))
            ax.annotate("", xy=(px, py), xytext=(px, ly), arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#333"))
            ax.text(px, ly, str(i), ha="center", va="center", fontsize=13, weight="bold",
                    bbox=dict(boxstyle="circle,pad=0.3", fc="white", ec="#222", lw=1.2))
            ax.text(px, ly + (5.5 if up else -5.5), n, ha="center", va="center", fontsize=9, color="#222")
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=16, weight="bold", loc="left")
    fig.text(0.01, 0.02, DISCLAIMER, fontsize=9, color="#a33")
    fig.savefig(os.path.join(OUT, fname), facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def drawing(parts, offs, ms_exp, ms_asm):
    fig = plt.figure(figsize=(16.54, 11.69))  # A3 landscape
    fig.patch.set_facecolor("white")
    fig.add_artist(plt.Rectangle((0.01, 0.01), 0.98, 0.98, fill=False, lw=2, transform=fig.transFigure))

    def section(ax, ms, num):
        for i, (n, m, rgb, a) in enumerate(ms, 1):
            sec = m.section(plane_origin=(0, 0, 0), plane_normal=(0, 1, 0))
            if sec is None:
                continue
            for e in sec.discrete:
                ax.plot(e[:, 2], e[:, 0], color=rgb if a == 1 else (0.3, 0.5, 0.7), lw=0.9)
            if num:
                zc = np.percentile(m.vertices[:, 2], 60 if n == "Ink_Column" else 50)
                xt = m.vertices[:, 0].max()
                up = i % 2 == 1
                ly = 30 if up else -30
                ax.annotate("", xy=(zc, xt if up else m.vertices[:, 0].min()), xytext=(zc, ly),
                            arrowprops=dict(arrowstyle="-|>", lw=0.7))
                ax.text(zc, ly, str(i), ha="center", va="center", fontsize=10, weight="bold",
                        bbox=dict(boxstyle="circle,pad=0.25", fc="white", ec="black"))
        ax.axhline(0, color="0.5", lw=0.5, ls=(0, (12, 3, 2, 3)))  # centre line
        ax.set_aspect("equal"); ax.axis("off")

    ax1 = fig.add_axes([0.03, 0.55, 0.94, 0.38])
    section(ax1, ms_exp, True); ax1.set_ylim(-38, 38)
    ax1.set_title("EXPLODED VIEW - half section on XZ plane (scale approx. 1:1.6)", loc="left", fontsize=11)
    ax2 = fig.add_axes([0.03, 0.36, 0.55, 0.16])
    section(ax2, ms_asm, False); ax2.set_ylim(-12, 12)
    ax2.set_title("ASSEMBLED - section, overall length 151 mm (cap fitted)", loc="left", fontsize=11)

    rows = [[str(i), n, "1", mat] for i, (n, s, rgb, a, mat, src) in enumerate(parts, 1)]
    ax3 = fig.add_axes([0.03, 0.04, 0.55, 0.28]); ax3.axis("off")
    t = ax3.table(cellText=rows, colLabels=["ITEM", "COMPONENT", "QTY", "MATERIAL (ASSUMED)"],
                  colWidths=[0.08, 0.37, 0.07, 0.48], loc="upper left", cellLoc="left")
    t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1, 1.35)
    ax3.set_title("BILL OF MATERIALS", loc="left", fontsize=11, weight="bold")

    ax4 = fig.add_axes([0.62, 0.04, 0.35, 0.28]); ax4.axis("off")
    ax4.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, lw=1.5))
    tb = [("TITLE", "Rorito B-Kmax 0.7 ballpoint pen - exploded assembly"),
          ("DWG NO.", "RBK-07-EXP-001   REV A"), ("UNITS", "mm   PROJECTION: section / orthographic"),
          ("DATE", "2026-10-15"), ("SOURCE", "1 reference photograph; CadQuery/OpenCascade model"),
          ("STATUS", "APPROXIMATE - NOT MANUFACTURER DATA")]
    for k, (a, b) in enumerate(tb):
        y = 1 - (k + 1) / len(tb)
        ax4.plot([0, 1], [y, y], color="black", lw=0.6); ax4.plot([0.22, 0.22], [0, 1], color="black", lw=0.6)
        ax4.text(0.02, y + 0.08, a, fontsize=8, weight="bold")
        ax4.text(0.25, y + 0.08, b, fontsize=9, color="#a33" if a == "STATUS" else "black")
    fig.text(0.62, 0.335, DISCLAIMER, fontsize=7.5, color="#a33", wrap=True)
    for ext in ("svg", "pdf"):
        fig.savefig(os.path.join(OUT, f"exploded_technical_drawing.{ext}"))
    plt.close(fig)


if __name__ == "__main__":
    parts, offs = bm.main()
    ms_asm, ms_exp = bm.meshes(parts), bm.meshes(parts, offs)
    render(ms_asm, "assembled_view.png", "Rorito B-Kmax 0.7 - assembled (approximate CAD reconstruction)")
    render(ms_exp, "exploded_view.png", "Rorito B-Kmax 0.7 - exploded assembly", labels=True)
    drawing(parts, offs, ms_exp, ms_asm)
    print("rendered")
