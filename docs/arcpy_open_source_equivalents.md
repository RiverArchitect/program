# arcpy inventory and open-source equivalents

Reference for replacing the Esri `arcpy` dependency in *River Architect* with an open-source
stack, so that the code can be executed and tested without an ArcGIS Pro / Spatial Analyst
license. arcpy reference: https://desktop.arcgis.com/de/arcmap/latest/analyze/arcpy/what-is-arcpy-.htm

Every mapping marked **verified** in this document was executed against the sample condition
`01_Conditions/rsrm_test` in the `ra-env` environment described below. Mappings marked
**by inspection** were derived from the arcpy documentation and the call sites but not run.

---

## 1. The `ra-env` environment

```bash
mamba create -y -n ra-env -c conda-forge python=3.12 \
    gdal rasterio geopandas shapely fiona pyproj \
    numpy scipy pandas openpyxl matplotlib scikit-image \
    rioxarray xarray whitebox pykrige richdem rasterstats
```

Resolved versions used for the verification runs:

| package | version | replaces |
|---|---|---|
| GDAL | 3.12.3 | raster/vector I/O, format conversion, warping |
| rasterio | 1.5.0 | `arcpy.Raster`, raster I/O, `RasterToNumPyArray` |
| geopandas | 1.1.4 | feature classes, attribute tables, cursors |
| shapely | 2.1.2 | `arcpy.Polygon`, `arcpy.Point`, geometry ops |
| pyproj | 3.7.2 | `DefineProjection_management`, coordinate systems |
| numpy | 2.5.1 | all map algebra (`Con`, `Float`, `Int`, `IsNull`, ...) |
| scipy | 1.18.0 | `RegionGroup`, focal filters, `Idw` neighbour search |
| scikit-image | 0.26.0 | morphology, labelling, region properties |
| rasterstats | 0.21.0 | `ZonalStatisticsAsTable`, `TabulateArea` |
| pykrige | 1.7.3 | `sa.Kriging`, `KrigingModelOrdinary` |
| whitebox | 2.3.6 | hydrology/terrain tools, `HillShade`, `Slope`, TIN raster |
| richdem | - | depression filling, flow routing (alternative to whitebox) |
| openpyxl | 3.1.5 | already vendored in `.site_packages/openpyxl` |

Run anything with `mamba run -n ra-env python <script>`.

---

## 2. Inventory

896 `arcpy.*` call sites across 30 modules. Distribution:

| module | call sites | dominant use |
|---|---|---|
| GetStarted | 182 | condition creation, WLE interpolation, detrended DEM |
| SHArC | 133 | HSI raster algebra, habitat area polygons |
| ProjectMaker | 125 | plantings/stabilization delineation, area tables |
| ModifyTerrain | 63 | DEM differencing, grading, RiverBuilder |
| LifespanDesign | 62 | threshold-based raster algebra |
| StrandingRisk | 56 | connectivity, rating curves, ExtractByMask |
| `.site_packages/riverpy` | 48 | shared raster/vector helpers, mapping |
| LifespanAnalysis | 35 | zonal statistics |
| RiparianRecruitment | 27 | recruitment bands, inundation tracking |
| VolumeAssessment | 24 | `SurfaceVolume_3d` earthworks |
| MaxLifespan | 21 | feature action assessment |
| Tools | 6 | standalone helper scripts |

The 20 most frequent calls, with `arcpy.sa` functions imported unqualified via
`from arcpy.sa import *`:

```
253  Con                    101  arcpy.Raster            34  Delete_management
136  Raster                  84  GetMessages             30  GetRasterProperties_management
134  Float                   74  env.workspace           26  CheckOutExtension
112  IsNull                  48  AddError                21  RasterToNumPyArray
 23  Int                     40  env.extent              15  ListRasters
 11  Square                  38  arcpy.sa.*              15  AddField_management
```

The dependency is therefore **overwhelmingly raster map algebra**, not exotic geoprocessing.
Roughly 85 % of the call sites are `Raster` / `Con` / `Float` / `Int` / `IsNull` /
`CellStatistics` / environment settings, all of which map onto plain numpy.

---

## 3. Semantic differences that will silently produce wrong results

These are the traps. They matter more than the function-by-function mapping, because a naive
port compiles, runs, and produces plausible-looking but wrong rasters.

### 3.1 `arcpy.env.extent` performs implicit alignment; numpy does not

