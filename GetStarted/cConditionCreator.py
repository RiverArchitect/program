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
        self.cache = os.path.join(config.dir2conditions, ".cache")
        self.error = False
        self.warning = False
        self.logger = logging.getLogger("logfile")
        fGl.chk_dir(self.cache)

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
            flows.make_disc_freq(condition)
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
            if not str(os.path.splitext(input_raster_name)[0]).startswith(type_id):
                return type_id + os.path.splitext(input_raster_name)[0] + ".tif"
            else:
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
        self.logger.info("     * " + dir2inp_ras)
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
            self.logger.info("     * eliminating 0 data ... ")
            ras4tif = Con(Float(input_ras) > 0.000, Float(input_ras))

        else:
            ras4tif = input_ras
        self.logger.info("     * saving " + self.dir2condition + target_raster_name)
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

    @staticmethod
    def check_alignment_pair(ras1, ras2):
        """Checks if a pair of rasters are aligned."""
        cell_sizes = []
        coordsyss = []
        mod_corners = []
        cells_match = True
        coords_match = True
        corners_match = True
        for path in [ras1, ras2]:
            cell_size_x = float(arcpy.GetRasterProperties_management(path, 'CELLSIZEX')[0])
            cell_size_y = float(arcpy.GetRasterProperties_management(path, 'CELLSIZEY')[0])
            cell_size = str(cell_size_x) + ', ' + str(cell_size_y)
            cell_sizes.append(cell_size)

            extent = arcpy.Describe(path).Extent

            coordsys = extent.spatialReference.name
            coordsyss.append(coordsys)

            xmin = extent.XMin
            ymin = extent.YMin
            mod_corners.append((xmin % cell_size_x, ymin % cell_size_y))
        if len(set(cell_sizes)) != 1:
            cells_match = False
        if len(set(coordsyss)) != 1:
            coords_match = False
        if len(set(mod_corners)) != 1:
            corners_match = False
        return cells_match, coords_match, corners_match

    def check_alignment(self, dir2new_condition):
        """Checks if all inputs in directory have same cell size/alignment."""
        self.logger.info("Checking alignment of input files...")
        paths = []
        cell_sizes = []
        coordsyss = []
        mod_corners = []
        for root, subdir, filenames in os.walk(dir2new_condition):
            for filename in filenames:
                if filename.endswith(".tif"):
                    path = os.path.join(root, filename)
                    paths.append(path)

                    cell_size_x = float(arcpy.GetRasterProperties_management(path, 'CELLSIZEX')[0])
                    cell_size_y = float(arcpy.GetRasterProperties_management(path, 'CELLSIZEY')[0])
                    cell_size = str(cell_size_x) + ', ' + str(cell_size_y)
                    cell_sizes.append(cell_size)

                    extent = arcpy.Describe(path).Extent

                    coordsys = extent.spatialReference.name
                    coordsyss.append(coordsys)

                    xmin = extent.XMin
                    ymin = extent.YMin
                    mod_corners.append((xmin % cell_size_x, ymin % cell_size_y))

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

        if len(set(mod_corners)) != 1:
            aligned = False
            self.logger.info("WARNING: Not all inputs share same extent.")
            for corner in set(mod_corners):
                self.logger.info("The following rasters have lower left corner (modulo cell size) %s:" % str(corner))
                self.logger.info([x for i, x in enumerate(paths) if mod_corners[i] == corner])

        if aligned:
            self.logger.info("Input rasters are aligned properly.")
        else:
            self.warning = True

    def fix_alignment(self, snap_raster):
        """Aligns all rasters according to cell size, coordinate system and extent of given raster.
        Args:
            snap_raster: raster used to set the cell size, snapping, and coordinate system of all other rasters.
        """
        self.logger.info("Aligning input rasters to %s..." % snap_raster)
        error = False
        arcpy.env.overwriteOutput = True
        # sorted so we handle h before u and va for proper null/zero depth handling
        for root, dirs, filenames in sorted(os.walk(self.dir2condition)):
            for filename in filenames:
                if filename.endswith(".tif"):
                    try:
                        misaligned_raster = os.path.join(root, filename)
                        
                        # check if raster needs to be aligned.
                        cells_match, coords_match, corners_match = self.check_alignment_pair(snap_raster, misaligned_raster)

                        if not (cells_match and coords_match and corners_match):
                            resample_ras = misaligned_raster
                            self.logger.info(" * aligning %s..." % str(misaligned_raster))
                            # if depth or velocity, set null values to zero for resampling interpolation accuracy
                            if filename.startswith("h") or filename.startswith("u"):
                                resample_ras = Con(IsNull(misaligned_raster), 0, misaligned_raster)

                            # if velocity angle, convert to x and y for smooth resampling
                            if filename.startswith("va"):
                                va_x = Sin(Raster(misaligned_raster) * np.pi/180)
                                va_y = Cos(Raster(misaligned_raster) * np.pi/180)
                                resample_ras = [va_x, va_y]

                            # set selected raster as environment snap raster and output coordinate system
                            arcpy.env.snapRaster = snap_raster
                            arcpy.env.outputCoordinateSystem = Raster(snap_raster).spatialReference
                            # get cell size
                            cell_size_x = arcpy.GetRasterProperties_management(snap_raster, 'CELLSIZEX')[0]
                            cell_size_y = arcpy.GetRasterProperties_management(snap_raster, 'CELLSIZEY')[0]
                            cell_size = str(cell_size_x) + ' ' + str(cell_size_y)

                            # resample using selected raster as cell size, bilinear interpolation method
                            if filename.startswith("va"):
                                for i, ras in enumerate(resample_ras):
                                    out_ras_path = os.path.join(self.cache, "resample_ras%i.tif" % i)
                                    if cells_match and corners_match:
                                        # just change coordinate system
                                        arcpy.Resample_management(ras, out_ras_path, cell_size=cell_size,
                                                                  resampling_type="NEAREST")
                                    else:
                                        arcpy.Resample_management(ras, out_ras_path, cell_size=cell_size,
                                                                  resampling_type="BILINEAR")
                            else:
                                out_ras_path = os.path.join(self.cache, "resample_ras.tif")
                                if cells_match and corners_match:
                                    # just change coordinate system
                                    arcpy.Resample_management(resample_ras, out_ras_path, cell_size=cell_size,
                                                              resampling_type="NEAREST")
                                else:
                                    arcpy.Resample_management(resample_ras, out_ras_path, cell_size=cell_size,
                                                              resampling_type="BILINEAR")

                            # if velocity angle, convert components back to angle
                            if filename.startswith("va"):
                                out_ras_path = os.path.join(self.cache, "resample_ras.tif")
                                x_ras = Raster(os.path.join(self.cache, "resample_ras0.tif"))
                                y_ras = Raster(os.path.join(self.cache, "resample_ras1.tif"))

                                # convert vx and vy to array
                                vx_mat = arcpy.RasterToNumPyArray(x_ras, nodata_to_value=np.nan)
                                vy_mat = arcpy.RasterToNumPyArray(y_ras, nodata_to_value=np.nan)
                                # compute vector angles
                                va_mat = np.empty(np.shape(vx_mat))
                                va_mat[:] = np.nan
                                for i in range(len(vx_mat)):
                                    for j in range(len(vx_mat[i])):
                                        va_mat[i, j] = fGl.va_from_xy(vx_mat[i, j], vy_mat[i, j])
                                # save va raster
                                ref_pt = arcpy.Point(x_ras.extent.XMin, x_ras.extent.YMin)
                                va_ras = arcpy.NumPyArrayToRaster(va_mat, lower_left_corner=ref_pt,
                                                                  x_cell_size=float(cell_size_x),
                                                                  y_cell_size=float(cell_size_y),
                                                                  value_to_nodata=np.nan)
                                va_ras.save(out_ras_path)
                                del x_ras, y_ras  # clean up

                            # convert zero depths back to null
                            if filename.startswith("h"):
                                h = SetNull(out_ras_path, out_ras_path, "VALUE <= 0")
                                h.save(out_ras_path)

                            # convert velocity and velocity angle back to null where depth is null
                            if filename.startswith("u") or filename.startswith("va"):
                                try:
                                    h = Raster(os.path.join(root, filename.replace('u', 'h').replace('va', 'h')))
                                except:
                                    self.logger.info("WARNING: Invalid alignment Raster name (%s)." % str(os.path.join(root, filename.replace('u', 'h').replace('va', 'h'))))
                                    continue
                                out_ras = SetNull(h, out_ras_path, "VALUE <= 0")
                                out_ras.save(out_ras_path)

                            # overwrite misaligned raster with resampled raster
                            out_ras = Raster(out_ras_path)
                            out_ras.save(misaligned_raster)
                    except Exception as e:
                        self.logger.info(e)
                        self.logger.info("WARNING: Failed to align input raster %s." % filename)

        self.clean_up()
        if not error:
            self.logger.info("Aligned successfully.")
            return 0
        else:
            self.logger.info("Finished alignment with errors (see logfile).")
            return -1

    def clean_up(self):
        try:
            self.logger.info(" * Cleaning up ...")
            fGl.clean_dir(self.cache)
            fGl.rm_dir(self.cache)
            self.logger.info(" * OK")
        except:
            self.logger.info(" * Failed to clean up .cache folder.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = ConditionCreator (%s)" % os.path.dirname(__file__))
        print(dir(self))

