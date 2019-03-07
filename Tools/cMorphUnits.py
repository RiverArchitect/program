#!/usr/bin/python
# Filename: cMorphUnits.py
import arcpy, os
from arcpy.sa import *

import fTools as ft


class MU:
    def __init__(self, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs

        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        ft.chk_dir(self.cache)

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

        self.logger = ft.initialize_logger(os.path.dirname(os.path.realpath(__file__)), "mu")
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
                self.logger.info("Reading input rasters ...")
                h = arcpy.Raster(path2h_ras)
                u = arcpy.Raster(path2u_ras)
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")

            try:
                self.logger.info("Evaluating morphological units ...")
                self.raster_dict.update({"slackwater": Con(((u < 0.5) & (h < 4.6)), 27)})
                self.raster_dict.update({"slow glide": Con(((u >= 0.5) & (u < 1.0) & (h >= 0.0) & (h < 4.6)), 28)})
                self.raster_dict.update({"riffle transition": Con(((u >= 1.0) & (u < 2.0) & (h >= 0.0) & (h < 2.3)), 25)})
                self.raster_dict.update({"fast glide": Con(((u >= 1.0) & (u < 2.0) & (h >= 2.3) & (h < 4.6)), 10)})
                self.raster_dict.update({"pool": Con(((u >= 0.0) & (u < 2.0) & (h >= 4.6)), 23)})
                self.raster_dict.update({"riffle": Con(((u >= 2.0) & (h >= 0.0) & (h < 2.3)), 24)})
                self.raster_dict.update({"run": Con(((u >= 2.0) & (u < 3.0) & (h >= 2.3)), 26)})
                self.raster_dict.update({"chute": Con(((u >= 3.0) & (h >= 2.3)), 8)})
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Base flow mu calculation failed.")

            try:
                self.logger.info("Updating MU raster ...")
                self.ras_mu = CellStatistics(self.raster_dict.values(), "MAXIMUM", "DATA")
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Base flow mu update failed.")

            arcpy.CheckInExtension('Spatial')
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: Base flow calculation failed.")

    def calculate_mu_bankfull(self, path2h_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            arcpy.env.extent = "MAXOF"

            try:
                self.logger.info("Reading input rasters ...")
                h = arcpy.Raster(path2h_ras)
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")

            try:
                self.logger.info("Evaluating morphological units (bankfull discharge) ...")
                temp_ras = Con(IsNull(self.ras_mu), 0.0, self.ras_mu)
                self.raster_dict.update({"in-channel bar": Con(((h > 0.0) & ~(temp_ras > 0)), 35, self.ras_mu)})
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Bankfull mu calculation failed.")

            try:
                self.logger.info("Updating MU raster ...")
                self.ras_mu = CellStatistics(self.raster_dict.values(), "MAXIMUM", "DATA")
                del temp_ras
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Bankfull mu update failed.")

            arcpy.CheckInExtension('Spatial')
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: Bankfull calculation failed.")

    def calculate_mu_floodway(self, path2h_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            arcpy.env.extent = "MAXOF"

            try:
                self.logger.info("Reading input rasters ...")
                h = arcpy.Raster(path2h_ras)
                self.logger.info("OK")
            except:
                self.logger.info("ERROR: Could not find / access input rasters.")

            try:
                self.logger.info("Evaluating morphological units (flood discharge) ...")
                temp_ras = Con(IsNull(self.ras_mu), 0.0, self.ras_mu)
                self.raster_dict.update({"floodplain": Con(((h > 0.0) & ~(temp_ras > 0)), 12, self.ras_mu)})
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Floodway mu calculation failed.")

            try:
                self.logger.info("Updating MU raster ...")
                self.ras_mu = CellStatistics(self.raster_dict.values(), "MAXIMUM", "DATA")
                del temp_ras
                self.logger.info("OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: Floodway update failed.")

            arcpy.CheckInExtension('Spatial')
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: Floodway calculation failed.")

    def clean_up(self):
        try:
            self.logger.info("Cleaning up ...")
            del self.ras_mu, self.raster_dict
            ft.clean_dir(self.cache)
            ft.rm_dir(self.cache)
            self.logger.info("OK")
        except:
            self.logger.info("Failed to clean up .cache folder.")

        try:
            ft.stop_logging(self.logger)
        except:
            self.logger.info("Could not finalize logfile.")

    def save_mu(self, *args):
        # args[0] can be an optional output directory
        try:
            self.out_dir = args[0]
        except:
            pass
        self.logger.info("")
        self.logger.info("SAVING ... ")
        arcpy.CheckOutExtension('Spatial')  # check out license
        arcpy.gp.overwriteOutput = True
        arcpy.env.workspace = self.cache
        arcpy.env.extent = "MAXOF"
        arcpy.CheckInExtension('Spatial')
        try:
            self.logger.info("Converting MU IDs to strings:")

            self.logger.info("  >> Converting raster to points ...")
            pts = arcpy.RasterToPoint_conversion(self.ras_mu, self.cache + "pts_del.shp")

            self.logger.info("  >> Converting numbers to strings ...")
            arcpy.AddField_management(pts, "MU", "TEXT")
            expression = "inverse_dict = {4: 'agriplain', 5: 'backswamp', 6: 'bank', 8: 'chute', 9: 'cutbank', 10: 'fast glide', 11: 'flood runner', 12: 'floodplain', 13: 'high floodplain', 14: 'bedrock', 15: 'island high floodplain', 16: 'island-floodplain', 17: 'lateral bar', 18: 'levee', 19: 'medial bar', 20: 'mining pit', 21: 'point bar', 22: 'pond', 23: 'pool', 24: 'riffle', 25: 'riffle transition', 26: 'run', 27: 'slackwater', 28: 'slow glide', 29: 'spur dike', 30: 'swale', 31: 'tailings', 32: 'terrace', 33: 'tributary channel', 34: 'tributary delta', 35: 'in-channel bar'}"
            arcpy.CalculateField_management(pts, "MU", "inverse_dict[!grid_code!]", "PYTHON", expression)

            self.logger.info("  >> OK")
            self.logger.info("Saving MU string raster as:")
            self.logger.info(str(self.out_dir) + "mu_str")
            arcpy.PointToRaster_conversion(in_features=pts, value_field="MU",
                                           out_rasterdataset=self.out_dir + "mu_str",
                                           cell_assignment="MOST_FREQUENT", cellsize=5)
            self.logger.info("OK")
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: Field assignment failed.")

        try:
            self.logger.info("Saving mu numeric raster as:")
            self.logger.info(str(self.out_dir) + "mu")
            self.ras_mu.save(self.out_dir + "mu")
            self.logger.info("OK")
        except arcpy.ExecuteError:
            self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
        except Exception as e:
            self.logger.info(arcpy.GetMessages(2))
        except:
            self.logger.info("ERROR: Saving failed.")

        self.clean_up()

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cMorphUnits.MU")