arcpy resolves every map-algebra operand against `arcpy.env.extent`, `env.snapRaster` and
`env.cellSize`, resampling and clipping on the fly. Operands with different extents are
aligned without warning. numpy has no such notion: it either raises on shape mismatch, or,
worse, broadcasts and produces a spatially meaningless result.

This is not hypothetical for this project. In the checked-in sample condition:

```
dem.tif             (842, 500)  bounds [1309.5, -320.5, 1559.5, 100.5]
h000098_750.tif     (440, 500)  bounds [1309.5, -220.0, 1559.5,   0.0]
```

`cWaterLevel.interpolate_wle` computes `Con(ras_h > 0, (ras_dem + ras_h))` on exactly these
two rasters, relying entirely on `arcpy.env.extent = ras_dem.extent` to make them conformable.
**Any port must make that alignment explicit.** Verified helper:

```python
from rasterio.enums import Resampling
from rasterio.warp import reproject
import numpy as np

def align(src_arr, src_prof, ref_prof, resampling=Resampling.nearest):
    """arcpy.env.extent + env.snapRaster + env.cellSize, done explicitly."""
    dst = np.full((ref_prof["height"], ref_prof["width"]), np.nan, dtype="float64")
    reproject(source=src_arr, destination=dst,
              src_transform=src_prof["transform"], src_crs=src_prof["crs"],
              dst_transform=ref_prof["transform"], dst_crs=ref_prof["crs"],
              src_nodata=np.nan, dst_nodata=np.nan, resampling=resampling)
    return dst
```

Verified: `h000098_750.tif` resampled from (440, 500) onto the DEM grid (842, 500), 215 000
valid cells preserved.

Use `Resampling.nearest` for anything categorical or where the original cell values must be
preserved exactly (depth, velocity, class rasters), `Resampling.bilinear` only for genuinely
continuous resampling. arcpy's `Resample_management` default is `NEAREST`; the calls in
`cConditionCreator.py` pass `BILINEAR` explicitly for depth and velocity.

### 3.2 NoData is not a value, and this condition mixes three conventions

arcpy tracks a NoData mask per raster and propagates it through every operation. numpy does
not, unless you use `np.nan` (float only) or masked arrays.

The sample condition declares **three different NoData values**, verified by reading every
raster:

| raster group | declared NoData | actually present |
|---|---|---|
| `dem.tif`, most `h*/u*/wse*` | `-999.0` | yes, up to 406 000 cells |
| `h000111_060`, `u000098_750`, `u000111_060`, `wse000098_750`, `wse000111_060` | `3.4e38` (float32 max) | yes |
| `dmean.tif` | `-3.4e38` | none |
| `ex_veg_sc*.tif` | `0.0` | yes, ~37 000 cells |

Consequences for a port:

- Always read with `masked=True` and convert to `np.nan`; never read raw and compare against a
  hard-coded sentinel.
- `arcpy.RasterToNumPyArray(ras, nodata_to_value=0)` is used in 21 places. Under the `-999`
  convention that turns NoData into a legitimate-looking `0`; under the `3.4e38` convention it
  does the same. Any downstream `> 0` test then behaves differently depending on which
  convention the input file happened to use. `cConnectivityAnalysis.py:498` does exactly this.
- `ex_veg_sc*.tif` declaring `NoData = 0` means "no vegetation" is indistinguishable from
  "outside the model domain". A masked read will drop those cells entirely rather than
  treating them as zero vegetation.

**Resolved for the in-repo condition.** `Tools/reconcile_nodata.py` rewrites a condition folder
so every raster declares `config.nodata = -999.0`, preserving the NoData *mask* rather than the
sentinel, so semantics such as `Con(IsNull(veg_ras), ras)` ("no existing vegetation") are
unchanged. Applied to `01_Conditions/rsrm_test`: 10 of 30 rasters rewritten, all 30 now at
-999.0, masks and valid ranges verified identical afterwards. `ex_veg_sc*.tif` were promoted
`uint8 -> int16` so that -999 is representable.

`RiverArchitect-SampleData` was deliberately **not** modified: it is a separate git clone of
upstream sample data, and its 128 analysis rasters are at least internally consistent
(-3.4e38). Reconcile it too if you want one convention everywhere:

```bash
mamba run -n ra-env python Tools/reconcile_nodata.py \
    /home/schwindt/github/RiverArchitect-SampleData/01_Conditions/2100_sample --dry-run
```

### 3.3 `Con` with two arguments produces NoData, not zero

