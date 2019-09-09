try:
    import sys, os, logging
    import numpy as np
    from shutil import copyfile
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, shutil, sys, logging).")

try:
    import cWaterLevel as cWL
    import cDetrendedDEM as cDD
    import cMorphUnits as cMU
    import fSubCondition as fSC
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
    import cMakeTable as cMT
    import cMakeInp as cMI
    import cFlows as cFl
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")


class ConditionCreator:
    def __init__(self, dir2condition):
        self.condition = os.path.basename(dir2condition.strip("\\").strip("/"))
        self.dir2condition = dir2condition  # string of the condition to be created
        self.error = False
        self.warning = False
        self.logger = logging.getLogger("logfile")

    def create_discharge_table(self):
        try:
            flow_table = cMT.MakeFlowTable(os.path.basename(self.dir2condition), "q_return")
            return flow_table.make_condition_xlsx()
        except:
            self.error = True

    def create_flow_duration_table(self, input_flow_xlsx, aquatic_ambiance):
        try:
            condition = os.path.basename(self.dir2condition)
            flows = cFl.SeasonalFlowProcessor(input_flow_xlsx)
            for fish in aquatic_ambiance.keys():
                for lfs in aquatic_ambiance[fish]:
                    flows.get_fish_seasons(fish, lfs)
            output_xlsx = flows.make_flow_duration(condition)
            flows.make_condition_flow2d_duration(condition)
            return output_xlsx
        except:
            self.error = True

    def create_sub_condition(self, dir2src_condition, dir2bound):
        src_condition = os.path.basename(dir2src_condition.strip("\\").strip("/"))
        try:
            copyfile(dir2src_condition + "flow_definitions.xlsx", self.dir2condition + "flow_definitions.xlsx")
            all_flow_files = fGl.file_names_in_dir(config.dir2flows + src_condition)
            for f_xlsx in all_flow_files:
                try:
                    copyfile(config.dir2flows + src_condition + "\\" + f_xlsx, config.dir2flows + self.condition + "\\" + f_xlsx)
                except:
                    pass
        except:
            self.logger.info(" *** Could not find FLOW DEFINITIONS for %s. Use ANALYZE FLOWS for new sub-condition." % dir2src_condition)
        try:
            copyfile(dir2src_condition + "input_definitions.inp", self.dir2condition + "input_definitions.inp")
        except:
            self.logger.info(
                " *** Could not find input_definitions.inp in %s. Use MAKE INPUT FILE for new sub-condition." % dir2src_condition)
        try:
            self.error = fSC.make_sub_condition(dir2src_condition, self.dir2condition, dir2bound)
        except:
            self.error = True

    def generate_input_file(self, dir2flow_definitions):
        try:
            new_inp_file = cMI.MakeInputFile(self.dir2condition)
            return new_inp_file.make_info(dir2flow_definitions)
        except:
            self.error = True

    def make_d2w(self, h_ras_dir, dem_ras_dir, *args, **kwargs):
        wle = cWL.WLE(h_ras_dir, dem_ras_dir, self.dir2condition, *args, **kwargs)
        try:
            self.error = wle.calculate_d2w()
        except:
            self.error = True

    def make_det(self, h_ras_dir, dem_ras_dir):
        det = cDD.DET(self.dir2condition)
        try:
            self.error = det.calculate_det(h_ras_dir, dem_ras_dir)
        except:
            self.error = True

    def make_mu(self, unit, h_ras_dir, u_ras_dir):
        # unit = STR (either "us" or "si")
        mu = cMU.MU(unit, self.dir2condition)
        try:
            mu.calculate_mu(h_ras_dir, u_ras_dir)
            self.error = mu.save_mu(self.dir2condition)
        except:
            self.error = True

    @staticmethod
    def make_raster_name(input_raster_name, type_id):
        if type_id == "dem":
            return "dem.tif"
        if type_id == "back":
            return "back.tif"
        if type_id == "fill":
            return "fill.tif"
        if (type_id == "h") or (type_id == "u") or (type_id == "va"):
            return os.path.splitext(input_raster_name)[0] + ".tif"
        if type_id == "dmean":
            return "dmean.tif"
        if type_id == "scour":
            return "scour.tif"

    def save_tif(self, dir2inp_ras, type_id, **kwargs):
        # dir2inp_ras = any Raster data type
        # type_id = STR (copied raster names will be named beginning with type_id)
        no_data = True  # if False from kwargs > no_data will be converted to zeros
        # parse keyword arguments
        try:
            for k in kwargs.items():
                if "no_data" in k[0]:
                    no_data = k[1]
        except:
            pass
        target_raster_name = self.make_raster_name(os.path.basename(dir2inp_ras), type_id)
        self.logger.info("   - loading " + dir2inp_ras)
        try:
            arcpy.CheckOutExtension('Spatial')
            arcpy.env.overwriteOutput = True
            arcpy.env.workspace = self.dir2condition
            arcpy.env.extent = "MAXOF"
        except:
            self.logger.info("ERROR: Could not set arcpy environment (permissions and licenses?).")
            self.error = True
            return -1
        try:
            input_ras = arcpy.Raster(dir2inp_ras.split(".aux.xml")[0])
        except:
            self.logger.info("ERROR: Failed to load %s ." % dir2inp_ras)
            self.error = True
            return -1
        # convert 0 to NoData for depth rasters
        if not no_data and type_id == "h":
            self.logger.info("     * eliminate 0 data ... ")
            ras4tif = Con(Float(input_ras) > 0.000, Float(input_ras))

        else:
            ras4tif = input_ras
        self.logger.info("   - saving " + self.dir2condition + target_raster_name)
        try:
            ras4tif.save(self.dir2condition + target_raster_name)
            self.logger.info("     * OK")
        except:
            self.error = True
            self.logger.info("ERROR: Could not save %s ." % target_raster_name)

    def transfer_rasters_from_folder(self, folder_dir, type_id, string_container):
        # folder_dir = STR (full directory)
        # type_id = STR (copied raster names will be named beginning with type_id)
        # string_container = STR (characters that need to be contained within raster names
        self.logger.info(" > Getting {0} Rasters containing {1} from {2}.".format(str(type_id), string_container, str(folder_dir)))
        arcpy.env.workspace = folder_dir
        raster_list = arcpy.ListRasters("*", "All")
        arcpy.env.workspace = self.dir2condition
        try:
            for ras in raster_list:
                if str(string_container).__len__() > 0:
                    if str(string_container).lower() in str(ras).lower():
                        self.logger.info("   * Copying %s." % str(folder_dir + ras))
                        self.save_tif(folder_dir + ras, type_id, no_data=False)
        except:
            self.logger.info("ERROR: The selected folder does not contain any Raster containing the defined string.")

    def check_alignment(self, dir2new_condition):
        """Checks if all inputs have same cell size/alignment."""
        self.logger.info("Checking alignment of input files...")
        paths = []
        cell_sizes = []
        coordsyss = []
        corners = []
        for root, subdir, filenames in os.walk(dir2new_condition):
            for filename in filenames:
                if filename.endswith(".tif"):
                    path = os.path.join(root, filename)
                    paths.append(path)

                    cell_size = arcpy.GetRasterProperties_management(path, 'CELLSIZEX')[0]
                    cell_sizes.append(cell_size)

                    extent = arcpy.Describe(path).Extent

                    coordsys = extent.spatialReference.name
                    coordsyss.append(coordsys)

                    xmin = extent.XMin
                    ymin = extent.YMin
                    corners.append((xmin, ymin))

        aligned = True
        if len(set(cell_sizes)) != 1:
            aligned = False
            self.logger.info("WARNING: Not all inputs share same cell size.")
            for size in set(cell_sizes):
                self.logger.info("The following rasters have cell size %s:" % str(size))
                self.logger.info([x for i, x in enumerate(paths) if cell_sizes[i] == size])

        if len(set(coordsyss)) != 1:
            aligned = False
            self.logger.info("WARNING: Not all inputs share same coordinate system.")
            for coordsys in set(coordsyss):
                self.logger.info("The following rasters have coordinate system %s:" % str(coordsys))
                self.logger.info([x for i, x in enumerate(paths) if coordsyss[i] == coordsys])

        if len(set(corners)) != 1:
            aligned = False
            self.logger.info("WARNING: Not all inputs share same extent.")
            for corner in set(corners):
                self.logger.info("The following rasters have lower left corner %s:" % str(corner))
                self.logger.info([x for i, x in enumerate(paths) if corners[i] == corner])

        if aligned:
            self.logger.info("Input rasters are aligned properly.")
        else:
            self.warning = True

    def fix_alignment(self, snap_raster, dir2new_condition):
        """Aligns all rasters according to cell size, coordinate system and extent of given raster.
        Args:
            snap_raster: raster used to set the cell size, snapping, and coordinate system of all other rasters.
            dir2new_condition: directory containing all rasters to be aligned.
        """
        for root, subdir, filenames in os.walk(dir2new_condition):
            for filename in filenames:
                if filename.endswith(".tif"):
                    misaligned_raster = os.path.join(root, filename)

                    resample_ras = misaligned_raster

                    # if depth or velocity, set null values to zero for resampling interpolation accuracy
                    if misaligned_raster.startswith("h") or misaligned_raster.startswith("u"):
                        resample_ras = Con(IsNull(misaligned_raster), 0, misaligned_raster)

                    # if velocity angle, convert to vx and vy for smooth resampling
                    if misaligned_raster.startswith("va"):
                        va_x = Sin(misaligned_raster)
                        va_y = Cos(misaligned_raster)
                        resample_ras = [va_x, va_y]

                    # set selected raster as environment snap raster and output coordinate system
                    arcpy.env.snapRaster = snap_raster
                    arcpy.env.outputCoordinateSystem = Raster(snap_raster).spatialReference
                    # resample using selected raster as cell size, bilinear interpolation method
                    if type(resample_ras) == list:
                        for i, ras in enumerate(resample_ras):
                            out_ras_path = os.path.join(self.cache, "resample_ras%i.tif" % i)
                            arcpy.Resample_management(ras, out_ras_path, cell_size=snap_raster, resampling_type="BILINEAR")
                    else:
                        out_ras_path = os.path.join(self.cache, "resample_ras.tif")
                        arcpy.Resample_management(resample_ras, out_ras_path, cell_size=snap_raster, resampling_type="BILINEAR")

                    # if velocity angle, convert components back to angle
                    if misaligned_raster.startswith("va"):
                        out_ras_path = os.path.join(self.cache, "resample_ras.tif")
                        x_ras = Raster(os.path.join(self.cache, "resample_ras1.tif"))
                        y_ras = Raster(os.path.join(self.cache, "resample_ras2.tif"))
                        # upper half of plane
                        temp_ras1 = Con(y_ras > 0, ATan(x_ras/y_ras) * 180/np.pi)
                        # 4th quadrant
                        temp_ras2 = Con(x_ras > 0 & y_ras < 0, 180 + ATan(x_ras/y_ras) * 180/np.pi, temp_ras1)
                        # 3rd quadrant
                        temp_ras3 = Con(x_ras < 0 & y_ras < 0, -(180 + ATan(x_ras/y_ras) * 180/np.pi), temp_ras2)
                        # if x = 0 and y < 0, set to 180
                        temp_ras4 = Con(x_ras == 0 & y_ras < 0, 180, temp_ras3)
                        # if y = 0, set to 90 or -90  depending on sign of x
                        temp_ras5 = Con(y_ras == 0 & x_ras > 0, 90, temp_ras4)
                        temp_ras6 = Con(y_ras == 0 & x_ras < 0, -90, temp_ras5)
                        # if x = 0 and y = 0, cannot get average angle
                        temp_ras7 = Con(y_ras == 0 & x_ras == 0, np.nan, temp_ras6)
                        temp_ras7.save(out_ras_path)
                    # overwrite misaligned raster with resampled raster
                    out_ras = Raster(out_ras_path)
                    out_ras.save(misaligned_raster)

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = ConditionCreator (%s)" % os.path.dirname(__file__))
        print(dir(self))

