
# !/usr/bin/python
try:
    import sys, os, arcpy, logging, random
    from arcpy.sa import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cReachManager as cRM
    import cDefinitions as cDef
    import fGlobal as fGl
    import cFeatures as cFe
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy, os, sys, logging, random).")


class ModifyTerrain:
    def __init__(self, condition, unit_system, feature_ids, topo_in_dir, feat_in_dir, reach_ids):
        # unit_system must be either "us" or "si"
        # feature_ids = list of feature shortnames
        # topo_in_dir = input directory for dem and d2w rasters
        # feat_in_dir = input directory for feature max lifespan rasters
        # reach_ids = list of reach names to limit the analysis

        # general directories and parameters
        self.all_rasters = []  # will get assigned an arcpy.ListRasters() list
        self.cache = config.dir2mt + ".cache%s\\" % str(random.randint(1000000, 9999999))
        fGl.chk_dir(self.cache)
        fGl.clean_dir(self.cache)
        self.features = cDef.FeatureDefinitions()
        self.condition = condition
        self.current_reach_id = ""
        self.logger = logging.getLogger("logfile")
        self.output_ras_dir = config.dir2mt + "Output\\ThresholdRivers\\" + str(condition) + "\\"
        fGl.chk_dir(self.output_ras_dir)
        fGl.clean_dir(self.output_ras_dir)
        self.raster_dict = {}
        self.raster_info = ""
        self.reader = cRM.Read()
        self.reaches = cDef.ReachDefinitions()

        # set relevant reaches
        try:
            self.reach_ids_applied = reach_ids
            self.reach_names_applied = []
            for rn in self.reach_ids_applied:
                self.reach_names_applied.append(self.reaches.dict_id_names[rn])
            self.reach_delineation = True
        except:
            self.reach_ids_applied = self.reaches.id_xlsx
            self.reach_names_applied = self.reaches.name_dict
            self.reach_delineation = False

        # set relevant (applied) features
        if feature_ids.__len__() > 0:
            self.applied_feat_ids = feature_ids
        else:
            self.applied_feat_ids = self.features.id_list
        self.applied_feat_names = []

        for feat in self.applied_feat_ids:
            self.applied_feat_names.append(self.features.feat_name_dict[feat])

        # set unit system variables
        if ("us" in str(unit_system)) or ("si" in str(unit_system)):
            self.units = unit_system
        else:
            self.units = "us"
            self.logger.info("WARNING: Invalid unit_system identifier. unit_system must be either \'us\' or \'si\'.")
            self.logger.info("         Setting unit_system default to \'us\'.")

        # get RASTERS from 01_Conditions folder
        try:
            self.input_dir_fa = topo_in_dir
        except:
            self.input_dir_fa = config.dir2conditions + str(condition) + "\\"

        try:
            self.ras_dem = arcpy.Raster(self.input_dir_fa + "dem.tif")
        except:
            try:
                self.ras_dem = arcpy.Raster(self.input_dir_fa + "dem")
            except:
                self.ras_dem = 0

        try:
            self.ras_d2w = arcpy.Raster(self.input_dir_fa + "d2w.tif")
        except:
            try:
                self.ras_d2w = arcpy.Raster(self.input_dir_fa + "d2w")
            except:
                self.ras_d2w = 0

        # get inputs and RASTERS from MaxLifespan
        try:
            self.input_dir_ap = feat_in_dir
        except:
            self.input_dir_ap = config.dir2ml + "Output\\Rasters\\" + str(condition) + "\\"

        try:
            self.make_zero_ras()
            self.zero_ras = arcpy.Raster(self.cache + "zeros.tif")
        except:
            print("ExceptionERROR: Could not create zero raster (base reference).")

    def get_action_raster(self, feature_name):
        arcpy.env.workspace = self.input_dir_ap
        self.all_rasters = arcpy.ListRasters()
        self.logger.info("  >> Collecting max. lifespan raster ...")
        for ras_name in self.all_rasters:
            if feature_name in ras_name:
                ras_act = self.input_dir_ap + ras_name
                raster = Float(arcpy.Raster(ras_act))
                break
        arcpy.env.workspace = self.cache
        if "raster" in locals():
            self.logger.info("     Success. Found: " + str(raster))
            return raster
        else:
            self.logger.info("ERROR: Cannot find " + str(feature_name) + " max. lifespan raster.")
            return -1

    def lower_dem_for_plants(self, feat_id, extents):
        self.logger.info("")
        feature_name = self.features.feat_name_dict[feat_id]
        self.logger.info("* *   * *   * * " + feature_name.capitalize() + " * *   * *  * *")
        # set arcpy env
        arcpy.gp.overwriteOutput = True
        arcpy.env.workspace = self.cache
        if not (type(extents) == str):
            try:
                # XMin, YMin, XMax, YMax
                arcpy.env.extent = arcpy.Extent(extents[0], extents[1], extents[2], extents[3])
            except:
                self.logger.info("ERROR: Failed to set reach extents -- output is corrupted.")
                return -1
        else:
            arcpy.env.extent = extents
        arcpy.CheckOutExtension('Spatial')  # check out license

        # set rasters
        feat_act_ras = self.get_action_raster(feat_id)
        feat_ras_cor = Float(Con(IsNull(feat_act_ras), self.zero_ras, feat_act_ras))
        self.logger.info("  >> Calculating DEM after terrain " + feature_name + " ... ")

        try:
            pl_1 = cFe.Feature(self.features.id_list_plants[0])
            try:
                pl_2 = cFe.Feature(self.features.id_list_plants[1])
                try:
                    pl_3 = cFe.Feature(self.features.id_list_plants[2])
                    try:
                        pl_4 = cFe.Feature(self.features.id_list_plants[3])
                        max_d2w = min([pl_1.threshold_d2w_up, pl_2.threshold_d2w_up, pl_3.threshold_d2w_up,
                                       pl_4.threshold_d2w_up])
                    except:
                        max_d2w = min([pl_1.threshold_d2w_up, pl_2.threshold_d2w_up, pl_3.threshold_d2w_up])
                except:
                    max_d2w = min([pl_1.threshold_d2w_up, pl_2.threshold_d2w_up])
            except:
                max_d2w = pl_1.threshold_d2w_up
        except:
            max_d2w = 10.0
            self.logger.info("ERROR: Failed to read maximum depth to water value for terrain grading/widening (using default = 10).")

        if self.raster_info.__len__() > 0:
            self.logger.info("     ... based on modified " + str(self.raster_info) + " DEM  ... ")
            dem = Float(self.raster_dict[self.raster_info])
            # det = self.dem_det - (self.ras_dem - self.raster_dict[self.raster_info])
            d2w = Float(self.ras_d2w) - (Float(self.ras_dem) - Float(self.raster_dict[self.raster_info]))
        else:
            dem = Float(self.ras_dem)
            # det = self.dem_det
            d2w = Float(self.ras_d2w)

        feat_dem = Con(feat_ras_cor > 0.0, Con((d2w > Float(max_d2w)), Float(dem - (d2w - max_d2w)), dem), dem)

        self.raster_info = feat_id[0:3]
        self.raster_dict.update({self.raster_info: feat_dem})

        arcpy.CheckInExtension('Spatial')  # release license

    def make_zero_ras(self):
        arcpy.CheckOutExtension('Spatial')  # check out license
        zero_ras_str = self.cache + "zeros.tif"
        if os.path.isfile(zero_ras_str):
            fGl.rm_file(zero_ras_str)
        try:
            try:
                base_dem = arcpy.Raster(self.input_dir_fa + "dem.tif")
            except:
                base_dem = arcpy.Raster(self.input_dir_fa + "dem")

            print("Preparing zero raster based on DEM extents ...")
            arcpy.env.extent = base_dem.extent
            arcpy.env.workspace = config.dir2conditions + self.condition + "\\"
            zero_ras = Con(IsNull(base_dem), 0, 0)
            zero_ras.save(zero_ras_str)
            arcpy.env.workspace = self.cache
        except:
            print("ExceptionERROR: Unable to create ZERO Raster.")
        arcpy.CheckInExtension('Spatial')  # check in license

    def modification_manager(self, feat_id):
        if not self.reach_delineation:
            extents = "MAXOF"
        else:
            try:
                extents = self.reader.get_reach_coordinates(self.reaches.dict_id_int_id[self.current_reach_id])
            except:
                extents = "MAXOF"
                self.logger.info("ERROR: Could not retrieve reach coordinates.")
        self.lower_dem_for_plants(feat_id, extents)

    def save_rasters(self):
        # Writes Raster Dataset as Esri Grid file to Output/Rasters/condition folder
        self.logger.info("")
        self.logger.info("* *   * *   * * SAVE RASTERS * *   * *  * *")
        # pass reach id number to save rasters (template name required to apply layout template)
        reach_no = self.reaches.id_no_dict[self.current_reach_id]
        reach_name = "r0%1d" % (reach_no,)
        try:
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            for ras in self.raster_dict.keys():
                if self.raster_dict[ras].maximum > 0:
                    if str(ras).__len__() > 5:
                        ras_name = reach_name + "_" + str(ras)[0:5] + ".tif"
                    else:
                        ras_name = reach_name + "_" + str(ras) + ".tif"

                    # save only relevant rasters -- empty rasters may crash python
                    try:
                        self.logger.info("  >> Saving raster: " + ras_name + " ... ")
                        self.logger.info("     *** takes time ***")
                        self.raster_dict[ras].save(self.cache + ras + ".tif")
                        self.logger.info(
                            "    -- Casting to " + self.output_ras_dir + ras_name + " ...")
                        arcpy.CopyRaster_management(self.cache + ras + ".tif", self.output_ras_dir + ras_name)

                    except:
                        self.logger.info("ERROR: Raster could not be saved.")
                else:
                    self.logger.info("    -- " + str(ras) + " is empty (not applicable on reach): Export canceled.")

        except arcpy.ExecuteError:
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
        except:
            self.logger.info("ERROR: Raster copy to Output folder failed.")
            self.logger.info(arcpy.GetMessages())

    def __call__(self):

        for rn in self.reach_ids_applied:
            self.current_reach_id = rn
            reach_name = self.reaches.dict_id_names[rn]
            self.logger.info("\n\n     REACH NAME: " + str(reach_name).capitalize())
            self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")

            for feat_id in self.applied_feat_ids:
                self.modification_manager(feat_id)

            self.save_rasters()
            # reset raster storage
            self.raster_dict = {}
            self.raster_info = ""

        try:
            self.logger.info("  >> Clearing .cache (arcpy.Delete_management - temp.designs - please wait) ...")
            for ras in self.raster_dict:
                try:
                    arcpy.Delete_management(self.raster_dict[ras])
                except:
                    self.logger.info("WARNING: Could not delete " + str(ras) + " from .cache folder.")
            self.logger.info("  >> Done.")
            fGl.rm_dir(self.cache)  # dump cache after feature analysis
        except:
            self.logger.info("WARNING: Could not clear .cache folder.")
        self.logger.info("FINISHED.")






