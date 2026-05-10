# Task: generate-ifc-model

> **Pattern:** AP-TP-001
> **Executor:** @bim-engineer (mind clone Mark Baldwin · Tier 1)
> **Squad:** architettura-progetto

---

## task_name
Generate IFC4 LOD 300 model + APS viewer + quantitativi

## status
ACTIVE · stable · v1.0

## responsible_executor
- **agent**: @bim-engineer
- **executor_type**: AP-EP-003 (Hybrid · Python + APS API)
- **worker**: IfcOpenShell 0.8.4 + APS Model Derivative

## execution_type
**Synchronous after CAD** · Output feeds @computo-engineer + @energy-prelim

## input
```yaml
required:
  schema_quotato_json: "From @cad-engineer"
  dxf_path: "pianta-progetto.dxf"
  materials_list: "From @concept-designer + briefing"
optional:
  classification: "UniFormat | Uniclass"  # default UniFormat
```

## output
```yaml
files:
  - "03-progetto-definitivo/modello.ifc"
  - "03-progetto-definitivo/thumbnail-3d.png"
  - "03-progetto-definitivo/viewer-url.txt"
  - "03-progetto-definitivo/quantitativi.json"
quantitativi_schema:
  muri: array[{ tipo, lunghezza_m, altezza_m, area_m2 }]
  finestre: array[{ larghezza_cm, altezza_cm, quantita }]
  porte: array[{ ... }]
  pavimenti: array[{ ... }]
  totale_aree_per_categoria: object
```

## action_items
1. Initialize IFC4 file via `ifcopenshell.file(schema='IFC4')`
2. Build IfcSite + IfcBuilding + IfcBuildingStorey
3. Build IfcWalls from schema-quotato (perimeter + internal)
4. Build IfcSlab (floor)
5. Build IfcDoors with panels (LOD 300)
6. Build IfcWindows (perimeter only)
7. Build IfcSpaces for ambienti
8. Apply property sets ISO 12006-3 (Pset_WallCommon, etc.)
9. Apply UniFormat classification per element
10. Run `ifcopenshell.validate()` · 0 errors required
11. Test web-ifc loads · APS Model Derivative success
12. Extract quantitativi via `ifcopenshell.api`
13. Generate thumbnail via PyVista or APS

## acceptance_criteria
- [ ] IFC4 schema valid
- [ ] `ifcopenshell.validate(model)` · 0 errors
- [ ] All elements have property sets ISO 12006-3
- [ ] All elements have UniFormat classification
- [ ] web-ifc loads file · ≥100 elements
- [ ] APS Viewer URL works (HTTP 200)
- [ ] quantitativi.json populated (muri, finestre, porte, pavimenti)
- [ ] thumbnail-3d.png generated
- [ ] Volumi vs DXF schema-quotato diff ≤2%

## dependencies
- **Libraries:**
  - IfcOpenShell 0.8.4
  - ifcopenshell.api (high-level)
  - PyVista (snapshots)
- **APIs:**
  - Autodesk Platform Services (Model Derivative + Viewer SDK)
- **Inputs:**
  - schema-quotato.json (@cad-engineer)
  - materials list

## templates
- IFC4 building skeleton template (IfcSite → IfcBuilding → IfcBuildingStorey)
- Property set definitions standard

## quality_gate
- **Gate:** QG-AP-1.2 (Misure · volumi vs DXF)
- **Reviewer:** @quality-misure
- **Threshold:** Volumi diff ≤2% vs DXF

## handoff
- **From:** @progetto-chief
- **To:** @progetto-chief (returns) → @computo-engineer (uses quantitativi) + @quality-misure (verifies)
- **Required announcement:** "Retornando ao @progetto-chief. IFC4 LOD 300 · {n} elements · viewer ready."

## veto_conditions
- IFC validate fails → REJECT internal · regenerate
- Volumi diff vs DXF >2% → halt + flag @quality-dati
- APS upload fail 3× → procede senza viewer · flag warning

## estimated_time
**60-90 seconds** (APS upload dominant · async)

## output_example
See `@bim-engineer.md` output_examples · 142 elements · IFC4 valid · UniFormat classified · viewer URL embeddable.
