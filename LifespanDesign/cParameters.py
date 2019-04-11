# !/usr/bin/python
try:
    from cReadInpLifespan import *
except:
    print("ExceptionERROR: Cannot find package files (classes_read_inp.py).")

try:
    import arcpy
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy")


class CHSI:
    # This class stores all information about combined habitat suitability rasters.

    def __init__(self, condition):
        input_info = Info("chsi")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
        except:
            self.raster = ""


class DEM:
    # This class stores all information about DEM rasters.

    def __init__(self, condition):
        input_info = Info("dem")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class DEMdet:
    # This class stores all information about detrended DEM rasters.

    def __init__(self, condition):
        input_info = Info("det")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class DoD:
    # This class stores all information about the topographic change rasters.
    # Instantiate an object by: myDoD = DoD() in feet

    def __init__(self, condition):
        input_info = Info("dod")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster_scour = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster_scour = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster_scour = ""
        try:
            self.raster_fill = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster_fill = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster_fill = ""


class FlowDepth:
    # This class stores all information about flow depth rasters.

    def __init__(self, condition):
        input_info = Info("h")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = True
        self.rasters = []
        for ras_name in self.raster_names:
            ras_act = self.raster_path + self.condition + "\\" + ras_name
            if arcpy.Exists(ras_act) or os.path.isfile(ras_act + '.tif'):
                try:
                    self.rasters.append(arcpy.Raster(ras_act + '.tif'))
                except:
                    self.rasters.append(arcpy.Raster(ras_act))
            else:
                self.rasters.append("")


class FlowVelocity:
    # This class stores all information about flow velocity rasters.
    def __init__(self, condition):
        input_info = Info("u")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.rasters = []
        for ras_name in self.raster_names:
            ras_act = self.raster_path + self.condition + "\\" + ras_name
            if arcpy.Exists(ras_act) or os.path.isfile(ras_act + '.tif'):
                try:
                    self.rasters.append(arcpy.Raster(ras_act + '.tif'))
                except:
                    self.rasters.append(arcpy.Raster(ras_act))
            else:
                self.rasters.append("")


class GrainSizes:
    def __init__(self, condition):
        input_info = Info("grains")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class MU:
    # This class stores all information about Morphological Units rasters and thresholds.
    def __init__(self, condition):
        input_info = Info("mu")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.mu_dict = {"agriplain": 4, "backswamp": 5, "bank": 6, "chute": 8, "cutbank": 9, "fast glide": 10,
                        "flood runner": 11, "floodplain": 12, "high floodplain": 13, "hillside": 14, "bedrock": 14,
                        "island high floodplain": 15, "island-floodplain": 16, "lateral bar": 17, "levee": 18,
                        "medial bar": 19, "mining pit": 20, "point bar": 21, "pond": 22, "pool": 23, "riffle": 24,
                        "riffle transition": 25, "run": 26, "slackwater": 27, "slow glide": 28, "spur dike": 29,
                        "swale": 30, "tailings": 31, "terrace": 32, "tributary channel": 33, "tributary delta": 34,
                        "in-channel bar": 35}
        self.raster_names = ["mu"]
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class SideChannelDelineation:
    # This class stores all information about depth to groundwater table rasters.

    def __init__(self, condition):
        input_info = Info("sidech")
        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class WaterTable:
    # This class stores all information about depth to groundwater table rasters.

    def __init__(self, condition):
        input_info = Info("d2w")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class Wildcard:
    # This class stores all information about depth to groundwater table rasters.

    def __init__(self, condition):
        input_info = Info("wild")

        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        self.raster_names = input_info.raster_read()
        self.flood_dependent = False
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
