#!/usr/bin/python
""" Triangulated-surface volume computation.

Replaces arcpy.SurfaceVolume_3d (3D Analyst) with an equivalent, license-free implementation.

Why triangulated and not a cell sum
-----------------------------------
Summing `z * cell_area` treats every cell as a vertical prism, which overestimates or
underestimates by a boundary term proportional to the perimeter of the surface. arcpy's
SurfaceVolume_3d instead integrates under the *triangulated* surface through the cell
centres, so cut and fill quantities are continuous under grid refinement. River Architect
reports earthworks quantities, so the triangulated result is authoritative.

The surface is built exactly as a TIN over the raster cell centres: every 2x2 block of
neighbouring centres forms a quad that is split into two triangles. Over each triangle the
elevation varies linearly, and the volume between the triangle and a horizontal reference
plane is integrated in closed form, clipping the triangle where it crosses the plane.

This module is pure numpy - it has no arcpy or GDAL dependency and can be tested anywhere.
"""

try:
    import numpy as np
except ImportError:
    print("ExceptionERROR: Missing fundamental package (required: numpy).")


def _triangle_volume_above(z1, z2, z3, area):
    """Volume between a planar triangle and the z = 0 plane, counting only z > 0.

    For a linear function over a triangle, the integral of z is area * mean(z). The integral
    of max(z, 0) is obtained by subtracting the integral over the sub-region where z < 0,
    which is itself a triangle similar to the original whenever exactly one vertex is
    negative (and the complement of one when exactly one vertex is positive).

    All arguments are arrays of equal shape; the computation is fully vectorised.
    """
    z = np.stack([z1, z2, z3])
    n_pos = (z > 0).sum(axis=0)

    volume = np.zeros(z1.shape, dtype="float64")

    # --- all three vertices above the plane: plain mean-height prism ---------------
    all_pos = n_pos == 3
    if all_pos.any():
        volume[all_pos] = area * z[:, all_pos].mean(axis=0)

    # --- exactly one vertex above the plane ---------------------------------------
    # The positive region is a triangle similar to the original, sharing the positive
    # vertex P. Its edges are cut where z = 0, at parameters s_i = z_P / (z_P - z_Ni).
    # Similar triangle => area_pos = area * s_1 * s_2, and the linear function over it
    # runs from z_P down to 0 at both cut points, so the integral is area_pos * z_P / 3.
    one_pos = n_pos == 1
    if one_pos.any():
        zs = z[:, one_pos]
        pos_idx = np.argmax(zs > 0, axis=0)
        cols = np.arange(zs.shape[1])
        z_p = zs[pos_idx, cols]
        neg = np.stack([zs[(pos_idx + 1) % 3, cols], zs[(pos_idx + 2) % 3, cols]])
        s = z_p / (z_p - neg)                      # both denominators are > 0 here
        volume[one_pos] = area * s[0] * s[1] * z_p / 3.0

    # --- exactly two vertices above the plane -------------------------------------
    # Integral of max(z, 0) = integral(z) over the whole triangle minus integral(z) over
    # the negative corner triangle (which is negative, hence the subtraction adds back).
    two_pos = n_pos == 2
    if two_pos.any():
        zs = z[:, two_pos]
        neg_idx = np.argmin(zs > 0, axis=0)
        cols = np.arange(zs.shape[1])
        z_n = zs[neg_idx, cols]
        pos = np.stack([zs[(neg_idx + 1) % 3, cols], zs[(neg_idx + 2) % 3, cols]])
        t = -z_n / (pos - z_n)                     # both denominators are > 0 here
        area_neg = area * t[0] * t[1]
        volume[two_pos] = area * zs.mean(axis=0) - area_neg * z_n / 3.0

    # n_pos == 0 leaves volume at 0, which is correct for "above".
    return volume


