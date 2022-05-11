#!/usr/bin/python
import random
try:
    from cParameters import *
    from cReadInpLifespan import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fGl
    import config
    import cThresholdDirector as cT
    import cDefinitions
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
    self.features = cDefinitions.FeatureDefinitions()
    self.feature_reader = cDefinitions.FeatureReader()
    self.thresh_xlsx = config.xlsx_thresholds

    try:
        self.wb = oxl.load_workbook(filename=self.thresh_xlsx, read_only=True, data_only=True)
        wb_open = True
    except:
        wb_open = False
        self.logger.info("ERROR: Could not open threshold_values.xlsx.")
    try:
        if wb_open:
            self.ws = self.wb['thresholds']
        else:
            self.ws = ""
    except:
        self.logger.info("ERROR: Could not find sheet \'thresholds\' in threshold_values.xlsx.")

    self.thresh_row_dict = self.feature_reader.get_rows()
    unit_cell = self.ws.cell(row=self.thresh_row_dict['unit'], column=5).value

    print(unit_cell)
    __n__ = 0.0473934

    if unit_cell == "U.S. customary":
        self.ft2m = config.ft2m
        self.ft2in = 12  # (in/ft) conversion factor for U.S. customary units
        self.n = __n__ / 1.49  # (s/ft^(1/3)) global Manning's n where k =1.49 converts to US customary
        self.n_label = "s/ft^(1/3)"
        self.rho_w = 1.937  # slug/ft^3
    else:
        self.ft2m = 1.0
        self.ft2in = 1  # (in/ft) dummy conversion factor in SI
        self.n = __n__  # (s/m^(1/3)) global Manning's n
        self.n_label = "s/m^(1/3)"
        self.rho_w = 1000  # kg/m^3

    self.g = 9.81 / self.ft2m  # (ft/s2) gravity acceleration
    self.s = 2.68  # (--) relative grain density (ratio of rho_s and rho_w)
    self.sf = 0.99
    dir_tb = config.dir2conditions + condition1 + "\\tb\\"
    dir_ts = config.dir2conditions + condition1 + "\\ts\\"

    os.mkdir(dir_ts)
    os.mkdir(dir_tb)

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