```python
Con(ras_h > 0, ras_dem + ras_h)     # false branch -> NoData
Con(ras_h > 0, ras_dem + ras_h, 0)  # false branch -> 0
```

The two-argument form appears throughout the codebase. The numpy equivalent must use `np.nan`,
not `0`:

```python
np.where(h > 0, dem + h, np.nan)    # correct
np.where(h > 0, dem + h, 0)         # WRONG - creates a wetted-area artefact
```

Verified: false branch correctly NaN over all cells where `h <= 0`.

### 3.4 Integer rasters, `Int()`, and attribute tables

`Int()` truncates toward zero (it is not rounding). `RasterToPolygon_conversion` requires an
integer raster, which is why `fGlobal.raster2shp` wraps its input in `Int()`. `numpy.astype("int32")`
also truncates, so the behaviour matches, but note that `Int(np.nan)` is undefined; mask first.

### 3.5 Shapefile field-name and value limits

`z_field = ras_wse.name[:10]` in `cWaterLevel.py:126` exists because shapefile (DBF) field
names are capped at 10 characters. GeoPandas writing to `.shp` inherits the same limit and
warns. Writing GeoPackage (`.gpkg`) instead removes the constraint and is a strict improvement
if the output format is not externally mandated.

`cWaterLevel.py:118-125` also documents that `RasterToPoint_conversion` loses float precision,
and works around it with an extra `arcpy.sa.Sample` call. A rasterio port does not need the
workaround: `rasterio.transform.xy` on the valid-cell indices returns exact coordinates and the
values come straight from the array at full precision.

---

## 4. Function-by-function mapping

### 4.1 Raster access and properties

| arcpy | open-source | status |
|---|---|---|
| `arcpy.Raster(path)` | `rasterio.open(path)`; `src.read(1, masked=True)` | verified |
| `ras.save(path)` | `rasterio.open(path,"w",**profile).write(arr,1)` | verified |
| `ras.extent` | `src.bounds` | verified |
| `ras.name` | `os.path.basename(src.name)` | by inspection |
| `arcpy.RasterToNumPyArray(ras, nodata_to_value=v)` | `src.read(1, masked=True).filled(v)` | verified |
| `arcpy.NumPyArrayToRaster(arr, ...)` | `rasterio.open(...,"w",**profile).write(arr,1)` | verified |
| `GetRasterProperties_management(r,"CELLSIZEX")` | `abs(src.transform.a)` | verified |
| `GetRasterProperties_management(r,"MEAN")` | `np.nanmean(arr)` | verified |
| `arcpy.Exists(path)` | `os.path.exists(path)` | trivial |
| `arcpy.ListRasters()` | `glob.glob(os.path.join(ws,"*.tif"))` | trivial |
| `arcpy.Delete_management(path)` | `os.remove` / `shutil.rmtree` | trivial |
| `arcpy.CopyRaster_management(src,dst)` | `shutil.copy` or `gdal.Translate` | trivial |
| `arcpy.Resample_management(r,out,cell_size,BILINEAR)` | `src.read(out_shape=..., resampling=Resampling.bilinear)` | verified |
| `arcpy.CompositeBands_management([a,b],out)` | multiband `rasterio` write (`profile["count"]=n`) | verified |
| `arcpy.Describe(x)` | `src.profile` / `gdf.crs` / `fiona.open(...).schema` | by inspection |
| `DefineProjection_management(shp, cs)` | `gdf.set_crs(epsg, allow_override=True)` | by inspection |
| `arcpy.management.GetCellValue(r,xy)` | `next(src.sample([(x,y)]))` | by inspection |
| `BuildRasterAttributeTable` | not needed; use `np.unique(arr, return_counts=True)` | n/a |

Reading pattern used throughout the verification:

```python
def read(path):
    """arcpy.Raster(path) -> (array with NoData as np.nan, profile)."""
    with rasterio.open(path) as src:
        a = src.read(1, masked=True).astype("float64")
        prof = src.profile
    return np.ma.filled(a, np.nan), prof
```

### 4.2 Map algebra (`arcpy.sa`)

