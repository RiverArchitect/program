# QGIS mapping

River Architect's map production runs on QGIS print layouts. The former ArcGIS Pro
implementation (`arcpy.mp`, `.aprx` projects, `.lyrx` layer files, `PDFDocumentCreate` page
stitching) has been removed; `.site_packages/riverpy/cMapper.py` no longer imports `arcpy`.

## Requirements

QGIS 3.x with its Python bindings on the interpreter's path. Verified against QGIS 3.44.7.

```bash
python3 -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
```

`cMapper` sets `QT_QPA_PLATFORM=offscreen` itself, so it renders headless without a display.
If QGIS lives somewhere other than `/usr`, point `QGIS_PREFIX_PATH` at it.

Note that the QGIS bindings are built against the system Python, not against the `ra-env`
analysis environment. Run mapping with the interpreter that owns the bindings.

## What replaced what

| ArcGIS Pro | QGIS |
|---|---|
| `.aprx` project | `.qgz` project, written to `02_Maps/<condition>/maps_<condition>_design.qgz` |
| `.lyrx` layer file | `.qml` layer style |
| `arcpy.mp.ArcGISProject` | `QgsProject` |
| layouts stored inside the template | `QgsPrintLayout` composed in code |
| `PDFDocumentCreate` + `appendPages` | QGIS **Atlas** + `QgsLayoutExporter.exportToPdf` |
| `layout.exportToPDF` per page | one multi-page PDF in a single call |
| `MakeRasterLayer_management` / `SaveToLayerFile_management` | `QgsRasterLayer` / `saveNamedStyle` |
| `lyr.visible = False` toggling | a clean layer stack per map sheet |

The page series is the substantive change. The old code zoomed the map frame to each centre
point, exported a temporary PDF, appended it to a growing document and deleted the temp file.
QGIS models this natively: a coverage layer holds one rectangle per page, the map frame is
marked atlas-driven, and the exporter writes every page in one operation.

## Layout

The layout is composed programmatically in `Mapper.build_layout()`, so no binary template is
needed. It contains a map frame, a legend filtered to the visible layers, a scale bar, a north
arrow, a title, and a footer carrying `condition` and `page N of M`.

Default page size is ANSI E landscape (1117.6 x 863.6 mm), reproducing the former arcpy
format. Override per instance with `mapper.page_size = (width_mm, height_mm)`.

If `02_Maps/templates/river_template.qgz` exists it is used as the starting project instead,
so a hand-built QGIS template can carry corporate styling, base layers or a custom layout.

## Symbology

Styles are read from `02_Maps/templates/symbology/<name>.qml`. `Mapper.choose_ref_layer()`
maps a raster name onto a style name (`lf_sym`, `ds_sym`, ...).

The published lifespan symbology was migrated from the original `.lyrx` with
`Tools/lyrx2qml.py`. `.lyrx` is JSON (Esri CIM), so class breaks, colours and labels convert
exactly:

```bash
python Tools/lyrx2qml.py 02_Maps/templates/symbology/LifespanRasterSymbology.lyrx
```

That produced `LifespanRasterSymbology.qml` (also copied to `lf_sym.qml`), preserving all nine
lifespan classes and their red-to-green ramp, with NoData transparent. The converter handles
`CIMRasterClassifyColorizer` (to `singlebandpseudocolor`, DISCRETE) and
`CIMRasterUniqueValueColorizer` (to `paletted`), and converts RGB, HSV, CMYK and gray CIM
colours.

When no `.qml` matches, the layer keeps QGIS defaults and a warning is logged; maps are still
produced, just unstyled.

## API

Unchanged, so existing callers work as they are:

```python
mapper = cMp.Mapper(condition, "lf")           # or "ds", "mlf", "mt"
mapper.prepare_layout(True, map_items=[...])   # True -> export immediately
mapper.make_pdf_maps("lf_grains", extent="raster")
if not mapper.error:
    ...
```

`extent` accepts `"raster"` (use the mapped raster's extent), `"MAXOF"`, or
`[xmin, ymin, xmax, ymax]`. For a multi-page series, set `mapper.xy_center_points` to a list of
`[x, y]` page centres together with `mapper.dx` / `mapper.dy`, exactly as before.

Callers: `LifespanDesign/feature_analysis.py`, `MaxLifespan/action_planner.py`,
`VolumeAssessment/volume_gui.py`.

## Verification

Exercised end to end against `RiverArchitect-SampleData/01_Conditions/2100_sample` on Linux
with no Esri software present:

- single-raster map: 1-page PDF, 3168 x 2448 pt (ANSI E landscape), 192 dpi
- three-window reach series: 3-page PDF from one atlas export
- `.qgz` project and per-layer `.qml` written alongside the PDFs
- rendered pages checked visually: title, map, north arrow, legend with all nine lifespan
  classes, scale bar, no overlap; NoData transparent

## Known gaps

- `02_Maps/templates/river_template.aprx`, `.gdb`, `.tbx` and the `Index/` folder are ArcGIS
  artefacts and are no longer read. They can be deleted once no one needs them for reference.
- Only `LifespanRasterSymbology.lyrx` existed to convert. Design-stage (`ds_sym`) and
  MaxLifespan styles fall back to QGIS defaults until `.qml` files are supplied.
- `config.py` now builds platform-neutral paths, but individual modules still concatenate
  hard-coded `"\\"` sub-paths, so the rest of River Architect remains Windows-only for now.
  `cMapper` normalises separators internally and runs on both.
