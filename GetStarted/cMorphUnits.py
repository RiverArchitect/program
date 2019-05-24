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


class MU:
    def __init__(self, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs

        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        fg.chk_dir(self.cache)

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = os.path.dirname(os.path.realpath(__file__)) + "\\"

        try:
            # for metric provide args[1] = 0.0304799
            self.unit_conv = float(args[1])
        except:
            # default: U.S. customary (1.0)
            self.unit_conv = 1.0

        self.logger = logging.getLogger("logfile")
        self.mu_dict = {"agriplain": 4, "backswamp": 5, "bank": 6, "chute": 8, "cutbank": 9, "fast glide": 10,
                        "flood runner": 11, "floodplain": 12, "high floodplain": 13, "hillside": 14, "bedrock": 14,
                        "island high floodplain": 15, "island-floodplain": 16, "lateral bar": 17, "levee": 18,
                        "medial bar": 19, "mining pit": 20, "point bar": 21, "pond": 22, "pool": 23, "riffle": 24,
                        "riffle transition": 25, "run": 26, "slackwater": 27, "slow glide": 28, "spur dike": 29,
                        "swale": 30, "tailings": 31, "terrace": 32, "tributary channel": 33, "tributary delta": 34,
                        "in-channel bar": 35}
        self.raster_dict = {}
        self.ras_mu = 0

    def calculate_mu_baseflow(self, path2h_ras, path2u_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            arcpy.env.extent = "MAXOF"

            try:
                self.logger.info(" * Reading input rasters ...")
                h = arcpy.Raster(path2h_ras)
                u = arcpy.Raster(path2u_ras)
                self.logger.info(" * OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")
                return True
            try:
                arcpy.env.extent = u.extent
            except:
                pass

            try:
                self.logger.info(" * Evaluating morphological units ...")
                # CHANGE MU DELINEATION CRITERIA IF REQUIRED (ORIGINAL U.S. customary according to Wyrick and Pasternack 2014)
                self.raster_dict.update({"slackwater": Con(((u > 0.0) & (u < 0.5) & (h > 0.0) & (h < 4.6)), 27)})
                self.raster_dict.update({"slow glide": Con(((u >= 0.5) & (u < 1.0) & (h > 0.0) & (h < 4.6)), 28)})
                self.raster_dict.update({"riffle transition": Con(((u >= 1.0) & (u < 2.0) & (h >= 0.0) & (h < 2.3)), 25)})
                self.raster_dict.update({"fast glide": Con(((u >= 1.0) & (u < 2.0) & (h >= 2.3) & (h < 4.6)), 10)})
                self.raster_dict.update({"pool": Con(((u > 0.0) & (u < 2.0) & (h >= 4.6)), 23)})
                self.raster_dict.update({"riffle": Con(((u >= 2.0) & (h >= 0.0) & (h < 2.3)), 24)})
                self.raster_dict.update({"run": Con(((u >= 2.0) & (u < 3.0) & (h >= 2.3)), 26)})
                self.raster_dict.update({"chute": Con(((u >= 3.0) & (h >= 2.3)), 8)})
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Baseflow MU calculation failed.")
                return True

            try:
                self.logger.info(" * Updating MU raster ...")
                self.ras_mu = CellStatistics(fg.dict_values2list(self.raster_dict.values()), "MAXIMUM", "DATA")
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Baseflow MU update failed.")
                return True

            # arcpy.CheckInExtension('Spatial')
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: Baseflow MU calculation failed.")
            return True

    def clean_up(self):
        try:
            self.logger.info(" * Cleaning up ...")
            del self.ras_mu, self.raster_dict
            fg.clean_dir(self.cache)
            fg.rm_dir(self.cache)
            self.logger.info(" * OK")
        except:
            self.logger.info(" * Failed to clean up .cache folder.")

    def save_mu(self, *args):
        # args[0] can be an optional output directory
        try:
            self.out_dir = args[0]
        except:
            pass
        self.logger.info("")
        self.logger.info(" * SAVING ... ")
        arcpy.CheckOutExtension('Spatial')  # check out license
        arcpy.gp.overwriteOutput = True
        arcpy.env.workspace = self.cache
        arcpy.env.extent = "MAXOF"
        arcpy.CheckInExtension('Spatial')
        try:
            self.logger.info(" * Converting MU IDs to strings:")

            self.logger.info("   >> Converting raster to points ...")
            pts = arcpy.RasterToPoint_conversion(self.ras_mu, self.cache + "pts_del.shp")

            self.logger.info("   >> Converting numbers to strings ...")
            arcpy.AddField_management(pts, "MU", "TEXT")
            expression = "inverse_dict = {4: 'agriplain', 5: 'backswamp', 6: 'bank', 8: 'chute', 9: 'cutbank', 10: 'fast glide', 11: 'flood runner', 12: 'floodplain', 13: 'high floodplain', 14: 'bedrock', 15: 'island high floodplain', 16: 'island-floodplain', 17: 'lateral bar', 18: 'levee', 19: 'medial bar', 20: 'mining pit', 21: 'point bar', 22: 'pond', 23: 'pool', 24: 'riffle', 25: 'riffle transition', 26: 'run', 27: 'slackwater', 28: 'slow glide', 29: 'spur dike', 30: 'swale', 31: 'tailings', 32: 'terrace', 33: 'tributary channel', 34: 'tributary delta', 35: 'in-channel bar'}"
            arcpy.CalculateField_management(pts, "MU", "inverse_dict[!grid_code!]", "PYTHON", expression)

            self.logger.info("   >> OK")
            self.logger.info(" * Saving MU string raster as:")
            self.logger.info(str(self.out_dir) + "mu_str")
            arcpy.PointToRaster_conversion(in_features=pts, value_field="MU",
                                           out_rasterdataset=self.out_dir + "mu_str",
                                           cell_assignment="MOST_FREQUENT", cellsize=5)
            self.logger.info(" * OK")
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: Field assignment failed.")
            return True

        try:
            self.logger.info(" * Saving mu numeric raster as:")
            self.logger.info(str(self.out_dir) + "mu.tif")
            self.ras_mu.save(self.out_dir + "mu.tif")
            self.logger.info(" * OK")
        except arcpy.ExecuteError:
            self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
        except Exception as e:
            self.logger.info(arcpy.GetMessages(2))
        except:
            self.logger.info("ERROR: Saving failed.")
            return True

        try:
            self.clean_up()
        except:
            pass
        return False

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cMorphUnits.MU")
