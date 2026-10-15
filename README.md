# Rorito B-Kmax 0.7 ballpoint pen: approximate reverse-engineered CAD assembly

> **This is an approximate model.** It was reconstructed from one photograph. It is not a design authorised by the manufacturer, and it does not use manufacturer data. All dimensions are estimates in **millimetres**.

## Deliverables (`output/`)
| File | What it is |
|---|---|
| `rorito_pen_assembly.step` / `rorito_pen_exploded.step` | B-rep solid assemblies (AP214) with 10 named, coloured solids. These are the primary files to open in CAD. |
| `rorito_pen_assembly.stl` / `rorito_pen_exploded.stl` | Tessellated meshes for printing or mesh tools. These are not editable solids. |
| `rorito_pen_assembly.glb` / `rorito_pen_exploded.glb` | Coloured meshes for viewing in a web browser (for example https://gltf-viewer.donmccurdy.com). |
| `exploded_view.png`, `assembled_view.png` | Isometric renders |
| `exploded_technical_drawing.svg/.pdf` | A3 drawing with a half-section exploded view, an assembled section, ballooned items, the BOM and a title block |
| `component_dimensions.csv`, `bill_of_materials.csv` | Estimated sizes and volumes per part; the BOM |

**No `.FCStd` file is included.** FreeCAD could not be installed in this environment because there is no apt or pip package for it. To make one, open FreeCAD, use *File → Import* on `rorito_pen_assembly.step`, then save. The parts keep their names.

## Components
1 Pen_Cap · 2 Pocket_Clip · 3 Cap_Insert · 4 Ballpoint_Ball (Ø0.7) · 5 Metal_Writing_Tip · 6 Refill_Connector · 7 Ink_Reservoir · 8 Ink_Column · 9 Transparent_Barrel · 10 Rear_End_Plug

**Seen in the photo:** the blue cap and clip, the clear barrel, the refill tube with its dark ink column, the blue rear plug, and the 0.7 marking.
**Inferred:** the cap insert, the tip/socket geometry, the refill connector, the plug spigot, and all wall thicknesses and clearances.
**Simplifications:**
- The barrel is modelled as round. The real barrel may be faceted.
- The clip is a separate solid. On the real pen it is probably moulded as part of the cap.
- The branding is not modelled.
- In the exploded view the ink column stays inside the reservoir.

Key estimates: overall length is 151 mm with the cap fitted. The barrel outside diameter is 8.0 mm with a 0.9 mm wall. The cap outside diameter is 9.4 mm. The refill outside diameter is 3.0 mm and its length is 121 mm.

## Rebuild / modify
```bash
pip install cadquery trimesh matplotlib networkx shapely
python render_views.py   # builds the model and all exports (calls build_model.main())
python validate.py       # re-imports STEP, checks solids, names, interference, STL watertightness, BOM
```
To change the design, edit the parameter dictionary `P` at the top of `build_model.py`. Each round part is a revolved (r, z) profile; this keeps the geometry parametric. The pen axis is +Z, and the apex of the writing ball is at Z=0.

## Validation results (last run)
- Both STEP files re-import with 10 solids each. All solids are valid (OCC `isValid`), and every component name is present.
- The two parts closest together, the ball and the tip socket, have 0.02 mm of clearance.
- Each STL contains 10 bodies with 12,806 triangles in total, and every body is watertight.
- There is zero interference volume between any pair of parts in the assembly.
- The BOM has 10 rows, which matches the 10 modelled parts.
