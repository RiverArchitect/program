
# !/usr/bin/python
try:
    import sys, os, arcpy, logging, random
    from arcpy.sa import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cReachManager as cRM
    import cDefinitions as cDef
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy, os, sys, logging, random).")


class VolumeAssessment:
    def __init__(self, unit_system, org_ras_dir, mod_ras_dir, reach_ids):
        # unit_system must be either "us" or "si"
        # feature_ids = list of feature shortnames
        # reach_ids = list of reach names to limit the analysis

        # general directories and parameters
        self.cache = config.dir2mt + ".cache%s\\" % str(random.randint(1000000, 9999999))
        self.vol_name = mod_ras_dir.split(":\\")[-1].split(":/")[-1].split("01_Conditions\\")[-1].split("01_Conditions/")[-1].split(".tif")[0].replace("\\", "_").replace("/", "_").replace("_dem", "")
        fGl.chk_dir(self.cache)
        fGl.clean_dir(self.cache)
        self.logger = logging.getLogger("logfile")
        self.output_ras_dir = config.dir2mt + "Output\\%s\\" % self.vol_name
        fGl.chk_dir(self.output_ras_dir)
        fGl.clean_dir(self.output_ras_dir)
        self.rasters = []
        self.raster_info = ""
        self.rasters_for_pos_vol = {}
        self.rasters_for_neg_vol = {}
        self.reader = cRM.Read()
        self.reaches = cDef.ReachDefinitions()
        self.volume_neg_dict = {}
        self.volume_pos_dict = {}

        try:
            self.orig_raster = arcpy.Raster(org_ras_dir)
        except:
            self.orig_raster = Float(-1)
            self.logger.info("ERROR: Cannot load original DEM")
        try:
            self.modified_raster = arcpy.Raster(mod_ras_dir)
        except:
            self.modified_raster = Float(-1)
            self.logger.info("ERROR: Cannot load modified DEM.")

        # set relevant reaches
        try:
            self.reach_ids_applied = reach_ids
            self.reach_names_applied = []
            for rn in self.reach_ids_applied:
                self.reach_names_applied.append(self.reaches.dict_id_names[rn])
        except:
            self.reach_ids_applied = self.reaches.id_xlsx
            self.reach_names_applied = self.reaches.name_dict
            self.logger.info("WARNING: Cannot identify reaches.")

        # set unit system variables
        if ("us" in str(unit_system)) or ("si" in str(unit_system)):
            self.units = unit_system
        else:
            self.units = "us"
            self.logger.info("WARNING: Invalid unit_system identifier. unit_system must be either \'us\' or \'si\'.")
            self.logger.info("         Setting unit_system default to \'us\'.")

        if self.units == "us":
            self.convert_volume_to_cy = 0.037037037037037037037037037037037  #ft3 -> cy: float((1/3)**3)
            self.unit_info = " cubic yard"
            self.volume_threshold = 0.99  # ft -- CHANGE lod US customary HERE --
        else:
            self.convert_volume_to_cy = 1.0  # m3
            self.unit_info = " cubic meter"
            self.volume_threshold = 0.30  # m -- CHANGE lod SI metric HERE --

    def make_volume_diff_rasters(self):
        # Writes Raster Dataset to Output/Rasters/vol_name folder
        self.logger.info("")
        self.logger.info(" * creating volume difference Rasters ...")

        for rn in self.reach_ids_applied:
            if not (rn == "none"):
                reach_name = str(rn)
            else:
                reach_name = "ras" + str(rn)[0]
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            try:
                extents = self.reader.get_reach_coordinates(self.reaches.dict_id_int_id[rn])
            except:
                extents = "MAXOF"
                self.logger.info("ERROR: Could not retrieve reach coordinates.")
            if not (type(extents) == str):
                try:
                    # XMin, YMin, XMax, YMax
                    arcpy.env.extent = arcpy.Extent(extents[0], extents[1], extents[2], extents[3])
                except:
                    self.logger.info("ERROR: Failed to set reach extents -- output is corrupted.")
                    continue
            else:
                arcpy.env.extent = extents

            if str(self.vol_name).__len__() > 5:
                ras_name = reach_name + "_" + str(self.vol_name)[0:5]
            else:
                ras_name = reach_name + "_" + str(self.vol_name)

            self.logger.info("   * making excavation Raster ... ")
            try:
                excav_ras = Con(Float(self.modified_raster) <= Float(self.orig_raster),
                                Con(Float(Abs(self.orig_raster - self.modified_raster)) >= self.volume_threshold,
                                    Float(Abs(self.orig_raster - self.modified_raster)), Float(0.0)),
                                Float(0.0))
            except arcpy.ExecuteError:
                self.logger.info(arcpy.GetMessages(2))
                arcpy.AddError(arcpy.GetMessages(2))
            except Exception as e:
                self.logger.info(e.args[0])
                arcpy.AddError(e.args[0])
            except:
                self.logger.info("ERROR: (arcpy).")
                self.logger.info(arcpy.GetMessages())
            try:
                self.rasters_for_neg_vol.update({rn: excav_ras})
                self.volume_neg_dict.update({rn: -0.0})
                self.rasters.append(ras_name + "exc.tif")
                excav_ras.save(self.output_ras_dir + ras_name + "exc.tif")
            except:
                self.logger.info("ERROR: Raster could not be saved.")

            self.logger.info("   * making fill Raster ... ")
            try:
                fill_ras = Con(Float(self.modified_raster) > Float(self.orig_raster),
                               Con(Float(Abs(self.modified_raster - self.orig_raster)) >= self.volume_threshold,
                                   Float(Abs(self.modified_raster - self.orig_raster)), Float(0.0)),
                               Float(0.0))
            except arcpy.ExecuteError:
                self.logger.info(arcpy.GetMessages(2))
                arcpy.AddError(arcpy.GetMessages(2))
            except Exception as e:
                self.logger.info(e.args[0])
                arcpy.AddError(e.args[0])
            except:
                self.logger.info("ERROR: (arcpy).")
                self.logger.info(arcpy.GetMessages())
            try:
                self.rasters_for_pos_vol.update({rn: fill_ras})
                self.volume_pos_dict.update({rn: +0.0})
                self.rasters.append(ras_name + "fill.tif")
                fill_ras.save(self.output_ras_dir + ras_name + "fill.tif")
            except:
                self.logger.info("ERROR: Raster could not be saved.")

    def volume_computation(self):
        self.logger.info(" * calculating volume differences ...")
        # requires 3D extension
        arcpy.CheckOutExtension("3D")
        arcpy.env.extent = "MAXOF"

        for rn in self.reach_ids_applied:
            try:
                self.logger.info("   * calculating fill volume from " + str(self.rasters_for_pos_vol[rn]))
                self.logger.info("     *** takes time ***")
                feat_vol = arcpy.SurfaceVolume_3d(self.rasters_for_pos_vol[rn], "", "ABOVE", 0.0, 1.0)
                voltxt = feat_vol.getMessage(1).split("Volume=")[1]
                self.logger.info("     RESULT: " + str(float(voltxt)*self.convert_volume_to_cy) + self.unit_info + ".")
                self.volume_pos_dict[rn] = float(voltxt) * self.convert_volume_to_cy
            except:
                self.logger.info("ERROR: Calculation of volume from " + str(self.rasters_for_pos_vol[rn]) + " failed.")

            try:
                self.logger.info("   * calculating excavation volume from " + str(self.rasters_for_neg_vol[rn]))
                self.logger.info("     *** takes time ***")
                feat_vol = arcpy.SurfaceVolume_3d(self.rasters_for_neg_vol[rn], "", "ABOVE", 0.0, 1.0)
                voltxt = feat_vol.getMessage(1).split("Volume=")[1]
                self.logger.info("     RESULT: " + str(float(voltxt)*self.convert_volume_to_cy) + self.unit_info + ".")
                self.volume_neg_dict[rn] = float(voltxt) * self.convert_volume_to_cy
            except:
                self.logger.info("ERROR: Calculation of volume from " + str(self.rasters_for_neg_vol[rn]) + " failed.")

        # ALTERNATIVE OPTION IF arcpy.SurfaceVolume_3d FAILS
        # import numpy
        # myArray = arcpy.RasterToNumPyArray(outVol)
        # totVolume = numpy.sum(myArray)
        arcpy.CheckInExtension("3D")

    def get_volumes(self):
        self.make_volume_diff_rasters()
        self.volume_computation()
        # write excavation volumes to workbook
        writer = cRM.Write(self.output_ras_dir)
        writer.write_volumes(self.vol_name, self.reach_names_applied,
                             fGl.dict_values2list(self.volume_neg_dict.values()), self.unit_info.strip(), -1)
        del writer

        # write fill volumes to workbook
        writer = cRM.Write(self.output_ras_dir)
        writer.write_volumes(self.vol_name, self.reach_names_applied,
                             fGl.dict_values2list(self.volume_pos_dict.values()), self.unit_info.strip(), 1)

        self.logger.info("FINISHED.")

        # copy logfile (contains volume information)
        try:
            from shutil import copyfile
            copyfile(config.dir2ra + "logfile.log", config.dir2va + "Output\\Logfiles\\logfile.log")
        except:
            pass

        return self.vol_name, self.output_ras_dir

    def __call__(self):
        print("Class Info: <type> = VolumeAssessment (%s)" % os.path.dirname(__file__))
        print(dir(self))