| arcpy.sa | numpy | status |
|---|---|---|
| `Con(cond, t)` | `np.where(cond, t, np.nan)` | verified |
| `Con(cond, t, f)` | `np.where(cond, t, f)` | verified |
| `IsNull(r)` | `np.isnan(r)` | verified |
| `Con(IsNull(r), 0, r)` | `np.where(np.isnan(r), 0, r)` or `np.nan_to_num(r)` | verified |
| `SetNull(cond, r)` | `np.where(cond, np.nan, r)` | verified |
| `Float(r)` | `r.astype("float64")` | verified |
| `Int(r)` | `r.astype("int32")` (truncates, as arcpy does) | verified |
| `Abs`, `Square`, `SquareRoot`, `Power` | `np.abs`, `np.square`, `np.sqrt`, `np.power` | verified |
| `Log10`, `Ln`, `Exp` | `np.log10`, `np.log`, `np.exp` | trivial |
| `Sin`, `Cos` | `np.sin`, `np.cos` (arcpy takes radians) | trivial |
| `CellStatistics([...], "MAXIMUM", "DATA")` | `np.nanmax(np.stack(rasters), axis=0)` | verified |
| `CellStatistics([...], "MINIMUM"/"MEAN"/"SUM", "DATA")` | `np.nanmin` / `np.nanmean` / `np.nansum` | verified |
| `Reclassify(r,"Value",RemapValue([[1,10],...]))` | lookup array or `np.select` | verified |
| `Reclassify(... RemapRange ...)` | `np.digitize(arr, bins)` | verified |

`CellStatistics(..., "DATA")` ignores NoData cells, which is exactly `np.nan*` reduction
semantics. `"NODATA"` (propagate) would instead be plain `np.max`/`np.sum`. All call sites in
this repository use `"DATA"`.

Note the `RuntimeWarning: All-NaN slice encountered` that `np.nanmax` emits when every operand
is NoData at a cell; arcpy silently returns NoData there. Suppress with
`np.errstate(invalid="ignore")` or `warnings.catch_warnings()`, and confirm the result is NaN.

### 4.3 Raster <-> vector conversion

| arcpy | open-source | status |
|---|---|---|
| `RasterToPolygon_conversion(Int(r), out, "NO_SIMPLIFY")` | `rasterio.features.shapes(arr, mask, transform)` -> `gpd.GeoDataFrame` | verified |
| `PolygonToRaster_conversion(shp, field, out, cellsize)` | `rasterio.features.rasterize(shapes, out_shape, transform)` | verified |
| `FeatureToRaster_conversion` | same as above | verified |
| `RasterToPoint_conversion(r, out)` | `rasterio.transform.xy(tr, *np.where(np.isfinite(arr)))` | verified |
| `PointToRaster_conversion` | `rasterio.features.rasterize` with point geometries | by inspection |
| `sa.ExtractByMask(r, mask_fc)` | `rasterio.mask.mask(src, geoms, crop=True)` | verified |
| `sa.ExtractValuesToPoints` | `list(src.sample(coords))` | by inspection |
| `sa.Sample(r, pts, out)` | `list(src.sample(coords))` | by inspection |
| `raster2shp` + `CalculateGeometryAttributes(AREA)` | `gdf["F_AREA"] = gdf.geometry.area` | verified |

Verified round-trip on the sample data: polygonizing the wetted area at Q = 98.75 gives a total
of **53 750.0 m²**, exactly matching the cell-count cross-check (`n_cells * cellsize²`), and
re-rasterizing the polygons reproduces the source mask with **100.00 % cell agreement**.

`rasterio.features.shapes` uses 4-connectivity by default (`connectivity=4`), matching arcpy's
`RasterToPolygon` default. Pass `connectivity=8` if diagonal joins are wanted.

### 4.4 Interpolation (the WLE workflow)

`GetStarted/cWaterLevel.py` offers four schemes. Verified replacements:

| arcpy | open-source | status |
|---|---|---|
| `arcpy.Idw_3d(..., search_radius="Variable 12")` | `scipy.spatial.cKDTree` k=12, weights `1/d²` | verified |
| `arcpy.Idw_3d(..., search_radius="VARIABLE 1")` ("Nearest Neighbor") | `cKDTree` k=1, or `scipy.interpolate.griddata(method="nearest")` | verified |
| `sa.Kriging(..., KrigingModelOrdinary("Spherical", lagSize=...))` | `pykrige.ok.OrdinaryKriging(variogram_model="spherical", nlags=...)` | verified |
| `arcpy.EmpiricalBayesianKriging_ga` (Geostatistical Analyst) | no direct equivalent; see gaps | - |
| `arcpy.SearchNeighborhoodStandardCircular(nbrMin, nbrMax)` | `cKDTree.query_ball_point` / `k=` argument | by inspection |

