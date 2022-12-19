try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")


def unit_constants(units):
    """
    get constants in unit system ('us' or 'si')
    g: gravitational acceleration, m/s^2 (si) or ft/s^2 (us)
    returns g
    """
    if units == 'us':
        g = 32.174
    elif units == 'si':
        g = 9.81
    else:
        print('ERROR: unknown unit system %s (\'us\' or \'si\')' % units)
        return
    return g


def calculate_taux(h_ras, u_ras, grain_ras, s, units):
    """
    Dimensionless bed shear stress
    """
    g = unit_constants(units)
    d84 = 2.2 * grain_ras
    temp_taux_ras = Square(u_ras / (5.75 * Log10(12.2 * h_ras / (2 * d84)))) / (g * (s - 1) * grain_ras)
    taux_ras = Con(h_ras > d84, temp_taux_ras, 0)
    return taux_ras

