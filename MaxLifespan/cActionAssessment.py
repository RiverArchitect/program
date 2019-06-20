#!/usr/bin/python
try:
    import cFeatureActions as cFA
    import os, logging, sys
    # load functions from riverpy
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
    import cDefinitions as cDef  # contains reach and feature definitions
except:
    print("ExceptionERROR: Missing packages (required: os, logging, sys, riverpy")

try:
    import arcpy
    from arcpy.sa import *  # good for raster processing
    import numpy as np
except:
    print("ExceptionERROR: Missing packages (required: arcpy, numpy")


class ArcPyContainer:
    def __init__(self, condition, feature_type, dir_base_ras, *args):
        self.logger = logging.getLogger("logfile")
        self.raster_info_lf = ""
        self.condition = str(condition)
        self.cache = config.dir2ml + ".cache\\"
        self.feature_info = cDef.FeatureDefinitions()
        self.output_ras = config.dir2ml + "Output\\Rasters\\" + self.condition + "\\"
        fGl.chk_dir(self.output_ras)
        self.output_shp = config.dir2ml + "Output\\Shapefiles\\" + self.condition + "\\"
        fGl.chk_dir(self.output_shp)
        try:
            # if optional input raster directory is provided ...
            if args[1]:
                self.features = cFA.Manager(condition, feature_type, args[1])  # feature class object
        except:
            self.features = cFA.Manager(condition, feature_type)  # feature class object
        self.raster_dict = {}
        try:
            # one zero-raster that is updated, another wont be updated
            self.make_zero_ras(dir_base_ras)
            self.best_lf_ras = arcpy.Raster(config.dir2ml + ".templates\\rasters\\zeros.tif")
            self.null_ras = arcpy.Raster(config.dir2ml + ".templates\\rasters\\zeros.tif")
        except:
            print("ExceptionERROR: Could not find base Raster for assigning lifespans.")
        self.shp_dict = {}
        self.applied_shortnames = []
        self.raster_info = ""
        self.errors = False

        try:
            unit_system = args[0]
        except:
            unit_system = "us"

        if unit_system == "us":
            self.ft2m = config.m2ft  # this is correctly assigned
            self.ft2in = 12  # (in/ft) conversion factor for U.S. customary units
        else:
            self.ft2m = 1.0
            self.ft2in = 1   # (in/ft) dummy conversion factor in SI

        self.g = 9.81 / self.ft2m   # (ft/s2) gravity acceleration
        self.s = 2.68               # (--) relative grain density (ratio of rho_s and rho_w)

    def get_design_data(self):
        # requires that get_best_lifespan is first executed!
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("   LOOK UP DESIGN MAP DATA")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        try:
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            arcpy.CheckOutExtension('Spatial')  # check out license
            for i in range(0, self.features.ds_rasters.__len__()):
                sn = self.get_feat_shortname(str(self.features.ds_rasters[i]))
                shortname = "ds_" + sn
                self.logger.info("   >> Adding design raster for " + shortname + " ...")
                try:
                    self.raster_dict.update({shortname: Float(Con((self.features.ds_rasters[i] > 0), 0.8))})
                    self.logger.info("      Success: Added applicability of " + str(sn) + " (ds).")
                except:
                    self.errors = True
                    self.logger.info("ERROR:" + shortname + " contains non-valid data or is empty.")

            self.logger.info("   >> Finished design map look-up.")

            arcpy.CheckInExtension('Spatial')  # release license
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: Lifespan/Design data fetch failed.")
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: Lifespan/Design data fetch failed.")
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
        except:
            self.errors = True
            self.logger.info("ERROR: Lifespan/Design data fetch failed.")
            self.logger.info(arcpy.GetMessages())

    def get_lifespan_data(self):
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("   LOOK UP LIFESPAN MAP DATA")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        try:
            arcpy.env.workspace = self.cache
            arcpy.CheckOutExtension('Spatial')  # check out license

            for i in range(0, self.features.lf_rasters.__len__()):
                sn = self.get_feat_shortname(str(self.features.lf_rasters[i]))
                shortname = "lf_" + sn
                self.logger.info("   >> Adding lifespan raster for " + shortname + " ...")

                try:
                    self.raster_dict.update({shortname: self.features.lf_rasters[i]})
                    self.logger.info("      Success: Added highest lifespans from " + str(sn) + " (lf).")
                except:
                    self.errors = True
                    self.logger.info("ERROR: " + shortname + " contains non-valid data or is empty.")

            self.logger.info("   >> Finished lifespan map look-up.")
            arcpy.CheckInExtension('Spatial')  # check in license
        except arcpy.ExecuteError:
            self.logger.info("ERROR: Lifespan/Design data fetch failed.")
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ERROR: Lifespan/Design data fetch failed.")
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
        except:
            self.errors = True
            self.logger.info("ERROR: Lifespan/Design data fetch failed.")
            self.logger.info(arcpy.GetMessages())

    def get_feat_name(self, raster_name):
        for sn in self.feature_info.id_list:
            if sn in raster_name:
                return self.feature_info.feat_name_dict[sn]

    def get_feat_shortname(self, raster_name):
        for sn in self.feature_info.id_list:
            if sn in raster_name:
                return sn

    def get_feat_num(self, raster_name):
        for sn in self.feature_info.id_list:
            if sn in raster_name:
                return self.feature_info.feat_num_dict[sn]

    def identify_best_features(self):
        # find highest lifespans and related features
        try:
            arcpy.env.workspace = self.cache
            arcpy.gp.overwriteOutput = True
            arcpy.env.extent = "MAXOF"
            arcpy.CheckOutExtension('Spatial')  # check out license
            self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
            self.logger.info("   BEST FEATURE ASSESSMENT")
            self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
            self.logger.info("   >> Identification of features with highest lifespans  ...")
            try:
                self.logger.info("   >> Calculating cell statistics ...")
                self.raster_dict.update({"temp": self.null_ras})  # temporal raster extension
                self.best_lf_ras = CellStatistics(fGl.dict_values2list(self.raster_dict.values()), "MAXIMUM", "DATA")
                del self.raster_dict["temp"]  # remove temp entry
                self.logger.info("      -> Extending raster ...")
            except:
                self.logger.info("ERROR: Calculation of cell statistics failed.")

            for sn in self.raster_dict.keys():
                feat_ras = self.raster_dict[sn]
                try:
                    arcpy.env.extent = feat_ras.extent
                except:
                    pass

                try:
                    self.logger.info(
                        "      -> Applying best performance of " + str(sn) + " ...")
                    __temp_ras__ = Con((Float(feat_ras) == Float(self.best_lf_ras)), 1)

                    self.logger.info("       > Saving raster " + str(sn) + " *** takes time *** ")
                    __temp_ras__.save(self.output_ras + str(sn) + ".tif")
                except:
                    self.errors = True
                    self.logger.info("WARNING: Identification failed (" + str(sn) + ").")
                    __temp_ras__ = 0

                try:
                    self.logger.info(
                        "       > Converting " + str(sn) + " to polygon ...")

                    if str(sn).__len__() > 13:
                        shp_name = str(sn)[0:12]
                    else:
                        shp_name = str(sn)

                    arcpy.RasterToPolygon_conversion(__temp_ras__, self.output_shp + shp_name + ".shp")
                except:
                    self.errors = True
                    self.logger.info("WARNING: Conversion to polygon failed (" + str(sn) + ").")

            try:
                self.logger.info("   >> Setting lifespans of design features to 20 years ...")
                update_ras_0 = Con((Float(self.best_lf_ras) == 0.8), Float(20.0), self.best_lf_ras)
                update_ras_1 = Con(~(Float(update_ras_0) == Float(0)), update_ras_0)
                self.best_lf_ras = update_ras_1

                self.logger.info("   >> Saving maximum lifespan rasters (all features) ...")
                self.best_lf_ras.save(self.cache + "max_lf.tif")
                try:
                    if not(self.feature_info.id_list_plants[0] in " ".join(fGl.dict_values2list(self.raster_dict.keys()))):
                        arcpy.CopyRaster_management(self.cache + "max_lf.tif", self.output_ras + "max_lf.tif")
                    else:
                        arcpy.CopyRaster_management(self.cache + "max_lf.tif", self.output_ras + "max_lf_plants.tif")
                except:
                    self.logger.info("      ** id note: cannot access plant shortnames")
                    arcpy.CopyRaster_management(self.cache + "max_lf.tif", self.output_ras + "max_lf.tif")
            except:
                self.errors = True
                self.logger.info("ERROR: Could not save best lifespan raster.")

            if not self.errors:
                self.logger.info("   >> Success.")
                self.logger.info("   >> Best suitable feature shapefiles are stored in:")
                self.logger.info("      " + str(self.output_shp))
                self.logger.info("   >> Best lifespans raster is stored in:")
                self.logger.info("      " + str(self.output_ras))

            arcpy.CheckInExtension('Spatial')  # check in license
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
        except:
            self.logger.info("ERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages())

    def make_zero_ras(self, dir_base_ras):
        arcpy.CheckOutExtension('Spatial')  # check out license
        zero_ras_str = config.dir2ml + ".templates\\rasters\\zeros.tif"
        if os.path.isfile(zero_ras_str):
            fGl.rm_file(zero_ras_str)
        try:
            base_dem = arcpy.Raster(dir_base_ras)
            self.logger.info(" >> Preparing zero raster based on \n    " + dir_base_ras)
            arcpy.env.extent = base_dem.extent
            arcpy.env.workspace = self.cache
            zero_ras = Con(IsNull(base_dem), 0, 0)
            zero_ras.save(zero_ras_str)
        except:
            self.logger.info("ExceptionERROR: Unable to create ZERO Raster. Manual intervention required: Check Package documentation (Troubleshooting).")
        arcpy.CheckInExtension('Spatial')  # check in license

    def __call__(self):
        self.get_lifespan_data()
        self.get_design_data()
        self.identify_best_features()
        self.logger.info("Finished all actions (cActionAssessment).")
