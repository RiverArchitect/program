from __future__ import division
# !/usr/bin/python
try:
    import sys, os, arcpy, logging
    from arcpy.sa import *

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cTerrainIO as cio
    import cDefinitions as cdef
    import fGlobal as fg
    import cPlants as cp

except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy, os, sys, logging).")


class ModifyTerrain:
    def __init__(self, condition, unit_system, feature_ids, topo_in_dir, feat_in_dir, reach_ids):
        # unit_system must be either "us" or "si"
        # feature_ids = list of feature shortnames
        # topo_in_dir = input directory for dem and d2w rasters
        # feat_in_dir = input directory for feature max lifespan rasters
        # reach_ids = list of reach names to limit the analysis

        # general directories and parameters
        self.all_rasters = []  # will get assigned an arcpy.ListRasters() list
        self.alt_dir_volDEM = r""
        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        fg.chk_dir(self.cache)
        fg.clean_dir(self.cache)
        self.features = cdef.Features()
        self.condition = condition
        self.current_reach_id = ""
        self.output_ras_dir = os.path.dirname(os.path.realpath(__file__)) + "\\Output\\Rasters\\" + str(condition) + "\\"
        fg.chk_dir(self.output_ras_dir)
        fg.clean_dir(self.output_ras_dir)
        self.raster_dict = {}
        self.raster_info = ""
        self.rasters_for_pos_vol = []
        self.rasters_for_neg_vol = []
        self.reader = cio.Read()
        self.reaches = cdef.Reaches()
        self.volume_neg_dict = {}
        self.volume_pos_dict = {}
        self.writer = cio.Write()
        try:
            self.zero_ras = arcpy.Raster(os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')) + "\\MaxLifespan\\.templates\\rasters\\zeros")
        except:
            print("ExceptionERROR: Could not retrieve zero raster from MaxLifespan.")

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
            self.volume_pos_dict.update({feat: []})
            self.volume_neg_dict.update({feat: []})
            for reach_id in self.reaches.id_dict.values():
                # prepare zero lists for volume computation
                self.volume_pos_dict[feat].append(+0.0)
                self.volume_neg_dict[feat].append(-0.0)

        # set unit system variables
        if ("us" in str(unit_system)) or ("si" in str(unit_system)):
            self.units = unit_system
        else:
            self.units = "us"
            print("WARNING: Invalid unit_system identifier. unit_system must be either \'us\' or \'si\'.")
            print("         Setting unit_system default to \'us\'.")

        if self.units == "us":
            self.convert_volume_to_cy = 0.037037037037037037037037037037037  #ft3 -> cy: float((1/3)**3)
            self.unit_info = " cubic yard"
            self.volume_threshold = 0.99
        else:
            self.convert_volume_to_cy = 1.0
            self.unit_info = " cubic meter"
            self.volume_threshold = 0.30

        # get RASTERS from 01_Conditions folder
        try:
            self.input_dir_fa = topo_in_dir
        except:
            self.input_dir_fa = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\" + str(condition) + "\\"
        try:
            self.ras_dem = arcpy.Raster(self.input_dir_fa + "dem")
        except:
            self.ras_dem = 0

        try:
            self.ras_d2w = arcpy.Raster(self.input_dir_fa + "d2w")
        except:
            self.ras_d2w = 0

        # get inputs and RASTERS from MaxLifespan
        try:
            self.input_dir_ap = feat_in_dir
        except:
            self.input_dir_ap = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')) + "\\MaxLifespan\\Output\\Rasters\\" + str(
                condition) + "\\"

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

    def get_cad_rasters_for_volume(self, feat_id):
        # instruction: rasters must contain feat_ids in names
        arcpy.env.workspace = self.alt_dir_volDEM
        # arcpy.env.extent = "MAXOF"
        arcpy.CheckOutExtension('Spatial')  # check out license
        all_rasters = arcpy.ListRasters()
        raster_identified = False
        for ras_name in all_rasters:
            if ("dem" in ras_name) or (feat_id in ras_name) or ("mod" in ras_name):
                raster_identified = True
                ras_neg_vol = Con(((self.ras_dem - arcpy.Raster(self.alt_dir_volDEM + ras_name)) >= self.volume_threshold),
                                  (self.ras_dem - arcpy.Raster(self.alt_dir_volDEM + ras_name)), 0)
                self.raster_dict.update({feat_id[0:3] + "_diffneg": ras_neg_vol})
                ras_pos_vol = Con(((self.ras_dem - arcpy.Raster(self.alt_dir_volDEM + ras_name)) <= -self.volume_threshold),
                                  (arcpy.Raster(self.alt_dir_volDEM + ras_name) - self.ras_dem), 0)
                self.raster_dict.update({feat_id[0:3] + "_diffpos": ras_pos_vol})

        if not raster_identified:
            self.logger.info("ERROR: Cannot find modified DEM. Ensure that file names contain \'dem\' or \'mod\'.")

        arcpy.env.workspace = self.cache
        arcpy.CheckInExtension('Spatial')  # release license

    def logging_start(self, logfile_name):
        logfilenames = ["error.log", logfile_name + ".log", "logfile.log"]
        for fn in logfilenames:
            fn_full = os.path.join(os.getcwd(), fn)
            if os.path.isfile(fn_full):
                try:
                    os.remove(fn_full)
                    print("Overwriting old logfiles (" + fn + ").")
                except:
                    print("WARNING: Old logfile is locked.")
        # start logging
        self.logger = logging.getLogger(logfile_name)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s")

        # create console handler and set level to info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        # create error file handler and set level to error
        err_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[0]), "w", encoding=None, delay="true")
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(formatter)
        self.logger.addHandler(err_handler)
        # create debug file handler and set level to debug
        debug_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[1]), "w")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)
        self.logger.info("initiated " + logfile_name + ".modify_terrain")

    def logging_stop(self):
        # stop logging and release logfile
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

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
            pl_1 = cp.Plant1(self.features.id_list_plants[0])
            try:
                pl_2 = cp.Plant2(self.features.id_list_plants[1])
                try:
                    pl_3 = cp.Plant3(self.features.id_list_plants[2])
                    try:
                        pl_4 = cp.Plant4(self.features.id_list_plants[3])
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

        if self.raster_info.__len__() > 0 and not ("diff" in self.raster_info):
            self.logger.info("     ... based on modified " + str(self.raster_info) + " DEM  ... ")
            dem = Float(self.raster_dict[self.raster_info])
            # det = self.dem_det - (self.ras_dem - self.raster_dict[self.raster_info])
            d2w = Float(self.ras_d2w) - (Float(self.ras_dem) -Float(self.raster_dict[self.raster_info]))
        else:
            dem = Float(self.ras_dem)
            # det = self.dem_det
            d2w = Float(self.ras_d2w)

        feat_dem = Con(feat_ras_cor > 0.0, Con((d2w > Float(max_d2w)), Float(dem - (d2w - max_d2w)), dem), dem)
        # feat_dem = Con(feat_ras_cor > 0.0, dem - 50, dem)  # neglect water table
        feat_dem_diff = dem - feat_dem

        self.raster_dict.update({feat_id[0:3] + "_diffneg": feat_dem_diff})
        self.raster_info = feat_id[0:3]
        self.raster_dict.update({self.raster_info: feat_dem})

        arcpy.CheckInExtension('Spatial')  # release license

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
            for ras in (self.raster_dict.keys()):
                if self.raster_dict[ras].maximum > 0:
                    if str(ras).__len__() > 5:
                        ras_name = reach_name + "_" + str(ras)[0:5]
                    else:
                        ras_name = reach_name + "_" + str(ras)

                    # save only relevant rasters -- empty rasters may crash python
                    try:
                        if "diff" in str(ras):
                            if "pos" in str(ras):
                                suffix = "_pos"
                            if "neg" in str(ras):
                                suffix = "_neg"
                        else:
                            suffix = ""

                        self.logger.info("  >> Saving raster: " + ras_name + " ... ")
                        self.logger.info("     *** takes time ***")
                        self.raster_dict[ras].save(self.cache + ras)
                        self.logger.info(
                            "    -- Casting to " + self.output_ras_dir + ras_name + suffix + " ...")
                        arcpy.CopyRaster_management(self.cache + ras, self.output_ras_dir + ras_name + suffix)

                        if "diff" in str(ras):
                            if "pos" in str(ras):
                                self.rasters_for_pos_vol.append(arcpy.Raster(self.output_ras_dir + ras_name + suffix))
                            if "neg" in str(ras):
                                self.rasters_for_neg_vol.append(arcpy.Raster(self.output_ras_dir + ras_name + suffix))

                    except:
                        self.logger.info("ERROR: Raster could not be saved.")
                else:
                    if "diff" in str(ras):
                        self.rasters_for_pos_vol.append(self.zero_ras)
                        self.rasters_for_neg_vol.append(self.zero_ras)
                    self.logger.info("    -- " + str(ras) + " is empty (not applicable on reach): Export cancelled.")

        except arcpy.ExecuteError:
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
        except:
            self.logger.info("ERROR: Raster copy to Output folder failed.")
            self.logger.info(arcpy.GetMessages())

    def volume_computation(self):
        self.logger.info("")
        self.logger.info("* *   * *   * * VOLUME CALCULATION * *   * *  * *")
        # requires 3D extension
        self.logger.info("  >> Calculating masses (volumes) of required earth works.")
        arcpy.CheckOutExtension("3D")
        arcpy.env.extent = "MAXOF"

        for vol_ras in self.rasters_for_pos_vol:
            try:
                if "zero" in str(vol_ras):
                    self.logger.info("     Dummy calculation (place holder to keep order in output files).")
                else:
                    self.logger.info("     Deriving fill volume of " + str(vol_ras))
                    self.logger.info("     *** takes time ***")
                feat_vol = arcpy.SurfaceVolume_3d(vol_ras, "", "ABOVE", 0.0, 1.0)
                voltxt = feat_vol.getMessage(2).split("Volume=")[1]
                self.logger.info("     RESULT: " + str(float(voltxt)*self.convert_volume_to_cy) + self.unit_info + ".")
                for feat_id in self.applied_feat_ids:
                    # parse applied feature id to find the accurate key in volume_pos_dict
                    if feat_id[0:3] in str(vol_ras):
                        # append volume to correct list entry
                        self.volume_pos_dict[feat_id][self.reaches.id_no_dict[self.current_reach_id]] = float(
                            voltxt) * self.convert_volume_to_cy
            except:
                self.logger.info("ERROR: Calculation of volume from " + str(vol_ras) + " failed.")

        for vol_ras in self.rasters_for_neg_vol:
            try:
                if "zero" in str(vol_ras):
                    self.logger.info("     Dummy calculation (place holder to keep order in output files).")
                else:
                    self.logger.info("     Deriving excavation volume of " + str(vol_ras))
                    self.logger.info("     *** takes time ***")
                feat_vol = arcpy.SurfaceVolume_3d(vol_ras, "", "ABOVE", 0.0, 1.0)
                voltxt = feat_vol.getMessage(2).split("Volume=")[1]
                self.logger.info("     RESULT: " + str(float(voltxt)*self.convert_volume_to_cy) + self.unit_info + ".")
                for feat_id in self.applied_feat_ids:
                    # parse applied feature id to find the accurate key in volume_pos_dict
                    if feat_id[0:3] in str(vol_ras):
                        # append volume to correct list entry
                        self.volume_neg_dict[feat_id][self.reaches.id_no_dict[self.current_reach_id]] = float(
                            voltxt) * self.convert_volume_to_cy
            except:
                self.logger.info("ERROR: Calculation of volume from " + str(vol_ras) + " failed.")

        # ALTERNATIVE OPTION IF arcpy.SurfaceVolume_3d FAILS
        # import numpy
        # myArray = arcpy.RasterToNumPyArray(outVol)
        # totVolume = numpy.sum(myArray)
        arcpy.CheckInExtension("3D")

    def __call__(self, *args):
        # args[0] can be volume_calculation_only = True or False (default: False)
        # args[1] directory of rasters to compare for volume computation
        try:
            volume_calculation_only = args[0]
            try:
                self.alt_dir_volDEM = args[1]
            except:
                print("ERROR: Received request for volume calculation but not input directory is provided.")
                return -1
        except:
            volume_calculation_only = False

        self.logging_start("logfile")

        for rn in self.reach_ids_applied:
            self.current_reach_id = rn
            reach_name = self.reaches.dict_id_names[rn]
            self.logger.info("")
            self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
            self.logger.info("     REACH NAME: " + str(reach_name).capitalize())
            self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")

            if not volume_calculation_only:
                for feat_id in self.applied_feat_ids:
                    self.modification_manager(feat_id)
            else:
                for feat_id in self.applied_feat_ids:
                    self.get_cad_rasters_for_volume(feat_id)
            self.save_rasters()
            self.volume_computation()
            # reset raster storage
            self.raster_dict = {}
            self.raster_info = ""
            self.rasters_for_neg_vol = []
            self.rasters_for_pos_vol = []

        # write excavation volumes to excel
        self.writer.write_volumes(self.condition, self.applied_feat_names, self.reaches.names_xlsx,
                                  self.volume_neg_dict.values(), self.unit_info.strip(), -1)
        # write fill volumes to excel
        self.writer.write_volumes(self.condition, self.applied_feat_names, self.reaches.names_xlsx,
                                  self.volume_pos_dict.values(), self.unit_info.strip(), 1)

        import time
        self.logger.info("  >> Waiting for processes to terminate ...")
        time.sleep(5)

        try:
            self.logger.info("  >> Clearing .cache (arcpy.Delete_management - temp.designs - please wait) ...")
            for ras in self.raster_dict:
                arcpy.Delete_management(self.raster_dict[ras])
            self.logger.info("  >> Done.")
            fg.rm_dir(self.cache)  # dump cache after feature analysis
        except:
            self.logger.info("WARNING: Could not clear .cache folder.")
        self.logger.info("FINISHED.")

        # copy logfile (contains important information!)
        from shutil import copyfile
        logfile_dir = os.path.dirname(__file__) + "\\Output\\Logfiles\\logfile.log"
        try:
            copyfile(os.path.dirname(__file__) + "\\" + logfile_name + ".log", logfile_dir)
        except:
            pass
        self.logging_stop()

        return logfile_dir





