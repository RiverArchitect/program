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
    rho_w: density of water, kg/m^3 (si) or slug/ft^3 (us)
    g: gravitational acceleration, m/s^2 (si) or ft/s^2 (us)
    returns rho_w, g
    """
    if units == 'us':
        rho_w = 1.937
        g = 32.174
    elif units == 'si':
        rho_w = 1000
        g = 9.81
    else:
        print('ERROR: unknown unit system %s (\'us\' or \'si\')' % units)
        return
    return rho_w, g


def calculate_tau(h_ras, u_ras, grain_ras, s, units):
    rho_w, g = unit_constants(units)
    tau_ras = (rho_w * Square(u_ras / (5.75 * Log10(12.2 * h_ras
                                                    /(2 * 2.2 * grain_ras))))) / (rho_w * g * (s - 1) * grain_ras)
    return tau_ras
