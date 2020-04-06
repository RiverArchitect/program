try:
    import sys, os, logging, random, shutil
    import numpy as np
    import pandas as pd
    import datetime as dt
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random, shutil).")
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")
try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")


class RatingCurves(object):
    def __init__(self, dem, q_h_interp_dict, q_disc_ras, *args, **kwargs):

        self.logger = logging.getLogger("logfile")
        self.cache = config.dir2co + ".cache%s" % str(random.randint(1000000, 9999999))
        fGl.chk_dir(self.cache)
        arcpy.env.workspace = self.cache
        arcpy.env.overwriteOutput = True

        self.dem = Raster(dem)
        # dictionary with discharge as key and wse raster as value
        self.q_h_interp_dict = q_h_interp_dict
        self.q_wse_dict = {q: self.dem + h for q, h in self.q_h_interp_dict.items()}
        # patches defining areas for which to fit rating curve
        self.q_disc_ras = q_disc_ras
        self.discharges = self.q_h_interp_dict.keys()

        # populated by self.create_patches()
        self.patch_ras = ''

        # populated by self.get_patch_wses()
        # patch number as key, [[WSEs,...], [Qs,...]] as values
        self.patch_wses = {}
        self.patch_qs = {}

        arcpy.env.snapRaster = self.q_disc_ras
        self.create_patches()
        self.get_patch_wses()
        self.fit_rating_curves()

    def create_patches(self):
        """Creates a patch for each separate stranding pool"""
        # reclassify q_disc ras to ints
        self.logger.info("Creating rating curve fit patches...")
        int_ras = Reclassify(self.q_disc_ras, 'Value', RemapValue(list(zip(self.discharges, range(len(self.discharges))))))
        # convert to polygon
        patch_poly = os.path.join(self.cache, 'patches.shp')
        arcpy.RasterToPolygon_conversion(int_ras, patch_poly, 'NO_SIMPLIFY')
        # convert back to raster, with unique val for each patch
        self.patch_ras = os.path.join(self.cache, 'patches.tif')
        arcpy.PolygonToRaster_conversion(patch_poly, 'FID', self.patch_ras)

    def get_patch_wses(self):
        """Gets list of WSE values in each patch at each discharge"""
        self.logger.info("Getting patch WSE values...")
        for q in self.discharges:
            # convert each WSE ras to points
            self.logger.info("Discharge: %s " % q)
            wse_pts = os.path.join(self.cache, 'wse_pts.shp')
            arcpy.RasterToPoint_conversion(self.q_wse_dict[q], wse_pts)
            # extract patch num. to each point
            wse_patch_pts = os.path.join(self.cache, 'wse_patch_pts.shp')
            ExtractValuesToPoints(wse_pts, self.patch_ras, wse_patch_pts)
            # export attribute table to csv
            wse_patch_table = 'patch_table%i.csv' % int(q)
            # 'RASTERVALU' = patch number, 'grid_code' = WSE
            array = arcpy.da.FeatureClassToNumPyArray(wse_patch_pts, ['RASTERVALU', 'grid_code'], skip_nulls=True,
                                                      where_clause='RASTERVALU <> -9999')
            df = pd.DataFrame(array.tolist(), columns=['patch', 'WSE'])
            df = df.groupby('patch')['WSE'].apply(list)
            for patch in df.index:
                if patch in self.patch_wses.keys():
                    self.patch_wses[patch].extend(df[patch])
                    self.patch_qs[patch].extend([q] * len(df[patch]))
                else:
                    self.patch_wses[patch] = df[patch]
                    self.patch_qs[patch] = [q] * len(df[patch])

    def fit_rating_curves(self):
        """Fits a rating curve to each patch, saves parameters as attributes"""
        for patch in self.patch_wses.keys():
            pass

