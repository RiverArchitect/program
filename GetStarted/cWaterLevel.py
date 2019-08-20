try:
    import sys, os, logging, random
    import datetime as dt
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
        kwargs["method"] (str): 'IDW', 'Kriging', or 'Nearest Neighbor'. Determines the interpolation scheme. Default 'IDW'.
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

        try:
            self.method = kwargs["method"]
        except:
            self.method = 'IDW'

        if self.unique_id:
            Q = int(os.path.splitext(os.path.basename(self.path2h_ras))[0].split("h")[1])
            self.out_wle = "wle%06d.tif" % Q
            self.out_wle_var = "wle%06d_var.tif" % Q
            self.out_h_interp = "h%06d_interp.tif" % Q
            self.out_d2w = "d2w%06d.tif" % Q
        else:
            self.out_wle = "wle.tif"
            self.out_wle_var = "wle_var.tif"
            self.out_h_interp = "h_interp.tif"
            self.out_d2w = "d2w.tif"

        self.logger = logging.getLogger("logfile")

    def interpolate_wle(self):
        """
        Interpolates water level elevation, used as preliminary step for getting depth to groundwater and disconnected wetted areas.

        Args:
            self.method: 'Kriging', 'IDW', or 'Nearest Neighbor'. Determines the method used to interpolate WLE.

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
                self.logger.info(e.args[0])
                return True

            if self.method == "Kriging":
                try:
                    self.logger.info("Ordinary Kriging interpolation ...")
                    # Spherical semivariogram using 12 nearest points to interpolate
                    ras_wle_dem = Kriging(in_point_features=pts_wse, z_field="grid_code",
                                          kriging_model=KrigingModelOrdinary("Spherical",
                                                                             lagSize=cell_size),
                                          cell_size=cell_size,
                                          search_radius="Variable 12")
                    ras_wle_dem.save(os.path.join(self.cache, "ras_wle_dem"))
                    # out_variance_prediction_raster=os.path.join(self.cache, "ras_wle_var") ***
                    ras_wle_dem = arcpy.Raster(os.path.join(self.cache, "ras_wle_dem"))
                    # ras_wle_var = arcpy.Raster(os.path.join(self.cache, "ras_wle_var")) ***
                    self.logger.info("OK")

                except arcpy.ExecuteError:
                    if "010079" in str(arcpy.GetMessages(2)):
                        self.logger.info("Could not fit semivariogram, increasing lag size and retrying...")
                        empty_bins = True
                        itr = 2
                        while empty_bins:
                            try:
                                ras_wle_dem = Kriging(in_point_features=pts_wse, z_field="grid_code",
                                                      kriging_model=KrigingModelOrdinary("Spherical",
                                                                                         lagSize=cell_size * itr),
                                                      cell_size=cell_size,
                                                      search_radius="Variable 12")
                                try:
                                    ras_wle_dem.save(os.path.join(self.cache, "ras_wle_dem"))
                                    # out_variance_prediction_raster=os.path.join(self.cache, "ras_wle_var") ***
                                    ras_wle_dem = arcpy.Raster(os.path.join(self.cache, "ras_wle_dem"))
                                    # ras_wle_var = arcpy.Raster(os.path.join(self.cache, "ras_wle_var")) ***
                                    self.logger.info("OK")
                                    empty_bins = False
                                except:
                                    self.logger.info("ERROR: Failed to produce interpolated raster.")
                                    return True
                            except:
                                self.logger.info("Still could not fit semivariogram, increasing lag and retrying...")
                                itr *= 2
                                if itr > 16:
                                    break

                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    self.logger.info(e.args[0])
                    return True

            elif self.method == "IDW":
                try:
                    self.logger.info("IDW interpolation...")
                    # using IDW power of 2 with 12 nearest neighbors
                    arcpy.Idw_3d(in_point_features=pts_wse, z_field="grid_code",
                                 out_raster=os.path.join(self.cache, "ras_wle_dem"),
                                 cell_size=cell_size,
                                 search_radius="Variable 12")
                    ras_wle_dem = arcpy.Raster(os.path.join(self.cache, "ras_wle_dem"))
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    self.logger.info(e.args[0])
                    return True

            elif self.method == "Nearest Neighbor":
                try:
                    self.logger.info("Nearest Neighbor interpolation...")
                    # using IDW with 1 nearest neighbor
                    arcpy.Idw_3d(in_point_features=pts_wse, z_field="grid_code",
                                 out_raster=os.path.join(self.cache, "ras_wle_dem"),
                                 cell_size=cell_size,
                                 search_radius="Variable 1")
                    ras_wle_dem = arcpy.Raster(os.path.join(self.cache, "ras_wle_dem"))
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    self.logger.info(e.args[0])
                    return True

            elif self.method == "EBK":
                try:
                    self.logger.info("Empirical Bayesian Kriging interpolation...")
                    search_nbrhood = arcpy.SearchNeighborhoodStandardCircular(nbrMin=12, nbrMax=12)
                    arcpy.EmpiricalBayesianKriging_ga(in_features=pts_wse,
                                                      z_field="grid_code",
                                                      out_raster=os.path.join(self.cache, "ras_wle_dem"),
                                                      cell_size=cell_size,
                                                      transformation_type="EMPIRICAL",
                                                      number_semivariograms=100,
                                                      search_neighborhood=search_nbrhood,
                                                      output_type="PREDICTION",
                                                      semivariogram_model_type="EXPONENTIAL"
                                                      )
                    ras_wle_dem = arcpy.Raster(os.path.join(self.cache, "ras_wle_dem"))
                    self.logger.info("OK")
                except arcpy.ExecuteError:
                    self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                    return True
                except Exception as e:
                    self.logger.info(arcpy.GetMessages(2))
                    self.logger.info(e.args[0])
                    return True

            else:
                self.logger.info("ERROR: invalid method for WSE interpolation: '%s'." % self.method)
                return True

            try:
                self.logger.info("Saving WLE raster to: %s" % os.path.join(self.out_dir, self.out_wle))
                ras_wle_dem.save(os.path.join(self.out_dir, self.out_wle))
                self.logger.info("OK")
                self.save_info_file(os.path.join(self.out_dir, self.out_wle))
                """ ***
                if self.method == "Kriging":
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
                self.logger.info(e.args[0])
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

    def check_interp_ras(self, h_interp_path):
        # checks if interpolated raster already exists using selected interpolation method
        if os.path.exists(h_interp_path):
            info_path = h_interp_path.replace(".tif", ".info.txt")
            try:
                with open(info_path) as f:
                    method_line = f.readlines()[0]
                    method = method_line.split(": ")[1]
                    method = method.replace("\n", "")
                    if method == self.method:
                        return True
                    else:
                        self.logger.info("Existing raster %s uses different interpolation method than selected. Re-interpolating..." % h_interp_path)
                        return False
            except:
                return False
        else:
            self.logger.info("Existing %s not found. Creating..." % h_interp_path)
            return False

    def calculate_h(self):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache

            # check if interpolated WLE already exists
            path2wle_ras = os.path.join(self.out_dir, self.out_wle)
            if not self.check_interp_ras(path2wle_ras):
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
                self.logger.info(e.args[0])
                return True

            try:
                self.logger.info("Saving interpolated depth raster to:%s" % os.path.join(self.out_dir, self.out_h_interp))
                ras_h_interp.save(os.path.join(self.out_dir, self.out_h_interp))
                self.logger.info("OK")
                self.save_info_file(os.path.join(self.out_dir, self.out_h_interp))
            except arcpy.ExecuteError:
                self.logger.info("ERROR: Failed to save interpolated depth raster.")
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info("ERROR: Failed to save interpolated depth raster.")
                self.logger.info(arcpy.GetMessages(2))
                self.logger.info(e.args[0])
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
            if not self.check_interp_ras(path2wle_ras):
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
                self.logger.info(e.args[0])
                return True

            try:
                self.logger.info("Saving depth to groundwater raster to: %s" % os.path.join(self.out_dir, self.out_d2w))
                ras_d2w.save(os.path.join(self.out_dir, self.out_d2w))
                self.logger.info("OK")
                self.save_info_file(os.path.join(self.out_dir, self.out_d2w))
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                return True
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
                self.logger.info(e.args[0])
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

    def save_info_file(self, path):
        info_path = os.path.join(os.path.dirname(path),
                                 os.path.basename(path).rsplit(".", 1)[0] + '.info.txt')
        with open(info_path, "w") as info_file:
            info_file.write("Interpolation method: %s" % self.method)
            info_file.write("\nTime created: %s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            info_file.write("\nDepth raster input: %s" % self.path2h_ras.replace("\\", "/"))
            info_file.write("\nDEM raster input: %s" % self.path2dem_ras.replace("\\", "/"))
        self.logger.info("Saved info file: %s " % info_path)

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
