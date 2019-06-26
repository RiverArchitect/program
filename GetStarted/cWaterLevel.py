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
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing RiverArchitect packages (riverpy).")


class WLE:
    def __init__(self, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs

        self.cache = config.dir2gs + ".cache\\"
        fGl.chk_dir(self.cache)

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2gs

        self.logger = logging.getLogger("logfile")

    def interpolate_wle(self, path2h_ras, path2dem_ras, method='Kriging'):
        """
        Interpolates water level elevation, used as preliminary step for getting depth to groundwater and disconnected wetted areas.

        Args:
            path2h_ras: path to the depth raster
            path2dem_ras: path to the DEM
            method: 'Kriging' or 'Nearest Neighbor'. Determines the method used to interpolate WLE.

        Saves interpolated WLE raster to self.out_dir (also saves a WLE variance raster if Kriging method is used).
        """

        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache


            try:
                self.logger.info("Reading input rasters ...")
                ras_h = arcpy.Raster(path2h_ras)
                ras_dem = arcpy.Raster(path2dem_ras)
                arcpy.env.extent = ras_dem.extent
                cell_size = arcpy.GetRasterProperties_management(ras_dem, 'CELLSIZEX').getOutput(0)
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")
                return True

            try:
                self.logger.info("Making WSE raster ...")
                ras_wse = Con(ras_h > 0, (ras_dem + ras_h))
                temp_dem = Con(((ras_dem > 0) & IsNull(ras_h)), ras_dem)
                ras_dem = temp_dem
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Input rasters contain invalid data.")
                return True

            try:
                self.logger.info("Converting WSE raster to points ...")
                pts_wse = arcpy.RasterToPoint_conversion(ras_wse, self.cache + "pts_wse.shp")
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            if method == "Kriging":
                try:
                    self.logger.info("Ordinary Kriging interpolation ...")
                    # default uses spherical semivariogram using 12 nearest points to interpolate
                    arcpy.Kriging_3d(in_point_features=pts_wse, z_field="grid_code",
                                     out_surface_raster=self.cache + "ras_wle_dem",
                                     semiVariogram_props="Spherical",
                                     cell_size=cell_size)
                    # out_variance_prediction_raster=self.cache + "ras_wle_var" ***
                    ras_wle_dem = arcpy.Raster(self.cache + "ras_wle_dem")
                    # ras_wle_var = arcpy.Raster(self.cache + "ras_wle_var") ***
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    return True

            elif method == "Nearest Neighbor":
                try:
                    self.logger.info("Converting DEM raster to points ...")
                    pts_dem = arcpy.RasterToPoint_conversion(ras_dem, self.cache + "pts_dem.shp")
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    return True

                try:
                    self.logger.info("Finding nearest neighbors ...")
                    base_join = arcpy.SpatialJoin_analysis(target_features=pts_dem, join_features=pts_gw,
                                                           out_feature_class=arcpy.FeatureSet,
                                                           join_operation='JOIN_ONE_TO_MANY',
                                                           join_type='KEEP_ALL',
                                                           match_option='CLOSEST')
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    return True

                try:
                    self.logger.info("Converting nearest neighbor points to raster ...")
                    arcpy.PointToRaster_conversion(in_features=base_join, value_field="grid_cod_1",
                                                   out_rasterdataset=self.cache + "ras_wle_dem",
                                                   cell_assignment="MEAN", cellsize=5)
                    ras_wle_dem = arcpy.Raster(self.cache + "ras_wle_dem")
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    return True

            else:
                self.logger.info("ERROR: invalid method for WSE interpolation: '%s'." % method)
                return True

            try:
                self.logger.info("Saving WLE raster to:\n%s" % str(self.out_dir) + "\\wle.tif")
                ras_wle_dem.save(self.out_dir + "\\wle.tif")
                self.logger.info("OK")
                """ ***
                if method == "Kriging":
                    self.logger.info("Saving WLE Kriging variance raster (%s) ..." % self.out_dir + "\\wle_var.tif")
                    ras_wle_var.save(self.out_dir + "\\wle_var.tif")
                    self.logger.info("OK")
                """
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
            return True
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
            return True

        self.clean_up()

        # return Boolean False if successful.
        return False

    def calculate_h(self, path2h_ras, path2dem_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            base_ras = arcpy.Raster(path2h_ras)
            arcpy.env.extent = base_ras.extent

            # check if interpolated WLE already exists
            path2wle_ras = os.path.join(self.out_dir, 'wle.tif')
            if not os.path.exists(path2wle_ras):
                self.interpolate_wle(path2h_ras, path2dem_ras)
            else:
                self.logger.info("Using existing interpolated WLE raster ...")

            try:
                self.logger.info("Reading input rasters ...")
                ras_wle = arcpy.Raster(path2wle_ras)
                ras_dem = arcpy.Raster(path2dem_ras)
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")
                return True

            try:
                self.logger.info("Calculating interpolated depth raster ...")
                ras_h_interp = ras_wle - ras_dem
                ras_h_interp = Con(ras_h_interp > 0, ras_h_interp)
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info("Saving interpolated depth raster to:\n%s" % self.out_dir + "\\h_interp.tif")
                ras_h_interp.save(self.out_dir + "\\h_interp.tif")
                self.logger.info("OK")
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

    def calculate_d2w(self, path2h_ras, path2dem_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache

            # check if interpolated WLE already exists
            path2wle_ras = os.path.join(self.out_dir, 'wle.tif')
            if not os.path.exists(path2wle_ras):
                self.interpolate_wle(path2h_ras, path2dem_ras)
            else:
                self.logger.info("Using existing interpolated WLE raster ...")

            try:
                self.logger.info("Reading input rasters ...")
                ras_wle = arcpy.Raster(path2wle_ras)
                ras_dem = arcpy.Raster(path2dem_ras)
                arcpy.env.extent = ras_dem.extent
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")
                return True

            try:
                self.logger.info("Calculating depth to groundwater raster ...")
                else_ras = arcpy.Raster(os.path.join(self.out_dir, 'wle_var.tif'))
                ras_d2w = Con((ras_wle > 0), Con((ras_dem - ras_wle) > 0, Float(ras_dem - ras_wle), Float(else_ras)))
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info("Saving depth to groundwater raster to:\n%s" % str(self.out_dir))
                ras_d2w.save(self.out_dir + "\\d2w.tif")
                self.logger.info("OK")
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

    def clean_up(self):
        try:
            self.logger.info("Cleaning up ...")
            fGl.clean_dir(self.cache)
            fGl.rm_dir(self.cache)
            self.logger.info("OK")
        except:
            self.logger.info("Failed to clean up .cache folder.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cWaterLevel.WLE")
