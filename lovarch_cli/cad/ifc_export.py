"""Real IFC4 export (ifcopenshell) — the BIM counterpart of the DXF floorplan.

Builds a genuine IFC4 model from the same room specs used by `cad genera`:
IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey, one IfcSpace per room
(extruded to the given height) and perimeter IfcWall segments. Deterministic
and free (no credits) — the file opens in any BIM viewer/Revit/BIMcollab.

ifcopenshell is an OPTIONAL dependency: `pip install lovarch-cli[ifc]` (or
`pipx inject lovarch-cli ifcopenshell`). The command degrades with a clear
install hint when it's missing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lovarch_cli.cad.floorplan import STANDARD_ROOMS, _norm_label

WALL_THICKNESS = 0.15
CEILING_HEIGHT = 2.70


@dataclass
class IfcResult:
    path: str
    rooms: list = field(default_factory=list)
    total_area_m2: float = 0.0
    spaces: int = 0
    walls: int = 0
    schema: str = "IFC4"


class IfcExportError(RuntimeError):
    """ifcopenshell missing or export failed."""


def _require_ifcopenshell():
    import importlib

    try:
        importlib.import_module("ifcopenshell.api")
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise IfcExportError(
            "ifcopenshell non installato. Installa con: pip install 'lovarch-cli[ifc]' "
            "(oppure: pipx inject lovarch-cli ifcopenshell)"
        ) from exc


def generate_ifc(
    out_path: str,
    *,
    rooms: list | None = None,
    project_name: str = "Progetto Lovarch",
    storey_name: str = "Piano Terra",
    height_m: float = CEILING_HEIGHT,
) -> IfcResult:
    """Generate an IFC4 model with one IfcSpace per room + perimeter walls.

    Rooms are packed left-to-right in a single strip — the same layout the DXF
    floorplan uses, so `cad genera` and `cad ifc` describe the SAME building.
    """
    _require_ifcopenshell()
    import ifcopenshell
    import ifcopenshell.api
    import numpy as np

    specs = rooms if rooms else [
        {"name": n, "width_m": w, "height_m": h} for n, w, h in STANDARD_ROOMS
    ]

    model = ifcopenshell.api.run("project.create_file", version="IFC4")
    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject", name=project_name,
    )
    ifcopenshell.api.run("unit.assign_unit", model)
    ctx = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context", model, context_type="Model",
        context_identifier="Body", target_view="MODEL_VIEW", parent=ctx,
    )

    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Sito")
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Edificio")
    storey = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name=storey_name)
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[storey])

    def _place(product, x: float, y: float) -> None:
        matrix = np.eye(4)
        matrix[0][3], matrix[1][3] = x, y
        ifcopenshell.api.run(
            "geometry.edit_object_placement", model, product=product, matrix=matrix,
        )

    placed = []
    spaces = 0
    walls = 0
    total_area = 0.0
    x = 0.0

    for spec in specs:
        label = _norm_label(str(spec.get("name", "")))
        w = float(spec.get("width_m", 3.0))
        d = float(spec.get("height_m", 3.0))  # depth in plan (same key as DXF)

        space = ifcopenshell.api.run(
            "root.create_entity", model, ifc_class="IfcSpace", name=label,
        )
        rep = ifcopenshell.api.run(
            "geometry.add_wall_representation", model, context=body,
            length=w, height=height_m, thickness=d,
        )
        ifcopenshell.api.run(
            "geometry.assign_representation", model, product=space, representation=rep,
        )
        _place(space, x, 0.0)
        # Spaces are spatial elements: they AGGREGATE into the storey
        # (assign_container is only for physical products like walls).
        ifcopenshell.api.run(
            "aggregate.assign_object", model, relating_object=storey, products=[space],
        )
        # Attach a property set with the room's real quantities so downstream
        # tools (Autodesk Model Derivative, Revit, computo) can READ the areas.
        # Without this the IFC has geometry but no queryable data.
        area = round(w * d, 2)
        pset = ifcopenshell.api.run(
            "pset.add_pset", model, product=space, name="Pset_SpaceCommon",
        )
        ifcopenshell.api.run(
            "pset.edit_pset", model, pset=pset,
            properties={"Reference": label, "GrossFloorArea": area,
                        "NetFloorArea": area, "Category": "Locale"},
        )
        # Base quantities (IfcElementQuantity) — the canonical place BIM tools
        # look for area/height.
        qto = ifcopenshell.api.run(
            "pset.add_qto", model, product=space, name="Qto_SpaceBaseQuantities",
        )
        ifcopenshell.api.run(
            "pset.edit_qto", model, qto=qto,
            properties={"GrossFloorArea": area, "NetFloorArea": area,
                        "Height": round(height_m, 2)},
        )
        spaces += 1
        total_area += w * d
        placed.append({"name": label, "width_m": w, "height_m": d, "x": x})
        x += w + WALL_THICKNESS

    # Perimeter walls of the whole strip (front, back, left, right).
    strip_w = max((p["x"] + p["width_m"] for p in placed), default=0.0)
    strip_d = max((p["height_m"] for p in placed), default=0.0)
    for name, length, wx, wy, rotate in (
        ("Parete sud", strip_w, 0.0, -WALL_THICKNESS, False),
        ("Parete nord", strip_w, 0.0, strip_d, False),
        ("Parete ovest", strip_d, -WALL_THICKNESS, 0.0, True),
        ("Parete est", strip_d, strip_w, 0.0, True),
    ):
        wall = ifcopenshell.api.run(
            "root.create_entity", model, ifc_class="IfcWall", name=name,
        )
        rep = ifcopenshell.api.run(
            "geometry.add_wall_representation", model, context=body,
            length=length, height=height_m, thickness=WALL_THICKNESS,
        )
        ifcopenshell.api.run(
            "geometry.assign_representation", model, product=wall, representation=rep,
        )
        matrix = np.eye(4)
        if rotate:  # 90° around Z for the side walls
            matrix[0][0], matrix[0][1] = 0.0, -1.0
            matrix[1][0], matrix[1][1] = 1.0, 0.0
        matrix[0][3], matrix[1][3] = wx, wy
        ifcopenshell.api.run(
            "geometry.edit_object_placement", model, product=wall, matrix=matrix,
        )
        ifcopenshell.api.run(
            "spatial.assign_container", model, relating_structure=storey, products=[wall],
        )
        walls += 1

    model.write(out_path)
    return IfcResult(
        path=out_path, rooms=placed, total_area_m2=round(total_area, 1),
        spaces=spaces, walls=walls,
    )
