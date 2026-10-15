"""Validate generated deliverables: STEP re-import, solid validity, interference, STL meshes, BOM count."""
import csv, itertools, os, sys
import cadquery as cq, trimesh
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_model as bm

OUT = bm.OUT
ok = True
def check(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg); ok &= bool(cond)

parts = bm.build_parts()
names = [p[0] for p in parts]
for tag in ("assembly", "exploded"):
    f = os.path.join(OUT, f"rorito_pen_{tag}.step")
    shp = cq.importers.importStep(f)
    solids = shp.solids().vals()
    check(len(solids) == len(parts), f"{tag}.step re-imports {len(solids)} solids (expected {len(parts)})")
    check(all(s.isValid() for s in solids), f"{tag}.step all solids valid")
    # names via XCAF
    doc = TDocStd_Document(TCollection_ExtendedString("doc")); r = STEPCAFControl_Reader(); r.SetNameMode(True)
    r.ReadFile(f); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); labs = TDF_LabelSequence(); st.GetShapes(labs)
    found = set()
    for i in range(1, labs.Length() + 1):
        a = TDataStd_Name()
        if labs.Value(i).FindAttribute(TDataStd_Name.GetID_s(), a): found.add(a.Get().ToExtString())
    check(set(names) <= found, f"{tag}.step contains all named components")
    m = trimesh.load(os.path.join(OUT, f"rorito_pen_{tag}.stl"))
    check(len(m.faces) > 0 and m.faces.shape[1] == 3, f"{tag}.stl {len(m.faces)} triangles")
    comps = m.split(only_watertight=False)
    check(all(c.is_watertight for c in comps), f"{tag}.stl {len(comps)} bodies, all watertight")
    bb = shp.val().BoundingBox()
    print(f"     {tag} overall Z length {bb.zlen:.2f} mm, max dia {max(bb.xlen,bb.ylen):.2f} mm")

# interference in assembled state
clash = []
for (a, sa, *_), (b, sb, *_) in itertools.combinations(parts, 2):
    v = sa.val().intersect(sb.val()).Volume()
    if v > 1e-6: clash.append((a, b, v))
check(not clash, f"no interferences in assembly {clash}")
with open(os.path.join(OUT, "bill_of_materials.csv")) as fh:
    rows = list(csv.DictReader(fh))
check(len(rows) == len(parts), f"BOM rows {len(rows)} == modelled parts {len(parts)}")
sys.exit(0 if ok else 1)