IDW with 12 neighbours and power 2, matching the arcpy parameters:

```python
from scipy.spatial import cKDTree
tree = cKDTree(pts)                       # pts = source point coordinates
d, i = tree.query(target, k=12)           # target = grid cell centres
d = np.maximum(d, 1e-12)                  # guard against exact coincidence
w = 1.0 / d ** 2.0
z = (w * vals[i]).sum(1) / w.sum(1)
```

Verified on `wse000098_750.tif`: 8 600 source points interpolated onto the 842 x 500 DEM grid.
Output range 2002.45 .. 2002.69, identical to the source value range, i.e. the interpolator does
not overshoot (as expected for inverse-distance weighting, which is bounded by its inputs).
Nearest-neighbour gave the same range.

Ordinary kriging with a spherical variogram ran successfully via pykrige. Two practical notes:

- pykrige exposes the **kriging variance** as the second return value of `execute()`. That is
  the `out_variance_prediction_raster` output which is currently commented out in
  `cWaterLevel.py:146-148` and `256-259`. The open-source route makes reinstating it free.
- Kriging is O(n³) in the number of source points. arcpy's `search_radius="Variable 12"` makes
  it local; pykrige's `OrdinaryKriging` is global by default. For realistic point counts use
  `pykrige.ok.OrdinaryKriging(..., n_closest_points=12, backend="loop")` in `execute()`, or
  subsample. The verification used a coarse grid deliberately to keep runtime bounded.

The arcpy code retries kriging with a doubled `lagSize` when it hits error `010079`
("could not fit semivariogram"). pykrige raises a plain `ValueError` in the analogous case; the
retry loop translates directly, with `nlags` in place of `lagSize`.

### 4.5 Zonal, tabular and vector operations

| arcpy | open-source | status |
|---|---|---|
| `sa.ZonalStatisticsAsTable(zones, field, value_ras, out)` | `rasterstats.zonal_stats(zones, raster, stats=[...])` | verified |
| `sa.TabulateArea` | `np.digitize` + `value_counts() * cell_area`, or `zonal_stats(categorical=True)` | verified |
| `AddField_management` | `gdf["name"] = ...` | verified |
| `CalculateField_management(shp, f, expr, "PYTHON", code_block)` | `gdf["f"] = gdf[...].map(...)` / `.apply(...)` | verified |
| `CalculateGeometryAttributes_management(..., "AREA")` | `gdf.geometry.area` | verified |
| `SelectLayerByAttribute_management(lyr,"NEW_SELECTION",expr)` | boolean mask `gdf[gdf.F_AREA > x]` | verified |
| `MakeFeatureLayer_management` | no equivalent needed; a filtered GeoDataFrame *is* the layer | n/a |
| `da.SearchCursor(fc, [fields])` | `gdf[fields].itertuples()` | verified |
| `da.UpdateCursor` | direct assignment on the GeoDataFrame | by inspection |
| `da.TableToNumPyArray` / `da.FeatureClassToNumPyArray` | `gdf[cols].to_records(index=False)` | verified |
| `SpatialJoin_analysis(target, join)` | `geopandas.sjoin(left, right, how, predicate)` | verified |
| `CopyFeatures_management` | `gdf.to_file(path)` | trivial |
| `TableToTable_conversion(shp, dir, "x.txt")` | `gdf.drop(columns="geometry").to_csv(path)` | trivial |
| `GetCount_management` | `len(gdf)` | trivial |
| `ListFields` | `gdf.columns` | trivial |
| `CreateFeatureclass_management` | `gpd.GeoDataFrame(...).to_file(...)` | trivial |

Verified: `zonal_stats` over the wetted-area polygon against `u000098_750.tif` returned
count = 215 000, mean = 0.608, max = 1.179, consistent with the raster's own statistics.
`sjoin` matched 2 of 3 test points to their containing polygon.

Note `rasterstats.zonal_stats` needs the NoData value passed explicitly when the raster's
declared NoData is one of the `3.4e38` files (see §3.2), otherwise those cells enter the
statistics.

### 4.6 Connectivity and region grouping (StrandingRisk)

`StrandingRisk/cConnectivityAnalysis.py` polygonizes the wetted area, computes polygon areas,
and treats every polygon except the largest as disconnected (a fish-stranding pool). The
raster-native equivalent is a connected-component labelling:

