#!/usr/bin/python
import random
try:
    from cParameters import *
    from cReadInpLifespan import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fGl
    import config
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")


def create_bed_shear(self, condition1):
    __n__ = 0.0473934
    self.ft2m = config.ft2m  # this is correctly assigned!
    self.ft2in = 12  # (in/ft) conversion factor for U.S. customary units
    self.n = __n__ / 1.49  # (s/ft^(1/3)) global Manning's n where k =1.49 converts to US customary
    self.n_label = "s/ft^(1/3)"
    self.rho_w = 1.937  # slug/ft^3
    threshold_taux = 0.047
    self.g = 9.81 / self.ft2m  # (ft/s2) gravity acceleration
    self.s = 2.68  # (--) relative grain density (ratio of rho_s and rho_w)
    self.sf = 0.99
    dir_tb = config.dir2conditions + condition1 + "\\tb\\"
    dir_ts = config.dir2conditions + condition1 + "\\ts\\"
    print(dir_tb)
    print(dir_ts)
    os.mkdir(dir_ts)
    os.mkdir(dir_tb)
    # self.set_extent()
    # self.logger.info("      >>> Creating Bed Shear Rasters.")
    h = FlowDepth(condition1)
    u = FlowVelocity(condition1)
    grains = GrainSizes(condition1)
    if str(grains.raster).__len__() > 1:
        tx_raster_list = []
        for i in range(0, h.raster_names.__len__()):
            if (str(u.rasters[i]).__len__() > 1) and (str(h.rasters[i]).__len__() > 1):
                _q_ = fGl.read_Q_str(h.raster_names[i], prefix='h')
                _name__ = 'tb' + fGl.write_Q_str(_q_) + '.tif'
                name__ = 'ts' + fGl.write_Q_str(_q_) + '.tif'
                _ras__ = Square(u.rasters[i] / (5.75 * Log10(12.2 * h.rasters[i] / (2 * 2.2 * grains.raster))))
                arcpy.CopyRaster_management(_ras__, dir_tb + _name__)
                __ras__ = (self.rho_w * _ras__) / (self.rho_w * self.g * (self.s - 1) * grains.raster)
                arcpy.CopyRaster_management(__ras__, dir_ts + name__)
                tx_raster_list.append(__ras__)

