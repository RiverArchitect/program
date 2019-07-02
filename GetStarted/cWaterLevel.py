try:
    import sys, os, logging, random
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

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
    def __init__(self, path2h_ras, path2dem_ras, *args, **kwargs):
        """
        path2h_ras (str): full path to the depth raster used for interpolating WLE
        path2dem_ras (str): full path to the DEM
        args[0] (str): optional out_dir -- otherwise: out_dir = script_dir
        kwargs["unique_id"] (Boolean): determines if output files have integer discharge value in output file name
        """

        self.cache = os.path.join(config.dir2gs, ".cache%s" % str(random.randint(1000000, 9999999)))
        fGl.chk_dir(self.cache)

        self.path2h_ras = path2h_ras
        self.path2dem_ras = path2dem_ras

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2gs

        try:
            self.unique_id = kwargs["unique_id"]
        except:
            self.unique_id = False

        if self.unique_id:
            Q = int(os.path.splitext(os.path.basename(self.path2h_ras))[0].split("h")[1])
            self.out_wle = "wle%i.tif" % Q
            self.out_wle_var = "wle%i_var.tif" % Q
            self.out_h_interp = "h%i_interp.tif" % Q
            self.out_d2w = "d2w%i.tif" % Q
        else:
            self.out_wle = "wle.tif"
            self.out_wle_var = "wle_var.tif"
            self.out_h_interp = "h_interp.tif"
            self.out_d2w = "d2w.tif"

        self.logger = logging.getLogger("logfile")

    def interpolate_wle(self, method='Kriging'):
        """
        Interpolates water level elevation, used as preliminary step for getting depth to groundwater and disconnected wetted areas.

        Args:
            method: 'Kriging' or 'Nearest Neighbor'. Determines the method used to interpolate WLE.

        Saves interpolated WLE raster to self.out_dir (also saves a WLE variance raster if Kriging method is used).
        """

        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache

            try:
                self.logger.info("Reading input rasters ...")
                ras_h = arcpy.Raster(self.path2h_ras)
                ras_dem = arcpy.Raster(self.path2dem_ras)
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
                pts_wse = arcpy.RasterToPoint_conversion(ras_wse, os.path.join(self.cache, "pts_wse.shp"))
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
                                     out_surface_raster=os.path.join(self.cache, "ras_wle_dem"),
                                     semiVariogram_props="Spherical",
                                     cell_size=cell_size)
                    # out_variance_prediction_raster=os.path.join(self.cache, "ras_wle_var") ***
                    ras_wle_dem = arcpy.Raster(os.path.join(self.cache, "ras_wle_dem"))
                    # ras_wle_var = arcpy.Raster(os.path.join(self.cache, "ras_wle_var")) ***
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
                    pts_dem = arcpy.RasterToPoint_conversion(ras_dem, os.path.join(self.cache, "pts_dem.shp"))
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    return True

                try:
                    self.logger.info("Finding nearest neighbors ...")
                    base_join = arcpy.SpatialJoin_analysis(target_features=pts_dem, join_features=pts_wse,
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
                                                   out_rasterdataset=os.path.join(self.cache, "ras_wle_dem"),
                                                   cell_assignment="MEAN", cellsize=5)
                    ras_wle_dem = arcpy.Raster(os.path.join(self.cache, "ras_wle_dem"))
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
                self.logger.info("Saving WLE raster to:\n%s" % os.path.join(self.out_dir, self.out_wle))
                ras_wle_dem.save(os.path.join(self.out_dir, self.out_wle))
                self.logger.info("OK")
                """ ***
                if method == "Kriging":
                    self.logger.info("Saving WLE Kriging variance raster (%s) ..." % os.path.join(self.out_dir, self.out_wle_var))
                    ras_wle_var.save(os.path.join(self.out_dir, self.out_wle_var))
                    self.logger.info("OK")
                """
                arcpy.CheckInExtension('Spatial')
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

    def calculate_h(self):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache

            # check if interpolated WLE already exists
            path2wle_ras = os.path.join(self.out_dir, self.out_wle)
            if not os.path.exists(path2wle_ras):
                self.interpolate_wle()
            else:
                self.logger.info("Using existing interpolated WLE raster ...")

            try:
                self.logger.info("Reading input rasters ...")
                ras_wle = arcpy.Raster(path2wle_ras)
                ras_dem = arcpy.Raster(self.path2dem_ras)
                arcpy.env.extent = ras_dem.extent
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
                self.logger.info("Saving interpolated depth raster to:\n%s" % os.path.join(self.out_dir, self.out_h_interp))
                ras_h_interp.save(os.path.join(self.out_dir, self.out_h_interp))
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

    def calculate_d2w(self):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache

            # check if interpolated WLE already exists
            path2wle_ras = os.path.join(self.out_dir, self.out_wle)
            if not os.path.exists(path2wle_ras):
                self.interpolate_wle()
            else:
                self.logger.info("Using existing interpolated WLE raster ...")

            try:
                self.logger.info("Reading input rasters ...")
                ras_wle = arcpy.Raster(path2wle_ras)
                ras_dem = arcpy.Raster(self.path2dem_ras)
                arcpy.env.extent = ras_dem.extent
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")
                return True

            try:
                self.logger.info("Calculating depth to groundwater raster ...")
                ras_d2w = Con((ras_wle > 0), (ras_dem - ras_wle))
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                return True

            try:
                self.logger.info("Saving depth to groundwater raster to:\n%s" % os.path.join(self.out_dir, self.out_d2w))
                ras_d2w.save(os.path.join(self.out_dir, self.out_d2w))
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
