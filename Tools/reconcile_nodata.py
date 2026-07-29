#!/usr/bin/python
""" Reconcile the NoData value of every raster in a condition folder to River Architect's
canonical NoData value (config.nodata = -999.0).

Rationale
---------
Conditions assembled from different preprocessing chains carry inconsistent NoData values
(-3.4e38, +3.4e38, 0.0, -9999, -128, ...). All of them are *declared* in the GeoTIFF header,
so a mask-aware read handles them correctly - but 21 call sites in River Architect use
arcpy.RasterToNumPyArray(..., nodata_to_value=0) or compare cell values directly, and those
behave differently depending on which sentinel the input file happens to use.

This tool rewrites the sentinel while preserving the NoData *mask* exactly. Cells that were
NoData before are still NoData afterwards, so raster semantics (e.g. IsNull(veg_ras) meaning
"no existing vegetation") are unchanged.

Usage
-----
    mamba run -n ra-env python reconcile_nodata.py <directory> [--dry-run] [--recursive]

    # a single condition
    python reconcile_nodata.py ../01_Conditions/rsrm_test
    # preview only
    python reconcile_nodata.py ../01_Conditions/rsrm_test --dry-run

Requires rasterio/GDAL (the `ra-env` environment); it does not use arcpy, so it runs on any
platform. Stale .aux.xml / .ovr sidecars are removed so that statistics and pyramids are
rebuilt from the corrected data.
"""

import argparse
import glob
import os
import sys

try:
    import numpy as np
    import rasterio
except ImportError:
    print("ERROR: This tool needs numpy and rasterio. Run it in the `ra-env` environment:\n"
          "       mamba run -n ra-env python reconcile_nodata.py <directory>")
    sys.exit(1)

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) +
                    os.sep + ".site_packages" + os.sep + "riverpy")
    import config
    NODATA = config.nodata
except ImportError:
    NODATA = -999.0

SIDECAR_SUFFIXES = (".aux.xml", ".ovr")


def representable(value, dtype):
    """True if `value` can be stored in `dtype` without overflow or truncation."""
    info = np.iinfo(dtype) if np.issubdtype(np.dtype(dtype), np.integer) else np.finfo(dtype)
    return info.min <= value <= info.max


def target_dtype(dtype):
    """Return a dtype that can hold NODATA, promoting the original as little as possible."""
    if representable(NODATA, dtype):
        return dtype
    if np.issubdtype(np.dtype(dtype), np.integer):
        for candidate in ("int16", "int32", "int64"):
            if representable(NODATA, candidate):
                return candidate
    return "float32"


def remove_sidecars(path, dry_run):
    for suffix in SIDECAR_SUFFIXES:
        for stale in (path + suffix, os.path.splitext(path)[0] + suffix):
            if os.path.isfile(stale):
                if dry_run:
                    print("        would remove stale sidecar %s" % os.path.basename(stale))
                else:
                    try:
                        os.remove(stale)
                    except OSError as e:
                        print("        WARNING: could not remove %s (%s)" % (stale, e))


def reconcile(path, dry_run=False):
    """Rewrite one raster so that its NoData value is NODATA. Returns True if changed."""
    with rasterio.open(path) as src:
        old_nodata = src.nodata
        profile = src.profile.copy()
        band = src.read(1, masked=True)
        n_masked = int(np.ma.count_masked(band))

    name = os.path.basename(path)

    if old_nodata is not None and float(old_nodata) == float(NODATA):
        print("    %-24s already %.1f (%d NoData cells) - skipped" % (name, NODATA, n_masked))
        return False

    if old_nodata is None:
        # No declared NoData: there is no mask to preserve, so only declare the value.
        # Do NOT invent a mask, that would silently delete valid cells.
        print("    %-24s no NoData declared - only tagging header" % name)
        if not dry_run:
            with rasterio.open(path, "r+") as dst:
                dst.nodata = NODATA
            remove_sidecars(path, dry_run)
        return True

    new_dtype = target_dtype(profile["dtype"])
    promoted = " (dtype %s -> %s)" % (profile["dtype"], new_dtype) \
        if new_dtype != profile["dtype"] else ""

    print("    %-24s %s -> %.1f, %d NoData cells%s"
          % (name, str(old_nodata), NODATA, n_masked, promoted))
    if dry_run:
        return True

    profile.update(dtype=new_dtype, nodata=NODATA)
    filled = band.astype(new_dtype).filled(NODATA)

    tmp = path + ".reconcile.tmp"
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(filled, 1)

    # Verify before replacing the original.
    with rasterio.open(tmp) as check:
        verify = check.read(1, masked=True)
        if int(np.ma.count_masked(verify)) != n_masked:
            os.remove(tmp)
            raise RuntimeError("mask changed for %s (%d -> %d NoData cells); aborted"
                               % (name, n_masked, int(np.ma.count_masked(verify))))

    os.replace(tmp, path)
    remove_sidecars(path, dry_run)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", help="condition folder holding the rasters")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    parser.add_argument("--recursive", action="store_true", help="descend into sub-folders")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print("ERROR: not a directory: %s" % args.directory)
        return 1

    pattern = "**/*.tif" if args.recursive else "*.tif"
    rasters = sorted(glob.glob(os.path.join(args.directory, pattern), recursive=args.recursive))
    if not rasters:
        print("No .tif rasters found in %s" % args.directory)
        return 1

    print("Reconciling NoData to %.1f in %s%s\n%d rasters found\n"
          % (NODATA, args.directory, " (dry run)" if args.dry_run else "", len(rasters)))

    changed = failed = 0
    for path in rasters:
        try:
            if reconcile(path, args.dry_run):
                changed += 1
        except Exception as e:
            failed += 1
            print("    ERROR %-24s %s" % (os.path.basename(path), e))

    print("\n%d/%d rasters %s, %d unchanged, %d failed"
          % (changed, len(rasters), "would change" if args.dry_run else "changed",
             len(rasters) - changed - failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
