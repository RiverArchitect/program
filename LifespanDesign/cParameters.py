# !/usr/bin/python
try:
    from cReadInpLifespan import *
except:
    print("ExceptionERROR: Cannot find package files (classes_read_inp.py).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cInputOutput as cIO
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class ParameterContainer:
    def __init__(self, condition, par_id):
        self.logger = logging.getLogger("logfile")
        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = config.dir2conditions
        input_info = Info(condition, par_id)
        self.raster_names = input_info.raster_read()
        self.flood_dependency_dict = {"chsi": False, "d2w": False, "dem": False, "det": False, "dod": False,
                                      "grains": False, "h": True, "mu": False, "sidech": False, "u": True,
                                      "wild": False}
        try:
            self.flood_dependent = self.flood_dependency_dict[par_id]
        except:
            self.flood_dependent = False


class CHSI(ParameterContainer):
    # This class stores all information about combined habitat suitability Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "chsi")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class DEM(ParameterContainer):
    # This class stores all information about DEM Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "dem")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class DEMdet(ParameterContainer):
    # This class stores all information about detrended DEM Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "det")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class DoD(ParameterContainer):
    # This class stores all information about the topographic change Rasters
    # Instantiate an object by: myDoD = DoD() in feet
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "dod")
        try:
            self.raster_scour = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster_scour = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster_scour = ""
        try:
            self.raster_fill = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster_fill = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster_fill = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class FlowDepth(ParameterContainer):
    # This class stores all information about flow depth Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "h")
        self.rasters = []
        for ras_name in self.raster_names:
            ras_act = self.raster_path + self.condition + "\\" + ras_name.split(".")[0]
            if arcpy.Exists(ras_act) or os.path.isfile(ras_act + '.tif'):
                try:
                    self.rasters.append(arcpy.Raster(str(ras_act + '.tif')))
                except:
                    self.rasters.append(arcpy.Raster(ras_act))
            else:
                self.rasters.append("")
                self.logger.info("ERROR: Could not load %s." % str(ras_act + '.tif'))
        self.logger.info(
            "      * Source(s): " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class FlowVelocity(ParameterContainer):
    # This class stores all information about flow velocity Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "u")
        self.rasters = []
        for ras_name in self.raster_names:
            ras_act = self.raster_path + self.condition + "\\" + ras_name.split(".")[0]
            if arcpy.Exists(ras_act) or os.path.isfile(ras_act + '.tif'):
                try:
                    self.rasters.append(arcpy.Raster(ras_act + '.tif'))
                except:
                    self.rasters.append(arcpy.Raster(ras_act))
            else:
                self.rasters.append("")
                self.logger.info("ERROR: Could not load %s." % str(ras_act + '.tif'))
        self.logger.info(
            "      * Source(s): " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class GrainSizes(ParameterContainer):
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "grains")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class MU(ParameterContainer):
    # This class stores all information about Morphological Units Rasters and thresholds.
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "mu")
        self.mu_dict = {}
        self.read_mus()

        self.raster_names = ["mu"]  # overwrites ParameterContainer.raster_names
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))

    def read_mus(self):
        mu_xlsx = cIO.Read(config.xlsx_mu)
        for i in range(6, 44):
            # loop over all mu-rows
            if not (i == 23):
                # jump over floodplain table headers
                mu_type = str(mu_xlsx.ws["D" + str(i)].value)
                try:
                    mu_ID = int(mu_xlsx.ws["E" + str(i)].value)
                except:
                    continue
                if not (mu_type.lower() == "none"):
                    try:
                        float(mu_xlsx.ws["F" + str(i)].value)
                        float(mu_xlsx.ws["G" + str(i)].value)
                        float(mu_xlsx.ws["H" + str(i)].value)
                        float(mu_xlsx.ws["I" + str(i)].value)
                        self.mu_dict.update({mu_type: mu_ID})  # add mu name and ID to dict
                        self.logger.info(" * added %s." % str(mu_type))
                    except:
                        self.logger.info(" * omitted {0} (no depth / velocity thresholds provided in row {1}).".format(mu_type, str(i)))
        mu_xlsx.close_wb()


class SideChannelDelineation(ParameterContainer):
    # This class stores all information about depth to water table Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "sidech")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class WaterTable(ParameterContainer):
    # This class stores all information about depth to water table Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "d2w")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))


class Wildcard(ParameterContainer):
    # This class stores all information about depth to water table Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "wild")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0].split(".")[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
        self.logger.info(
            "      * Source: " + self.raster_path + self.condition + "\\" + " --".join(self.raster_names))