```python
from scipy import ndimage
structure = ndimage.generate_binary_structure(2, 1)     # 4-connected, arcpy default
lab, n = ndimage.label(binary, structure=structure)
sizes = ndimage.sum(binary, lab, range(1, n + 1))
main = int(np.argmax(sizes)) + 1
disconnected = (lab > 0) & (lab != main)
```

Verified on a synthetic pattern with a known diagonal bridge: 4-connectivity found 3 regions,
8-connectivity (`structure=np.ones((3,3))`) correctly merged the diagonally-adjacent pair into
2 regions. The "all but the largest region" rule reproduced the expected 10 disconnected cells.

**Use `RiverArchitect-SampleData` for this, not `rsrm_test`.** At every discharge in
`rsrm_test` the wetted area forms exactly one connected region (Q = 1.06: 3 750 m²,
Q = 3.89: 4 750 m², Q = 25.40: 30 250 m², single-region under both 4- and 8-connectivity),
because that condition is an idealized prismatic channel with a constant `dmean` of 0.001 and
monotonically growing depths. It cannot exercise StrandingRisk at all.

`RiverArchitect-SampleData/01_Conditions/2100_sample` (real gravel-cobble reach, US customary)
does: **all 60 depth rasters produce disconnected pools**, from 2 pools at Q = 300 cfs to 119
pools at Q = 7 250 cfs, with stranded areas of 18 to 3 060 ft². Pool counts peak around
Q = 7 250 and again at Q = 10 000, which is the behaviour the module exists to quantify. This
is the condition to regression-test connectivity against.

### 4.7 Surface analysis

| arcpy | open-source | status |
|---|---|---|
| `sa.Slope(dem, "DEGREE")` | `np.gradient` + `np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))`, or `whitebox.slope()`, or `gdal.DEMProcessing(..., "slope")` | verified |
| `arcpy.HillShade_3d(r, out, azimuth, altitude)` | `gdal.DEMProcessing(out, dem, "hillshade", azimuth=, altitude=)` or `matplotlib.colors.LightSource` | by inspection |
| `arcpy.SurfaceVolume_3d(r, "", "ABOVE", plane, z_factor)` | `riverpy/fVolume.surface_volume()` | verified |
| `sa.Fill` | `richdem.FillDepressions` or `whitebox.fill_depressions()` | by inspection |

**Resolved in favour of the triangulated method.** `arcpy.SurfaceVolume_3d` integrates under a
*triangulated* surface through the cell centres; a cell-prism sum (`sum(z) * cell_area`)
instead carries a boundary error proportional to the perimeter of the surface. On a flat 10 x
10 m test surface the prism sum overestimates by 21 %, and that error does not vanish under
refinement for surfaces truncated at their edge. Earthworks quantities are a reported
deliverable, so the triangulated result is authoritative.

`.site_packages/riverpy/fVolume.py` implements it in pure numpy (no arcpy, no 3D Analyst, no
GDAL): every 2 x 2 block of cell centres is split into two triangles, and the volume between
each triangle and the reference plane is integrated in closed form, clipping triangles that
cross the plane. `VolumeAssessment/cVolumeAssessment.py` now calls it instead of
`SurfaceVolume_3d`, which also removes the fragile string-parsing of the geoprocessing message
(`feat_vol.getMessage(1).split("Volume=")[1]`) and the 3D Analyst checkout.

Verified against 11 cases with exact analytical answers: flat surfaces, tilted planes, planes
crossing the reference (clipping), non-zero reference planes, `reference="BELOW"`, anisotropic
cells, NoData exclusion, and draped surface area on a 45-degree slope (100·√2). Grid-refinement
on a pyramid converges to the exact volume (1330.0 → 1332.5 → 1333.125 → 1333.28 against an
exact 1333.33). The function also returns planimetric and draped (3-D) surface area, which
`SurfaceVolume_3d` reported and the old code discarded.

`whitebox` (`whitebox.WhiteboxTools()`) covers slope, aspect, curvature, hillshade, flow
accumulation, depression filling, and TIN gridding as a single dependency and is the closest
functional analogue to Spatial Analyst + 3D Analyst.

### 4.8 TIN (`ModifyTerrain/RiverBuilder/RiverBuilderRenderer.py`)

