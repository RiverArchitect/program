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


def calculate_taux(h_ras, u_ras, grain_ras, s, units):
    rho_w, g = unit_constants(units)
    taux_ras = (rho_w * Square(u_ras / (5.75 * Log10(12.2 * h_ras
                                                    /(2 * 2.2 * grain_ras))))) / (rho_w * g * (s - 1) * grain_ras)
    return taux_ras

def compare_raster_set(raster_set, threshold):
    __ras__ = []
    r_index = 0
    for ras in raster_set:
        try:
            if str(ras).__len__() > 1:
                __ras__.append(Float(Con(Float(ras) >= Float(threshold), Float(self.lifespans[r_index]))))
        except:
            self.logger.error("ERROR: Incoherent data in " + str(ras) + " (raster comparison).")
            self.logger.info("ERROR HINT: Verify Raster definitions in 01_Conditions/%s/input_definitions.inp." % self.condition)
        r_index += 1
    try:
        if __ras__.__len__() > 1:
            return Float(CellStatistics(__ras__, "MINIMUM", "DATA"))
        else:
            self.logger.info("          * Nothing to do (CellStatistics returns None-types)")
            return None
    except:
        self.logger.error("ERROR: Could not calculate CellStatistics (Raster comparison).")