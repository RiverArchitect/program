#!/usr/bin/python
# Filename: cDetrendedDEM.py
import arcpy, os
from arcpy.sa import *

import fTools as ft


class DET:
    def __init__(self, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs

        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        ft.chk_dir(self.cache)

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = os.path.dirname(os.path.realpath(__file__)) + "\\"

        self.logger = ft.initialize_logger(os.path.dirname(os.path.realpath(__file__)), "detrendedDEM")

    def calculate_det(self, path2h_ras, path2dem_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            arcpy.env.extent = "MAXOF"

            try:
                self.logger.info("Reading input rasters ...")
                ras_h = arcpy.Raster(path2h_ras)
                ras_dem = arcpy.Raster(path2dem_ras)
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")

            try:
                self.logger.info("Making thalweg elevation raster ...")
                ras_hmin = Con(ras_h > 0, (ras_dem + ras_h))
                temp_dem = Con(((ras_dem > 0) & IsNull(ras_h)), ras_dem)
                ras_dem = temp_dem
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Input rasters contain invalid data.")

            try:
                self.logger.info("Converting thalweg raster to points ...")
                pts_hmin = arcpy.RasterToPoint_conversion(ras_hmin, self.cache + "pts_hmin.shp")
                self.logger.info("OK")
                self.logger.info("Converting DEM raster to points ...")
                pts_dem = arcpy.RasterToPoint_conversion(ras_dem, self.cache + "pts_dem.shp")
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))

            try:
                self.logger.info("Spatial join analysis ...")
                base_join = arcpy.SpatialJoin_analysis(target_features=pts_dem, join_features=pts_hmin,
                                                   out_feature_class=arcpy.FeatureSet,
                                                   join_operation='JOIN_ONE_TO_MANY',
                                                   join_type='KEEP_ALL',
                                                   match_option='CLOSEST')
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))

            try:
                self.logger.info("Converting depth to groundwater dem to raster ...")
                arcpy.PointToRaster_conversion(in_features=base_join, value_field="grid_cod_1",
                                           out_rasterdataset=self.cache + "ras_hmin_dem",
                                           cell_assignment="MEAN", cellsize=5)
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))

            try:
                self.logger.info("Calculating depth to groundwater raster ...")
                ras_hmin_dem = arcpy.Raster(self.cache + "ras_hmin_dem")
                ras_det = Con((ras_hmin_dem > 0), (ras_dem - ras_hmin_dem))
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))

            try:
                self.logger.info("Saving depth to groundwater raster to:")
                self.logger.info(str(self.out_dir))
                ras_det.save(self.out_dir + "dem_detrend")
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))

            arcpy.CheckInExtension('Spatial')
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        try:
            del ras_det, ras_hmin, base_join, pts_dem, pts_hmin, ras_hmin_dem
        except:
            pass

        self.clean_up()

    def clean_up(self):
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.cache
        ras_list = arcpy.ListRasters()
        shp_list = arcpy.ListFeatureClasses()
        try:

            self.logger.info("   * clearing .cache (arcpy.Delete_management) ...")
            for ras in ras_list:
                try:
                    arcpy.Delete_management(str(ras))
                except:
                    pass
            for shp in shp_list:
                try:
                    arcpy.Delete_management(str(shp))
                except:
                    pass
            ft.rm_dir(self.cache)
            self.cache_count = 0
            if recreate_cache:
                ff.chk_dir(self.cache)
            self.logger.info("   * ok")
        except:
            self.logger.info("WARNING: .cache folder will be removed by package controls.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cDetrendedDEM.DET")