| arcpy | open-source |
|---|---|
| `MakeXYEventLayer_management(csv,'X','Y',lyr)` | `gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.X, df.Y))` |
| `CreateTin_3d(name)` + `EditTin_3d(..., Mass_Points, Soft_Clip)` | `scipy.spatial.Delaunay(points)`, clip with the boundary polygon |
| `TinRaster_3d(tin, out, 'FLOAT', 'LINEAR', 'CELLSIZE n')` | `scipy.interpolate.LinearNDInterpolator(tri, z)` evaluated on the target grid, or `whitebox.lidar_tin_gridding()` |
| `HillShade_3d(...)` | `gdal.DEMProcessing(..., "hillshade")` |

Linear interpolation over a Delaunay triangulation is mathematically the same operation as
arcpy's `TinRaster` with `LINEAR` interpolation, so this path should reproduce closely.

### 4.9 Environment, licensing and messaging

| arcpy | replacement |
|---|---|
| `arcpy.CheckOutExtension('Spatial')` / `'3D'` | delete; the `@spatial_license` decorator in `fGlobal.py` becomes a no-op |
| `arcpy.env.workspace` | pass explicit paths; do not rely on process-global state |
| `arcpy.env.extent` / `snapRaster` / `cellSize` | the explicit `align()` helper in §3.1 |
| `arcpy.env.overwriteOutput` / `arcpy.gp.overwriteOutput` | delete; `rasterio.open(...,"w")` overwrites |
| `arcpy.env.outputCoordinateSystem` | `dst_crs` in `reproject`, or `gdf.to_crs()` |
| `arcpy.GetMessages(2)` / `AddError` / `AddMessage` | the existing `logging.getLogger("logfile")` |
| `arcpy.ExecuteError` | `rasterio.errors.RasterioError`, `RuntimeError`, or a project-local exception |
| `arcpy.GetParameterAsText` / `GetParameter` | `argparse`; only used in the standalone `Tools/` scripts |

Removing `arcpy.env.workspace` is worth calling out separately. It is process-global mutable
state that interacts badly with `parent_gui.py`'s per-tab `os.chdir` (see `CLAUDE.md`).
Several modules set `arcpy.env.workspace` in one method and depend on it in another; that
coupling disappears entirely once paths are explicit, and it is a plausible source of
order-dependent bugs.

---

## 5. Where there is no clean equivalent

| arcpy feature | situation |
|---|---|
| `arcpy.mp.ArcGISProject` (`.aprx`), `LayerFile` (`.lyrx`), `PDFDocumentCreate`, `exportToPDF`, layout/legend/mapframe elements | **Done.** `riverpy/cMapper.py` was rewritten against QGIS print layouts and no longer imports `arcpy`; the page series now uses a QGIS Atlas instead of stitching per-page PDFs. `.lyrx` symbology was migrated to `.qml` with `Tools/lyrx2qml.py`. See `docs/qgis_mapping.md`. |
| `arcpy.EmpiricalBayesianKriging_ga` | Geostatistical Analyst. No direct port. Closest options: `gstools` with a fitted variogram ensemble, or `scikit-learn` Gaussian process regression. Only used as one of four selectable WLE methods, so it can be dropped from the dropdown rather than reimplemented. |
| Esri Grid rasters (`.save(path_without_extension)`) | GDAL reads Esri Grid (AIG driver) but does not write it. Several modules save to extensionless paths, producing Esri Grids, then re-open them. Port these to `.tif`. Note the 13-character name limit on Esri Grids, which is why some cache raster names are cryptic. |
| File geodatabase write (`.gdb`) | GDAL's OpenFileGDB driver supports reading and, since GDAL 3.6, writing. `02_Maps/river_template.gdb` is only used by the mapping path. |

---

## 6. Suggested porting order

1. **`.site_packages/riverpy/fGlobal.py`** (`raster2shp`, `shp2raster`, `spatial_license`,
   `err_info`) and a new `align()`/`read()`/`write()` raster helper module. Everything else
   depends on these, and they are only 48 call sites.
2. **LifespanDesign / MaxLifespan** - pure threshold map algebra, the most mechanical
   conversion, and the module with published reference results (Schwindt et al. 2019) to
   validate against.
3. **GetStarted** (`cWaterLevel`, `cDetrendedDEM`, `cConditionCreator`) - highest call count,
   but the interpolation replacements are already verified above.
4. **SHArC / RiparianRecruitment / StrandingRisk** - depend on 1-3.
5. **VolumeAssessment** - trivial once the cell-sum-vs-TIN question in §4.7 is decided.
6. **`cMapper`** - separate project, QGIS-based.

Keeping the numpy layer behind the same function signatures the `c*.py` classes already use
means the GUI layer (`child_gui.py`, `*_gui.py`) needs no changes at all.