def surface_volume(z, dx, dy, plane=0.0, reference="ABOVE"):
    """Volume between a raster surface and a horizontal reference plane.

    Equivalent to arcpy.SurfaceVolume_3d(in_surface, "", reference, plane, 1.0).

    Args:
        z (np.ndarray): 2-D elevation array. NoData cells must be np.nan.
        dx (float): cell size in x (map units).
        dy (float): cell size in y (map units).
        plane (float): reference plane elevation.
        reference (str): "ABOVE" for the volume between the plane and the surface where the
            surface lies above it, "BELOW" for the volume where it lies below.

    Returns:
        dict: {"volume": float, "area_2d": float, "area_3d": float}
            volume  - cubic map units
            area_2d - planimetric area contributing to the volume
            area_3d - surface (draped) area contributing to the volume

    Triangles touching a NoData cell are omitted, matching arcpy's behaviour of building the
    TIN only over cells that carry data.
    """
    z = np.asarray(z, dtype="float64")
    if z.ndim != 2:
        raise ValueError("surface_volume expects a 2-D array, got shape %s" % (z.shape,))
    if z.shape[0] < 2 or z.shape[1] < 2:
        return {"volume": 0.0, "area_2d": 0.0, "area_3d": 0.0}

    h = z - float(plane)
    if str(reference).upper() == "BELOW":
        h = -h
    elif str(reference).upper() != "ABOVE":
        raise ValueError("reference must be 'ABOVE' or 'BELOW', got %r" % reference)

    # Corners of every quad spanned by four neighbouring cell centres.
    ul, ur = h[:-1, :-1], h[:-1, 1:]
    ll, lr = h[1:, :-1], h[1:, 1:]

    tri_area = 0.5 * abs(dx) * abs(dy)
    volume = 0.0
    area_2d = 0.0
    area_3d = 0.0

    # Split each quad along the upper-left / lower-right diagonal, as a TIN would.
    for a, b, c in ((ul, ur, ll), (ur, lr, ll)):
        valid = np.isfinite(a) & np.isfinite(b) & np.isfinite(c)
        if not valid.any():
            continue
        za, zb, zc = a[valid], b[valid], c[valid]

        volume += float(_triangle_volume_above(za, zb, zc, tri_area).sum())

        # Planimetric and draped area of the part of the triangle above the plane.
        frac = _fraction_above(za, zb, zc)
        area_2d += float((frac * tri_area).sum())
        area_3d += float((frac * _triangle_slope_area(za, zb, zc, dx, dy)).sum())

    return {"volume": volume, "area_2d": area_2d, "area_3d": area_3d}


def _fraction_above(z1, z2, z3):
    """Fraction of a triangle's planimetric area on which the linear surface is above 0."""
    z = np.stack([z1, z2, z3])
    n_pos = (z > 0).sum(axis=0)
    frac = np.zeros(z1.shape, dtype="float64")
    frac[n_pos == 3] = 1.0

    one_pos = n_pos == 1
    if one_pos.any():
        zs = z[:, one_pos]
        pos_idx = np.argmax(zs > 0, axis=0)
        cols = np.arange(zs.shape[1])
        z_p = zs[pos_idx, cols]
        neg = np.stack([zs[(pos_idx + 1) % 3, cols], zs[(pos_idx + 2) % 3, cols]])
        s = z_p / (z_p - neg)
        frac[one_pos] = s[0] * s[1]

    two_pos = n_pos == 2
    if two_pos.any():
        zs = z[:, two_pos]
        neg_idx = np.argmin(zs > 0, axis=0)
        cols = np.arange(zs.shape[1])
        z_n = zs[neg_idx, cols]
        pos = np.stack([zs[(neg_idx + 1) % 3, cols], zs[(neg_idx + 2) % 3, cols]])
        t = -z_n / (pos - z_n)
        frac[two_pos] = 1.0 - t[0] * t[1]

    return frac


def _triangle_slope_area(z1, z2, z3, dx, dy):
    """True (draped) area of a right triangle whose legs are dx and dy in plan view."""
    # Gradient of the linear surface over the triangle: the two legs meet at vertex 1.
    gx = (z2 - z1) / abs(dx)
    gy = (z3 - z1) / abs(dy)
    return 0.5 * abs(dx) * abs(dy) * np.sqrt(1.0 + gx ** 2 + gy ** 2)
