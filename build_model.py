"""Approximate reverse-engineered CAD model of a Rorito B-Kmax 0.7 ballpoint pen.

Built from ONE reference photograph; dimensions are estimates, not manufacturer data.
Units: millimetres. Pen axis = global Z, writing ball apex at Z = 0, rear end at +Z.

Run:  python build_model.py          (writes everything into ./output)
Needs: cadquery, trimesh, matplotlib, numpy
"""
import csv
import os

import cadquery as cq
import numpy as np
import trimesh

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# Parameters (all mm). Edit these to modify the design.
# --------------------------------------------------------------------------
P = dict(
    ball_d=0.70,            # "0.7" on the cap
    socket_clear=0.02,      # radial clearance ball <-> tip socket
    tip_len=7.0, tip_r_front=0.50, tip_r_shank=1.15, tip_bore_r=0.55,
    conn_z0=4.6, conn_z1=14.0, conn_r=1.45, conn_spigot_r=0.95, conn_flange_z=9.0,
    res_r_out=1.50, res_r_in=1.00, res_z0=9.05, res_z1=130.0,
    ink_z1=112.0,           # ink level visible in photo (column ends near rear)
    bar_z0=12.0, bar_z1=140.0, bar_r_out=4.00, bar_r_in=3.10,
    nose_r_out=1.90, nose_r_in=1.55, nose_cone_end=30.0,
    plug_spigot_r=3.05, plug_head_r=4.00, plug_head_len=7.0, plug_z0=130.3,
    cap_z0=-4.0, cap_z1=45.0, cap_r_out=4.70, cap_r_in=4.10, cap_end=1.2,
    ins_r_out=4.05, ins_r_in=2.00, ins_z1=11.8,
    clip_w=3.2, clip_z0=2.0, clip_z1=40.0, clip_root_len=6.0, clip_t=0.8, clip_gap=0.9,
    explode_gap=12.0,
)


def revolve(pts):
    """Revolve a closed (r, z) profile 360 deg about the global Z axis."""
    return cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))


def tube(r_out, r_in, z0, z1):
    return revolve([(r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1)])


# --------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------
def build_parts():
    p = P
    br = p["ball_d"] / 2
    ball = cq.Workplane("XY").sphere(br).translate((0, 0, br))

    tip = revolve([(0.30, 0.30), (p["tip_r_front"], 0.30), (p["tip_r_shank"], 4.5),
                   (p["tip_r_shank"], p["tip_len"]), (p["tip_bore_r"], p["tip_len"]),
                   (p["tip_bore_r"], 1.0), (0.30, 0.8)])
    tip = tip.cut(cq.Workplane("XY").sphere(br + p["socket_clear"]).translate((0, 0, br)))

    z0, z1, zf = p["conn_z0"], p["conn_z1"], p["conn_flange_z"]
    conn = revolve([(p["tip_r_shank"] + 0.02, z0), (p["conn_r"], z0), (p["conn_r"], zf),
                    (p["conn_spigot_r"], zf), (p["conn_spigot_r"], z1), (0.40, z1),
                    (0.40, p["tip_len"] + 0.1), (p["tip_r_shank"] + 0.02, p["tip_len"] + 0.1)])

    res = tube(p["res_r_out"], p["res_r_in"], p["res_z0"], p["res_z1"])
    ink = revolve([(0, z1 + 0.05), (p["res_r_in"] - 0.02, z1 + 0.05),
                   (p["res_r_in"] - 0.02, p["ink_z1"]), (0, p["ink_z1"])])

    barrel = revolve([(p["nose_r_in"], p["bar_z0"]), (p["nose_r_out"], p["bar_z0"]),
                      (p["bar_r_out"], p["nose_cone_end"]), (p["bar_r_out"], p["bar_z1"]),
                      (p["bar_r_in"], p["bar_z1"]), (p["bar_r_in"], p["nose_cone_end"]),
                      (p["nose_r_in"], p["bar_z0"] + 2.0)])

    pz0, pz1 = p["plug_z0"], p["bar_z1"]
    hz1 = pz1 + p["plug_head_len"]
    plug = revolve([(0, pz0), (p["plug_spigot_r"], pz0), (p["plug_spigot_r"], pz1 + 0.02),
                    (p["plug_head_r"], pz1 + 0.02), (p["plug_head_r"], hz1 - 0.8),
                    (p["plug_head_r"] - 0.8, hz1), (0, hz1)])

    c0, c1 = p["cap_z0"], p["cap_z1"]
    cap = revolve([(0, c0), (p["cap_r_out"] - 0.6, c0), (p["cap_r_out"], c0 + 0.6),
                   (p["cap_r_out"], c1), (p["cap_r_in"], c1), (p["cap_r_in"], c0 + p["cap_end"]),
                   (0, c0 + p["cap_end"])])
    ins = tube(p["ins_r_out"], p["ins_r_in"], c0 + p["cap_end"] + 0.05, p["ins_z1"])

    # Pocket clip: root block on the cap + flat arm with a gap to the cap wall.
    x_root = p["cap_r_out"] + 0.02
    x_arm = p["cap_r_out"] + p["clip_gap"]
    w = p["clip_w"]
    def box(x0, x1, za, zb):
        return cq.Workplane("XY").box(x1 - x0, w, zb - za, centered=False).translate((x0, -w / 2, za))
    clip = (box(x_root, x_arm + p["clip_t"], p["clip_z0"], p["clip_z0"] + p["clip_root_len"])
            .union(box(x_arm, x_arm + p["clip_t"], p["clip_z0"], p["clip_z1"]))
            .union(box(x_root + 0.3, x_arm + p["clip_t"], p["clip_z1"] - 2.0, p["clip_z1"])))

    # (name, solid, rgb, alpha, material, source)
    blue, clear = (0.08, 0.25, 0.85), (0.85, 0.92, 0.97)
    return [
        ("Pen_Cap", cap, blue, 1.0, "PP, blue", "photo: shape, colour, branding (branding not modelled)"),
        ("Pocket_Clip", clip, blue, 1.0, "PP, blue", "photo: visible; modelled as separate solid (likely moulded integral)"),
        ("Cap_Insert", ins, (0.15, 0.35, 0.95), 1.0, "PP, blue", "inferred: inner sleeve/stop"),
        ("Ballpoint_Ball", ball, (0.25, 0.25, 0.28), 1.0, "Tungsten carbide", "inferred from 0.7 mm marking"),
        ("Metal_Writing_Tip", tip, (0.78, 0.78, 0.80), 1.0, "Brass / nickel-silver", "inferred, partly visible"),
        ("Refill_Connector", conn, (0.92, 0.92, 0.92), 1.0, "PE, natural", "inferred"),
        ("Ink_Reservoir", res, (0.90, 0.93, 0.97), 0.25, "PP, translucent", "photo: visible tube in barrel"),
        ("Ink_Column", ink, (0.05, 0.12, 0.65), 1.0, "Oil-based ink, blue", "photo: dark ink column"),
        ("Transparent_Barrel", barrel, clear, 0.15, "PS, clear", "photo: clear barrel"),
        ("Rear_End_Plug", plug, blue, 1.0, "PP, blue", "photo: blue rear plug; spigot inferred"),
    ]