---

## 7. Defects found

### Fixed

1. **`fGlobal.py` - the entire import block failed on Python 3.10+.** `from collections import
   Iterable` has raised `ImportError` since Python 3.10 (the name moved to `collections.abc`
   in 3.3). The bare `except` around the import block swallowed it, so `numpy`, `bisect_left`,
   `glob`, `time` and `webbrowser` were all silently absent from `fGlobal`'s namespace, and
   every function depending on them failed later with `NameError` far from the cause. This is
   the most likely explanation for broad, hard-to-localise breakage on a recent ArcGIS Pro
   Python. Fixed to import from `collections.abc`; `fGlobal` now imports cleanly and `flatten`,
   `write_Q_str`, `read_Q_str` were re-verified.

2. **`GetStarted/cWaterLevel.py` - the kriging retry could never succeed.** In the
   `except arcpy.ExecuteError` handler the `while empty_bins` retry loop was nested inside
   `if "010079" in ...`, but the trailing `self.logger.info(arcpy.AddError(...))` and
   `return True` sat at the *same* indentation as that `if`. Even when a retry produced a
   valid raster, control fell through and the method returned `True`, which callers read as
   failure. Restructured so a successful retry breaks out to the shared save block and any
   non-010079 error returns immediately.

3. **`cWaterLevel.py` - `cell_size` was a string.**
   `GetRasterProperties_management(...).getOutput(0)` returns a *string*, and it is localised
   (comma decimal separator on non-English systems). `lagSize=cell_size * itr` therefore
   repeated the string ("0.50.5") instead of multiplying, so the retry fed nonsense lag sizes
   to `KrigingModelOrdinary`. Now coerced to `float` with a comma-to-dot fallback.

4. **`fGlobal.raster2shp` - `area_unit` received a file path.**
   `area_unit=out_shp_name` passed the output shapefile name where a unit keyword belongs.
   `raster2shp` now takes a `unit` argument ("us"/"si") and resolves it through the new
   `fGlobal.area_unit_str()` helper.

   Correction to an earlier claim: `ProjectMaker/s30_terrain_stabilization.py:192` is **not**
   affected. It passes `area_units`, correctly set to `SQUARE_FEET_US` or `SQUARE_METERS` at
   lines 34/38. Only `raster2shp` had the bug, and it currently has no callers, so it was
   latent rather than active.

5. **Mixed NoData conventions.** `01_Conditions/rsrm_test` has been reconciled to
   `config.nodata = -999.0` with `Tools/reconcile_nodata.py` (10 of 30 rasters rewritten;
   masks and valid data verified unchanged). See §3.2.

### Open

6. **`cWaterLevel.calculate_h` and `calculate_d2w` have no success return.**
   `interpolate_wle` returns `False` on success and `True` on error, but the other two fall
   off the end returning `None`. `None` is falsy so callers behave correctly today, but the
   asymmetry makes the error contract easy to get wrong in new code. Left alone because
   changing it without being able to run the callers is a gratuitous risk.

7. **`cWaterLevel.calculate_d2w` gates on `ras_wle > 0`.** WLE is an absolute elevation
   (about 2002 m in `rsrm_test`, about 200 ft in the SampleData condition). For a project
   referenced to a datum where water levels are negative, every cell would be dropped as
   NoData. `IsNull` would be the intent-preserving test. Not changed, because it alters
   analysis results and should be a deliberate decision.

8. **21 call sites still use `RasterToNumPyArray(..., nodata_to_value=0)`**, which converts
   NoData into a legitimate-looking zero. Now that inputs are reconciled to -999.0 the
   behaviour is at least consistent, but `0` remains a poor sentinel for depth and velocity
   rasters where zero is a valid measurement.

---

## 8. Reproducing the verification

The validation scripts live in the session scratchpad and are not part of the repository. They
exercised the mappings above against `01_Conditions/rsrm_test`:

- 22 of 24 mappings passed on the first run. The two "failures" were incorrect assertions in
  the harness, not mapping failures: `dem.tif` contains zero NoData cells (so a masked read
  correctly masks nothing), and the wetted area at Q = 98.75 is a single connected region (so
  no disconnected pools exist to find). Both were re-checked separately and confirmed in §3.2
  and §4.6.
- The remaining zonal, tabular, vector and connectivity mappings were verified in a second and
  third pass, including the 4- vs 8-connectivity distinction and the polygonize/rasterize
  round trip.
