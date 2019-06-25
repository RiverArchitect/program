try:
    import sys, os, logging
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
        self.condition = dir2condition.strip("\\").strip("/").split("\\")[-1].split("/")[-1]
        self.dir2condition = dir2condition  # string of the condition to be created
        self.error = False
        self.logger = logging.getLogger("logfile")

    def create_discharge_table(self):
        try:
            flow_table = cMT.MakeFlowTable(self.dir2condition.split("/")[-1].split("\\")[-1], "q_return")
            return flow_table.make_condition_xlsx()
        except:
            self.error = True

    def create_flow_duration_table(self, input_flow_xlsx, aquatic_ambiance):
        try:
            condition = self.dir2condition.split("/")[-1].split("\\")[-1]
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
        src_condition = dir2src_condition.strip("\\").strip("/").split("\\")[-1].split("/")[-1]
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

    def make_d2w(self, h_ras_dir, dem_ras_dir):
        wle = cWL.WLE(self.dir2condition)
        try:
            self.error = wle.calculate_d2w(h_ras_dir, dem_ras_dir)
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

    def make_raster_name(self, input_raster_name, type_id):
        if type_id == "dem":
            return "dem.tif"
        if type_id == "back":
            return "back.tif"
        if type_id == "fill":
            return "fill.tif"
        if (type_id == "h") or (type_id == "u"):
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
        target_raster_name = self.make_raster_name(str(dir2inp_ras).split("\\")[-1].split("/")[-1], type_id)
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
        if not no_data:
            self.logger.info("     * converting NoData to 0 ... ")
            ras4tif = Con((IsNull(input_ras) == 1), (IsNull(input_ras) * 0), Float(input_ras))
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
            self.logger.info("ERROR: The selected folder does not contain any depth/velocity Raster containing the defined string.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = ConditionCreator (%s)" % os.path.dirname(__file__))
        print(dir(self))