def explode(parts):
    """Axial explosion in assembly order; clip lifted radially from the cap."""
    gap = P["explode_gap"]
    groups = [["Pen_Cap", "Pocket_Clip"], ["Cap_Insert"], ["Ballpoint_Ball"], ["Metal_Writing_Tip"],
              ["Refill_Connector"], ["Ink_Reservoir", "Ink_Column"], ["Transparent_Barrel"], ["Rear_End_Plug"]]
    by = {n: s for n, s, *_ in parts}
    offs, z_next = {}, None
    for g in groups:
        bbs = [by[n].val().BoundingBox() for n in g]
        zmin, zmax = min(b.zmin for b in bbs), max(b.zmax for b in bbs)
        dz = 0.0 if z_next is None else z_next - zmin
        for n in g:
            offs[n] = (0.0, 0.0, dz)
        z_next = zmax + dz + gap
    offs["Pocket_Clip"] = (6.0, 0.0, offs["Pocket_Clip"][2])
    return offs


def make_assembly(parts, offs=None):
    asm = cq.Assembly(name="Rorito_BKmax_07_approx")
    for n, s, rgb, a, *_ in parts:
        loc = cq.Location(cq.Vector(*(offs[n] if offs else (0, 0, 0))))
        asm.add(s, name=n, loc=loc, color=cq.Color(*rgb, a))
    return asm


def meshes(parts, offs=None):
    out = []
    for n, s, rgb, a, *_ in parts:
        v, f = s.val().tessellate(0.02, 0.2)
        m = trimesh.Trimesh(np.array([x.toTuple() for x in v]), np.array(f), process=True)
        if n == "Ballpoint_Ball":  # OCC sphere tessellation leaves open poles; use an exact icosphere
            m = trimesh.creation.icosphere(4, P["ball_d"] / 2).apply_translation((0, 0, P["ball_d"] / 2))
        if offs:
            m.apply_translation(offs[n])
        m.visual.face_colors = [int(c * 255) for c in rgb] + [int(a * 255)]
        out.append((n, m, rgb, a))
    return out


def main():
    parts = build_parts()
    for n, s, *_ in parts:
        assert s.val().isValid(), n
    offs = explode(parts)

    make_assembly(parts).export(os.path.join(OUT, "rorito_pen_assembly.step"))
    make_assembly(parts, offs).export(os.path.join(OUT, "rorito_pen_exploded.step"))

    for tag, o in (("assembly", None), ("exploded", offs)):
        ms = meshes(parts, o)
        trimesh.util.concatenate([m for _, m, *_ in ms]).export(os.path.join(OUT, f"rorito_pen_{tag}.stl"))
        scene = trimesh.Scene()
        for n, m, *_ in ms:
            scene.add_geometry(m, node_name=n, geom_name=n)
        scene.export(os.path.join(OUT, f"rorito_pen_{tag}.glb"))

    with open(os.path.join(OUT, "component_dimensions.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "component", "length_z_mm", "max_diameter_mm", "volume_mm3", "units", "basis"])
        for i, (n, s, rgb, a, mat, src) in enumerate(parts, 1):
            bb = s.val().BoundingBox()
            w.writerow([i, n, f"{bb.zlen:.2f}", f"{max(bb.xlen, bb.ylen):.2f}",
                        f"{s.val().Volume():.2f}", "mm", src])
    with open(os.path.join(OUT, "bill_of_materials.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "component", "qty", "material (assumed)", "notes"])
        for i, (n, s, rgb, a, mat, src) in enumerate(parts, 1):
            w.writerow([i, n, 1, mat, src])
    return parts, offs


if __name__ == "__main__":
    main()
    print("written to", OUT)
