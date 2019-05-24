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

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: RP/fGlobal).")


class D2W:
    def __init__(self, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs

        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        fg.chk_dir(self.cache)

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = os.path.dirname(os.path.realpath(__file__)) + "\\"

        self.logger = logging.getLogger("logfile")

    def calculate_d2w(self, path2h_ras, path2dem_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache

            try:
                self.logger.info(" * Reading input Rasters ...")
                ras_h = arcpy.Raster(path2h_ras)
                ras_dem = arcpy.Raster(path2dem_ras)
                self.logger.info(" * OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")
                return True

            try:
                self.logger.info(" * Setting calculation extent ...")
                arcpy.env.extent = ras_h.extent
            except:
                self.logger.info("WARNING: Could not access hydraulic Raster extents. Using MAXOF instead.")
                arcpy.env.extent = "MAXOF"

            try:
                self.logger.info(" * Making groundwater Raster at river level ...")
                ras_gw = Con(Float(ras_h) > 0.0, Float(ras_dem + ras_h))
                temp_dem = Con(((Float(ras_dem) > 0.0) & IsNull(ras_h)), Float(ras_dem))
                ras_dem = temp_dem
                self.logger.info(" * OK")
            except:
                self.logger.info("ERROR: Input Rasters contain invalid data.")
                return True

            try:
                self.logger.info(" * Converting groundwater raster to points ...")
                if not os.path.isfile(self.cache + "pts_gw.shp"):
                    pts_gw = arcpy.RasterToPoint_conversion(ras_gw, self.cache + "pts_gw.shp")
                    self.logger.info(" * OK")                   
                else:
                    pts_gw = self.cache + "pts_gw.shp"
                    self.logger.info(" -- using existing file (" + self.cache + "pts_gw.shp" + ").")

                self.logger.info(" * Converting DEM raster to points ...")
                if not os.path.isfile(self.cache + "pts_dem.shp"):
                    pts_dem = arcpy.RasterToPoint_conversion(ras_dem, self.cache + "pts_dem.shp")
                    self.logger.info(" * OK")
                else:
                    pts_dem = self.cache + "pts_dem.shp"
                    self.logger.info(" -- using existing file (" + self.cache + "pts_dem.shp" + ").")
                
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            base_join = self.out_dir + 'spat_join.shp'

            try:
                self.logger.info(" * Spatial join analysis ...")
                arcpy.SpatialJoin_analysis(target_features=pts_dem, join_features=pts_gw,
                                           out_feature_class=base_join,
                                           join_operation='JOIN_ONE_TO_MANY',
                                           join_type='KEEP_ALL',
                                           match_option='CLOSEST')
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info(" * Converting depth to groundwater dem to raster ...")
                arcpy.PointToRaster_conversion(in_features=base_join, value_field="grid_cod_1",
                                               out_rasterdataset=self.cache + "ras_gw_dem",
                                               cell_assignment="MEAN", cellsize=5)
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info(" * Calculating depth to groundwater raster ...")
                ras_d2w_dem = arcpy.Raster(self.cache + "ras_gw_dem")
                ras_d2w = Con((ras_d2w_dem > 0), (ras_dem - ras_d2w_dem))
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info(" * Saving depth to groundwater raster to:")
                self.logger.info(str(self.out_dir))
                ras_d2w.save(self.out_dir + "d2w.tif")
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            arcpy.CheckInExtension('Spatial')
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])

        try:
            self.clean_up()
        except:
            pass
        # return Boolean False if successful.
        return False

    def clean_up(self):
        try:
            self.logger.info("Cleaning up ...")
            fg.clean_dir(self.cache)
            fg.rm_dir(self.cache)
            self.logger.info(" * OK")
        except:
            self.logger.info(" * Failed to clean up .cache folder.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cDepth2Groundwater.D2W")
