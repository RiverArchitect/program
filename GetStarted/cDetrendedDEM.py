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
    import fGlobal as fGl
    import config
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: RP/fGlobal).")


class DET:
    def __init__(self, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs

        self.cache = config.dir2gs + ".cache2\\"  # use cache2 to enable parallel proc.
        self.reset_cache = False
        fGl.chk_dir(self.cache)

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2gs

        self.logger = logging.getLogger("logfile")

    def calculate_det(self, path2h_ras, path2dem_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            arcpy.env.extent = "MAXOF"

            try:
                self.logger.info(" * Reading input rasters ...")
                ras_h = arcpy.Raster(path2h_ras)
                ras_dem = arcpy.Raster(path2dem_ras)
                self.logger.info(" * OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")
                return True

            try:
                self.logger.info(" * Making Thalweg elevation raster ...")
                ras_hmin = Con((ras_h > 0.0), Float(ras_dem))
                ras_h_with_null = Con((Float(ras_h) > 0.0), Float(ras_h))
                temp_dem = Con(((ras_dem > 0) & IsNull(ras_h_with_null)), Float(ras_dem))
                ras_dem = temp_dem
                self.logger.info(" * OK")
            except:
                self.logger.info("ERROR: Input Rasters contain invalid data.")
                return True

            try:
                self.logger.info(" * Converting Thalweg raster to points ...")
                pts_hmin = arcpy.RasterToPoint_conversion(ras_hmin, self.cache + "pts_hmin.shp")
                self.logger.info(" * OK")
                self.logger.info(" * Converting DEM raster to points ...")
                pts_dem = arcpy.RasterToPoint_conversion(ras_dem, self.cache + "pts_dem.shp")
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            base_join = self.out_dir + 'spat_join_det.shp'
            try:
                self.logger.info(" * Spatial join analysis ...")
                base_join = arcpy.SpatialJoin_analysis(target_features=pts_dem, join_features=pts_hmin,
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
                self.logger.info(" * Converting relative Thalweg dem to raster ...")
                arcpy.PointToRaster_conversion(in_features=base_join, value_field="grid_cod_1",
                                               out_rasterdataset=self.cache + "ras_hmin_dem",
                                               cell_assignment="MEAN", cellsize=5)
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info(" * Calculating depth to Thalweg raster (detrended DEM) ...")
                ras_hmin_dem = arcpy.Raster(self.cache + "ras_hmin_dem")
                ras_det = Con((ras_hmin_dem > 0), (ras_dem - ras_hmin_dem))
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info(" * Saving depth to Thalweg raster (detrended DEM) to:")
                self.logger.info(str(self.out_dir))
                ras_det.save(self.out_dir + "dem_detrend.tif")
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
            return True
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
            return True
        try:
            del ras_det, ras_hmin, base_join, pts_dem, pts_hmin, ras_hmin_dem
        except:
            pass

        try:
            self.clean_up()
        except:
            pass
        # return False if successfull
        return False

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
            fGl.rm_dir(self.cache)
            if self.reset_cache:
                fGl.chk_dir(self.cache)
            self.logger.info("   * ok")
        except:
            self.logger.info("WARNING: .cache folder will be removed by package controls.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cDetrendedDEM.DET")
