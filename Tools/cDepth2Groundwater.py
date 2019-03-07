#!/usr/bin/python
# Filename: cDepth2Groundwater.py
import arcpy, os
from arcpy.sa import *

import fTools as ft

class D2W:
    def __init__(self, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs

        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        ft.chk_dir(self.cache)

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = os.path.dirname(os.path.realpath(__file__)) + "\\"

        self.logger = ft.initialize_logger(os.path.dirname(os.path.realpath(__file__)), "depth2groundwater")

    def calculate_d2w(self, path2h_ras, path2dem_ras):
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
                self.logger.info("Making groundwater raster ...")
                ras_gw = Con(ras_h > 0, (ras_dem + ras_h))
                temp_dem = Con(((ras_dem > 0) & IsNull(ras_h)), ras_dem)
                ras_dem = temp_dem
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Input rasters contain invalid data.")

            try:
                self.logger.info("Converting groundwater raster to points ...")
                pts_gw = arcpy.RasterToPoint_conversion(ras_gw, self.cache + "pts_gw.shp")
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
                base_join = arcpy.SpatialJoin_analysis(target_features=pts_dem, join_features=pts_gw,
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
                                           out_rasterdataset=self.cache + "ras_gw_dem",
                                           cell_assignment="MEAN", cellsize=5)
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))

            try:
                self.logger.info("Calculating depth to groundwater raster ...")
                ras_d2w_dem = arcpy.Raster(self.cache + "ras_gw_dem")
                ras_d2w = Con((ras_d2w_dem > 0), (ras_dem - ras_d2w_dem))
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))

            try:
                self.logger.info("Saving depth to groundwater raster to:")
                self.logger.info(str(self.out_dir))
                ras_d2w.save(self.out_dir + "d2w")
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

        self.clean_up()

    def clean_up(self):
        try:
            self.logger.info("Cleaning up ...")
            ft.clean_dir(self.cache)
            ft.rm_dir(self.cache)
            self.logger.info("OK")
        except:
            self.logger.info("Failed to clean up .cache folder.")

        try:
            ft.stop_logging(self.logger)
        except:
            self.logger.info("Could not finalize logfile.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cDepth2Groundwater.D2W")