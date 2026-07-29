try:
    import os, sys
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys).")

# Paths are built with os.path.join / os.sep instead of hard-coded "\\" so that the same
# constants resolve on Windows (os.sep == "\\", byte-identical to the previous values) and
# on POSIX, where the QGIS-based mapping and the open-source tooling are developed and
# tested. Note that individual modules still concatenate their own "\\" sub-paths; those are
# migrated separately.

_here = os.path.dirname(os.path.abspath(__file__))          # .../.site_packages/riverpy
_site_packages = os.path.abspath(os.path.join(_here, os.pardir))
_ra = os.path.abspath(os.path.join(_here, os.pardir, os.pardir))


def _d(*parts):
    """Directory path with a trailing separator (callers concatenate file names directly)."""
    return os.path.join(*parts) + os.sep


def _f(*parts):
    """File path without a trailing separator."""
    return os.path.join(*parts)


code_icon = _f(_site_packages, "templates", "code_icon.ico")

dir2ra = _d(_ra)
dir2co = _d(_ra, "StrandingRisk")
dir2rp = _d(_ra, "RiparianRecruitment")
dir2conditions = _d(_ra, "01_Conditions")
dir2flows = _d(_ra, "00_Flows")
dir2gs = _d(_ra, "GetStarted")
dir2lf = _d(_ra, "LifespanDesign")
dir2map = _d(_ra, "02_Maps")
dir2map_templates = _d(_ra, "02_Maps", "templates")
dir2ml = _d(_ra, "MaxLifespan")
dir2mt = _d(_ra, "ModifyTerrain")
dir2oxl = _d(_site_packages, "openpyxl")
dir2pm = _d(_ra, "ProjectMaker")
dir2rb = _d(_ra, "ModifyTerrain", "RiverBuilder")
dir2ripy = _d(_here)
dir2templates = _d(_site_packages, "templates")
dir2sh = _d(_ra, "SHArC")
dir2va = _d(_ra, "VolumeAssessment")
dir2output = _d(_ra, "LifespanDesign", "Output", "Rasters")

ft2ac = float(1 / 43560)
ft2m = 0.3048

# Canonical NoData value for every raster River Architect writes. Input conditions are
# reconciled to this value with Tools/reconcile_nodata.py. Never test cell values against
# this constant directly - always go through the raster's declared NoData mask (arcpy:
# IsNull(); rasterio: read(masked=True)), because third-party inputs may still carry
# -3.4e38, 3.4e38, 0 or -9999.
nodata = -999.0

empty_file = _f(_site_packages, "templates", "oups.txt")
xlsx_aqua = _f(_site_packages, "templates", "Fish.xlsx")
xlsx_dummy = _f(_site_packages, "templates", "empty.xlsx")
xlsx_mu = _f(_site_packages, "templates", "morphological_units.xlsx")
xlsx_reaches = _f(_ra, "ModifyTerrain", ".templates", "computation_extents.xlsx")
xlsx_thresholds = _f(_ra, "LifespanDesign", ".templates", "threshold_values.xlsx")
xlsx_volumes = _f(_ra, "VolumeAssessment", ".templates", "volumes_template.xlsx")
xlsx_connectivity = _f(_ra, "StrandingRisk", ".templates", "disconnected_area_template.xlsx")
xlsx_recruitment_parameters = _f(_ra, "RiparianRecruitment", ".templates", "recruitment_parameters.xlsx")
xlsx_recruitment_output = _f(_ra, "RiparianRecruitment", ".templates", "recruitment_area_template.xlsx")
